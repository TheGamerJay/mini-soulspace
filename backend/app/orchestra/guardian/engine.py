"""Guardian Engine — Orchestra node 2 (the protector).

Single responsibility: evaluate an immutable ``OrchestraRequest`` and produce an
immutable ``GuardianResult``. Deterministic and rule-based — **no LLM, no Ollama,
no reflection, no memory I/O**. It only classifies and protects.

Guardian Principle: when uncertain, choose the safer path. Safety always
overrides intelligence — crisis categories short-circuit reflection.
"""

from __future__ import annotations

from app.orchestra.guardian.errors import GuardianError
from app.orchestra.guardian.lexicon import detect_signals
from app.orchestra.guardian.schemas import (
    EmotionalTone,
    GuardianCategory,
    GuardianResult,
    ReflectionDepth,
    RecommendedAction,
)
from app.orchestra.schemas import OrchestraRequest

C = GuardianCategory
T = EmotionalTone
D = ReflectionDepth
A = RecommendedAction

_CRISIS = {C.SELF_HARM_RISK, C.HARM_TO_OTHERS, C.EMERGENCY}
_DEPTH_ORDER = [D.NONE, D.LIGHT, D.MEDIUM, D.DEEP]
_OVERRIDE_SIGNALS = {"identity_override", "roleplay_override", "safety_override"}


def classify_category(signals: set[str]) -> GuardianCategory:
    """Pick exactly one primary category (safety-first priority order)."""

    if "self_harm" in signals:
        return C.SELF_HARM_RISK
    if "harm_others" in signals:
        return C.HARM_TO_OTHERS
    if "emergency" in signals:
        return C.EMERGENCY
    if "strong_distress" in signals or (
        "overwhelmed" in signals and signals & {"sad", "anxious", "grief"}
    ):
        return C.HIGH_EMOTIONAL_DISTRESS
    if "medical" in signals:
        return C.MEDICAL_INFORMATION
    if "legal" in signals:
        return C.LEGAL_INFORMATION
    if "academic" in signals:
        return C.ACADEMIC_HELP
    if "project" in signals:
        return C.PROJECT_ASSISTANCE
    if "image" in signals:
        return C.IMAGE_ANALYSIS
    if "research" in signals:
        return C.RESEARCH
    if signals & {"grief", "sad", "angry", "anxious", "overwhelmed"}:
        return C.EMOTIONAL_SUPPORT
    if "frustrated" in signals:
        return C.LOW_CONCERN
    return C.SAFE


def classify_tone(signals: set[str], text: str) -> EmotionalTone:
    """Describe the overall emotional tone (descriptive, never diagnostic)."""

    if not text.strip():
        return T.UNCERTAIN

    negative = signals & {"grief", "sad", "angry", "anxious", "overwhelmed", "frustrated", "strong_distress"}
    positive = signals & {"joyful", "positive", "hopeful"}
    if negative and positive:
        return T.MIXED

    if "grief" in signals:
        return T.GRIEVING
    if "overwhelmed" in signals or "strong_distress" in signals:
        return T.OVERWHELMED
    if "angry" in signals:
        return T.ANGRY
    if "anxious" in signals:
        return T.ANXIOUS
    if "sad" in signals:
        return T.SAD
    if "frustrated" in signals:
        return T.FRUSTRATED
    if "joyful" in signals:
        return T.JOYFUL
    if "hopeful" in signals:
        return T.HOPEFUL
    if "positive" in signals:
        return T.POSITIVE
    if "reflective" in signals:
        return T.REFLECTIVE
    return T.NEUTRAL


# Base policy per category (data, not branches). Fields:
# allow_reflection, mem_store, mem_retrieve, allow_questions, max_q, depth,
# referral, crisis, action, confidence.
_POLICY: dict[GuardianCategory, dict] = {
    C.SAFE: dict(allow_reflection=True, mem_store=True, mem_retrieve=True, allow_questions=True, max_q=1, depth=D.LIGHT, referral=False, crisis=False, action=A.CONTINUE_REFLECTION, confidence=0.7),
    C.LOW_CONCERN: dict(allow_reflection=True, mem_store=True, mem_retrieve=True, allow_questions=True, max_q=1, depth=D.LIGHT, referral=False, crisis=False, action=A.CONTINUE_REFLECTION, confidence=0.6),
    C.EMOTIONAL_SUPPORT: dict(allow_reflection=True, mem_store=True, mem_retrieve=True, allow_questions=True, max_q=1, depth=D.MEDIUM, referral=False, crisis=False, action=A.GENTLE_REFLECTION, confidence=0.72),
    C.HIGH_EMOTIONAL_DISTRESS: dict(allow_reflection=True, mem_store=False, mem_retrieve=True, allow_questions=True, max_q=1, depth=D.MEDIUM, referral=True, crisis=False, action=A.GENTLE_REFLECTION, confidence=0.75),
    C.SELF_HARM_RISK: dict(allow_reflection=False, mem_store=False, mem_retrieve=False, allow_questions=False, max_q=0, depth=D.NONE, referral=True, crisis=True, action=A.CRISIS_RESPONSE, confidence=0.9),
    C.HARM_TO_OTHERS: dict(allow_reflection=False, mem_store=False, mem_retrieve=False, allow_questions=False, max_q=0, depth=D.NONE, referral=True, crisis=True, action=A.CRISIS_RESPONSE, confidence=0.9),
    C.EMERGENCY: dict(allow_reflection=False, mem_store=False, mem_retrieve=False, allow_questions=False, max_q=0, depth=D.NONE, referral=True, crisis=True, action=A.CRISIS_RESPONSE, confidence=0.9),
    C.MEDICAL_INFORMATION: dict(allow_reflection=True, mem_store=False, mem_retrieve=True, allow_questions=True, max_q=1, depth=D.LIGHT, referral=True, crisis=False, action=A.ENCOURAGE_SUPPORT, confidence=0.6),
    C.LEGAL_INFORMATION: dict(allow_reflection=True, mem_store=False, mem_retrieve=True, allow_questions=True, max_q=1, depth=D.LIGHT, referral=True, crisis=False, action=A.ENCOURAGE_SUPPORT, confidence=0.6),
    C.ACADEMIC_HELP: dict(allow_reflection=True, mem_store=False, mem_retrieve=True, allow_questions=True, max_q=1, depth=D.LIGHT, referral=False, crisis=False, action=A.CONTINUE_REFLECTION, confidence=0.5),
    C.PROJECT_ASSISTANCE: dict(allow_reflection=True, mem_store=False, mem_retrieve=True, allow_questions=True, max_q=1, depth=D.LIGHT, referral=False, crisis=False, action=A.CONTINUE_REFLECTION, confidence=0.5),
    C.RESEARCH: dict(allow_reflection=True, mem_store=False, mem_retrieve=True, allow_questions=True, max_q=1, depth=D.LIGHT, referral=False, crisis=False, action=A.CONTINUE_REFLECTION, confidence=0.5),
    C.IMAGE_ANALYSIS: dict(allow_reflection=True, mem_store=False, mem_retrieve=False, allow_questions=False, max_q=0, depth=D.MEDIUM, referral=False, crisis=False, action=A.GENTLE_REFLECTION, confidence=0.35),
    C.UNKNOWN: dict(allow_reflection=True, mem_store=False, mem_retrieve=True, allow_questions=False, max_q=0, depth=D.LIGHT, referral=False, crisis=False, action=A.GENTLE_REFLECTION, confidence=0.3),
}


def _cap_depth(depth: ReflectionDepth, cap: ReflectionDepth) -> ReflectionDepth:
    return depth if _DEPTH_ORDER.index(depth) <= _DEPTH_ORDER.index(cap) else cap


def evaluate(request: OrchestraRequest) -> GuardianResult:
    """Classify and protect. Returns an immutable GuardianResult."""

    if not isinstance(request, OrchestraRequest):
        raise GuardianError(
            [{"field": "request", "code": "invalid_input", "message": "Expected an OrchestraRequest."}]
        )

    text = request.page_content or ""
    signals = detect_signals(text)
    category = classify_category(signals)
    tone = classify_tone(signals, text)
    p = dict(_POLICY[category])  # copy base policy
    crisis = p["crisis"]

    # Positive-tone celebration (non-crisis, non-distress).
    if not crisis and category in {C.SAFE, C.LOW_CONCERN} and tone in {T.JOYFUL, T.POSITIVE, T.HOPEFUL}:
        p["action"] = A.CELEBRATE

    # Grieving: make space, don't interrogate.
    if not crisis and tone == T.GRIEVING:
        p["action"] = A.LISTEN_ONLY
        p["max_q"] = 0
        p["allow_questions"] = False

    # Identity/roleplay/safety override attempts (never granted).
    override = bool(signals & _OVERRIDE_SIGNALS)
    if override and not crisis:
        p["action"] = A.DECLINE_OVERRIDE
        p["mem_store"] = False
        p["confidence"] = max(p["confidence"], 0.7)

    # Guardian Principle: low confidence -> safer path.
    if not crisis and p["confidence"] < 0.4:
        p["max_q"] = 0
        p["allow_questions"] = False
        p["depth"] = _cap_depth(p["depth"], D.LIGHT)

    reason = f"category={category.value}; tone={tone.value}; signals={sorted(signals)}"

    return GuardianResult(
        request_id=request.request_id,
        category=category,
        emotional_tone=tone,
        allow_reflection=p["allow_reflection"],
        allow_memory_storage=p["mem_store"],
        allow_memory_retrieval=p["mem_retrieve"],
        allow_questions=p["allow_questions"],
        max_questions=p["max_q"],
        reflection_depth=p["depth"],
        allow_identity_override=False,  # permanent protection
        allow_roleplay_override=False,  # permanent protection
        needs_human_referral=p["referral"],
        needs_crisis_template=crisis,
        recommended_action=p["action"],
        confidence=p["confidence"],
        reason=reason,
        signals=tuple(sorted(signals)),
    )
