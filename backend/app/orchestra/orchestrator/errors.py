"""Structured errors for the Specialist Orchestrator."""

from __future__ import annotations


class OrchestratorError(Exception):
    """Raised for structurally invalid input, an unloadable config, or a
    forbidden workspace overwrite. Ordinary specialist failures are NOT errors —
    they become structured task results and degrade gracefully."""

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Orchestrator error: {errors}")

    @property
    def code(self) -> str:
        return self.errors[0]["code"] if self.errors else "unknown"
