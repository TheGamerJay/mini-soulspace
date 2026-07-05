"""Context Builder — Orchestra node 5 (the architect).

Single responsibility: assemble the minimum, highest-quality ``ContextPackage``
for the Prompt Builder. It never generates prompts or text, calls an LLM,
retrieves memories, or plans. It only selects, orders, deduplicates and budgets
context that upstream nodes already produced.

Rule 13 (Minimum Sufficient Context): pass only what the next node needs.
"""

from __future__ import annotations

import json

from app.orchestra.context.errors import ContextBuilderError
from app.orchestra.context.schemas import (
    ContextBlock,
    ContextBudget,
    ContextLayer,
    ContextPackage,
    ContextPriority,
    ContextStatistics,
    ExcludedNote,
)
from app.orchestra.guardian.schemas import GuardianResult
from app.orchestra.memory.schemas import MemoryType, RetrievalResult
from app.orchestra.planner.schemas import PlannerResult
from app.orchestra.schemas import OrchestraRequest

L = ContextLayer
P = ContextPriority

_LAYER_ORDER = {L.IDENTITY: 0, L.GUARDIAN: 1, L.CURRENT_PAGE: 2, L.MEMORY: 3, L.REFLECTION: 4, L.RESERVED: 5}
_PRIO_RANK = {P.CRITICAL: 0, P.HIGH: 1, P.MEDIUM: 2, P.LOW: 3}

DEFAULT_BUDGET = ContextBudget()


def _chars(content: dict) -> int:
    return len(json.dumps(content, default=str, sort_keys=True))


def _select_memories(guardian, retrieval, planner, budget):
    """Guardian- and Planner-approved memories, deduped and capped. Returns
    (items, excluded_notes)."""

    if not guardian.allow_memory_retrieval:
        return [], [ExcludedNote(item="memory", reason="blocked_by_guardian")]
    if retrieval.blocked:
        return [], [ExcludedNote(item="memory", reason="retrieval_blocked")]
    if not planner.plan.reference_memories:
        return [], [ExcludedNote(item="memory", reason="planner_excluded")]

    by_id = {m.id: m for m in retrieval.retrieved}
    seen: set = set()
    items: list[dict] = []
    excluded: list[ExcludedNote] = []
    goals = projects = 0

    for mid in planner.plan.memories_to_use:
        memory = by_id.get(mid)
        if memory is None:
            excluded.append(ExcludedNote(item=str(mid), reason="not_in_retrieval"))
            continue
        if memory.id in seen:
            excluded.append(ExcludedNote(item=str(mid), reason="duplicate"))
            continue
        seen.add(memory.id)
        if len(items) >= budget.max_memories:
            excluded.append(ExcludedNote(item=str(mid), reason="max_memories"))
            continue
        if memory.memory_type == MemoryType.GOAL and goals >= budget.max_goals:
            excluded.append(ExcludedNote(item=str(mid), reason="max_goals"))
            continue
        if memory.memory_type == MemoryType.PROJECT and projects >= budget.max_projects:
            excluded.append(ExcludedNote(item=str(mid), reason="max_projects"))
            continue
        goals += memory.memory_type == MemoryType.GOAL
        projects += memory.memory_type == MemoryType.PROJECT
        items.append(
            {
                "id": str(memory.id),
                "type": memory.memory_type.value,
                "priority": memory.priority.value,
                "title": memory.title,
                "summary": memory.summary,
                "why_selected": memory.why_selected,
            }
        )
    return items, excluded


def build(
    request: OrchestraRequest,
    guardian: GuardianResult,
    retrieval: RetrievalResult,
    planner: PlannerResult,
    *,
    budget: ContextBudget = DEFAULT_BUDGET,
) -> ContextPackage:
    """Assemble an immutable ContextPackage. Never modifies its inputs."""

    if not isinstance(request, OrchestraRequest):
        raise ContextBuilderError([{"field": "request", "code": "invalid_input", "message": "Expected an OrchestraRequest."}])
    if not isinstance(guardian, GuardianResult):
        raise ContextBuilderError([{"field": "guardian", "code": "invalid_input", "message": "Expected a GuardianResult."}])
    if not isinstance(retrieval, RetrievalResult):
        raise ContextBuilderError([{"field": "retrieval", "code": "invalid_input", "message": "Expected a RetrievalResult."}])
    if not isinstance(planner, PlannerResult):
        raise ContextBuilderError([{"field": "planner", "code": "invalid_input", "message": "Expected a PlannerResult."}])

    excluded: list[ExcludedNote] = []
    # Mutable candidates: dicts assembled first, frozen into ContextBlocks last.
    candidates: list[dict] = []

    # Layer 1 — Identity (reference; full identity text is the Prompt Builder's static layer).
    candidates.append(dict(
        type=L.IDENTITY, priority=P.CRITICAL, source="soul_companion_guide",
        reason="Soul Companion identity must anchor every reflection.",
        content={"applies": "soul_companion_guide", "note": "identity enforced by Prompt Builder"},
    ))

    # Layer 2 — Guardian decisions/restrictions.
    candidates.append(dict(
        type=L.GUARDIAN, priority=P.CRITICAL, source="guardian",
        reason="Guardian decisions constrain the reflection (safety-first).",
        content={
            "category": guardian.category.value,
            "emotional_tone": guardian.emotional_tone.value,
            "allow_reflection": guardian.allow_reflection,
            "allow_memory_retrieval": guardian.allow_memory_retrieval,
            "allow_memory_storage": guardian.allow_memory_storage,
            "allow_questions": guardian.allow_questions,
            "max_questions": guardian.max_questions,
            "reflection_depth": guardian.reflection_depth.value,
            "allow_identity_override": guardian.allow_identity_override,
            "allow_roleplay_override": guardian.allow_roleplay_override,
            "needs_human_referral": guardian.needs_human_referral,
            "needs_crisis_template": guardian.needs_crisis_template,
            "recommended_action": guardian.recommended_action.value,
        },
    ))

    # Layer 3 — Current page + metadata.
    candidates.append(dict(
        type=L.CURRENT_PAGE, priority=P.HIGH, source="input_receiver",
        reason="The page the user wrote is the subject of the reflection.",
        content={
            "book_title": request.book.title,
            "chapter_title": request.chapter.title,
            "page_title": request.page.title,
            "content": request.page_content,
            "content_format": request.page.content_format,
            "word_count": request.statistics.word_count,
            "character_count": request.statistics.character_count,
            "language": request.language,
            "timezone": request.timezone,
        },
    ))

    # Layer 4 — Memory (only if Guardian + Planner approve).
    memory_items, mem_excluded = _select_memories(guardian, retrieval, planner, budget)
    excluded.extend(mem_excluded)
    if memory_items:
        candidates.append(dict(
            type=L.MEMORY, priority=P.MEDIUM, source="memory_retriever",
            reason="Relevant memories the Planner chose to reference.",
            content={"memories": memory_items},
        ))

    # Layer 5 — Reflection plan.
    plan = planner.plan
    candidates.append(dict(
        type=L.REFLECTION, priority=P.HIGH, source="reflection_planner",
        reason="The plan directs how to reflect.",
        content={
            "reflection_type": plan.reflection_type.value,
            "tone": plan.tone.value,
            "depth": plan.depth.value,
            "emotional_style": plan.emotional_style,
            "ask_question": plan.ask_question,
            "question_type": plan.question_type.value,
            "question_count": plan.question_count,
            "celebrate": plan.celebrate,
            "encourage": plan.encourage,
            "listen_only": plan.listen_only,
        },
    ))

    # Layer 6 — Reserved: intentionally empty (future specialists).

    for c in candidates:
        c["char_count"] = _chars(c["content"])

    # Budget: drop the memory block first, then truncate page content (never
    # touch Identity/Guardian/Reflection).
    total = sum(c["char_count"] for c in candidates)
    if total > budget.max_total_chars:
        mem = next((c for c in candidates if c["type"] == L.MEMORY), None)
        if mem is not None:
            candidates.remove(mem)
            memory_items = []
            excluded.append(ExcludedNote(item="memory_block", reason="budget_char_limit"))
            total = sum(c["char_count"] for c in candidates)
        if total > budget.max_total_chars:
            page = next(c for c in candidates if c["type"] == L.CURRENT_PAGE)
            overflow = total - budget.max_total_chars
            old = page["content"]["content"]
            keep = max(0, len(old) - overflow - 1)
            page["content"] = {**page["content"], "content": old[:keep] + "…", "truncated": True}
            page["char_count"] = _chars(page["content"])
            excluded.append(ExcludedNote(item="page_content", reason="budget_char_limit_truncated"))

    candidates.sort(key=lambda c: (_LAYER_ORDER[c["type"]], _PRIO_RANK[c["priority"]]))
    blocks = tuple(
        ContextBlock(
            type=c["type"], priority=c["priority"], source=c["source"],
            reason=c["reason"], content=c["content"], char_count=c["char_count"],
        )
        for c in candidates
    )

    statistics = ContextStatistics(
        block_count=len(blocks),
        total_chars=sum(b.char_count for b in blocks),
        memory_count=len(memory_items),
        excluded_count=len(excluded),
    )
    confidence = round((guardian.confidence + planner.confidence) / 2, 2)

    return ContextPackage(
        request_id=request.request_id,
        blocks=blocks,
        statistics=statistics,
        budget=budget,
        excluded=tuple(excluded),
        confidence=confidence,
    )
