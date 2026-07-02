"""Memory Retriever — Orchestra node 3 (the Memory Librarian).

Single responsibility: retrieve the minimum set of relevant, user-scoped memories
for an OrchestraRequest. It **only retrieves** — it never reflects, plans,
prompts, calls an LLM, stores, edits, or answers. It honors the Guardian and
never fabricates memories.

Relevance here is a deterministic keyword overlap (no AI). Semantic scoring is
designed to replace this scorer without changing the node's contract.
"""

from __future__ import annotations

import re
import uuid

from app.orchestra.guardian.schemas import GuardianResult
from app.orchestra.memory.errors import RetrievalError
from app.orchestra.memory.schemas import (
    MemoryPriority,
    MemoryType,
    RetrievalResult,
    RetrievedMemory,
)
from app.orchestra.memory.source import MemorySource
from app.orchestra.schemas import OrchestraRequest

# Minimum-useful-context limit; quality over quantity.
MAX_MEMORIES = 5
_RELEVANCE_MIN = 0.01

_PRIORITY_RANK = {
    MemoryPriority.CRITICAL: 0,
    MemoryPriority.HIGH: 1,
    MemoryPriority.MEDIUM: 2,
    MemoryPriority.LOW: 3,
}

_STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "was", "have", "had", "not",
    "you", "are", "but", "his", "her", "she", "him", "about", "from", "have",
    "into", "some", "just", "were", "them", "then", "than", "your", "our",
}
_TOKEN_RE = re.compile(r"[a-z]{3,}")


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall((text or "").lower()) if t not in _STOPWORDS}


def _score(memory, request_tokens: set[str]) -> tuple[float, str]:
    """Deterministic relevance: shared meaningful tokens. Returns (score, why)."""

    mem_text = " ".join(filter(None, [memory.title, memory.summary, memory.keywords or ""]))
    mem_tokens = _tokens(mem_text)
    matched = sorted(request_tokens & mem_tokens)
    if not matched:
        return 0.0, ""
    score = min(1.0, len(matched) / 3.0)
    return score, "matched: " + ", ".join(matched)


def _empty(request_id: uuid.UUID, *, blocked: bool, reason: str) -> RetrievalResult:
    return RetrievalResult(request_id=request_id, retrieved=(), count=0, blocked=blocked, reason=reason)


def retrieve(
    request: OrchestraRequest, guardian: GuardianResult, source: MemorySource
) -> RetrievalResult:
    """Retrieve relevant memories, honoring the Guardian. Immutable result."""

    if not isinstance(request, OrchestraRequest):
        raise RetrievalError(
            [{"field": "request", "code": "invalid_input", "message": "Expected an OrchestraRequest."}]
        )
    if not isinstance(guardian, GuardianResult):
        raise RetrievalError(
            [{"field": "guardian", "code": "invalid_input", "message": "Expected a GuardianResult."}]
        )

    # Never bypass the Guardian.
    if not guardian.allow_memory_retrieval:
        return _empty(request.request_id, blocked=True, reason="blocked_by_guardian")

    request_tokens = _tokens(f"{request.page.title} {request.page_content}")

    selected: list[RetrievedMemory] = []
    for memory in source.candidates(request.user.id):
        score, why = _score(memory, request_tokens)
        if score < _RELEVANCE_MIN:
            continue  # relevant only — never retrieve unrelated memories
        related = (memory.related_to_id,) if memory.related_to_id else ()
        selected.append(
            RetrievedMemory(
                id=memory.id,
                memory_type=MemoryType(memory.memory_type),
                priority=MemoryPriority(memory.priority),
                title=memory.title,
                summary=memory.summary,
                relevance_score=round(score, 3),
                confidence=round(score, 3),
                why_selected=why,
                related_ids=related,
                created_at=memory.created_at,
            )
        )

    # Critical first, then by relevance. Low, low-relevance items trim out first.
    selected.sort(key=lambda m: (_PRIORITY_RANK[m.priority], -m.relevance_score))
    selected = selected[:MAX_MEMORIES]

    if not selected:
        return _empty(request.request_id, blocked=False, reason="no_relevant_memories")

    return RetrievalResult(
        request_id=request.request_id,
        retrieved=tuple(selected),
        count=len(selected),
        blocked=False,
        reason=f"retrieved {len(selected)} memories",
    )
