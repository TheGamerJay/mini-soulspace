"""Structured errors for the Meaning & Intent Engine."""

from __future__ import annotations


class MeaningError(Exception):
    """Raised for structurally invalid input. Ordinary ambiguity is not an error
    — it is reported as ``real_world_intent = unclear`` (never guessed)."""

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Meaning error: {errors}")
