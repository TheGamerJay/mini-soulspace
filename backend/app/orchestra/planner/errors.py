"""Structured errors for the Reflection Planner (never unstructured throws)."""

from __future__ import annotations


class PlannerError(Exception):
    """Raised for structurally invalid planner input.

    Carries a structured ``errors`` list. Ordinary uncertainty is not an error —
    the planner falls back to the simplest safe plan instead. This is only for
    malformed input (wrong object types).
    """

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Planner error: {errors}")
