"""Structured errors for Mini Vision."""

from __future__ import annotations


class VisionError(Exception):
    """Raised for structurally invalid input or an unloadable config.

    Content problems (unsupported format, oversized, unreadable) are NOT errors —
    they become honest, degraded VisionResults with warnings."""

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Vision error: {errors}")

    @property
    def code(self) -> str:
        return self.errors[0]["code"] if self.errors else "unknown"
