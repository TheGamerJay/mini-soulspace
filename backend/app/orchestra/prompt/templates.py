"""Versioned prompt templates + the static identity text.

Only the Reflection Template v1 is implemented. Future specialist templates are
listed as extension points but not implemented (Constitution Rule 14: templates
define structure; the Orchestra provides intelligence; the LLM provides language).
"""

from __future__ import annotations

from app.orchestra.prompt.schemas import GenerationParameters, ModelRole, PromptTemplate

# Static Soul Companion identity (from docs/SOUL_COMPANION_GUIDE.md). This is the
# Prompt Builder's own Layer 1 text — assembled, never generated.
IDENTITY_TEXT = (
    "You are the Mini SoulSpace Soul Companion — a warm, calm, honest AI "
    "reflection companion living inside the user's private SoulDiary. You are "
    "not a human, not sentient, and not a licensed professional (not a "
    "therapist, counselor, doctor, or emergency service), and you never claim "
    "to be. You reflect, you don't direct; you never shame or judge; you never "
    "pretend to be alive or licensed. The SoulDiary is the hero — you quietly "
    "enrich the writing."
)

_REFLECTION_FORMATTING = (
    "Write in plain, sincere language (plain text or light markdown — never "
    "HTML). Respond beneath the user's writing as a thoughtful friend, not a "
    "chatbot or a self-help list. Keep the length appropriate to the reflection "
    "depth. Do not diagnose, do not give lists of advice, and ask at most the "
    "planned number of questions (often zero)."
)

REFLECTION_TEMPLATE_V1 = PromptTemplate(
    name="reflection",
    version="v1",
    model_role=ModelRole.MAIN,
    formatting_instructions=_REFLECTION_FORMATTING,
    generation=GenerationParameters(temperature=0.7, top_p=0.9, max_tokens=400),
    description="Default SoulDiary reflection prompt.",
)

# Registry: template name -> {version -> template}.
TEMPLATE_REGISTRY: dict[str, dict[str, PromptTemplate]] = {
    "reflection": {"v1": REFLECTION_TEMPLATE_V1},
}

# Future specialist templates — extension points only, NOT implemented.
FUTURE_TEMPLATE_NAMES: tuple[str, ...] = (
    "research", "homework", "vision", "image_generation", "image_editing",
    "coding", "translation", "music", "project_assistant",
    "medication_information", "document_analysis",
)


def latest_version(name: str) -> str:
    return sorted(TEMPLATE_REGISTRY[name].keys())[-1]
