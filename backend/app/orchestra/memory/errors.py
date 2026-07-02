"""Structured errors for the Memory Retriever (never unstructured throws)."""

from __future__ import annotations


class RetrievalError(Exception):
    """Raised for structurally invalid retriever input.

    Carries a structured ``errors`` list. Ordinary "no relevant memories" is not
    an error — it returns an empty RetrievalResult. This is only for malformed
    input (e.g. a non-request / non-guardian object).
    """

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Retrieval error: {errors}")
