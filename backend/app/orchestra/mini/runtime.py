"""Local runtime connector — the ONLY place the underlying runtime lives.

Mini SoulSpace is not an Ollama app; the Ollama runtime is an internal
implementation detail sealed inside this file. No other Orchestra node imports or
references it. A runtime is any object with:

    generate(model: str, messages: list[dict], params: dict, timeout_s: float)
        -> RuntimeResponse

raising ``RuntimeTimeout`` or ``RuntimeUnavailable`` on failure. Streaming is a
planned extension (not implemented).
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.orchestra.mini.schemas import RuntimeResponse


class RuntimeTimeout(Exception):
    """The local runtime did not respond within the timeout."""


class RuntimeUnavailable(Exception):
    """The local runtime could not be reached or returned a transport error."""


class OllamaRuntime:
    """Local runtime backed by Ollama's chat API (internal detail)."""

    def __init__(self, base_url: str | None = None):
        self._base = (base_url or settings.OLLAMA_URL).rstrip("/")

    def generate(self, model: str, messages: list[dict], params: dict, timeout_s: float) -> RuntimeResponse:
        payload = {"model": model, "messages": messages, "stream": False, "options": params}
        try:
            resp = httpx.post(f"{self._base}/api/chat", json=payload, timeout=timeout_s)
            resp.raise_for_status()
        except httpx.TimeoutException as exc:
            raise RuntimeTimeout(str(exc)) from exc
        except httpx.HTTPError as exc:
            raise RuntimeUnavailable(str(exc)) from exc

        data = resp.json()
        message = data.get("message") or {}
        return RuntimeResponse(
            text=message.get("content", ""),
            model=data.get("model", model),
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            finish_reason=data.get("done_reason", "stop"),
            duration_ms=int(data.get("total_duration", 0) / 1_000_000),
        )
