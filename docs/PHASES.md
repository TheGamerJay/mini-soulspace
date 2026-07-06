# Mini SoulSpace — Development Phases

Mini SoulSpace is built phase by phase as a production-quality application.
Each phase must be production-ready, tested, modular, documented and
maintainable before the next begins.

## Phase 0 — Repository Foundation ✅

Backend (FastAPI, brains, config, Alembic), frontend (Next.js App Router,
landing page), AI config scaffolding, Docker, setup scripts, documentation.

## Phase 1 — Authentication & User Foundation ✅

JWT auth via httpOnly cookies (Argon2id, rotating refresh tokens with reuse
detection), Redis rate limiting, mandatory signup agreement (modal-gated),
full user profiles + preferences, protected routes, Home screen. Configurable
minimum signup age.

## Phase 2 — SoulBook Engine ✅ (current)

The permanent journal — no AI yet.

- **Data model:** `soul_books` → `soul_chapters` → `soul_pages`, plus
  `soul_bookmarks`, `soul_recent_books`, `soul_recent_chapters`. Soft delete,
  archive/restore, ordering, recency, word/character counts.
- **Storage:** pages are **plain text / markdown, never HTML** (lightweight,
  searchable, versionable, export- and AI-friendly). No rich-text dependency.
- **API:** `/api/soulbooks/**` — books, chapters, pages, autosave, search, sort;
  every record ownership-scoped to the authenticated user.
- **Frontend:** Soul Library (create/rename/archive/restore/delete, search,
  sort), immersive SoulBook cover, chapter/page navigation, and a writing engine
  with `Dear Diary...` starter, live counts, debounced auto-save + manual save.
- **Future AI slot:** each writing page reserves a layout region beneath the
  writing for the future flow (user writing → AI reflection → conversation).

## Phase 2.5 — Soul Companion Architecture ✅ (current)

Documentation & architecture only — **no AI runtime, no behavior change**.
Defines the permanent identity, behavior, memory, safety, presence and prompt
rules the future Soul Companion Engine must follow:

- [Soul Companion Guide](SOUL_COMPANION_GUIDE.md) — identity, personality, tone.
- [Reflection Rules](REFLECTION_RULES.md) — how the diary talks back (good vs bad).
- [Memory Rules](MEMORY_RULES.md) — importance levels, scoping, user control.
- [Safety Rules](SAFETY_RULES.md) — crisis-safe behavior + response templates.
- [Soul Presence Rules](SOUL_PRESENCE_RULES.md) — meaningful, optional moments.
- [AI Prompt Architecture](AI_PROMPT_ARCHITECTURE.md) — 8 prompt layers + model roles.

**Phase 3 will build the first Soul Companion Engine using these rules.**

## Phase 2.75 — Soul Intelligence Architecture ✅ (current)

Documentation & architecture only — **no AI runtime, no behavior change**.
Designs the permanent reasoning pipeline ("the Orchestra") every future model
must follow. The LLM is not the brain — the Orchestra is; models are replaceable,
the Soul Companion is not.

- [Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md) — philosophy + 10-node pipeline.
- [Orchestra Nodes](ORCHESTRA_NODES.md) — each node's purpose/inputs/outputs/failure/contract.
- [Conversation Flow](CONVERSATION_FLOW.md) — 11 flows + book open/close experience.
- [Context Strategy](CONTEXT_STRATEGY.md) · [Quality Guardrails](QUALITY_GUARDRAILS.md).
- [Memory Integration](MEMORY_INTEGRATION.md) · [Orchestration Events](ORCHESTRATION_EVENTS.md).
- [Future API Contracts](FUTURE_API_CONTRACTS.md) · [Phase 2.75 Summary](PHASE_2_75_SUMMARY.md).

## Phase 3.0 — Input Receiver Engine ✅ (current)

The **first working Orchestra node** — data packaging only, **no AI**. Converts
raw application state (authenticated user + book/chapter/page) into one
**immutable, versioned `OrchestraRequest`** (schema v1.0) after validating
existence, ownership, relationship integrity, content, language and timezone.
Reuses the Phase 2 SoulBook service (no duplicated data access). Structured
`InputValidationError` on failure; **100% unit coverage** of `app.orchestra`.

- [Input Receiver](INPUT_RECEIVER.md) — purpose, schema, validation, contract.
- Source: `backend/app/orchestra/` · Tests: `backend/tests/test_input_receiver.py`.

## Phase 3.1 — Guardian Engine ✅ (current)

The **second Orchestra node** (the protector) — classify + protect only, **no
AI**. Consumes the immutable `OrchestraRequest` and returns an immutable,
versioned `GuardianResult` (schema v1.0): one primary category, emotional tone,
and structured decisions (reflection/memory/question permissions, depth,
identity/roleplay/safety protection, human referral, crisis flag, confidence,
reasoning). Deterministic + rule-based; **safety always wins**; when uncertain,
the safer path. Structured `GuardianError` on malformed input. **100% coverage**
of `app.orchestra.guardian`, testable without the rest of the Orchestra.

- [Guardian Engine](GUARDIAN_ENGINE.md) · Source: `backend/app/orchestra/guardian/`.

## Phase 3.2 — Memory Retriever ✅ (current)

The **third Orchestra node** ("the Memory Librarian") — retrieve only, **no AI,
no storage**. Consumes the `OrchestraRequest` + `GuardianResult`; honors the
Guardian (`allow_memory_retrieval == false` → empty, never bypassed). Introduces
the `soul_memories` store (migration 0003, populated later by the Memory Writer)
and a `MemorySource` interface so future semantic/graph retrieval plugs in.
Returns an immutable, versioned `RetrievalResult` of `RetrievedMemory` objects
ordered by priority (Critical→Low) then relevance; relevant-only; capped;
never fabricates. **100% coverage** of `app.orchestra.memory`.

- [Memory Retriever](MEMORY_RETRIEVER.md) · Source: `backend/app/orchestra/memory/`.

## Phase 3.3 — Reflection Planner ✅ (current)

The **fourth Orchestra node** ("the director") — plan only, **no AI, no LLM, no
memory I/O**. Consumes the `OrchestraRequest` + `GuardianResult` +
`RetrievalResult` and emits an immutable `PlannerResult`/`ReflectionPlan`:
reflection type, tone, depth, question plan, memory-referencing, celebration and
listening decisions. Honors the Guardian (may reduce, never exceeds depth/question
limits; blocked ⇒ `NO_REFLECTION`); simplest-safe plan when uncertain. Reuses the
Guardian's `ReflectionDepth`. **100% coverage** of `app.orchestra.planner`.

- [Reflection Planner](REFLECTION_PLANNER.md) · Source: `backend/app/orchestra/planner/`.

## Phase 3.4 — Context Builder ✅ (current)

The **fifth Orchestra node** ("the architect") — assemble only, **no AI, no
prompts**. Consumes all four upstream outputs and emits an immutable
`ContextPackage` of ordered `ContextBlock`s across six layers (Identity, Guardian,
Current Page, Memory, Reflection, Reserved). Memory appears only when the Guardian
*and* the Planner approve; content is deduped, priority-ordered, and kept within a
configurable `ContextBudget` (memory dropped first, then page truncated) — every
exclusion recorded, never silently discarded. Added **Constitution Rule 13 —
Minimum Sufficient Context**. **100% coverage** of `app.orchestra.context`.

- [Context Builder](CONTEXT_BUILDER.md) · Source: `backend/app/orchestra/context/`.

## Phase 3.5 — Prompt Builder ✅ (current)

The **sixth Orchestra node** — assemble only, **no AI**. Transforms the
`ContextPackage` into an immutable `PromptPackage`: a seven-layer `system_prompt`
(Identity · Safety/Guardian · Current Page · Memories · Reflection Plan · Response
Style · Output Formatting), a conversation blueprint, a versioned template
(Reflection v1), a model role, and depth-scaled generation parameters. Required
layers are validated (never silently omitted); templates are versioned. Added
**Constitution Rule 14 — separation of structure, intelligence, and language**.
**100% coverage** of `app.orchestra.prompt`.

- [Prompt Builder](PROMPT_BUILDER.md) · Source: `backend/app/orchestra/prompt/`.

## Phase 3.6 — Mini Engine ✅ (current)

The **seventh Orchestra node** — the **first node that talks to a local model**.
The Orchestra addresses **Mini Services** by name (Mini Core / Swift / Insight /
Creator, …); the Mini Engine maps role → service → local model via
`mini_services.json` and calls the runtime. The runtime (Ollama) is **sealed
inside `runtime.py`** — no other node references it. Consumes the `PromptPackage`,
returns an immutable `CandidateResponse` with structured errors, configurable
timeout/retries, and metrics (no journal content logged). Added **Constitution
Rule 15 — language generation makes no architectural decisions**. **100%
coverage** of `app.orchestra.mini`.

- [Mini Engine](MINI_ENGINE.md) · Source: `backend/app/orchestra/mini/`.

## Phase 3.65 — Meaning & Intent Engine ✅ (current)

A **pre-Guardian analyzer** — new flow: Input → **Meaning Analysis** → Guardian →
Planner. Deterministic, **no AI**. Determines meaning / context / intent /
real-world intent (immutable `MeaningIntentResult`) so safety is never based on
isolated words. The Guardian's `evaluate(request, meaning=None)` is backwards
compatible: `real_world_intent == false` (lyrics, fiction, quotes, awareness)
**downgrades** a keyword-only crisis; `true` keeps it; `unclear` stays protected.
Added **Constitution Rule 16 — understand meaning before judging**. **100%
coverage** of `app.orchestra.meaning` and the updated `app.orchestra.guardian`.

- [Meaning & Intent Engine](MEANING_INTENT_ENGINE.md) · Source: `backend/app/orchestra/meaning/`.

## Phase 3.7 — Quality Checker ✅ (current)

The **eighth Orchestra node** — the gate before the user. Reviews the Mini
Engine's `CandidateResponse` and returns an immutable `QualityResult`
(approved / rejected / needs_retry) with structured `Violation`s. Deterministic,
**no AI, no model calls, no delivery, no rewriting**. Checks identity/sentience,
hidden-prompt/knowledge protection, raw model-name leaks, fabricated memory,
unsafe advice, crisis handling, manipulation, generic/robotic phrasing, question/
tone/depth compliance — and **honors `MeaningIntentResult`** so creative content
isn't over-escalated. Added **Constitution Rule 17 — nothing reaches the user
unverified**. **100% coverage** of `app.orchestra.quality`.

- [Quality Checker](QUALITY_CHECKER.md) · Source: `backend/app/orchestra/quality/`.

## Future roadmap

- **Phase 3.8** — Memory Writer (node 9), then Final Responder (node 10), on the
  Phase 2.75 architecture, Phase 2.5 rules, and the
  [Orchestra Constitution](ORCHESTRA_ENGINEERING_RULES.md).
- **Phase 4** — Semantic memory (pgvector embeddings + recall).
- **Phase 5** — Conversation threads on pages.
- **Phase 6** — Emotional analytics, charts and timeline.
- **Phase 7** — Exports (PDF / DOCX / TXT), bookmarks UI, printing.
- **Phase 8** — Safety hardening + realtime (WebSocket / voice).

> The roadmap is directional and refined as the product matures.
