"""Version-history store for the Memory Intelligence Engine.

History must never be lost: every change writes an immutable version row. The
engine depends on this interface so future stores plug in without changes.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import SoulMemory, SoulMemoryVersion


class IntelligenceStore(Protocol):
    def versions(self, memory_id: uuid.UUID) -> list[SoulMemoryVersion]: ...
    def record_version(self, memory: SoulMemory, *, reason: str, author: str, is_outdated: bool) -> SoulMemoryVersion: ...
    def stamp(self, memory: SoulMemory, **fields) -> SoulMemory: ...
    def corrections_by_type(self, user_id: uuid.UUID) -> dict[str, int]: ...


class DbIntelligenceStore:
    """Concrete store backed by ``soul_memory_versions``."""

    def __init__(self, db: Session):
        self._db = db

    def versions(self, memory_id: uuid.UUID) -> list[SoulMemoryVersion]:
        return list(
            self._db.scalars(
                select(SoulMemoryVersion)
                .where(SoulMemoryVersion.memory_id == memory_id)
                .order_by(SoulMemoryVersion.version.asc())
            ).all()
        )

    def record_version(
        self, memory: SoulMemory, *, reason: str, author: str, is_outdated: bool
    ) -> SoulMemoryVersion:
        row = SoulMemoryVersion(
            memory_id=memory.id,
            version=memory.version,
            title=memory.title,
            summary=memory.summary,
            confidence=memory.confidence,
            reason_changed=reason,
            author=author,
            is_outdated=is_outdated,
        )
        self._db.add(row)
        self._db.flush()
        return row

    def stamp(self, memory: SoulMemory, **fields) -> SoulMemory:
        for key, value in fields.items():
            setattr(memory, key, value)
        self._db.flush()
        return memory

    def corrections_by_type(self, user_id: uuid.UUID) -> dict[str, int]:
        rows = self._db.scalars(
            select(SoulMemoryVersion)
            .join(SoulMemory, SoulMemory.id == SoulMemoryVersion.memory_id)
            .where(SoulMemory.user_id == user_id, SoulMemoryVersion.reason_changed == "user_correction")
        ).all()
        counts: dict[str, int] = {}
        for row in rows:
            counts[row.memory.memory_type] = counts.get(row.memory.memory_type, 0) + 1
        return counts
