"""Memory Writer — Orchestra node 9.

Decides whether a completed, **approved** exchange should become a long-term
memory, and (optionally, when a store is provided) persists it. It never
retrieves memories for reflection, generates reflections, calls the Mini Engine,
or delivers responses. Deterministic — **no AI**.

Rule 18: memory is earned. When uncertain, Mini chooses not to remember.
"""

from __future__ import annotations

from app.orchestra.guardian.schemas import GuardianResult
from app.orchestra.meaning.schemas import MeaningIntentResult
from app.orchestra.memory.schemas import MemoryPriority, MemoryType
from app.orchestra.quality.schemas import QualityResult, QualityStatus
from app.orchestra.schemas import OrchestraRequest
from app.orchestra.writer.errors import MemoryWriterError
from app.orchestra.writer.extractor import CandidateMemory, extract
from app.orchestra.writer.schemas import MemoryDecision
from app.orchestra.writer.store import MemoryStore

# Types whose memory evolves in place (update, don't duplicate).
_EVOLVING = {
    MemoryType.PROJECT, MemoryType.CREATIVE_PROJECT, MemoryType.PREFERENCE,
    MemoryType.FAVORITE, MemoryType.GOAL, MemoryType.LEARNING_PROGRESS, MemoryType.HABIT,
}
_CONFIDENCE = {P: 0.6 for P in MemoryPriority}
_CONFIDENCE.update({
    MemoryPriority.CRITICAL: 0.85, MemoryPriority.HIGH: 0.8,
    MemoryPriority.MEDIUM: 0.7, MemoryPriority.LOW: 0.6,
})


def _no(request_id, reason: str) -> MemoryDecision:
    return MemoryDecision(request_id=request_id, store_memory=False, reason=reason, confidence=0.6, metadata={"op": "none"})


def _find_match(cand: CandidateMemory, existing):
    """First existing memory of the same type sharing a significant keyword."""

    for e in existing:
        if e.memory_type != cand.memory_type.value:
            continue
        e_keywords = {t for t in (e.keywords or "").lower().split() if t}
        if cand.keywords & e_keywords:
            return e
    return None


def write(
    request: OrchestraRequest,
    quality: QualityResult,
    guardian: GuardianResult,
    *,
    meaning: MeaningIntentResult | None = None,
    store: MemoryStore | None = None,
) -> MemoryDecision:
    """Decide (and optionally persist) whether to remember this exchange."""

    if not isinstance(request, OrchestraRequest):
        raise MemoryWriterError([{"field": "request", "code": "invalid_input", "message": "Expected an OrchestraRequest."}])
    if not isinstance(quality, QualityResult):
        raise MemoryWriterError([{"field": "quality", "code": "invalid_input", "message": "Expected a QualityResult."}])
    if not isinstance(guardian, GuardianResult):
        raise MemoryWriterError([{"field": "guardian", "code": "invalid_input", "message": "Expected a GuardianResult."}])

    # Only approved exchanges may create memories.
    if quality.status != QualityStatus.APPROVED:
        return _no(request.request_id, "not_approved")
    # Honor the Guardian's memory-storage decision (blocks crisis/sensitive/override).
    if not guardian.allow_memory_storage:
        return _no(request.request_id, "guardian_blocked")

    cand = extract(request.page_content)
    if cand is None:
        return _no(request.request_id, "nothing_worth_remembering")

    existing = list(store.existing(request.user.id)) if store is not None else []
    match = _find_match(cand, existing)

    op = "create"
    related_to_id = None
    reason = "new_memory"
    if match is not None:
        if match.summary == cand.summary:
            return _no(request.request_id, "duplicate")  # never create clutter
        if cand.memory_type == MemoryType.RELATIONSHIP:
            related_to_id = match.id  # keep the relationship timeline connected
            reason = "relationship_linked"
        elif cand.memory_type in _EVOLVING:
            op = "update"
            reason = "evolved_memory"
        else:
            return _no(request.request_id, "duplicate")

    memory_id = None
    if store is not None:
        keywords = " ".join(sorted(cand.keywords))
        if op == "update":
            row = store.update(match, priority=cand.importance.value, title=cand.title, summary=cand.summary, keywords=keywords)
        else:
            row = store.create(
                user_id=request.user.id, memory_type=cand.memory_type.value,
                priority=cand.importance.value, title=cand.title, summary=cand.summary,
                keywords=keywords, related_to_id=related_to_id, source_ref=str(request.page.id),
            )
        memory_id = row.id

    return MemoryDecision(
        request_id=request.request_id,
        store_memory=True,
        importance=cand.importance,
        memory_type=cand.memory_type,
        title=cand.title,
        summary=cand.summary,
        reason=reason,
        confidence=_CONFIDENCE[cand.importance],
        metadata={
            "op": op,
            "memory_id": str(memory_id) if memory_id else None,
            "linked_to": str(related_to_id) if related_to_id else None,
            "keywords": sorted(cand.keywords),
        },
    )
