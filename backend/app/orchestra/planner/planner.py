"""Reflection Planner — Orchestra node 4 (the director).

Single responsibility: decide *what kind* of reflection should happen and emit an
immutable ``PlannerResult`` wrapping a ``ReflectionPlan``. It never writes the
reflection, calls an LLM, or touches memory. It honors the Guardian: it may
reduce depth/questions but never exceed the Guardian's limits, and it produces a
``NO_REFLECTION`` plan whenever the Guardian disallows reflection.

Deterministic and rule-based. When uncertain, it chooses the simplest safe plan.
"""

from __future__ import annotations

from app.orchestra.guardian.schemas import (
    EmotionalTone,
    GuardianCategory,
    GuardianResult,
    RecommendedAction,
    ReflectionDepth,
)
from app.orchestra.memory.schemas import MemoryType, RetrievalResult
from app.orchestra.planner.errors import PlannerError
from app.orchestra.planner.schemas import (
    PlannerResult,
    PlanTone,
    QuestionType,
    ReflectionPlan,
    ReflectionType,
)
from app.orchestra.schemas import OrchestraRequest

RT = ReflectionType
Tone = PlanTone
QT = QuestionType
Depth = ReflectionDepth
Cat = GuardianCategory
ETone = EmotionalTone

_DEPTH_ORDER = [Depth.NONE, Depth.LIGHT, Depth.MEDIUM, Depth.DEEP]
_CONFIDENCE_FLOOR = 0.4
_MAX_REFERENCED = 3
_CREATIVE_WORDS = {"story", "stories", "song", "songs", "poem", "poetry", "creative", "idea", "ideas", "lyrics", "fiction", "novel", "art"}
_MEMORY_FRIENDLY = {RT.REFLECTION, RT.MEMORY_RECALL, RT.VALIDATION, RT.ENCOURAGEMENT, RT.GOAL_SUPPORT, RT.CELEBRATION, RT.LISTENING}

# Per reflection-type presentation: (tone, emotional_style, proposed_depth,
# desired_question_count, question_type).
_TYPE_PLAN: dict[ReflectionType, tuple] = {
    RT.LISTENING: (Tone.GENTLE, "hold_space", Depth.LIGHT, 0, QT.NONE),
    RT.VALIDATION: (Tone.WARM, "validate_gently", Depth.MEDIUM, 1, QT.REFLECTIVE),
    RT.ENCOURAGEMENT: (Tone.ENCOURAGING, "encourage_gently", Depth.MEDIUM, 1, QT.OPEN),
    RT.CELEBRATION: (Tone.CELEBRATORY, "celebratory", Depth.LIGHT, 1, QT.OPEN),
    RT.REFLECTION: (Tone.THOUGHTFUL, "thoughtful", Depth.MEDIUM, 1, QT.REFLECTIVE),
    RT.GOAL_SUPPORT: (Tone.ENCOURAGING, "support_goal", Depth.MEDIUM, 1, QT.FUTURE_ORIENTED),
    RT.MEMORY_RECALL: (Tone.WARM, "connect_past", Depth.MEDIUM, 1, QT.REFLECTIVE),
    RT.EDUCATION: (Tone.THOUGHTFUL, "informative", Depth.LIGHT, 1, QT.CLARIFYING),
    RT.RESEARCH_SUMMARY: (Tone.THOUGHTFUL, "informative", Depth.LIGHT, 0, QT.NONE),
    RT.PROJECT_SUPPORT: (Tone.ENCOURAGING, "support_project", Depth.LIGHT, 1, QT.CLARIFYING),
    RT.CREATIVE_INSPIRATION: (Tone.CURIOUS, "inspire", Depth.LIGHT, 1, QT.OPEN),
    RT.SIMPLE_ACKNOWLEDGEMENT: (Tone.RESPECTFUL, "acknowledge", Depth.LIGHT, 0, QT.NONE),
}


def _cap_depth(proposed: ReflectionDepth, cap: ReflectionDepth) -> ReflectionDepth:
    return proposed if _DEPTH_ORDER.index(proposed) <= _DEPTH_ORDER.index(cap) else cap


def _is_creative(request: OrchestraRequest) -> bool:
    text = f"{request.book.title} {request.book.book_type}".lower()
    return any(word in text.split() for word in _CREATIVE_WORDS)


def _has_goal_memory(retrieval: RetrievalResult) -> bool:
    return any(m.memory_type in {MemoryType.GOAL, MemoryType.MILESTONE} for m in retrieval.retrieved)


def _decide_type(request, guardian, retrieval) -> ReflectionType:
    cat = guardian.category
    tone = guardian.emotional_tone
    action = guardian.recommended_action

    if action == RecommendedAction.DECLINE_OVERRIDE:
        return RT.SIMPLE_ACKNOWLEDGEMENT
    if cat in {Cat.MEDICAL_INFORMATION, Cat.LEGAL_INFORMATION}:
        return RT.SIMPLE_ACKNOWLEDGEMENT
    if cat == Cat.ACADEMIC_HELP:
        return RT.EDUCATION
    if cat == Cat.RESEARCH:
        return RT.RESEARCH_SUMMARY
    if cat == Cat.PROJECT_ASSISTANCE:
        return RT.PROJECT_SUPPORT
    if cat == Cat.IMAGE_ANALYSIS:
        return RT.SIMPLE_ACKNOWLEDGEMENT
    if tone == ETone.GRIEVING or action == RecommendedAction.LISTEN_ONLY:
        return RT.LISTENING
    if action == RecommendedAction.CELEBRATE or tone in {ETone.JOYFUL, ETone.POSITIVE, ETone.HOPEFUL}:
        return RT.CELEBRATION
    if cat == Cat.HIGH_EMOTIONAL_DISTRESS:
        return RT.VALIDATION
    if cat == Cat.EMOTIONAL_SUPPORT:
        if tone in {ETone.ANXIOUS, ETone.OVERWHELMED, ETone.FRUSTRATED}:
            return RT.ENCOURAGEMENT
        return RT.VALIDATION
    # SAFE / LOW_CONCERN
    if _is_creative(request):
        return RT.CREATIVE_INSPIRATION
    if retrieval.count > 0:
        return RT.GOAL_SUPPORT if _has_goal_memory(retrieval) else RT.MEMORY_RECALL
    return RT.REFLECTION


def plan(
    request: OrchestraRequest, guardian: GuardianResult, retrieval: RetrievalResult
) -> PlannerResult:
    """Create a structured ReflectionPlan. Immutable result."""

    if not isinstance(request, OrchestraRequest):
        raise PlannerError([{"field": "request", "code": "invalid_input", "message": "Expected an OrchestraRequest."}])
    if not isinstance(guardian, GuardianResult):
        raise PlannerError([{"field": "guardian", "code": "invalid_input", "message": "Expected a GuardianResult."}])
    if not isinstance(retrieval, RetrievalResult):
        raise PlannerError([{"field": "retrieval", "code": "invalid_input", "message": "Expected a RetrievalResult."}])

    confidence = round(guardian.confidence, 2)

    # Guardian forbids reflection (e.g. crisis) -> a safe pause.
    if not guardian.allow_reflection:
        no_plan = ReflectionPlan(
            reflection_type=RT.NO_REFLECTION, tone=Tone.QUIET, depth=Depth.NONE,
            emotional_style="safe_pause", ask_question=False, question_type=QT.NONE,
            question_count=0, reference_memories=False, memories_to_use=(), max_memories=0,
            celebrate=False, encourage=False, listen_only=False,
        )
        return PlannerResult(
            request_id=request.request_id, plan=no_plan, confidence=confidence,
            reason=f"no_reflection; guardian={guardian.category.value}/{guardian.recommended_action.value}",
        )

    rtype = _decide_type(request, guardian, retrieval)

    # When uncertain, choose the simplest safe plan.
    simplest = confidence < _CONFIDENCE_FLOOR
    if simplest:
        rtype = RT.SIMPLE_ACKNOWLEDGEMENT

    tone, style, proposed_depth, desired_q, qtype = _TYPE_PLAN[rtype]

    # Depth: honor the Guardian cap; never exceed it.
    depth = _cap_depth(proposed_depth, guardian.reflection_depth)

    # Questions: honor the Guardian cap and permission.
    if not guardian.allow_questions or simplest:
        question_count = 0
    else:
        question_count = min(desired_q, guardian.max_questions)
    ask_question = question_count > 0
    question_type = qtype if ask_question else QT.NONE

    # Memory referencing (planner selects; never edits).
    reference = (not simplest) and retrieval.count > 0 and rtype in _MEMORY_FRIENDLY
    memories = tuple(m.id for m in retrieval.retrieved[:_MAX_REFERENCED]) if reference else ()

    celebrate = rtype == RT.CELEBRATION
    encourage = rtype in {RT.ENCOURAGEMENT, RT.GOAL_SUPPORT, RT.PROJECT_SUPPORT, RT.CELEBRATION} or (
        guardian.needs_human_referral and guardian.category in {Cat.MEDICAL_INFORMATION, Cat.LEGAL_INFORMATION}
    )
    listen_only = rtype == RT.LISTENING

    reflection_plan = ReflectionPlan(
        reflection_type=rtype, tone=tone, depth=depth,
        emotional_style="simplest_safe" if simplest else style,
        ask_question=ask_question, question_type=question_type, question_count=question_count,
        reference_memories=reference, memories_to_use=memories, max_memories=len(memories),
        celebrate=celebrate, encourage=encourage, listen_only=listen_only,
    )
    return PlannerResult(
        request_id=request.request_id, plan=reflection_plan, confidence=confidence,
        reason=(
            f"type={rtype.value}; tone={tone.value}; depth={depth.value}; questions={question_count}; "
            f"guardian={guardian.category.value}/{guardian.recommended_action.value}"
        ),
    )
