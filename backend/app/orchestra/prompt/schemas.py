"""PromptTemplate + PromptPackage — immutable, versioned outputs of node 6.

The Prompt Builder assembles (never generates). The PromptPackage is the sole
input to the Response Generator. Additive changes must stay backwards compatible
(optional fields; bump the minor version). Templates are versioned so future
updates never break previous versions.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"


class ModelRole(str, enum.Enum):
    MAIN = "main"
    FAST = "fast"
    VISION = "vision"
    RESEARCH = "research"
    CODING = "coding"
    SUMMARY = "summary"
    IMAGE = "image"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class GenerationParameters(_Frozen):
    """Model configuration only — the Prompt Builder never applies these."""

    temperature: float = 0.7
    top_p: float = 0.9
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    max_tokens: int = 400


class PromptTemplate(_Frozen):
    name: str
    version: str
    model_role: ModelRole
    formatting_instructions: str
    generation: GenerationParameters
    description: str = ""


class PromptMessage(_Frozen):
    role: str  # "system" | "user" | "assistant"
    content: str


class PromptStatistics(_Frozen):
    layer_count: int
    system_prompt_chars: int
    message_count: int
    memory_count: int


class PromptPackage(_Frozen):
    schema_version: str = SCHEMA_VERSION
    package_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: uuid.UUID

    template_name: str
    template_version: str
    template_used: str
    model_role: ModelRole

    system_prompt: str
    conversation_blueprint: tuple[PromptMessage, ...]
    generation_parameters: GenerationParameters

    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    statistics: PromptStatistics
    future_reserved: dict[str, Any] = Field(default_factory=dict)
