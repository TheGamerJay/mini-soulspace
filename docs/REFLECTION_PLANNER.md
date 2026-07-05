# Reflection Planner (Orchestra Node 4 — "The Director")

> **Status:** Implemented (Phase 3.3). Decides *what kind* of reflection should
> happen — it never writes the reflection, calls an LLM, or touches memory.
> Source: `backend/app/orchestra/planner/`.

## Purpose

Create a structured **ReflectionPlan**. The planner is the director: it decides
what should happen; later nodes execute the plan. **No AI, no prompts, no memory
I/O, no user-facing text.**

## Inputs / Outputs (API contract)

```
plan(request: OrchestraRequest, guardian: GuardianResult, retrieval: RetrievalResult)
    -> PlannerResult
```

- **Inputs:** the immutable request, the Guardian's decision, and the retrieval
  result. None is modified.
- **Output:** an immutable `PlannerResult` wrapping a `ReflectionPlan`. Malformed
  input raises a structured `PlannerError` (never an unstructured throw). When
  uncertain (low Guardian confidence), it falls back to the **simplest safe
  plan**.

## Schemas (v1.0, immutable)

**ReflectionPlan:** `reflection_type`, `tone`, `depth`, `emotional_style`,
`ask_question`, `question_type`, `question_count` (0–2), `reference_memories`,
`memories_to_use`, `max_memories`, `celebrate`, `encourage`, `listen_only`.

**PlannerResult:** `schema_version`, `result_id`, `created_at`, `request_id`,
`plan`, `confidence` (0–1), `reason` (internal reasoning only).

## Reflection type system

`Listening · Validation · Encouragement · Celebration · Reflection · Goal Support
· Memory Recall · Gentle Challenge · Clarification · Education · Research Summary
· Project Support · Creative Inspiration · Simple Acknowledgement · No Reflection`
(extend naturally). Chosen from the Guardian's category, recommended action, and
emotional tone; the SoulBook type (e.g. "Story Ideas") biases toward Creative
Inspiration; retrieved memories bias toward Memory Recall / Goal Support.

## Tone system

`Calm · Warm · Gentle · Hopeful · Thoughtful · Celebratory · Curious ·
Encouraging · Quiet · Respectful`. **Never** judgmental, manipulative, overly
dramatic, or condescending. Each reflection type maps to a fitting tone.

## Question system

Honors Guardian limits: `question_count = min(desired, guardian.max_questions)`
and `0` when the Guardian disallows questions or the plan is the simplest-safe
fallback. `question_type ∈ {open, reflective, clarifying, future_oriented, none}`
— **never exceeds two**, and often zero (listening).

## Depth strategy

Starts from a per-type proposed depth, then **caps at the Guardian's depth** —
the planner may reduce depth but **never exceeds** the Guardian's limit. Blocked
reflection ⇒ depth `None`.

## Memory strategy

References memories only for memory-friendly reflection types when the retrieval
returned some, selecting up to 3 by the Retriever's ordering. It **selects**,
never edits, and never fabricates. Unrelated types (education, research, project,
creative, override-acknowledgement) don't reference memory.

## Celebration strategy

`celebrate = True` for Celebration (Guardian `CELEBRATE` action or a joyful /
positive / hopeful tone) — birthdays, goal completion, promotions, milestones.
Balanced: no forced positivity or motivation.

## Listening strategy

Sometimes the best response is to simply listen. Grieving tone / Guardian
`LISTEN_ONLY` ⇒ reflection type **Listening**, `listen_only = True`,
`question_count = 0`. Not every page needs advice or a question.

## Emotional balance

The planner matches the emotional context — avoiding too much positivity or
negativity, and forced optimism/motivation. Crisis (Guardian disallows
reflection) ⇒ a quiet **No Reflection** plan (safety over intelligence).

## Testing

`backend/tests/test_reflection_planner.py` — **100% coverage** of
`app.orchestra.planner` (`pytest-cov`): happy/sad/anxious/grieving/high-distress,
celebration, creative, research, homework, medical/legal, override, memory
recall / goal support, memory cap, Guardian-blocked (No Reflection), question and
depth limits, low-confidence simplest-safe, confidence bounds, immutability, and
failure cases.

## Where it sits

Node **4 of 10** in the [Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md).
Consumes [Input Receiver](INPUT_RECEIVER.md), [Guardian](GUARDIAN_ENGINE.md), and
[Memory Retriever](MEMORY_RETRIEVER.md) outputs; feeds the Context Builder (node
5). Governed by the [Reflection Rules](REFLECTION_RULES.md),
[Soul Companion Guide](SOUL_COMPANION_GUIDE.md), and the
[Orchestra Constitution](ORCHESTRA_ENGINEERING_RULES.md).
