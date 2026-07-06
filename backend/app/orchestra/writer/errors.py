"""Structured errors for the Memory Writer."""

from __future__ import annotations


class MemoryWriterError(Exception):
    """Raised for structurally invalid input. Deciding *not* to store is a normal
    ``MemoryDecision`` (``store_memory = False``), never an error."""

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Memory writer error: {errors}")
