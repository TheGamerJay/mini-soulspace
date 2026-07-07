# Orchestra Integration & Validation (Phase 4.0)

> **Status:** Implemented. All ten Orchestra nodes are wired into **one fully
> operational pipeline** — the SoulDiary talks back. No new nodes were built and
> nothing was redesigned. Source: `backend/app/orchestra/pipeline.py`.

## The pipeline

```
User → Input Receiver → Meaning & Intent → Guardian → Memory Retriever →
Reflection Planner → Context Builder → Prompt Builder → Mini Engine →
Quality Checker → Memory Writer (+ Memory Intelligence) → Conversation Composer
→ Frontend
```

`run_orchestra(db, user, book_id, chapter_id, page_id, *, runtime=, config=)`
executes the flow and returns an `OrchestraOutcome` (trace, package, metrics).
**Nothing bypasses the pipeline** (Constitution **Rule 21**): the API routes call
`run_orchestra`, which delivers only through the Composer (Rule 20), which
delivers only Quality-approved candidates (Rule 17).

### Crisis short-circuit
When the Guardian raises a crisis, Context/Prompt/Mini Engine are **skipped**
(logged as skipped, reason `crisis_short_circuit`) and a **deterministic safety
template** becomes the candidate — still verified by the Quality Checker and
still delivered only through the Composer. Crisis content is never stored as
memory (Guardian blocks storage).

### Quality retry
A fixable candidate (`needs_retry`) is regenerated up to
`quality_retry_limit` times and re-verified each time; exhausted retries become
a structured failure package.

## End-to-end flow (the book experience)

Open SoulBook → open Chapter → write → **Close SoulDiary** →
page **saves first** → the Orchestra executes → the reflection appears beneath
the writing (`data-slot="ai-reflection"`) → the **ribbon bookmark** slides in →
the book closes → it returns to the shelf → the location (book/chapter/page/
cursor/last-opened/session) is remembered. Reopening: the Soul Library shows the
ribboned book and a "Continue your story" card that returns to the bookmarked page.

### API
| Endpoint | Purpose |
| --- | --- |
| `POST /api/soulbooks/{b}/chapters/{c}/pages/{p}/close` | final save + bookmark + run the Orchestra |
| `POST /api/soulbooks/{b}/chapters/{c}/pages/{p}/reflect` | run the Orchestra on a saved page |
| `GET /api/soulbooks/bookmark` | the ribbon bookmark (reopen target) |

## Orchestra Trace

Every request receives a **Trace ID** at the pipeline entrance; it is stamped
into the `OrchestraRequest` metadata and appears in every node log line and the
outcome — one ID to follow a request through all ten nodes.

## Pipeline logging

Every node emits structured logs: `orchestra trace=<id> node=<name>
status=<started|completed|failed|skipped> ms=<n> reason=<r>`. **No journal
content ever appears in logs** (verified by test). Logging, metrics and tracing
are configurable.

## Failure recovery

Any node failure **stops safely**: a structured failure package
(`not_delivered`, failed node + reason) is returned; the Orchestra never
crashes, memories are never corrupted (the memory stage can fail without
blocking delivery), and **the diary page — saved and committed before the
Orchestra runs — is never lost.** Saving always has priority.

## Performance metrics

Per-node execution time, total Orchestra time, and the slowest node are captured
per run (config-gated) — preparation for a future dashboard. Debug mode
(`orchestra.json: debug_mode`) exposes metrics through the API **for developers
only**; users never see debug information.

## Configuration — `orchestra.json`

`log_execution · trace_requests · save_node_metrics · allow_parallel_nodes ·
performance_metrics · debug_mode · quality_retry_limit` — nothing hardcoded;
missing config falls back to safe defaults (never crashes).

## Validation

`backend/tests/test_orchestra_integration.py` — true end-to-end tests (the real
pipeline; only the sealed runtime is faked): 17 delivery scenarios (normal /
happy / sad / goal / birthday / project / creative / novel+fictional violence /
poem / song lyrics / homework / research / medication / image placeholder /
health awareness / historical / metaphor), real crisis (template + no memory),
Guardian rejection, quality retry recovered + exhausted, memory written +
intelligence assessed, memory evolution, nothing-worth-remembering, runtime-down
recovery (page survives), input failure, memory-failure-never-blocks-delivery,
trace propagation + content-free logging, metrics + slowest node, observability
toggles, config fallback, and the reflect/close/bookmark API round-trip.
**`app.orchestra.pipeline`: 100% coverage.**

## Where this leaves the app

Phase 0 foundation → Phase 1 auth → Phase 2 SoulBook engine → Phases 2.5–3.9 the
Orchestra → **Phase 4.0: Mini SoulSpace works end-to-end. The SoulDiary talks
back.** Next: Phase 4.1 — Soul Companion Experience.
