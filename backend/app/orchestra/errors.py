"""Structured error types for the Orchestra."""

from __future__ import annotations


class InputValidationError(Exception):
    """Raised by the Input Receiver when the request cannot be built.

    Carries a structured ``errors`` list so callers/tests can inspect exactly
    what failed without parsing strings. The node never continues with invalid
    data.
    """

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Input validation failed: {errors}")


def error(field: str, code: str, message: str) -> dict[str, str]:
    """Build a single structured error entry."""

    return {"field": field, "code": code, "message": message}
