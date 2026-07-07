"""Conversation Composer — Orchestra node 10, the frontend gateway.

The ONLY Orchestra node permitted to communicate with the frontend. Assembles
approved information into an immutable ConversationPackage. No AI, no response
generation or modification. See docs/CONVERSATION_COMPOSER.md.
"""

from app.orchestra.composer.composer import compose
from app.orchestra.composer.errors import ComposerError
from app.orchestra.composer.schemas import (
    FRONTEND_EVENT_NAMES,
    MEMORY_NOTIFICATION_TEMPLATES,
    SCHEMA_VERSION,
    Action,
    ActionType,
    Attachment,
    AttachmentType,
    Citation,
    ConversationPackage,
    DeliveryStatus,
    FrontendEvent,
    MemoryUpdate,
    Notification,
    NotificationType,
)

__all__ = [
    "compose",
    "ComposerError",
    "ConversationPackage",
    "DeliveryStatus",
    "Attachment",
    "AttachmentType",
    "Action",
    "ActionType",
    "Notification",
    "NotificationType",
    "Citation",
    "MemoryUpdate",
    "FrontendEvent",
    "FRONTEND_EVENT_NAMES",
    "MEMORY_NOTIFICATION_TEMPLATES",
    "SCHEMA_VERSION",
]
