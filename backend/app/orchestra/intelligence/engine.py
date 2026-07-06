"""Memory Intelligence Engine — manages memory *quality* over time.

Single responsibility: keep existing memories accurate, trustworthy,
explainable, verifiable, and able to evolve. It never retrieves memories for
reflection, generates anything, calls the Mini Engine, decides whether memories
should exist (that is the Memory Writer's job), or delivers responses.
Deterministic — **no AI**.

Rule 19: every memory must be explainable (confidence + evidence + source +
provenance). The user is the final authority; corrections permanently replace
outdated information and never resurface.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.memory import SoulMemory, SoulMemoryVersion
from app.orchestra.intelligence.errors import MemoryIntelligenceError
from app.orchestra.intelligence.schemas import (
    IntelligenceConfig,
    MemoryIntelligenceResult,
    MemorySource,
    NextAction,
    VerificationStatus,
)
from app.orchestra.intelligence.store import IntelligenceStore
from app.orchestra.writer.schemas import MemoryDecision

DEFAULT_CONFIG_PATH = Path(__file__).with_name("memory_intelligence.json")

# Sources that come directly from the user's own explicit data entry.
_USER_AUTHORED = {MemorySource.SIGNUP_FORM, MemorySource.MANUAL_USER_ENTRY}

# Deterministic statement-strength tiers (evidence-backed, never guessed).
_EXPLICIT = (
    "my favorite", "my birthday", "i was born", "my goal is", "my name is",
    "i live in", "i am allergic", "it's now", "it is now", "no. it's", "no, it's",
)
_STRONG = ("i usually", "i often", "i always", "i typically", "i tend to", "most of the time")
_CASUAL = ("looks nice", "seems nice", "maybe", "i guess", "kind of", "sort of", "might be")


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> IntelligenceConfig:
    """Load configurable thresholds (no thresholds are hardcoded)."""

    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise MemoryIntelligenceError(
            [{"field": "config", "code": "missing_config", "message": "memory_intelligence.json could not be loaded."}]
        )
    return IntelligenceConfig(**raw)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def score_confidence(statement: str, source: MemorySource) -> tuple[float, str]:
    """Deterministic confidence from statement strength + source. Never guessed —
    the returned reason names the evidence tier."""

    if source in _USER_AUTHORED:
        return 1.0, f"user-authored via {source.value}"
    low = (statement or "").lower()
    if any(m in low for m in _CASUAL):
        return 0.40, "casual mention"
    if any(m in low for m in _STRONG):
        return 0.80, "strong implication"
    if any(m in low for m in _EXPLICIT):
        return 0.99, "explicit user statement"
    return 0.60, "unclassified statement strength"


def _status_and_action(
    confidence: float, source: MemorySource, config: IntelligenceConfig
) -> tuple[VerificationStatus, NextAction]:
    if source in _USER_AUTHORED:
        return VerificationStatus.VERIFIED, NextAction.NONE
    if confidence < config.low_confidence_threshold:
        status = VerificationStatus.NEEDS_VERIFICATION if config.verification_enabled else VerificationStatus.UNVERIFIED
        return status, NextAction.MONITOR
    if confidence < config.needs_verification_threshold:
        status = VerificationStatus.NEEDS_VERIFICATION if config.verification_enabled else VerificationStatus.UNVERIFIED
        return status, NextAction.SCHEDULE_VERIFICATION
    return VerificationStatus.UNVERIFIED, NextAction.NONE


def _result(memory: SoulMemory, **overrides) -> MemoryIntelligenceResult:
    defaults: dict[str, Any] = dict(
        memory_id=memory.id,
        confidence=memory.confidence,
        confidence_reason="",
        memory_source=MemorySource(memory.source),
        evidence=json.loads(memory.evidence) if memory.evidence else {},
        verification_status=VerificationStatus(memory.verification_status),
        last_verified_at=memory.last_verified_at,
        last_updated_at=memory.updated_at,
        previous_version=memory.version - 1 if memory.version > 1 else None,
        next_action=NextAction.NONE,
        metadata={},
    )
    defaults.update(overrides)
    return MemoryIntelligenceResult(**defaults)


def assess(
    decision: MemoryDecision,
    memory: SoulMemory,
    *,
    source: MemorySource,
    evidence: dict[str, Any],
    store: IntelligenceStore,
    config: IntelligenceConfig | None = None,
) -> MemoryIntelligenceResult:
    """Stamp a newly written/updated memory with provenance + open its history."""

    if not isinstance(decision, MemoryDecision):
        raise MemoryIntelligenceError([{"field": "decision", "code": "invalid_input", "message": "Expected a MemoryDecision."}])
    if not isinstance(memory, SoulMemory):
        raise MemoryIntelligenceError([{"field": "memory", "code": "invalid_input", "message": "Expected a SoulMemory."}])
    if not evidence:
        raise MemoryIntelligenceError([{"field": "evidence", "code": "missing_evidence", "message": "No memory exists without evidence."}])

    config = config or load_config()
    confidence, reason = score_confidence(memory.summary, source)
    confidence = max(config.minimum_confidence, min(1.0, confidence))
    status, action = _status_and_action(confidence, source, config)

    evidence = {**evidence, "reason_stored": decision.reason, "stored_at": _now().isoformat()}
    verified_at = _now() if status == VerificationStatus.VERIFIED else None
    store.stamp(
        memory,
        confidence=confidence,
        source=source.value,
        evidence=json.dumps(evidence),
        verification_status=status.value,
        last_verified_at=verified_at,
    )
    op = decision.metadata.get("op", "create")
    store.record_version(memory, reason=op, author="system", is_outdated=False)

    return _result(
        memory,
        confidence=confidence,
        confidence_reason=reason,
        memory_source=source,
        evidence=evidence,
        verification_status=status,
        last_verified_at=verified_at,
        next_action=NextAction.UPDATED if op == "update" else action,
        metadata={"op": op, "version": memory.version},
    )


def apply_decay(
    memory: SoulMemory, *, store: IntelligenceStore, config: IntelligenceConfig | None = None, now: datetime | None = None
) -> MemoryIntelligenceResult:
    """Slowly lower confidence with age. The memory itself is never deleted."""

    if not isinstance(memory, SoulMemory):
        raise MemoryIntelligenceError([{"field": "memory", "code": "invalid_input", "message": "Expected a SoulMemory."}])
    config = config or load_config()
    if not config.confidence_decay_enabled:
        return _result(memory, confidence_reason="decay disabled", metadata={"decayed": False})

    now = now or _now()
    anchor = memory.last_verified_at or memory.updated_at
    if anchor.tzinfo is None:
        anchor = anchor.replace(tzinfo=timezone.utc)
    days = max(0.0, (now - anchor).total_seconds() / 86400)
    decayed = max(config.minimum_confidence, memory.confidence - config.decay_per_day * days)
    changed = decayed < memory.confidence
    if changed:
        store.stamp(memory, confidence=decayed)

    status, action = _status_and_action(decayed, MemorySource(memory.source), config)
    if action != NextAction.NONE and config.verification_enabled:
        store.stamp(memory, verification_status=status.value)
    return _result(
        memory,
        confidence=decayed,
        confidence_reason=f"decay over {days:.1f} days" if changed else "no decay applied",
        verification_status=VerificationStatus(memory.verification_status),
        next_action=action,
        metadata={"decayed": changed, "days": round(days, 2)},
    )


def needs_verification(memory: SoulMemory, config: IntelligenceConfig | None = None) -> bool:
    """True when confidence has dropped below the verification threshold."""

    config = config or load_config()
    return config.verification_enabled and memory.confidence < config.needs_verification_threshold


def apply_correction(
    memory: SoulMemory,
    *,
    new_summary: str,
    new_title: str | None = None,
    evidence: dict[str, Any],
    store: IntelligenceStore,
) -> MemoryIntelligenceResult:
    """The user is the final authority — corrections permanently replace.

    Archives the previous value (outdated, never lost), updates in place, raises
    confidence (explicit correction), and records correction evidence.
    """

    if not isinstance(memory, SoulMemory):
        raise MemoryIntelligenceError([{"field": "memory", "code": "invalid_input", "message": "Expected a SoulMemory."}])
    if not evidence:
        raise MemoryIntelligenceError([{"field": "evidence", "code": "missing_evidence", "message": "Corrections require evidence."}])

    # Preserve the outdated value in history first — history is never lost.
    store.record_version(memory, reason="user_correction", author="user", is_outdated=True)

    now = _now()
    merged = {**(json.loads(memory.evidence) if memory.evidence else {}), "correction": evidence, "corrected_at": now.isoformat()}
    store.stamp(
        memory,
        summary=new_summary,
        title=new_title or memory.title,
        confidence=0.99,  # explicit user correction
        verification_status=VerificationStatus.VERIFIED.value,
        last_verified_at=now,
        evidence=json.dumps(merged),
        version=memory.version + 1,
    )
    return _result(
        memory,
        confidence=0.99,
        confidence_reason="user explicitly corrected this memory",
        evidence=merged,
        verification_status=VerificationStatus.VERIFIED,
        last_verified_at=now,
        previous_version=memory.version - 1,
        next_action=NextAction.CORRECTED,
        metadata={"version": memory.version},
    )


def would_resurface(versions: list[SoulMemoryVersion], candidate_summary: str) -> bool:
    """True if a candidate matches a value the user already corrected away —
    the same incorrect memory must never resurface."""

    low = (candidate_summary or "").strip().lower()
    return any(v.is_outdated and v.summary.strip().lower() == low for v in versions)


def required_confidence(
    memory_type: str, corrections_by_type: dict[str, int], config: IntelligenceConfig | None = None
) -> float:
    """Correction-pattern learning: frequently corrected types require stronger
    evidence before storing. Uses explicit correction history + config only —
    no model retraining, no hidden prompt changes."""

    config = config or load_config()
    override = config.type_overrides.get(memory_type, {})
    base = override.get("auto_store_threshold", config.auto_store_threshold)
    count = corrections_by_type.get(memory_type, 0)
    if count < config.correction_pattern_threshold:
        return base
    extra = (count - config.correction_pattern_threshold + 1) * config.correction_confidence_penalty
    return min(0.99, base + extra)
