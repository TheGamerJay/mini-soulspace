# Mini Engine (Orchestra Node 7)

> **Status:** Implemented (Phase 3.6). The **first** node allowed to talk to a
> local language model. Source: `backend/app/orchestra/mini/`.

## The idea

**Mini SoulSpace is not an Ollama app — it owns its intelligence layer.** The
Orchestra talks to **Mini Services** (by name); the Mini Engine maps a service to
a local model and calls the runtime. The runtime (currently Ollama) is an
internal implementation detail **sealed inside `runtime.py`** — no other node
imports or references it.

```
Orchestra  →  Mini Engine  →  Mini Services  →  Local Models
(intelligence)  (runtime access)   (by name)      (language)
```

## Purpose (single responsibility)

Receive a `PromptPackage`, resolve a Mini Service, call the local runtime, and
return an immutable `CandidateResponse`. It does **not** plan, reflect, judge
quality, read/write memory, or deliver the final response.

## Inputs / Outputs (API contract)

```
generate(prompt_package, *, runtime=None, timeout_s=None, retries=None,
         services_path=DEFAULT_SERVICES_PATH) -> CandidateResponse
```

- **Input:** the immutable `PromptPackage` (never modified). The `runtime` is
  injectable so the Orchestra never binds to a model runtime and tests never hit
  the network.
- **Output:** an immutable `CandidateResponse`. `RuntimeResponse` is **internal**
  — raw runtime payloads are never exposed downstream.

## Mini Services

The Orchestra uses **service names only**. Model roles map to services:

| Role | Mini Service | Purpose |
| --- | --- | --- |
| main | **Mini Core** | Primary Soul Companion conversations |
| fast | **Mini Swift** | Fast lightweight tasks |
| summary | **Mini Insight** | Summaries, tagging, organization, memory analysis |
| coding | **Mini Creator** | Coding, writing, creative generation |
| vision | Mini Vision | Image understanding *(future)* |
| research | Mini Research | Research and document analysis *(future)* |
| image | Mini Canvas | Image generation and editing *(future)* |

Additional catalog services (Mini Harmony — music/lyrics, Mini Tutor — learning,
Mini Translate — translation) are reserved names for future config entries. New
services are added by editing `mini_services.json` — **no Orchestra redesign**.

### Config: `mini_services.json`
Bundled at `backend/app/orchestra/mini/mini_services.json` (so it ships in the
container). Each entry: `display_name`, `purpose`, `runtime`, `model`.

## CandidateResponse (v1.0, immutable)

`schema_version` · `response_id` · `created_at` · `request_id` · `service_name` ·
`service_display_name` · `model_used` · `response_text` · `generation_time_ms` ·
`token_counts` · `finish_reason` · `confidence` · `metadata`.

`metadata` carries **metrics only** (retry_count, attempts, prompt_chars,
response_chars, timeout_ms) — never journal content or personal data.

## Local runtime

`runtime.py` holds `OllamaRuntime` (Ollama `/api/chat`) and the runtime
exceptions `RuntimeTimeout` / `RuntimeUnavailable`. Any object implementing
`generate(model, messages, params, timeout_s) -> RuntimeResponse` is a valid
runtime. **Streaming** is a planned extension — not implemented.

## Error handling

Returns structured `MiniEngineError` (never crashes the Orchestra, never
fabricates a response). Codes: `invalid_input`, `missing_service`,
`missing_config`, `runtime_unavailable`, `timeout`, `retry_failure`,
`malformed_runtime_response`, `empty_response`.

## Retries & metrics

Configurable `timeout_s` and `retries` (defaults from `MINI_TIMEOUT_SECONDS` /
`MINI_RETRIES`). With `retries=0`, a single failure surfaces its specific code;
with retries, exhausting all attempts yields `retry_failure`. Metrics captured:
generation timing, prompt/response sizes, retry count — **no personal content
logged**.

## Testing

`backend/tests/test_mini_engine.py` — **100% coverage** of `app.orchestra.mini`
(`pytest-cov`): success + service resolution, elapsed-time fallback, missing
service, missing config, invalid input, timeout, runtime-unavailable, retry
success, retry failure, malformed response, empty response, immutability, metrics,
no raw-payload/journal leak, and the sealed Ollama runtime (success, timeout,
connect error, HTTP status error) via a mocked `httpx`.

## Where it sits

Node **7 of 10** in the [Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md).
Consumes the [Prompt Builder](PROMPT_BUILDER.md)'s `PromptPackage`; its
`CandidateResponse` feeds the Quality Checker (node 8). Governed by the
[Orchestra Constitution](ORCHESTRA_ENGINEERING_RULES.md) (esp. Rules 5, 14, 15).
