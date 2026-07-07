"""ConversationPackage — immutable, versioned output of node 10 (the Composer).

The ONLY payload the frontend ever receives from the Orchestra. Attachment /
action / notification / citation types are **architecture only** in Phase 3.9 —
the shapes exist so future specialists plug in without redesign, but nothing is
implemented or displayed yet.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"


class DeliveryStatus(str, enum.Enum):
    DELIVERED = "delivered"
    NOT_DELIVERED = "not_delivered"


class AttachmentType(str, enum.Enum):
    """Future attachment kinds — architecture only, not implemented."""

    IMAGE = "image"
    GENERATED_IMAGE = "generated_image"
    DOCUMENT = "document"
    PDF = "pdf"
    AUDIO = "audio"
    VOICE = "voice"
    VIDEO = "video"
    RESEARCH_REPORT = "research_report"
    CODE_FILE = "code_file"
    MODEL_3D = "model_3d"


class ActionType(str, enum.Enum):
    """Future UI actions — architecture only, not implemented."""

    OPEN_SOULDIARY = "open_souldiary"
    OPEN_PROJECT = "open_project"
    CREATE_REMINDER = "create_reminder"
    GENERATE_IMAGE = "generate_image"
    START_VOICE_CHAT = "start_voice_chat"
    VIEW_MEMORY = "view_memory"
    VIEW_TIMELINE = "view_timeline"


class NotificationType(str, enum.Enum):
    """Future notifications — architecture only, not implemented."""

    BIRTHDAY = "birthday"
    MILESTONE = "milestone"
    MEMORY_UPDATED = "memory_updated"
    GOAL_ACHIEVED = "goal_achieved"
    PROJECT_PROGRESS = "project_progress"
    STREAK = "streak"
    ANNIVERSARY = "anniversary"
    REMINDER = "reminder"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class Attachment(_Frozen):
    type: AttachmentType
    ref: str
    label: str = ""


class Action(_Frozen):
    type: ActionType
    label: str
    payload: dict[str, Any] = Field(default_factory=dict)


class Notification(_Frozen):
    type: NotificationType
    text: str


class Citation(_Frozen):
    """Future research/document/memory/knowledge citation — architecture only."""

    kind: str  # research | document | memory | knowledge
    ref: str
    label: str = ""


class MemoryUpdate(_Frozen):
    """Structured summary of what the memory system did this turn."""

    op: str  # create | update | none
    memory_type: str | None = None
    importance: str | None = None
    title: str | None = None
    confidence: float | None = None
    verification_status: str | None = None


class FrontendEvent(_Frozen):
    name: str
    payload: dict[str, Any] = Field(default_factory=dict)


#: Known frontend event names — future events extend naturally.
FRONTEND_EVENT_NAMES: tuple[str, ...] = (
    "ConversationDelivered",
    "ConversationNotDelivered",
    "MemoryStored",
    "MemoryUpdated",
    "BirthdayDetected",
    "MilestoneReached",
    "AttachmentReady",
    "ImageGenerated",
    "ResearchCompleted",
    "VoiceReady",
)

#: Future memory-notification copy — PREPARED, not displayed yet.
MEMORY_NOTIFICATION_TEMPLATES: dict[str, str] = {
    "create": "I'll remember that.",
    "update": "Your memory has been updated.",
    "project": "Your project has been updated.",
    "birthday": "Your birthday has been saved.",
}


class ConversationPackage(_Frozen):
    schema_version: str = SCHEMA_VERSION
    package_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: uuid.UUID

    status: DeliveryStatus
    text: str
    attachments: tuple[Attachment, ...] = Field(default_factory=tuple)
    actions: tuple[Action, ...] = Field(default_factory=tuple)
    memory_updates: tuple[MemoryUpdate, ...] = Field(default_factory=tuple)
    notifications: tuple[Notification, ...] = Field(default_factory=tuple)
    citations: tuple[Citation, ...] = Field(default_factory=tuple)
    sources: tuple[str, ...] = Field(default_factory=tuple)
    frontend_events: tuple[FrontendEvent, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
