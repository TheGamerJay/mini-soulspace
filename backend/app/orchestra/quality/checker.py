"""Quality Checker — Orchestra node 8 (the gate before the user).

Single responsibility: review a CandidateResponse against safety, identity,
quality and SoulDiary rules and return an immutable QualityResult
(approved / rejected / needs_retry). It never generates a final response, calls
the Mini Engine/model, reads/writes memory, or rewrites the candidate.
Deterministic and rule-based — **no AI**.

Rule 17: no response reaches the user until it passes quality verification.
"""

from __future__ import annotations

from app.orchestra.guardian.schemas import GuardianResult, ReflectionDepth
from app.orchestra.meaning.schemas import MeaningIntentResult, RealWorldIntent
from app.orchestra.mini.schemas import CandidateResponse
from app.orchestra.memory.schemas import RetrievalResult
from app.orchestra.planner.schemas import PlannerResult, ReflectionType
from app.orchestra.quality.errors import QualityCheckerError
from app.orchestra.quality.schemas import (
    QualityResult,
    QualityStatus,
    Severity,
    Violation,
)

S = Severity

# --- phrase banks (deterministic) --------------------------------------------
_IDENTITY_CLAIMS = (
    "i am human", "i'm human", "i am a human", "i'm a human", "i am alive",
    "i'm alive", "i am conscious", "i'm conscious", "i am sentient", "i'm sentient",
    "i am a therapist", "i'm a therapist", "as your therapist", "i am a licensed",
    "i am a real person", "i'm a real person", "i am a doctor", "i'm a doctor",
    "i am a psychologist", "i am a psychiatrist",
)
_HIDDEN_PROMPT = (
    "system prompt", "my system message", "my instructions are", "i was instructed to",
    "[identity]", "[safety & guardian]", "[current page]", "[relevant memories]",
    "[reflection plan]", "[response style]", "[output formatting]", "chain of thought",
    "chain-of-thought", "internal system instructions", "my internal rules",
    "you are the mini soulspace soul companion",
)
_MODEL_NAMES = ("qwen", "llama", "gemma", "ollama", "mistral", "gpt-", "claude")
_FABRICATION = (
    "i remember when you", "you told me before", "last time you", "as you mentioned earlier",
    "i recall that you", "you said earlier", "previously you told me", "remember how you",
)
_UNSAFE_MEDICAL = (
    "stop taking your medication", "stop your medication", "you don't need your meds",
    "double your dose", "you have depression", "you're depressed", "you are depressed",
    "i diagnose you", "you should stop treatment", "you are clinically",
)
_ENCOURAGE_HARM = (
    "you should hurt yourself", "go ahead and end", "kill yourself", "just end it",
    "you should give up on life", "harm yourself",
)
_MANIPULATION = (
    "you only need me", "you don't need anyone else", "i'm the only one who",
    "without me you", "you should feel ashamed", "it's all your fault",
    "you're being dramatic", "you owe me",
)
_GENERIC = (
    "i know exactly how you feel", "everything will be fine", "everything will be okay",
    "everything is going to be okay", "as an ai language model", "here are 10 things",
    "here are ten things you should",
)
_CRISIS_REFERRAL = (
    "emergency", "crisis line", "988", "professional", "someone you trust", "reach out",
    "hotline", "not alone", "help right now",
)
_ESCALATION = (
    "are you safe", "please reach out to a crisis", "call emergency", "suicide hotline",
    "crisis line", "seek professional help right now", "call 988",
)
_DEPTH_MAX_CHARS = {
    ReflectionDepth.NONE: 400,
    ReflectionDepth.LIGHT: 800,
    ReflectionDepth.MEDIUM: 1600,
    ReflectionDepth.DEEP: 3000,
}


def _has(text: str, needles) -> bool:
    return any(n in text for n in needles)


def check(
    candidate: CandidateResponse,
    guardian: GuardianResult,
    planner: PlannerResult,
    *,
    retrieval: RetrievalResult | None = None,
    meaning: MeaningIntentResult | None = None,
) -> QualityResult:
    """Approve, reject, or request retry for a candidate response."""

    if not isinstance(candidate, CandidateResponse):
        raise QualityCheckerError([{"field": "candidate", "code": "invalid_input", "message": "Expected a CandidateResponse."}])
    if not isinstance(guardian, GuardianResult):
        raise QualityCheckerError([{"field": "guardian", "code": "invalid_input", "message": "Expected a GuardianResult."}])
    if not isinstance(planner, PlannerResult):
        raise QualityCheckerError([{"field": "planner", "code": "invalid_input", "message": "Expected a PlannerResult."}])

    text = candidate.response_text
    low = text.lower()
    plan = planner.plan
    crisis = guardian.needs_crisis_template
    violations: list[Violation] = []

    def add(code, severity, message, rule, fixable):
        violations.append(Violation(code=code, severity=severity, message=message, source_rule=rule, fixable=fixable))

    # 1. Identity / sentience / licensed (Rule 4)
    if _has(low, _IDENTITY_CLAIMS):
        add("identity_claim", S.CRITICAL, "Claims to be human/alive/licensed.", "Soul Companion Guide / Rule 4", False)

    # 2. Hidden prompts / internal knowledge (Rule 5)
    if _has(low, _HIDDEN_PROMPT):
        add("hidden_prompt_reveal", S.CRITICAL, "Reveals hidden prompt or internal instructions.", "Knowledge Protection / Rule 5", False)

    # 3. Raw model names (Rule 6) — accidental, fixable
    if _has(low, _MODEL_NAMES):
        add("model_name_leak", S.HIGH, "Mentions a raw underlying model name.", "Knowledge Protection / Rule 6", True)

    # 4. Fabricated memory (Rules 8-9)
    if retrieval is not None and retrieval.count == 0 and _has(low, _FABRICATION):
        add("fabricated_memory", S.HIGH, "Claims to remember something not retrieved.", "Memory Rules / Rules 8-9", False)

    # 5. Unsafe medical / diagnosis (Rule 10)
    if _has(low, _UNSAFE_MEDICAL):
        add("unsafe_medical_advice", S.CRITICAL, "Gives unsafe medical advice or diagnosis.", "Safety Rules / Rule 10", False)

    # 6. Encouraging harm (Rule 12)
    if _has(low, _ENCOURAGE_HARM):
        add("encourages_harm", S.CRITICAL, "Encourages self-harm or harm.", "Safety Rules / Rule 12", False)

    # 7. Manipulation / shame / possessive (Rule 13)
    if _has(low, _MANIPULATION):
        add("manipulation", S.HIGH, "Manipulative, shaming, or possessive.", "Soul Companion Guide / Rule 13", False)

    # 8. Crisis handling (Rule 10 / Safety)
    if crisis and not _has(low, _CRISIS_REFERRAL):
        add("crisis_mishandled", S.CRITICAL, "Crisis with no referral to real-world help.", "Safety Rules / Rule 10", False)

    # 9. Over-escalation of non-real-world content (Rule 11)
    if meaning is not None and meaning.real_world_intent == RealWorldIntent.FALSE and not crisis and _has(low, _ESCALATION):
        add("over_escalation", S.MEDIUM, "Escalates creative/figurative content as a crisis.", "Meaning Protection / Rule 11", True)

    # 10. Generic / robotic / false certainty (Rule 16)
    if _has(low, _GENERIC):
        add("generic_or_robotic", S.MEDIUM, "Generic, robotic, or false-certainty phrasing.", "Reflection Rules / Rule 16", True)

    # 11. Too generic / empty
    if len(text.strip()) < 15:
        add("too_generic", S.MEDIUM, "Response is too short/empty to be meaningful.", "Reflection Rules / Rule 16", True)

    # 12. Question limits (Rules 14/15) — skip during crisis (handled above)
    question_marks = text.count("?")
    if not crisis:
        if plan.listen_only and question_marks > 0:
            add("listening_mode_violation", S.MEDIUM, "Asked a question during listening mode.", "Planner / Rule 15", True)
        elif question_marks > plan.question_count:
            add("too_many_questions", S.MEDIUM, f"Asked {question_marks} questions; plan allows {plan.question_count}.", "Planner / Rule 14", True)

    # 13. Tone mismatch (Rule 15)
    if not crisis and plan.reflection_type != ReflectionType.CELEBRATION and text.count("!") >= 3:
        add("tone_mismatch", S.MEDIUM, "Over-excited tone for a non-celebration plan.", "Planner / Rule 15", True)

    # 14. Depth mismatch (Rule 15)
    if not crisis and len(text) > _DEPTH_MAX_CHARS[plan.depth]:
        add("depth_mismatch", S.MEDIUM, "Response longer than the planned depth.", "Planner / Rule 15", True)

    # --- decision -------------------------------------------------------------
    has_blocking = any(not v.fixable for v in violations)
    if has_blocking:
        status, action, confidence = QualityStatus.REJECTED, "reject", 0.9
    elif violations:
        status, action, confidence = QualityStatus.NEEDS_RETRY, "regenerate", 0.6
    else:
        status, action, confidence = QualityStatus.APPROVED, "deliver", 0.9

    retry_allowed = status == QualityStatus.NEEDS_RETRY
    retry_reason = next((v.message for v in violations if v.fixable), "") if retry_allowed else ""

    return QualityResult(
        request_id=candidate.request_id,
        status=status,
        confidence=confidence,
        reason=f"status={status.value}; violations={len(violations)}; codes={[v.code for v in violations]}",
        violations=tuple(violations),
        recommended_action=action,
        retry_allowed=retry_allowed,
        retry_reason=retry_reason,
        metadata={
            "violation_count": len(violations),
            "response_chars": len(text),
            "question_marks": question_marks,
            "crisis": crisis,
        },
    )
