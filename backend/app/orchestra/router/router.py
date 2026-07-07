"""Specialist Router — the Orchestra node that decides WHO should help.

Deterministic: selections come from the Meaning & Intent result, the Guardian,
the Planner, and requested capabilities (e.g. future attachments) matched
against the discoverable registry — **never keywords alone**. The Router never
generates language, never reasons, never replaces the Planner, and never
decides how the conversation flows (Rule 23).

It may select one specialist, multiple specialists (sequential; parallel is
future architecture), or none (crisis — the Guardian always has authority).
"""

from __future__ import annotations

from app.orchestra.guardian.schemas import GuardianCategory, GuardianResult
from app.orchestra.meaning.schemas import ContextType, IntentType, MeaningIntentResult
from app.orchestra.planner.schemas import PlannerResult
from app.orchestra.router.errors import RouterError
from app.orchestra.router.registry import find_by_capability
from app.orchestra.router.schemas import Complexity, RoutingPlan, SpecialistCard
from app.orchestra.schemas import OrchestraRequest

FALLBACK = "mini_core"

# Structured decision → desired capability. Enum-driven, never raw keywords.
_INTENT_CAPS: dict[IntentType, str] = {
    IntentType.LEARNING: "tutoring",
    IntentType.RESEARCH: "internet_research",
    IntentType.INFORMATION_REQUEST: "internet_research",
    IntentType.HEALTH_AWARENESS: "internet_research",
}
_CONTEXT_CAPS: dict[ContextType, str] = {
    ContextType.HOMEWORK: "tutoring",
    ContextType.RESEARCH: "internet_research",
    ContextType.MEDICAL_QUESTION: "internet_research",
}
_GUARDIAN_CAPS: dict[GuardianCategory, str] = {
    GuardianCategory.IMAGE_ANALYSIS: "image_understanding",
    GuardianCategory.ACADEMIC_HELP: "tutoring",
    GuardianCategory.PROJECT_ASSISTANCE: "programming",
    GuardianCategory.RESEARCH: "internet_research",
    GuardianCategory.MEDICAL_INFORMATION: "internet_research",
}


def _desired_capabilities(
    meaning: MeaningIntentResult,
    guardian: GuardianResult,
    requested: tuple[str, ...],
) -> set[str]:
    desired: set[str] = set(requested)
    cap = _GUARDIAN_CAPS.get(guardian.category)
    if cap:
        desired.add(cap)
    cap = _CONTEXT_CAPS.get(meaning.context_type)
    if cap:
        desired.add(cap)
    cap = _INTENT_CAPS.get(meaning.intent_type)
    if cap:
        desired.add(cap)
    return desired


def route(
    request: OrchestraRequest,
    meaning: MeaningIntentResult,
    guardian: GuardianResult,
    planner: PlannerResult,
    registry: dict[str, SpecialistCard],
    *,
    requested_capabilities: tuple[str, ...] = (),
) -> RoutingPlan:
    """Select the specialists for this request. Immutable plan."""

    if not isinstance(request, OrchestraRequest):
        raise RouterError([{"field": "request", "code": "invalid_input", "message": "Expected an OrchestraRequest."}])
    if not isinstance(meaning, MeaningIntentResult):
        raise RouterError([{"field": "meaning", "code": "invalid_input", "message": "Expected a MeaningIntentResult."}])
    if not isinstance(guardian, GuardianResult):
        raise RouterError([{"field": "guardian", "code": "invalid_input", "message": "Expected a GuardianResult."}])
    if not isinstance(planner, PlannerResult):
        raise RouterError([{"field": "planner", "code": "invalid_input", "message": "Expected a PlannerResult."}])

    # The Guardian always has final authority: a crisis selects NO specialists —
    # the pipeline's deterministic safety template takes over.
    if guardian.needs_crisis_template:
        return RoutingPlan(
            request_id=request.request_id,
            primary_specialist=None,
            primary_service=None,
            fallback_specialist=None,
            reasoning="crisis: guardian authority — no specialists selected",
            confidence=1.0,
        )

    desired = _desired_capabilities(meaning, guardian, requested_capabilities)
    fallback_card = registry.get(FALLBACK)
    fallback = fallback_card.name if fallback_card and fallback_card.participates else None

    matched = find_by_capability(registry, desired) if desired else []
    available = [c for c in matched if c.participates]
    unavailable = tuple(c.name for c in matched if not c.participates)

    if available:
        selected = available
        reasoning = (
            f"capabilities={sorted(desired)}; selected={[c.name for c in selected]}"
            + (f"; unavailable={list(unavailable)}" if unavailable else "")
        )
        confidence = 0.85
    else:
        # Nothing matched (a plain diary page) or every match is architecture-only:
        # the Soul Companion itself reflects.
        if fallback_card is None or not fallback_card.participates:
            raise RouterError(
                [{"field": "registry", "code": "no_available_specialist", "message": "No available specialist, including the fallback."}]
            )
        selected = [fallback_card]
        if desired:
            reasoning = f"capabilities={sorted(desired)}; unavailable={list(unavailable)}; fallback={FALLBACK}"
            confidence = 0.6
        else:
            reasoning = "reflection: routed to the Soul Companion"
            confidence = 0.9

    order = tuple(c.name for c in selected)
    complexity = Complexity.LOW if len(order) == 1 else Complexity.MEDIUM if len(order) == 2 else Complexity.HIGH

    return RoutingPlan(
        request_id=request.request_id,
        primary_specialist=selected[0].name,
        primary_service=selected[0].service,
        secondary_specialists=tuple(c.name for c in selected[1:]),
        fallback_specialist=fallback,
        execution_order=order,
        unavailable_specialists=unavailable,
        reasoning=reasoning,
        confidence=confidence,
        estimated_complexity=complexity,
        parallel_ready=False,
    )
