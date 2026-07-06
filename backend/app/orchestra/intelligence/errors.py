"""Structured errors for the Memory Intelligence Engine."""

from __future__ import annotations


class MemoryIntelligenceError(Exception):
    """Raised for structurally invalid input — most importantly, a memory with
    no evidence (no memory exists without evidence, Rule 19)."""

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Memory intelligence error: {errors}")
