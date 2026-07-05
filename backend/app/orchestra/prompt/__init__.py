"""Prompt Builder — Orchestra node 6.

Transforms a ContextPackage into an immutable PromptPackage. No AI, no LLM, no
text generation beyond assembling the prompt. See docs/PROMPT_BUILDER.md.
"""

from app.orchestra.prompt.builder import build
from app.orchestra.prompt.errors import PromptBuilderError
from app.orchestra.prompt.schemas import (
    SCHEMA_VERSION,
    GenerationParameters,
    ModelRole,
    PromptMessage,
    PromptPackage,
    PromptStatistics,
    PromptTemplate,
)
from app.orchestra.prompt.templates import (
    FUTURE_TEMPLATE_NAMES,
    IDENTITY_TEXT,
    REFLECTION_TEMPLATE_V1,
    TEMPLATE_REGISTRY,
)

__all__ = [
    "build",
    "PromptBuilderError",
    "PromptPackage",
    "PromptTemplate",
    "PromptMessage",
    "GenerationParameters",
    "PromptStatistics",
    "ModelRole",
    "TEMPLATE_REGISTRY",
    "REFLECTION_TEMPLATE_V1",
    "FUTURE_TEMPLATE_NAMES",
    "IDENTITY_TEXT",
    "SCHEMA_VERSION",
]
