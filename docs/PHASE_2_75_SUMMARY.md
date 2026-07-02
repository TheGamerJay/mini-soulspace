# Phase 2.75 — Soul Intelligence Architecture (Summary)

> **Status:** Complete. Architecture & documentation only — **no AI, no runtime
> code, no behavior change.** Defines the permanent reasoning pipeline every
> future model must follow.

## The one idea

**The LLM is not the brain — the Orchestra is.** Models will change; the Soul
Companion must not. The AI is never the hero; the **SoulDiary is the hero**, and
the AI quietly enriches the writing experience. Think before speaking, never
guess, never fake memories, quality over speed.

## The pipeline (10 nodes)

`Input Receiver → Safety Checker → Memory Retriever → Reflection Planner →
Context Builder → Prompt Builder → Response Generator → Quality Checker →
Memory Writer → Final Responder.` Safety can short-circuit the whole pipeline to
a safe response. Every node has a Purpose, Inputs, Outputs, Responsibilities,
Failure behavior, and a Future API contract; nodes are loosely coupled.

## What this phase documented

- [Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md) — philosophy + pipeline.
- [Orchestra Nodes](ORCHESTRA_NODES.md) — all 10 nodes in full.
- [Conversation Flow](CONVERSATION_FLOW.md) — 11 flows + book open/close experience.
- [Context Strategy](CONTEXT_STRATEGY.md) — minimal, relevant context.
- [Quality Guardrails](QUALITY_GUARDRAILS.md) — the Quality Checker.
- [Memory Integration](MEMORY_INTEGRATION.md) — retrieve/write/ignore/update/expire/conflict/delete/edit.
- [Orchestration Events](ORCHESTRATION_EVENTS.md) — internal event vocabulary.
- [Future API Contracts](FUTURE_API_CONTRACTS.md) — node interfaces.

## Book open/close (permanent experience)

Close: page saves → reflection appears beneath the writing → ribbon bookmark
slides in → book closes → returns to the bookshelf → system remembers book /
chapter / page / cursor / last-opened / session. Reopen: bookshelf → bookmarked
book slides off, turns, opens → returns to the bookmarked page. It should feel
like closing and reopening a treasured personal journal.

## Model roles (replaceable)

Main `qwen3:14b` · Fast `llama3.1:8b` · Summary/Tags `gemma3:4b` · Coder
`qwen2.5-coder:14b`. Addressed by role, never hard-coded.

## Next

**Phase 3** implements the first Soul Companion Engine on top of this
architecture and the [Phase 2.5](SOUL_COMPANION_GUIDE.md) behavior rules —
starting with the safe, non-hero reflection path.
