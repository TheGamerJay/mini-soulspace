# Mini SoulSpace — Architecture

## Overview

Mini SoulSpace is an AI-powered personal **SoulDiary** — a diary that talks
back. The system is split into three cleanly separated layers plus the
infrastructure that supports them.

```
┌─────────────┐     HTTP/WebSocket     ┌─────────────┐     Ollama HTTP     ┌──────────┐
│  frontend   │ ─────────────────────▶ │   backend   │ ──────────────────▶ │  Ollama  │
│  (Next.js)  │ ◀───────────────────── │  (FastAPI)  │ ◀────────────────── │  models  │
└─────────────┘                        └──────┬──────┘                     └──────────┘
                                              │
                              ┌───────────────┴───────────────┐
                              ▼                               ▼
                       ┌────────────┐                  ┌────────────┐
                       │ PostgreSQL │                  │   Redis    │
                       │ + pgvector │                  │  (cache)   │
                       └────────────┘                  └────────────┘
```

## Backend (`backend/`)

A production FastAPI application using the application-factory pattern.

- `app/api` — HTTP routers and route modules.
- `app/core` — configuration (pydantic-settings) and logging.
- `app/db` — SQLAlchemy engine, session and declarative base.
- `app/models` — ORM models (Alembic-managed).
- `app/schemas` — Pydantic request/response contracts.
- `app/services` — application services orchestrating brains + data.
- `app/brains` — single-responsibility reasoning units (see below).
- Domain packages — `memory`, `diary`, `library`, `analytics`, `auth`,
  `websocket`, `safety`, `utils`.

### The Brain architecture

Each *brain* owns one cognitive concern and implements a common `Brain`
interface (`app/brains/base.py`). A name-keyed `REGISTRY` (`app/brains/__init__.py`)
allows the **router brain** to dispatch dynamically.

| Brain              | Responsibility                                  |
| ------------------ | ----------------------------------------------- |
| `router_brain`     | Decide which brain(s) handle a request.         |
| `emotional_brain`  | Interpret emotional tone / mood.                |
| `reflection_brain` | Generate the diary's "talking back" responses.  |
| `memory_brain`     | Store and recall long-term semantic memory.     |
| `builder_brain`    | Assemble structured artefacts.                  |
| `analytics_brain`  | Derive trends and metrics.                      |
| `safety_brain`     | Screen for risk and crisis signals.             |

## Frontend (`frontend/`)

Next.js (App Router) + TypeScript + TailwindCSS + Framer Motion.

- `src/app` — routes and layouts.
- `src/components` — shared UI components.
- `src/features/*` — feature modules (`soulbook`, `diary`, `library`, `charts`,
  `timeline`, `reflections`).
- `src/hooks`, `src/stores`, `src/lib`, `src/styles` — cross-cutting concerns.

## AI layer (`ai/`)

Model-facing assets (prompts, routing, embeddings, safety) decoupled from the
backend so intelligence can evolve independently. See `ai/README.md`.

## Data & infrastructure

- **PostgreSQL + pgvector** — relational data and vector memory.
- **Redis** — caching and future queues.
- **Ollama** — local LLM inference.

All three run via `docker-compose.yml`.

## SoulBook Engine (Phase 2)

The permanent journal. No AI in this phase — it builds the durable structure
everything else attaches to.

### Schema

```
users ─1─* soul_books ─1─* soul_chapters ─1─* soul_pages
                    └── soul_bookmarks (book/chapter/page)
                    └── soul_recent_books / soul_recent_chapters (per-user recency)
```

- **soul_books** — `id, user_id, title, description?, cover_style, is_archived,
  is_deleted, created_at, updated_at, last_opened_at`.
- **soul_chapters** — `id, user_id, book_id, title, chapter_number, is_deleted,
  timestamps, last_opened_at`.
- **soul_pages** — `id, user_id, book_id, chapter_id, title, content,
  page_number, content_format, timezone, word_count, character_count,
  is_deleted, timestamps`.
- **soul_bookmarks / soul_recent_books / soul_recent_chapters** — future-proofing
  seams (bookmarks UI, recency lists).

Soft delete (`is_deleted`) and archive (`is_archived`) everywhere; ownership is
enforced in the service layer (every query filters by `user_id`; missing/foreign
records raise 404).

### Storage format

Page content is stored as **`plain_text` or `markdown` — never HTML**. There is
no rich-text-editor dependency; the frontend renderer controls appearance. This
keeps content lightweight, searchable, versionable, export-friendly and
AI-friendly.

### API (all under `/api/soulbooks`, protected)

Books: `GET/POST /`, `GET/PATCH/DELETE /{book}`, `POST /{book}/archive|restore`,
`GET /search?q=`, list `?sort=recently_opened|recently_updated|alphabetical|newest|oldest`.
Chapters: `GET/POST /{book}/chapters`, `GET/PATCH/DELETE /{book}/chapters/{ch}`.
Pages: `GET/POST /{book}/chapters/{ch}/pages`, `GET/PATCH/DELETE .../pages/{pg}`,
`PATCH .../pages/{pg}/autosave`.

Routes are thin and call `app.services.soulbook_service` (no business logic in
routes).

### Frontend hosting note

The frontend is a Next.js **static export** served by FastAPI. Dynamic SoulBook
routes are exported once under a placeholder segment; `app/spa.py`
(`SpaStaticFiles`) serves that template for any concrete id so deep-links and
refreshes resolve. Screens read the real ids from the live URL
(`lib/soulPath.ts`).

### Future AI attachment points

Designed so later phases attach without rebuilding the engine:

- The writing page reserves a layout slot (`data-slot="ai-reflection"`) beneath
  the user's writing for the future flow: **writing → AI reflection → follow-up
  conversation**.
- Pages carry `content_format` + `timezone` and clean text content, ready for
  embeddings/memory (pgvector), summaries, exports and conversation threads —
  each can reference `soul_pages.id` via new tables.

## Soul Companion (Phase 2.5 — architecture only)

Before the diary "talks back," Phase 2.5 defines the permanent rules for the
future Soul Companion Engine. **No AI runtime, memory API, crisis classifier, or
Ollama calls are built yet** — these are design documents that Phase 3+ will
implement:

- [Soul Companion Guide](SOUL_COMPANION_GUIDE.md) — identity, personality, tone
  (human-like but honest AI; never a professional; never sentient).
- [Reflection Rules](REFLECTION_RULES.md) — how reflections should (and should
  not) sound.
- [Memory Rules](MEMORY_RULES.md) — Low/Medium/High/Critical importance,
  per-user scoping, never invented, user-controlled.
- [Safety Rules](SAFETY_RULES.md) — crisis triggers, required behavior, response
  templates; never pretends to handle a crisis alone.
- [Soul Presence Rules](SOUL_PRESENCE_RULES.md) — birthdays, milestones,
  check-ins; meaningful, optional, never clingy.
- [AI Prompt Architecture](AI_PROMPT_ARCHITECTURE.md) — the 8 prompt layers
  (Identity → Safety → User → Memory → Page → Reflection → Style → Formatting)
  and the Ollama model roles they route to.

These attach to existing seams: the Phase 2 writing page reserves a slot for
reflections (`data-slot="ai-reflection"`), pages store clean text for the Memory
and Page layers, and Phase 0's `ai/configs/models.json` + `MAIN/FAST/TAG/CODER`
settings define the models.

## Soul Intelligence — the Orchestra (Phase 2.75 — architecture only)

**The LLM is not the brain; the Orchestra is.** A reflection is produced by a
permanent, loosely-coupled pipeline of 10 specialist nodes — models plug in by
role and are replaceable without redesign. **No orchestration runtime is built
yet.**

```
Input Receiver → Safety Checker → Memory Retriever → Reflection Planner →
Context Builder → Prompt Builder → Response Generator → Quality Checker →
Memory Writer → Final Responder     (Safety may short-circuit to a safe response)
```

**Nodes 1–2 are implemented; no AI yet.**
- **Node 1 — Input Receiver (Phase 3.0)** — packages application state into an
  immutable, versioned `OrchestraRequest`. See [Input Receiver](INPUT_RECEIVER.md).
- **Node 2 — Guardian Engine (Phase 3.1)** — the protector: classifies the
  request and returns an immutable `GuardianResult` (category, tone, and
  structured reflection/memory/identity/safety decisions). Deterministic,
  rule-based, safety-first. See [Guardian Engine](GUARDIAN_ENGINE.md).
- **Node 3 — Memory Retriever (Phase 3.2)** — "the Memory Librarian": honors the
  Guardian, then retrieves the minimum set of relevant, user-scoped memories from
  the `soul_memories` store into an immutable `RetrievalResult`. Retrieve only,
  no AI, no fabrication. See [Memory Retriever](MEMORY_RETRIEVER.md).
- **Node 4 — Reflection Planner (Phase 3.3)** — "the director": decides *what
  kind* of reflection should happen (type, tone, depth, questions, memory
  referencing, celebration, listening) as an immutable `ReflectionPlan`. Honors
  Guardian caps; plan only, no AI. See [Reflection Planner](REFLECTION_PLANNER.md).
- **Node 5 — Context Builder (Phase 3.4)** — "the architect": assembles the
  minimal, ordered, deduplicated, budgeted `ContextPackage` (Identity · Guardian ·
  Current Page · Memory · Reflection · Reserved) — the sole input to the Prompt
  Builder. Memory only when Guardian + Planner approve; assemble only, no AI. See
  [Context Builder](CONTEXT_BUILDER.md).

The remaining nodes (6–10) are still architecture.

Every node must obey the permanent
[Orchestra Engineering Rules](ORCHESTRA_ENGINEERING_RULES.md) — the engineering
constitution that overrides implementation preferences.

- [Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md) — pipeline & philosophy.
- [Orchestra Nodes](ORCHESTRA_NODES.md) · [Future API Contracts](FUTURE_API_CONTRACTS.md) — node contracts.
- [Conversation Flow](CONVERSATION_FLOW.md) — flows + book open/close experience.
- [Context Strategy](CONTEXT_STRATEGY.md) · [Quality Guardrails](QUALITY_GUARDRAILS.md) ·
  [Memory Integration](MEMORY_INTEGRATION.md) · [Orchestration Events](ORCHESTRATION_EVENTS.md).

## Configuration

Every runtime value is environment-driven through `app.core.config.Settings`.
See `.env.example` for the full list.
