"""User preferences model (foundation for future personalization)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserPreferences(Base, TimestampMixin):
    """Basic per-user preferences.

    Phase 1 keeps this intentionally small — a seam for future personalization
    (birthday/milestone messages, reflection reminders, theme). Advanced
    companion customization is deliberately out of scope.
    """

    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    birthday_messages_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    milestone_messages_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reflection_reminders_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    preferred_theme: Mapped[str] = mapped_column(String(20), nullable=False, default="soul-dark")
    timezone_auto_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped[User] = relationship(back_populates="preferences")
