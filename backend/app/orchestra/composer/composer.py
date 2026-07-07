"""Conversation Composer — Orchestra node 10 (the frontend gateway).

Single responsibility: assemble the final user experience from approved
Orchestra results. It never generates or modifies responses, never touches
memory, never plans, never re-judges safety or quality. Deterministic — no AI.

Rule 20: the Composer is the single gateway between the Orchestra and the
frontend. Only APPROVED QualityResults are delivered; rejected / needs_retry
responses never reach the frontend — they become a structured failure package.
"""

from __future__ import annotations

from app.orchestra.composer.errors import ComposerError
from app.orchestra.composer.schemas import (
    ConversationPackage,
    DeliveryStatus,
    FrontendEvent,
    MemoryUpdate,
)
from app.orchestra.intelligence.schemas import MemoryIntelligenceResult
from app.orchestra.mini.schemas import CandidateResponse
from app.orchestra.quality.schemas import QualityResult, QualityStatus
from app.orchestra.schemas import OrchestraRequest
from app.orchestra.writer.schemas import MemoryDecision


def _memory_parts(
    decision: MemoryDecision | None, intelligence: MemoryIntelligenceResult | None
) -> tuple[tuple[MemoryUpdate, ...], tuple[FrontendEvent, ...]]:
    """Package what the memory system did this turn (structured, not displayed)."""

    if decision is None or not decision.store_memory:
        return (), ()
    op = decision.metadata.get("op", "create")
    update = MemoryUpdate(
        op=op,
        memory_type=decision.memory_type.value if decision.memory_type else None,
        importance=decision.importance.value if decision.importance else None,
        title=decision.title,
        confidence=intelligence.confidence if intelligence else decision.confidence,
        verification_status=intelligence.verification_status.value if intelligence else None,
    )
    event = FrontendEvent(
        name="MemoryUpdated" if op == "update" else "MemoryStored",
        payload={"memory_type": update.memory_type, "op": op},
    )
    return (update,), (event,)


def compose(
    request: OrchestraRequest,
    quality: QualityResult,
    candidate: CandidateResponse | None = None,
    *,
    memory_decision: MemoryDecision | None = None,
    memory_intelligence: MemoryIntelligenceResult | None = None,
) -> ConversationPackage:
    """Assemble the final ConversationPackage for the frontend."""

    if not isinstance(request, OrchestraRequest):
        raise ComposerError([{"field": "request", "code": "invalid_input", "message": "Expected an OrchestraRequest."}])
    if not isinstance(quality, QualityResult):
        raise ComposerError([{"field": "quality", "code": "invalid_input", "message": "Expected a QualityResult."}])

    # Never bypass the Quality Checker: anything not approved never reaches the
    # frontend — return a structured failure package instead.
    if quality.status != QualityStatus.APPROVED:
        return ConversationPackage(
            request_id=request.request_id,
            status=DeliveryStatus.NOT_DELIVERED,
            text="",
            frontend_events=(
                FrontendEvent(
                    name="ConversationNotDelivered",
                    payload={"quality_status": quality.status.value},
                ),
            ),
            metadata={
                "failure_reason": quality.status.value,
                "violation_codes": [v.code for v in quality.violations],
                "retry_allowed": quality.retry_allowed,
            },
        )

    if not isinstance(candidate, CandidateResponse):
        raise ComposerError(
            [{"field": "candidate", "code": "missing_candidate", "message": "Approved delivery requires a CandidateResponse."}]
        )

    memory_updates, memory_events = _memory_parts(memory_decision, memory_intelligence)

    return ConversationPackage(
        request_id=request.request_id,
        status=DeliveryStatus.DELIVERED,
        # Exactly as approved — never rewritten, paraphrased, or regenerated.
        text=candidate.response_text,
        memory_updates=memory_updates,
        frontend_events=(
            FrontendEvent(name="ConversationDelivered", payload={"service": candidate.service_display_name}),
            *memory_events,
        ),
        metadata={
            "service": candidate.service_name,
            "generation_time_ms": candidate.generation_time_ms,
            "quality_confidence": quality.confidence,
        },
    )
