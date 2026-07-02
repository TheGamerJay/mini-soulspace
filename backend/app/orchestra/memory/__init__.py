"""Memory Retriever — Orchestra node 3 (the Memory Librarian).

Retrieves the minimum set of relevant, user-scoped memories. No AI, no storage,
no reflection. See docs/MEMORY_RETRIEVER.md.
"""

from app.orchestra.memory.errors import RetrievalError
from app.orchestra.memory.retriever import MAX_MEMORIES, retrieve
from app.orchestra.memory.schemas import (
    SCHEMA_VERSION,
    MemoryPriority,
    MemoryType,
    RetrievalResult,
    RetrievedMemory,
)
from app.orchestra.memory.source import DbMemorySource, MemorySource

__all__ = [
    "retrieve",
    "MAX_MEMORIES",
    "RetrievalError",
    "RetrievalResult",
    "RetrievedMemory",
    "MemoryType",
    "MemoryPriority",
    "MemorySource",
    "DbMemorySource",
    "SCHEMA_VERSION",
]
