# Specialist Orchestrator (Phase 4.25)

> **Status:** Implemented. The Router decides **WHO** should help; the
> Orchestrator decides **HOW the selected specialists work together** —
> sequentially, safely, deterministically (Constitution **Rule 24**). It never
> replaces the Orchestra or the Router, never performs specialist work, and
> never generates user-facing responses. Source:
> `backend/app/orchestra/orchestrator/`.

## The core rule

```
Router chooses the team → Orchestrator controls the work →
Specialists perform only their assigned task → Quality Checker verifies →
Conversation Composer delivers
```

## API contract

```
build_execution_plan(routing_plan, config) -> SpecialistExecutionPlan
orchestrate(routing_plan, executors, *, trace_id, config) -> OrchestrationResult
```

`executors` maps a specialist name to a callable that performs **one assigned
task** — `(task, dependency_outputs) -> structured output dict`. Specialists
never talk to each other and never see shared state: the Orchestrator passes
dependency outputs in and records results into a **write-once workspace**.

## Schemas (v1.0, immutable)

- **SpecialistTask** — `specialist · order · role (primary/supporting) ·
  assignment · depends_on · timeout_s · retries`.
- **SpecialistExecutionPlan** — ordered tasks, primary + supporting specialists,
  `truncated` (beyond the per-request cap), `allow_parallel=false` (future).
- **SpecialistResult** — `status (completed/failed/skipped/timeout/degraded) ·
  output · confidence · attempts · duration_ms · error`.
- **SpecialistWorkspace** — write-once per specialist; overwriting another
  specialist's result raises (`workspace_conflict`). No races, no shared-state
  mutation.
- **OrchestrationResult** — `trace_id · routing_plan_id · execution_order ·
  primary/supporting · completed/failed/skipped tasks · conflicts ·
  merged_result · confidence · status (completed/degraded/failed/blocked) ·
  audit_trail · metadata`.

## No overlap, no races

Only one specialist is primary; the others provide **evidence, extracted data,
analysis, or context**. Execution is strictly sequential in this phase
(`allow_parallel_execution=false`); parallel fan-out/fan-in is architecture only.
Only the Orchestrator merges outputs: `merged_result = { primary: …, evidence:
{specialist: output} }`.

## Dependencies

Declared in configuration (e.g. `mini_research → mini_vision`): a dependency
binds only when that specialist runs earlier in the same plan. If a dependency
fails or is skipped, the dependent is **skipped — never guessed**.

## Failure / retry / timeout handling

- Per-specialist configurable retries (bounded — never infinite) and a soft
  timeout per attempt; a timeout result is discarded, never delivered.
- A failed specialist **never crashes the Orchestra**: it becomes a structured
  failed result, and safe siblings continue.
- `fail_fast_on_primary_failure`: when the primary fails, remaining tasks are
  skipped and the Router's **fallback specialist** (Mini Core) is executed as the
  primary voice — the outcome is honest (`degraded`), never hidden.
- `allow_degraded_results=false` turns any degradation into a failure — serious
  uncertainty is never masked. Missing specialist results are never fabricated.

## Conflict detection

Two completed specialists reporting **different values for the same finding
key** (e.g. Vision says one medication, Research says another) become a
structured `Conflict {key, specialists, values}`. Conflicts are **never resolved
by guessing** — the result is marked degraded, confidence drops, and the Quality
Checker receives them downstream.

## Audit trail

Every event is recorded in order: `task_started · attempt · retried · completed
· failed · timeout · skipped · degraded · conflict_detected · merged · blocked`
— a full, sequenced account of one orchestration.

## Configuration — `specialist_orchestrator.json`

`default_timeout_seconds · default_retries · allow_parallel_execution (false) ·
max_specialists_per_request · fail_fast_on_primary_failure ·
allow_degraded_results · low_confidence_threshold · dependencies`. Nothing
hardcoded.

## Safety

Guardian authority always wins: a crisis routing plan (no specialists) makes the
Orchestrator **do nothing** (`status=blocked`). No specialist can bypass the
Meaning Engine, Guardian, Quality Checker, memory nodes, or the Composer — the
Orchestrator sits between the Router and the Mini Services inside the verified
pipeline.

## Activation

With only Mini Core executable today, every execution plan degenerates to a
single task, so the live pipeline still calls the Mini Engine directly. The
pipeline switches to orchestrated execution in **Phase 4.3 (Mini Vision)** — the
first multi-specialist flow — with zero redesign: the Router's plan and the
executor map already match this contract.

## Testing

`backend/tests/test_specialist_orchestrator.py` — **100% coverage** of
`app.orchestra.orchestrator` (24 tests): plan roles/dependencies/order,
dependency-only-when-present, truncation, single + multi-specialist sequential
merge, failed dependency → skipped dependent, retry success/bounded failure,
soft timeout, missing executor, fail-fast, fallback recovery + fallback failure,
conflict detection, low-confidence degradation, degraded-not-allowed → failed,
guardian-blocked no-op, workspace write-once (no overwrite), audit ordering,
immutability, config loading, invalid inputs.
