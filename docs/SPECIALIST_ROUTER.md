# Specialist Router (Phase 4.2)

> **Status:** Implemented. A permanent Orchestra node between the Prompt Builder
> and the Mini Services. It decides **WHO should help** — never HOW the
> conversation flows (Constitution **Rule 23**). Deterministic — it never
> generates language, never reasons, never replaces the Planner. Source:
> `backend/app/orchestra/router/`.

## The updated Orchestra

```
User → Input Receiver → Meaning & Intent → Guardian → Memory Retriever →
Reflection Planner → Context Builder → Prompt Builder → **Specialist Router** →
Mini Services → Quality Checker → Memory Writer → Memory Intelligence →
Conversation Composer → Frontend
```

The Router replaces the direct call to Mini Core — **Mini Core is now one
available specialist**, selected like any other. Nothing bypasses the Orchestra.

## API contract

```
route(request, meaning, guardian, planner, registry,
      *, requested_capabilities=()) -> RoutingPlan
```

Selections are based on the **Meaning & Intent result, the Guardian's category,
the Planner, the context, and available capabilities — never keywords alone.**
`requested_capabilities` is the seam for future attachments (an image upload
requests `image_understanding`; a CSV requests `data_analysis`).

## RoutingPlan (v1.0, immutable)

`primary_specialist · primary_service · secondary_specialists ·
fallback_specialist · execution_order · unavailable_specialists · reasoning ·
confidence · estimated_complexity (low/medium/high) · parallel_ready ·
future_reserved`. It may select **one, several (sequential), or no** specialists.
Parallel fan-out/fan-in is architecture-only (`parallel_ready = false`).

## Selection behavior

| Situation | Plan |
| --- | --- |
| Plain diary page | Mini Core (the Soul Companion reflects) |
| Homework (`ACADEMIC_HELP` / `tutoring`) | Mini Tutor → falls back to Mini Core while Tutor is architecture-only |
| Medication photo (`image_understanding` + `MEDICAL_INFORMATION`) | Mini Vision → Mini Research (sequential) |
| Research (`internet_research`) | Mini Research |
| Programming (`PROJECT_ASSISTANCE`) | Mini Creator |
| Spreadsheet (`data_analysis` requested) | Mini Analyst |
| **Crisis** | **No specialists** — the Guardian has final authority; the deterministic safety template takes over |

Desired specialists that exist but are not deployable are reported in
`unavailable_specialists`, and the **fallback (Mini Core)** becomes primary —
so specialists activate purely by registry configuration.

## Safety

The Guardian always has final authority. No specialist may bypass the Meaning
Engine, Guardian, Quality Checker, Memory Writer, Memory Intelligence, or the
Conversation Composer — the Router sits *inside* the pipeline and its output
feeds the same verified flow (integration-tested: the router node appears in
every delivery's metrics and is skipped under guardian authority in a crisis).

## Execution

The Mini Engine gained an **additive** `service_key` parameter: the pipeline
passes `RoutingPlan.primary_service`, and the engine resolves that Mini Service
directly (the runtime stays sealed inside the engine). Today only
`mini_core` executes; when another specialist's service lands in
`mini_services.json` and its card flips to `enabled`, it executes with **zero
code changes**.

## Testing

`backend/tests/test_specialist_router.py` — **100% coverage** of
`app.orchestra.router`: registry loading + missing registry, capability
discovery (priority order), diary/homework/research routing, enabled-by-config
selection, multi-specialist sequential routing, unavailable → fallback,
requested capabilities, crisis (no specialists), empty-registry failure,
immutability, invalid inputs, and future-specialist registration. Plus pipeline
integration assertions (router in the verified flow; skipped in crisis).

See also [Mini Services](MINI_SERVICES.md) and the
[Orchestra Constitution](ORCHESTRA_ENGINEERING_RULES.md) (Rules 4, 8, 15, 21, 23).
