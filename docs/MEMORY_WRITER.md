# Memory Writer (Orchestra Node 9)

> **Status:** Implemented (Phase 3.8). Decides what — if anything — a completed,
> **approved** exchange should become a long-term memory, and optionally persists
> it. Deterministic, rule-based — **no AI**, no reflection, no Mini Engine, no
> retrieval-for-reflection, no delivery. Source: `backend/app/orchestra/writer/`.

## Purpose (single responsibility)

Evaluate the finished conversation and decide whether something is valuable
enough to remember. Default posture: **"when in doubt, don't save it."** Mini
remembers *fewer* things, but the *right* things (Constitution **Rule 18**).

## Pipeline

```
Approved Candidate → Memory Writer → MemoryDecision → (optional Memory Record) → Final Responder
```

## Inputs / Outputs (API contract)

```
write(request, quality, guardian, *, meaning=None, store=None) -> MemoryDecision
```

- **Only APPROVED** `QualityResult`s create memories — rejected / needs_retry
  never do, nor does Guardian-blocked content (`allow_memory_storage == False`).
- `store` (a `MemoryStore`) is optional: with it, the decision is **persisted**
  to `soul_memories`; without it, only the decision is returned. Invalid input
  raises a structured `MemoryWriterError`.
- Facts are extracted from the **user's own writing** (never the AI response) —
  nothing is fabricated, inferred, or exaggerated.

## MemoryDecision (v1.0, immutable)

`schema_version` · `decision_id` · `created_at` · `request_id` · `store_memory` ·
`importance` · `memory_type` · `title` · `summary` · `reason` · `confidence` ·
`metadata` (`op`, `memory_id`, `linked_to`, `keywords`).

## Memory types

Goal · Achievement · Milestone · Birthday · Anniversary · Preference · Project ·
Relationship · Life Event · Skill · Habit · Routine · Favorite · Reminder
Preference · Creative Project · Learning Progress · Health Preference · Travel ·
Pet · Quote · Custom (extends the Retriever's shared `MemoryType` — additive, so
the Retriever accepts them). Future types extend naturally.

## Importance system

`Low` (temporary preference) · `Medium` (favorite food/music) · `High` (birthday,
long-term project, major goal, relationship) · `Critical` (death of a loved one,
life-changing event). Critical memories are handled carefully and never
referenced casually (Memory Rules).

## Do not store

Small talk, one-time jokes, temporary emotions, model errors, rejected responses,
Guardian-blocked content, hidden prompts / system messages / runtime info. If no
clear first-person fact is present, the decision is `store_memory = false`.

## Duplicate detection

Before storing, the Writer reads existing memories **for de-duplication only**
(this is not reflection retrieval). A match is an existing memory of the same
type sharing a significant keyword. An exact-summary match → **do nothing**
(`duplicate`); never create clutter.

## Project evolution

Projects stay **one evolving memory**: a later update to the same project
(shared keywords, different summary) **updates in place** (`op = update`) instead
of creating dozens of rows.

## Preference evolution

Preferences change (favorite color blue → green): the existing memory is
**updated in place**, not duplicated.

## Relationship evolution (graph-ready)

Relationships evolve ("my son started kindergarten" → "graduated" → "married").
Rather than overwrite history, a new relationship memory is **created and linked**
to the prior one via `related_to_id` — preparing the timeline for future graph
support.

## Quality requirements

Never fabricate, infer, exaggerate, or rewrite history. Only facts supported by
the conversation are stored. Nothing is permanently locked — future phases add
user view / edit / delete / export / import.

## Testing

`backend/tests/test_memory_writer.py` — **100% coverage** of
`app.orchestra.writer` (`pytest-cov`): birthday/goal/achievement/preference/
relationship/project/critical types and importance, nothing-worth-remembering,
rejected-quality and Guardian-blocked gates, immutability, invalid inputs,
sentence fallback, and DB-backed persistence, exact-duplicate skip, one-off
same-type skip, preference/project evolution (update-in-place), and relationship
linking.

## Where it sits

Node **9 of 10** in the [Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md).
Runs only after the [Quality Checker](QUALITY_CHECKER.md) approves; writes to the
`soul_memories` store the [Memory Retriever](MEMORY_RETRIEVER.md) reads. Governed
by the [Memory Rules](MEMORY_RULES.md), [Memory Integration](MEMORY_INTEGRATION.md),
and the [Orchestra Constitution](ORCHESTRA_ENGINEERING_RULES.md) (esp. Rules 9, 18).
