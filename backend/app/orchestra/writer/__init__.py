"""Memory Writer — Orchestra node 9.

Decides what (if anything) to remember from an approved exchange, and optionally
persists it to the soul_memories store. No AI, no reflection, no delivery.
See docs/MEMORY_WRITER.md.
"""

from app.orchestra.writer.errors import MemoryWriterError
from app.orchestra.writer.extractor import CandidateMemory, extract
from app.orchestra.writer.schemas import SCHEMA_VERSION, MemoryDecision
from app.orchestra.writer.store import DbMemoryStore, MemoryStore
from app.orchestra.writer.writer import write

__all__ = [
    "write",
    "extract",
    "CandidateMemory",
    "MemoryDecision",
    "MemoryWriterError",
    "MemoryStore",
    "DbMemoryStore",
    "SCHEMA_VERSION",
]
