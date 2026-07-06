"""SQLAlchemy ORM models.

Importing every model here ensures they register on ``Base.metadata`` for
Alembic autogeneration and test schema creation.
"""

from app.models.auth import AgreementDocument, RefreshSession, UserAgreement
from app.models.memory import SoulMemory, SoulMemoryVersion
from app.models.preferences import UserPreferences
from app.models.soulbook import (
    ContentFormat,
    SoulBook,
    SoulBookmark,
    SoulChapter,
    SoulPage,
    SoulRecentBook,
    SoulRecentChapter,
)
from app.models.user import User

__all__ = [
    "User",
    "RefreshSession",
    "UserAgreement",
    "AgreementDocument",
    "UserPreferences",
    "SoulBook",
    "SoulChapter",
    "SoulPage",
    "SoulBookmark",
    "SoulRecentBook",
    "SoulRecentChapter",
    "ContentFormat",
    "SoulMemory",
    "SoulMemoryVersion",
]
