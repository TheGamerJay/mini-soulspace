# Context Strategy

> **Status:** Architecture only (Phase 2.75). Defines how the Context Builder
> (node 5) assembles the minimal, relevant context for a reflection. Not
> implemented.

## Principle

**Less, but relevant.** Context is not "everything we know" — it is only what
earns its place for *this* page. Irrelevant context dilutes quality, wastes
tokens, and invites hallucination. The page the user just wrote is always the
center of gravity.

## What context may include

Ordered by priority (highest first):

1. **The current page** — title + content (always).
2. **Immediate page context** — the chapter and book it belongs to; adjacent
   pages only if continuity clearly matters.
3. **Reflection plan** — intent/tone/depth/question decision from node 4.
4. **Relevant memories** — from the Memory Retriever, filtered by relevance and
   importance; unrelated memories are excluded (see [Memory Rules](MEMORY_RULES.md)).
5. **User context** — display name, timezone, preferred language, locale (for
   tone only; never sensitive profile data beyond what's needed).
6. **Detected occasion** — birthday/milestone flags, if present.

## What context must exclude

- Other users' or other projects' data (hard boundary).
- Memories with no relevance to this page.
- Critical memories, unless the page itself clearly invokes them and the moment
  is handled with care.
- Raw internal metadata that doesn't shape the reflection.

## Budgeting

- Respect a token budget per model role; when over budget, **drop least-relevant
  context first** (adjacent pages, then lower-importance memories) — never drop
  Identity/Safety layers.
- Prefer summaries (Summary/Tags model) of long histories over raw dumps.

## Anti-hallucination posture

- If a fact isn't in context, the companion does not assert it.
- The Context Builder never fabricates connective tissue between page and memory;
  relationships must come from the memory store, not invention.

## Handoff

Output `BuiltContext` feeds the Prompt Builder (node 6), which maps it onto the
Memory, Page, and User layers of the [AI Prompt Architecture](AI_PROMPT_ARCHITECTURE.md).
