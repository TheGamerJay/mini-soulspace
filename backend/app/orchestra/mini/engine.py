"""Mini Engine — Orchestra node 7 (first node with model access).

Single responsibility: receive a PromptPackage, resolve a Mini Service, call the
local runtime, and return an immutable CandidateResponse. It does not plan,
reflect, judge quality, read/write memory, or deliver the final response.

The runtime is injected (default ``OllamaRuntime``) so the Orchestra never binds
to a model runtime and tests never touch the network.
"""

from __future__ import annotations

import time
from pathlib import Path

from app.core.config import settings
from app.orchestra.mini.errors import MiniEngineError, err
from app.orchestra.mini.registry import DEFAULT_SERVICES_PATH, load_registry, resolve_service
from app.orchestra.mini.runtime import OllamaRuntime, RuntimeTimeout, RuntimeUnavailable
from app.orchestra.mini.schemas import (
    CandidateResponse,
    MiniService,
    RuntimeResponse,
    TokenCounts,
)
from app.orchestra.prompt.schemas import PromptPackage


def _params(prompt_package: PromptPackage) -> dict:
    g = prompt_package.generation_parameters
    return {
        "temperature": g.temperature,
        "top_p": g.top_p,
        "presence_penalty": g.presence_penalty,
        "frequency_penalty": g.frequency_penalty,
        "num_predict": g.max_tokens,
    }


def _candidate(
    prompt_package: PromptPackage,
    service: MiniService,
    rr: RuntimeResponse,
    *,
    elapsed_ms: int,
    retry_count: int,
    attempts: int,
    prompt_chars: int,
    timeout_s: float,
) -> CandidateResponse:
    # metadata carries metrics only — never journal content or personal data.
    metadata = {
        "retry_count": retry_count,
        "attempts": attempts,
        "prompt_chars": prompt_chars,
        "response_chars": len(rr.text),
        "timeout_ms": int(timeout_s * 1000),
    }
    return CandidateResponse(
        request_id=prompt_package.request_id,
        service_name=service.key,
        service_display_name=service.display_name,
        model_used=service.model,
        response_text=rr.text,
        generation_time_ms=rr.duration_ms or elapsed_ms,
        token_counts=TokenCounts(
            prompt=rr.prompt_tokens,
            completion=rr.completion_tokens,
            total=rr.prompt_tokens + rr.completion_tokens,
        ),
        finish_reason=rr.finish_reason,
        confidence=prompt_package.confidence,
        metadata=metadata,
    )


def generate(
    prompt_package: PromptPackage,
    *,
    runtime=None,
    timeout_s: float | None = None,
    retries: int | None = None,
    services_path: Path | str = DEFAULT_SERVICES_PATH,
    service_key: str | None = None,
) -> CandidateResponse:
    """Resolve a Mini Service and generate a candidate response.

    ``service_key`` (Phase 4.2, additive) lets the Specialist Router address a
    Mini Service directly; without it, the template's model role resolves as
    before.
    """

    if not isinstance(prompt_package, PromptPackage):
        raise MiniEngineError([err("prompt_package", "invalid_input", "Expected a PromptPackage.")])

    runtime = runtime or OllamaRuntime()
    timeout_s = settings.MINI_TIMEOUT_SECONDS if timeout_s is None else timeout_s
    retries = settings.MINI_RETRIES if retries is None else retries

    try:
        registry = load_registry(services_path)
    except (OSError, ValueError):  # missing file / bad JSON
        raise MiniEngineError([err("config", "missing_config", "Mini service registry could not be loaded.")])

    if service_key is not None:
        if service_key not in registry:
            raise MiniEngineError(
                [err("service", "missing_service", f"No Mini Service named '{service_key}'.")]
            )
        service = registry[service_key]
    else:
        try:
            service = resolve_service(prompt_package.model_role, registry)
        except KeyError:
            raise MiniEngineError(
                [err("service", "missing_service", f"No Mini Service for role '{prompt_package.model_role.value}'.")]
            )

    messages = [{"role": m.role, "content": m.content} for m in prompt_package.conversation_blueprint]
    params = _params(prompt_package)
    prompt_chars = sum(len(m["content"]) for m in messages)

    last_code = "unknown"
    attempts = 0
    for attempt in range(retries + 1):
        attempts = attempt + 1
        start = time.perf_counter()
        try:
            rr = runtime.generate(service.model, messages, params, timeout_s)
        except RuntimeTimeout:
            last_code = "timeout"
            continue
        except RuntimeUnavailable:
            last_code = "runtime_unavailable"
            continue
        if not isinstance(rr, RuntimeResponse):
            last_code = "malformed_runtime_response"
            continue
        if not rr.text.strip():
            last_code = "empty_response"
            continue
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return _candidate(
            prompt_package, service, rr,
            elapsed_ms=elapsed_ms, retry_count=attempt, attempts=attempts,
            prompt_chars=prompt_chars, timeout_s=timeout_s,
        )

    code = last_code if retries == 0 else "retry_failure"
    raise MiniEngineError([err("runtime", code, f"Generation failed after {attempts} attempt(s): {last_code}.")])
