# Memory Retriever (Orchestra Node 3 — "The Memory Librarian")

> **Status:** Implemented (Phase 3.2). Like a librarian, it does not think,
> answer, or reflect — it **finds the most relevant memories** for the current
> request and returns them. **No AI, no storage, no editing.** Source:
> `backend/app/orchestra/memory/`.

## Responsibilities (single responsibility)

Retrieve the **minimum set of relevant, user-scoped memories** for one
`OrchestraRequest`. It never reflects, plans, prompts, calls an LLM, stores,
edits, or answers users. It **honors the Guardian** and never fabricates.

## Inputs / Outputs (API contract)

```
retrieve(request: OrchestraRequest, guardian: GuardianResult, source: MemorySource)
    -> RetrievalResult
```

- **Inputs:** the immutable `OrchestraRequest`, the `GuardianResult`, and a
  `MemorySource`. Neither input is modified.
- **Guardian gate:** if `guardian.allow_memory_retrieval is False`, it
  **immediately returns an empty `RetrievalResult`** (`blocked=True`) — the
  Guardian is never bypassed.
- **Output:** an immutable `RetrievalResult` of structured `RetrievedMemory`
  objects (never raw DB rows). Malformed input raises a structured
  `RetrievalError` (never an unstructured throw).

## Schemas (v1.0, immutable)

**RetrievedMemory:** `id`, `memory_type`, `priority`, `title`, `summary`,
`relevance_score` (0–1), `confidence` (0–1), `why_selected`, `related_ids`
(future graph), `created_at`.

**RetrievalResult:** `schema_version`, `result_id`, `created_at`, `request_id`,
`retrieved` (ordered tuple), `count`, `blocked`, `reason`.

**Memory types:** goal, achievement, project, birthday, relationship,
preference, life_event, diary_entry, writing_history, milestone (extend
naturally). **Priorities:** critical, high, medium, low.

## The store

`soul_memories` (migration 0003) is the retrieval **source of truth** — scoped
per user, with soft-delete + archive and a self-referential `related_to_id`. The
future **Memory Writer** node populates it; the Retriever only reads it.

## Selection rules

1. **Guardian first** — blocked ⇒ empty result.
2. **Scoped** — only the requesting user's memories; **deleted/archived
   excluded** (enforced by the source).
3. **Relevant only** — a memory is kept only if it shares meaningful tokens with
   the page (title + content). Unrelated memories are never returned.
4. **Minimum useful context** — capped at `MAX_MEMORIES` (5); quality over
   quantity; low-priority, low-relevance items trim out first.
5. **No fabrication** — if nothing is relevant, return an empty result with
   `reason="no_relevant_memories"`.

Relevance today is a deterministic keyword overlap producing `relevance_score`,
`confidence`, and a `why_selected` explanation (internal — never shown to users).

## Priority rules

Results are ordered by **priority first (Critical → High → Medium → Low), then
relevance**. Critical always appears first *among retrieved* memories; it is not
force-included when irrelevant (Memory Rules: recall only when relevant, never
reference Critical casually).

## Future semantic retrieval

The `MemorySource` interface decouples the Retriever from the store. A future
**semantic** source (pgvector embeddings) implements the same `candidates(...)`
contract and a semantic scorer replaces the keyword scorer — **no change to the
node's contract** (Constitution: model-agnostic, loose coupling).

## Future graph retrieval

`related_to_id` (self-FK) and `RetrievedMemory.related_ids` reserve the seam for
connected memories (goal → interview → job → promotion). Graph traversal is
**not** implemented yet — only the architecture is prepared.

## Testing

`backend/tests/test_memory_retriever.py` — **100% coverage** of
`app.orchestra.memory` (`pytest-cov`): no/single/multiple memories, priority and
relevance ordering, limit cap, Guardian-blocked, wrong user, deleted/archived
exclusion, preference/goal/project/milestone/relationship retrieval, confidence
bounds, immutability, structured reasoning, and failure cases.

## Where it sits

Node **3 of 10** in the [Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md).
Consumes the [Input Receiver](INPUT_RECEIVER.md) request and the
[Guardian](GUARDIAN_ENGINE.md) result; feeds the Reflection Planner (node 4).
Governed by the [Memory Rules](MEMORY_RULES.md),
[Memory Integration](MEMORY_INTEGRATION.md), and the
[Orchestra Constitution](ORCHESTRA_ENGINEERING_RULES.md).
