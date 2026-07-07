"""Structured errors for the Conversation Composer."""

from __future__ import annotations


class ComposerError(Exception):
    """Raised for structurally invalid input. A non-approved QualityResult is
    NOT an error — it produces a structured failure package instead."""

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Composer error: {errors}")
