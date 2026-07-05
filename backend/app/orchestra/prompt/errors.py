"""Structured errors for the Prompt Builder (never unstructured throws)."""

from __future__ import annotations


class PromptBuilderError(Exception):
    """Raised for invalid input, unknown templates, or missing required layers.

    Carries a structured ``errors`` list. The Prompt Builder never guesses and
    never silently omits a required layer — a missing required layer is an error.
    """

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Prompt builder error: {errors}")
