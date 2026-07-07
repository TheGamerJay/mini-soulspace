"""The Soul Orchestra pipeline — Phase 4.0 integration.

Wires every completed node into one verified flow (Rule 21 — no feature may
bypass the Orchestra):

    Input Receiver → Meaning & Intent → Guardian → Memory Retriever →
    Reflection Planner → Context Builder → Prompt Builder → Mini Engine →
    Quality Checker → Memory Writer (+ Memory Intelligence) → Conversation
    Composer → frontend

Guarantees:
- Every request gets an **Orchestra Trace ID** that follows it through every node.
- Every node emits structured logs (started/completed/failed/skipped, timing,
  reason) — **never journal content**.
- **Failure recovery**: any node failure stops safely and returns a structured
  failure package; the Orchestra never crashes, never corrupts memories, and the
  diary page (saved before the Orchestra runs) is never lost.
- Crisis short-circuit: the Guardian's crisis decision routes to deterministic
  safety templates (never free generation), still verified by the Quality
  Checker and delivered only through the Composer.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.memory import SoulMemory
from app.models.user import User
from app.orchestra import composer as composer_node
from app.orchestra import input_receiver
from app.orchestra import meaning as meaning_node
from app.orchestra import mini as mini_node
from app.orchestra import quality as quality_node
from app.orchestra import writer as writer_node
from app.orchestra.composer.schemas import ConversationPackage, DeliveryStatus, FrontendEvent
from app.orchestra.context import build as context_build
from app.orchestra.guardian import evaluate as guardian_evaluate
from app.orchestra.guardian.schemas import GuardianCategory
from app.orchestra.intelligence import DbIntelligenceStore, MemorySource
from app.orchestra.intelligence import assess as intelligence_assess
from app.orchestra.memory import DbMemorySource
from app.orchestra.memory import retrieve as memory_retrieve
from app.orchestra.mini.schemas import CandidateResponse, TokenCounts
from app.orchestra.planner import plan as planner_plan
from app.orchestra.prompt import build as prompt_build
from app.orchestra.quality.schemas import QualityStatus
from app.orchestra.writer import DbMemoryStore

logger = get_logger("app.orchestra.pipeline")

DEFAULT_ORCHESTRA_CONFIG_PATH = Path(__file__).with_name("orchestra.json")


class OrchestraConfig(BaseModel):
    """Pipeline configuration — loaded from orchestra.json, nothing hardcoded."""

    model_config = ConfigDict(frozen=True)

    log_execution: bool = True
    trace_requests: bool = True
    save_node_metrics: bool = True
    allow_parallel_nodes: bool = False
    performance_metrics: bool = True
    debug_mode: bool = False
    quality_retry_limit: int = 1


def load_orchestra_config(path: Path | str = DEFAULT_ORCHESTRA_CONFIG_PATH) -> OrchestraConfig:
    """Load pipeline config; fall back to safe defaults (never crash)."""

    try:
        return OrchestraConfig(**json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        logger.warning("orchestra.json could not be loaded; using defaults")
        return OrchestraConfig()


class NodeMetric(BaseModel):
    model_config = ConfigDict(frozen=True)

    node: str
    status: str  # completed | failed | skipped
    ms: int
    reason: str = ""


class OrchestraOutcome(BaseModel):
    """What one full Orchestra run produced (package + observability)."""

    model_config = ConfigDict(frozen=True)

    trace_id: uuid.UUID
    delivered: bool
    package: ConversationPackage
    total_ms: int
    metrics: tuple[NodeMetric, ...] = Field(default_factory=tuple)
    slowest_node: str | None = None


# Deterministic crisis templates (Safety Rules) — never free generation. Wording
# intentionally passes the Quality Checker's crisis-referral requirements.
_CRISIS_TEMPLATES: dict[GuardianCategory, str] = {
    GuardianCategory.SELF_HARM_RISK: (
        "I'm really glad you trusted this page with something so heavy, and I "
        "want you to be safe. I'm an AI companion, not a crisis service — "
        "please reach out right now to your local emergency number or a crisis "
        "line, or someone you trust. You don't have to face this alone, and "
        "people are trained to help."
    ),
    GuardianCategory.HARM_TO_OTHERS: (
        "This sounds serious, and safety comes first — for you and for anyone "
        "else involved. Please reach out to your local emergency services or a "
        "professional who can help right now. I'm an AI companion and can't "
        "handle this safely on my own. You're not alone in this."
    ),
    GuardianCategory.EMERGENCY: (
        "This may need real help right away. Please call your local emergency "
        "number or reach out to someone you trust or a professional now. I'm an "
        "AI companion, not an emergency service — you're not alone."
    ),
}


class _Run:
    """One pipeline execution: trace, metrics, structured logging."""

    def __init__(self, trace_id: uuid.UUID, config: OrchestraConfig):
        self.trace_id = trace_id
        self.config = config
        self.metrics: list[NodeMetric] = []
        self.started = time.perf_counter()

    def _log(self, node: str, status: str, ms: int, reason: str) -> None:
        if self.config.log_execution:
            # Structured, content-free: trace/node/status/timing/reason only.
            logger.info(
                "orchestra trace=%s node=%s status=%s ms=%d reason=%s",
                self.trace_id, node, status, ms, reason or "-",
            )

    def record(self, node: str, status: str, ms: int, reason: str = "") -> None:
        if self.config.save_node_metrics:
            self.metrics.append(NodeMetric(node=node, status=status, ms=ms, reason=reason))
        self._log(node, status, ms, reason)

    def run(self, node: str, fn):
        start = time.perf_counter()
        try:
            result = fn()
        except Exception:
            self.record(node, "failed", int((time.perf_counter() - start) * 1000))
            raise
        self.record(node, "completed", int((time.perf_counter() - start) * 1000))
        return result

    def skip(self, node: str, reason: str) -> None:
        self.record(node, "skipped", 0, reason)

    def outcome(self, package: ConversationPackage) -> OrchestraOutcome:
        total_ms = int((time.perf_counter() - self.started) * 1000)
        slowest = None
        if self.config.performance_metrics and self.metrics:
            slowest = max(self.metrics, key=lambda m: m.ms).node
        return OrchestraOutcome(
            trace_id=self.trace_id,
            delivered=package.status == DeliveryStatus.DELIVERED,
            package=package,
            total_ms=total_ms,
            metrics=tuple(self.metrics),
            slowest_node=slowest,
        )


def _failure_package(request_id: uuid.UUID, node: str, reason: str) -> ConversationPackage:
    """Structured infrastructure-failure package (stop safely, never crash).

    Conversational failure packages come from the Composer; this covers failures
    *before* composition is possible. Same shape, same guarantees: no unsafe
    text ever reaches the frontend, and the saved diary page is untouched.
    """

    return ConversationPackage(
        request_id=request_id,
        status=DeliveryStatus.NOT_DELIVERED,
        text="",
        frontend_events=(FrontendEvent(name="ConversationNotDelivered", payload={"failed_node": node}),),
        metadata={"failure_reason": reason, "failed_node": node},
    )


def _crisis_candidate(request_id: uuid.UUID, category: GuardianCategory, confidence: float) -> CandidateResponse:
    return CandidateResponse(
        request_id=request_id,
        service_name="guardian_safety",
        service_display_name="Mini Guardian",
        model_used="deterministic_template",
        response_text=_CRISIS_TEMPLATES[category],
        generation_time_ms=0,
        token_counts=TokenCounts(),
        finish_reason="template",
        confidence=confidence,
        metadata={"template": category.value},
    )


def run_orchestra(
    db: Session,
    user: User,
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    page_id: uuid.UUID,
    *,
    session_id: str | None = None,
    runtime=None,
    config: OrchestraConfig | None = None,
) -> OrchestraOutcome:
    """Execute the complete Orchestra for one saved page."""

    config = config or load_orchestra_config()
    trace_id = uuid.uuid4()
    run = _Run(trace_id, config)
    request_id = trace_id  # until the Input Receiver mints the request

    try:
        # 1. Input Receiver ----------------------------------------------------
        request = run.run(
            "input_receiver",
            lambda: input_receiver.build_orchestra_request(
                db, user, book_id, chapter_id, page_id,
                session_id=session_id,
                metadata={"trace_id": str(trace_id)} if config.trace_requests else {},
            ),
        )
        request_id = request.request_id

        # 2. Meaning & Intent --------------------------------------------------
        meaning = run.run("meaning_intent", lambda: meaning_node.analyze(request))

        # 3. Guardian ----------------------------------------------------------
        guardian = run.run("guardian", lambda: guardian_evaluate(request, meaning))

        # 4. Memory Retriever (honors the Guardian internally) ------------------
        retrieval = run.run(
            "memory_retriever",
            lambda: memory_retrieve(request, guardian, DbMemorySource(db)),
        )

        # 5. Reflection Planner ------------------------------------------------
        planner = run.run("reflection_planner", lambda: planner_plan(request, guardian, retrieval))

        # 6-8. Context → Prompt → Mini Engine (or crisis short-circuit) ---------
        if guardian.needs_crisis_template:
            run.skip("context_builder", "crisis_short_circuit")
            run.skip("prompt_builder", "crisis_short_circuit")
            run.skip("mini_engine", "crisis_short_circuit")
            candidate = _crisis_candidate(request.request_id, guardian.category, guardian.confidence)
            quality = run.run(
                "quality_checker",
                lambda: quality_node.check(candidate, guardian, planner, retrieval=retrieval, meaning=meaning),
            )
        else:
            context = run.run("context_builder", lambda: context_build(request, guardian, retrieval, planner))
            prompt = run.run("prompt_builder", lambda: prompt_build(context))
            candidate = run.run("mini_engine", lambda: mini_node.generate(prompt, runtime=runtime))
            quality = run.run(
                "quality_checker",
                lambda: quality_node.check(candidate, guardian, planner, retrieval=retrieval, meaning=meaning),
            )

            # Quality retry: regenerate fixable candidates, re-verify each time.
            retries = 0
            while quality.status == QualityStatus.NEEDS_RETRY and retries < config.quality_retry_limit:
                retries += 1
                candidate = run.run(f"mini_engine_retry_{retries}", lambda: mini_node.generate(prompt, runtime=runtime))
                quality = run.run(
                    f"quality_checker_retry_{retries}",
                    lambda: quality_node.check(candidate, guardian, planner, retrieval=retrieval, meaning=meaning),
                )

        # 9. Memory Writer + Memory Intelligence (never blocks delivery) --------
        memory_decision = None
        memory_intelligence = None
        if quality.status == QualityStatus.APPROVED:
            try:
                memory_decision = run.run(
                    "memory_writer",
                    lambda: writer_node.write(request, quality, guardian, meaning=meaning, store=DbMemoryStore(db)),
                )
                memory_id = memory_decision.metadata.get("memory_id")
                if memory_decision.store_memory and memory_id:
                    memory_row = db.get(SoulMemory, uuid.UUID(memory_id))
                    memory_intelligence = run.run(
                        "memory_intelligence",
                        lambda: intelligence_assess(
                            memory_decision, memory_row,
                            source=MemorySource.SOULDIARY,
                            evidence={"page_id": str(page_id), "trace_id": str(trace_id)},
                            store=DbIntelligenceStore(db),
                        ),
                    )
                else:
                    run.skip("memory_intelligence", memory_decision.reason)
            except Exception:
                # Memory problems must never block or corrupt the conversation.
                logger.warning("orchestra trace=%s memory stage failed; continuing", trace_id)
                memory_decision, memory_intelligence = None, None
        else:
            run.skip("memory_writer", f"quality_{quality.status.value}")
            run.skip("memory_intelligence", f"quality_{quality.status.value}")

        # 10. Conversation Composer — the only gateway to the frontend ----------
        package = run.run(
            "conversation_composer",
            lambda: composer_node.compose(
                request, quality, candidate,
                memory_decision=memory_decision,
                memory_intelligence=memory_intelligence,
            ),
        )
        return run.outcome(package)

    except Exception as exc:  # noqa: BLE001 — stop safely, never crash
        node = run.metrics[-1].node if run.metrics and run.metrics[-1].status == "failed" else "pipeline"
        reason = getattr(exc, "code", None) or type(exc).__name__
        logger.warning("orchestra trace=%s failed at node=%s reason=%s", trace_id, node, reason)
        return run.outcome(_failure_package(request_id, node, str(reason)))
