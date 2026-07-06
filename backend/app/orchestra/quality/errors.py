"""Structured errors for the Quality Checker."""

from __future__ import annotations


class QualityCheckerError(Exception):
    """Raised for structurally invalid input (not for ordinary rejections —
    those are reported as a ``QualityResult`` with ``status = rejected``)."""

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Quality checker error: {errors}")
