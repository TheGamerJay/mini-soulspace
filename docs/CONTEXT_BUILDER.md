# Context Builder (Orchestra Node 5 — "The Architect")

> **Status:** Implemented (Phase 3.4). Prepares the workspace before the Prompt
> Builder: it assembles the minimum, highest-quality context and nothing else.
> **No AI, no prompts, no text generation, no memory I/O.** Source:
> `backend/app/orchestra/context/`.

## Purpose

Assemble a clean, minimal, structured **ContextPackage** — the *only* input to
the Prompt Builder (node 6). It embodies **Rule 13 — Minimum Sufficient
Context**: pass only what the next node needs; quality beats quantity.

## Inputs / Outputs (API contract)

```
build(request, guardian, retrieval, planner, *, budget=DEFAULT_BUDGET)
    -> ContextPackage
```

- **Inputs:** the immutable `OrchestraRequest`, `GuardianResult`,
  `RetrievalResult`, and `PlannerResult`. None is modified.
- **Output:** an immutable `ContextPackage`. Malformed input raises a structured
  `ContextBuilderError`. Anything excluded (budget/relevance) is recorded as an
  `ExcludedNote` — **never silently discarded**.

## Schemas (v1.0, immutable)

**ContextBlock:** `id`, `type` (layer), `priority`, `source`, `reason` (why it
exists — internal), `content` (structured), `metadata`, `char_count`.

**ContextPackage:** `schema_version`, `package_id`, `created_at`, `request_id`,
`blocks` (ordered), `statistics`, `budget`, `excluded`, `confidence`.

## Layer system

Ordered layers (sorted by layer, then priority):

1. **Identity** — reserved reference to the Soul Companion identity (the full
   identity text is the Prompt Builder's static layer). *Critical.*
2. **Guardian** — the Guardian's decisions and restrictions. *Critical.*
3. **Current Page** — the journal page, its writing, and metadata. *High.*
4. **Memory** — only memories approved by **both** the Guardian and the Planner
   (`allow_memory_retrieval` and `plan.reference_memories`), deduped and capped.
   *Medium.* Omitted entirely when not approved.
5. **Reflection** — the `ReflectionPlan`. *High.*
6. **Reserved** — future specialists (see below). **Empty for now.**

## Budget system

Configurable `ContextBudget`: `max_memories`, `max_projects`, `max_goals`,
`max_total_chars`, `max_total_tokens` (future). Enforcement:

- Memory items are deduped and capped by `max_memories` / `max_goals` /
  `max_projects` (excess recorded as `ExcludedNote`s).
- If total characters exceed `max_total_chars`, the **Memory block is dropped
  first**; if still over, the **page content is truncated** (flagged
  `truncated: true`). Identity, Guardian, and Reflection are never dropped.

## Priority system

Every block carries a `priority` (Critical / High / Medium / Low), a `reason`,
and a `source`. Blocks are ordered by layer then priority so future nodes can
trim lower-priority blocks predictably.

## No duplication

Memory items are deduplicated by id (duplicates recorded as `ExcludedNote`s), and
each layer holds distinct facts — no fact is included twice.

## Future specialist integration

Layer 6 (**Reserved**) is the extension point for future specialist context —
Vision, Research, Homework, Medication, Coding, Image Generation, Image Editing,
Translation, Music, Document Analysis. **Not implemented** — the `ContextLayer`
enum reserves the slot and the layer stays empty until those specialists exist.

## Testing

`backend/tests/test_context_builder.py` — **100% coverage** of
`app.orchestra.context` (`pytest-cov`): layer assembly + ordering, empty/multiple
memories, Guardian block, retrieval-blocked, planner-excluded, not-in-retrieval,
dedup, `max_memories`/`max_goals`/`max_projects` caps, budget drop-memory and
page-truncation, large-entry-within-budget, confidence, statistics, immutability,
and failure cases.

## Where it sits

Node **5 of 10** in the [Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md).
Consumes nodes 1–4; its `ContextPackage` is the sole input to the Prompt Builder
(node 6). Governed by [Context Strategy](CONTEXT_STRATEGY.md) and the
[Orchestra Constitution](ORCHESTRA_ENGINEERING_RULES.md) (esp. Rule 13).
