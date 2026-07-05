"""Structured errors for the Context Builder (never unstructured throws)."""

from __future__ import annotations


class ContextBuilderError(Exception):
    """Raised for structurally invalid Context Builder input.

    Carries a structured ``errors`` list. Budget/relevance exclusions are not
    errors — they are recorded as ``ExcludedNote`` entries (never silently
    discarded). This is only for malformed input (wrong object types).
    """

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Context builder error: {errors}")
