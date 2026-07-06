"""Memory store abstraction for the Writer.

Reading existing memories here is for **de-duplication / evolution only** — it is
not reflection retrieval (that is node 3's job). The Writer depends on this
interface so a future store can plug in without changes.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import SoulMemory


class MemoryStore(Protocol):
    def existing(self, user_id: uuid.UUID) -> list[SoulMemory]: ...
    def create(self, **fields) -> SoulMemory: ...
    def update(self, memory: SoulMemory, **fields) -> SoulMemory: ...


class DbMemoryStore:
    """Concrete store backed by the ``soul_memories`` table."""

    def __init__(self, db: Session):
        self._db = db

    def existing(self, user_id: uuid.UUID) -> list[SoulMemory]:
        return list(
            self._db.scalars(
                select(SoulMemory).where(
                    SoulMemory.user_id == user_id, SoulMemory.is_deleted.is_(False)
                )
            ).all()
        )

    def create(self, **fields) -> SoulMemory:
        memory = SoulMemory(**fields)
        self._db.add(memory)
        self._db.flush()
        return memory

    def update(self, memory: SoulMemory, **fields) -> SoulMemory:
        for key, value in fields.items():
            setattr(memory, key, value)
        self._db.flush()
        return memory
