"""Structured errors for the Specialist Router."""

from __future__ import annotations


class RouterError(Exception):
    """Raised for structurally invalid input or an unloadable registry."""

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Router error: {errors}")

    @property
    def code(self) -> str:
        return self.errors[0]["code"] if self.errors else "unknown"
