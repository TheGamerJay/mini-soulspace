"""Structured errors for the Guardian Engine (never unstructured exceptions)."""

from __future__ import annotations


class GuardianError(Exception):
    """Raised for structurally invalid Guardian input.

    Carries a structured ``errors`` list. The Guardian never raises for ordinary
    content — uncertain content is classified conservatively instead (safer
    path). This is only for malformed input (e.g. a non-request object).
    """

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Guardian error: {errors}")
