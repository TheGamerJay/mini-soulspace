"""Memory source abstraction.

The Retriever depends on this interface, not on any concrete store — so a future
**semantic** source (pgvector) or **graph** source can plug in without changing
the Retriever (Constitution: loose coupling, model-agnostic).
"""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import SoulMemory


class MemorySource(Protocol):
    """Returns candidate memories for a user (already ownership-scoped and
    excluding deleted/archived). The Retriever does the relevance selection."""

    def candidates(self, user_id: uuid.UUID) -> list[SoulMemory]: ...


class DbMemorySource:
    """Concrete source backed by the ``soul_memories`` table."""

    def __init__(self, db: Session):
        self._db = db

    def candidates(self, user_id: uuid.UUID) -> list[SoulMemory]:
        return list(
            self._db.scalars(
                select(SoulMemory).where(
                    SoulMemory.user_id == user_id,
                    SoulMemory.is_deleted.is_(False),
                    SoulMemory.is_archived.is_(False),
                )
            ).all()
        )
