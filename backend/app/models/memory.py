"""Long-term memory store (read by the Memory Retriever, node 3).

This is the *store*; the future Memory Writer (a later Orchestra node) populates
it. The Retriever only reads from it — it never writes. Content is clean text
(memory-friendly), scoped per user, with soft-delete + archive and a
self-referential ``related_to_id`` seam for future graph retrieval.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class SoulMemory(Base, TimestampMixin):
    __tablename__ = "soul_memories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    memory_type: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), index=True, nullable=False, default="medium")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    keywords: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Future graph retrieval seam (goal -> interview -> job -> promotion).
    related_to_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("soul_memories.id", ondelete="SET NULL"), nullable=True
    )
    source_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    last_referenced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Memory Intelligence provenance (Phase 3.8.5) -------------------------
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.6)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="souldiary")
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON blob
    verification_status: Mapped[str] = mapped_column(String(30), nullable=False, default="unverified")
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    user: Mapped[User] = relationship()
    versions: Mapped[list[SoulMemoryVersion]] = relationship(
        back_populates="memory", cascade="all, delete-orphan"
    )


class SoulMemoryVersion(Base):
    """Immutable version-history row — history must never be lost."""

    __tablename__ = "soul_memory_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("soul_memories.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.6)
    reason_changed: Mapped[str] = mapped_column(String(100), nullable=False)
    author: Mapped[str] = mapped_column(String(20), nullable=False, default="system")
    is_outdated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    memory: Mapped[SoulMemory] = relationship(back_populates="versions")
