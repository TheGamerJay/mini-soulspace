"""Structured errors for the Mini Engine (never crash the Orchestra)."""

from __future__ import annotations


class MiniEngineError(Exception):
    """Structured Mini Engine failure.

    ``code`` is one of: invalid_input, missing_service, missing_config,
    runtime_unavailable, timeout, retry_failure, malformed_runtime_response,
    empty_response. The Mini Engine never fabricates a response and never lets an
    unstructured exception escape to the Orchestra.
    """

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"Mini engine error: {errors}")

    @property
    def code(self) -> str:
        return self.errors[0]["code"] if self.errors else "unknown"


def err(field: str, code: str, message: str) -> dict[str, str]:
    return {"field": field, "code": code, "message": message}
