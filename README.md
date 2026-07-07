# Mini SoulSpace

> Your personal SoulDiary — a diary that talks back.

Mini SoulSpace is an AI-powered personal **SoulDiary**: a private space where
you write, and the diary reflects back with warmth, memory and insight. It is
built as a production-quality application from day one — scalable, modular,
tested and maintainable.

---

## ✨ Project Vision

A diary should be more than a place to store words. Mini SoulSpace listens,
remembers and reflects — helping you understand yourself over time while keeping
your inner world private and safe. Every phase of development is treated as if
it were shipped by a professional software company: architecture first, quality
over speed.

## 🏗️ Architecture

Three cleanly separated layers over shared infrastructure:

- **Frontend** — Next.js App Router UI (the writing experience).
- **Backend** — FastAPI application with a modular **brain** architecture.
- **AI layer** — prompts, routing, embeddings and safety assets driving Ollama.
- **Infrastructure** — PostgreSQL + pgvector, Redis, Ollama.

The backend organises intelligence into single-responsibility **brains**
(router, emotional, reflection, memory, builder, analytics, safety), each
implementing a shared interface and discoverable through a registry.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full picture.

## 📁 Repository Structure

```
mini-soulspace/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/          # Routers and route modules
│   │   ├── core/         # Config (pydantic-settings) + logging
│   │   ├── db/           # SQLAlchemy engine, session, base
│   │   ├── models/       # ORM models (Alembic-managed)
│   │   ├── schemas/      # Pydantic contracts
│   │   ├── services/     # Application services
│   │   ├── brains/       # router / emotional / reflection / memory /
│   │   │                 #   builder / analytics / safety
│   │   ├── memory/  diary/  library/  analytics/
│   │   ├── auth/  websocket/  safety/  utils/
│   │   └── main.py       # App factory + entry point
│   ├── alembic/          # Migrations
│   ├── tests/            # Pytest smoke tests
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/             # Next.js application
│   └── src/
│       ├── app/          # App Router (layout + landing page)
│       ├── components/   # Shared UI
│       ├── features/     # soulbook / diary / library / charts /
│       │                 #   timeline / reflections
│       ├── hooks/  stores/  lib/  styles/
├── ai/                   # Prompts, model config, routing, embeddings, safety
│   └── configs/models.json
├── docker/               # Dockerfiles
├── scripts/              # PowerShell setup scripts
├── docs/                 # Architecture & phase documentation
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## 🧰 Tech Stack

| Layer      | Technologies                                                        |
| ---------- | ------------------------------------------------------------------- |
| Frontend   | Next.js, React, TypeScript, TailwindCSS, Framer Motion              |
| Backend    | FastAPI, PostgreSQL, SQLAlchemy, Alembic, Redis, pgvector           |
| AI         | Ollama (`qwen3:14b`, `llama3.1:8b`, `gemma3:4b`, `qwen2.5-coder:14b`)|
| Infra      | Docker Compose                                                      |

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop (for PostgreSQL, Redis, Ollama)
- Ollama (optional — can also run via Docker)

### 1. Clone

```powershell
git clone https://github.com/TheGamerJay/mini-soulspace.git
cd mini-soulspace
Copy-Item .env.example .env
```

### 2. Infrastructure (Docker)

Start the datastores (PostgreSQL + Redis):

```powershell
docker compose up -d
```

Start the full stack including backend + Ollama:

```powershell
docker compose --profile app up -d
```

### Backend Setup

```powershell
./scripts/setup_backend.ps1
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000 — verify (API is served under `/api`):

```powershell
curl http://localhost:8000/api           # {"app":"Mini SoulSpace","status":"running","phase":"0"}
curl http://localhost:8000/api/health    # {"status":"healthy"}
curl http://localhost:8000/api/health/ready  # readiness: Postgres + Redis checks
```

Interactive API docs: http://localhost:8000/docs

Run the tests:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

### Frontend Setup

```powershell
./scripts/setup_frontend.ps1
cd frontend
npm run dev
```

Frontend runs at http://localhost:3000.

### Database Setup (PostgreSQL + pgvector)

The `pgvector/pgvector:pg16` image ships the `vector` extension. With the
container running, apply migrations (once models exist):

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

Connection string (default): `postgresql+psycopg://soulspace:soulspace@localhost:5432/soulspace`

### Redis Setup

Redis runs from the same compose file at `redis://localhost:6379/0`. Verify:

```powershell
docker exec -it soulspace-redis redis-cli ping   # PONG
```

### Ollama Setup

If running Ollama locally, pull the configured models:

```powershell
./scripts/pull_ollama_models.ps1
```

Or use the Dockerised Ollama service (`docker compose --profile app up -d ollama`)
and pull inside the container. Endpoint: `http://localhost:11434`.

## ☁️ Deployment

Mini SoulSpace deploys as a **single unified service** (one container): the
Next.js frontend is built to a static export and served by the FastAPI backend
alongside the API. See [`docs/DEPLOY_RAILWAY.md`](docs/DEPLOY_RAILWAY.md).

Build/run the production container locally:

```powershell
docker build -t mini-soulspace .
docker run -p 8080:8080 --env-file .env mini-soulspace   # http://localhost:8080
```

## 📍 Current Phase

**Phase 2 — SoulBook Engine.** The permanent journal: a **Soul Library** of
**SoulBooks**, each with **Chapters** and **Pages**. Create / rename / archive /
restore / soft-delete SoulBooks; search and sort; write on immersive journal
pages that **auto-save** (debounced) with manual save, live word/character
counts, and a reserved slot for future AI reflections. Pages store as plain
text / markdown (never HTML). Built on Phase 1 auth (ownership-scoped) and the
Phase 0 foundation.

### SoulBook API (protected, `/api/soulbooks`)

```
GET/POST                          /api/soulbooks
GET/PATCH/DELETE                  /api/soulbooks/{book_id}
POST                              /api/soulbooks/{book_id}/archive | /restore
GET                               /api/soulbooks/search?q=&        (+ ?sort= on list)
GET/POST                          /api/soulbooks/{book_id}/chapters
GET/PATCH/DELETE                  /api/soulbooks/{book_id}/chapters/{chapter_id}
GET/POST                          /api/soulbooks/{book_id}/chapters/{chapter_id}/pages
GET/PATCH/DELETE                  .../pages/{page_id}
PATCH                             .../pages/{page_id}/autosave
```

Sort options: `recently_opened`, `recently_updated`, `alphabetical`, `newest`, `oldest`.

### Frontend routes

`/home` · `/soul-library` · `/soulbooks/[bookId]` ·
`/soulbooks/[bookId]/chapters/[chapterId]` ·
`/soulbooks/[bookId]/chapters/[chapterId]/pages/[pageId]`

### Soul Companion Architecture (Phase 2.5 — docs only)

The rules for how the SoulDiary will one day talk back — identity, reflection,
memory, safety, presence and prompt design — are defined **before** any AI is
built (no runtime code in this phase):

- [Soul Companion Guide](docs/SOUL_COMPANION_GUIDE.md)
- [Reflection Rules](docs/REFLECTION_RULES.md)
- [Memory Rules](docs/MEMORY_RULES.md)
- [Safety Rules](docs/SAFETY_RULES.md)
- [Soul Presence Rules](docs/SOUL_PRESENCE_RULES.md)
- [AI Prompt Architecture](docs/AI_PROMPT_ARCHITECTURE.md)

Phase 3 will build the first Soul Companion Engine using these rules.

### Soul Intelligence Architecture (Phase 2.75 — docs only)

**The LLM is not the brain — the Orchestra is.** The permanent 10-node reasoning
pipeline (Input → Safety → Memory → Plan → Context → Prompt → Generate → Quality
→ Memory Write → Respond) that every future model plugs into by role:

- [Soul Intelligence Architecture](docs/SOUL_INTELLIGENCE_ARCHITECTURE.md)
- [Orchestra Nodes](docs/ORCHESTRA_NODES.md)
- [Conversation Flow](docs/CONVERSATION_FLOW.md) (incl. book open/close experience)
- [Context Strategy](docs/CONTEXT_STRATEGY.md) · [Quality Guardrails](docs/QUALITY_GUARDRAILS.md)
- [Memory Integration](docs/MEMORY_INTEGRATION.md) · [Orchestration Events](docs/ORCHESTRATION_EVENTS.md)
- [Future API Contracts](docs/FUTURE_API_CONTRACTS.md) · [Phase 2.75 Summary](docs/PHASE_2_75_SUMMARY.md)

**Phase 3.0 — Input Receiver Engine** builds the first working Orchestra node
(`backend/app/orchestra/`): it packages application state into an immutable,
versioned `OrchestraRequest` (facts only — **no AI**), with ownership +
relationship validation and 100% unit coverage. See
[Input Receiver](docs/INPUT_RECEIVER.md).

**Phase 3.1 — Guardian Engine** builds the second node
(`backend/app/orchestra/guardian/`): the protector. It classifies the request
(category + emotional tone) and returns an immutable `GuardianResult` of
structured decisions — reflection/memory/question permissions, identity &
safety protection, human referral, crisis flag, confidence — deterministically,
**no AI**, safety-first, 100% coverage. See [Guardian Engine](docs/GUARDIAN_ENGINE.md).

**Phase 3.2 — Memory Retriever** builds the third node
(`backend/app/orchestra/memory/`): "the Memory Librarian". It honors the Guardian
and retrieves the minimum set of relevant, user-scoped memories (from the new
`soul_memories` store) into an immutable `RetrievalResult`, ordered by priority
then relevance — retrieve only, **no AI**, no fabrication, 100% coverage. See
[Memory Retriever](docs/MEMORY_RETRIEVER.md).

**Phase 3.3 — Reflection Planner** builds the fourth node
(`backend/app/orchestra/planner/`): "the director". It decides *what kind* of
reflection should happen — type, tone, depth, question plan, memory referencing,
celebration, listening — as an immutable `ReflectionPlan`, honoring Guardian caps
(blocked ⇒ No Reflection). Plan only, **no AI, no LLM**, 100% coverage. See
[Reflection Planner](docs/REFLECTION_PLANNER.md).

**Phase 3.4 — Context Builder** builds the fifth node
(`backend/app/orchestra/context/`): "the architect". It assembles the minimal,
ordered, deduplicated, budget-bounded `ContextPackage` (Identity · Guardian ·
Current Page · Memory · Reflection · Reserved) that becomes the sole input to the
Prompt Builder — memory only when the Guardian and Planner approve. Assemble only,
**no AI**, 100% coverage. See [Context Builder](docs/CONTEXT_BUILDER.md).

**Phase 3.5 — Prompt Builder** builds the sixth node
(`backend/app/orchestra/prompt/`). It transforms the `ContextPackage` into an
immutable `PromptPackage` — a seven-layer system prompt (Identity · Safety ·
Page · Memories · Reflection Plan · Style · Formatting), a conversation
blueprint, a versioned template (Reflection v1), a model role, and generation
parameters. Assemble only, **no LLM call**, 100% coverage. See
[Prompt Builder](docs/PROMPT_BUILDER.md).

**Phase 3.65 — Meaning & Intent Engine** adds a **pre-Guardian analyzer**
(`backend/app/orchestra/meaning/`): Input → Meaning Analysis → Guardian. It
determines meaning / context / intent / real-world intent so safety is never
based on isolated words — a song "Kill Yourself" or a novel murder is downgraded,
a literal journal self-disclosure still activates the crisis path; ambiguity
stays protected. The Guardian is now meaning-aware (backwards compatible). No AI,
100% coverage. See [Meaning & Intent Engine](docs/MEANING_INTENT_ENGINE.md).

**Phase 3.6 — Mini Engine** builds the seventh node
(`backend/app/orchestra/mini/`): the **first node that talks to a local model**.
The Orchestra addresses **Mini Services** by name (Mini Core / Swift / Insight /
Creator …); the Mini Engine maps role → service → model via `mini_services.json`
and calls the runtime — Ollama is **sealed inside `runtime.py`**. Returns an
immutable `CandidateResponse` with structured errors, retries, and metrics (no
journal content logged), 100% coverage. See [Mini Engine](docs/MINI_ENGINE.md).

**Phase 3.7 — Quality Checker** builds the eighth node
(`backend/app/orchestra/quality/`): the gate before the user. It reviews the
`CandidateResponse` against safety/identity/quality/SoulDiary rules and returns
an immutable `QualityResult` (approved / rejected / needs_retry) with structured
violations — catching sentience claims, hidden-prompt leaks, raw model names,
fabricated memory, unsafe advice, manipulation, and generic/robotic phrasing,
while honoring the meaning engine so creative content isn't over-escalated.
Deterministic, **no AI, no delivery**, 100% coverage. See
[Quality Checker](docs/QUALITY_CHECKER.md).

**Phase 3.8 — Memory Writer** builds the ninth node
(`backend/app/orchestra/writer/`). It decides what — if anything — an **approved**
exchange should become a long-term memory ("when in doubt, don't save"), and
optionally persists it to the `soul_memories` store the Retriever reads. Facts
come only from the user's own writing (never fabricated); duplicates are skipped,
preferences/projects **evolve in place**, and relationships are **linked** via
`related_to_id` (graph-ready). Immutable `MemoryDecision` with Low→Critical
importance. Deterministic, **no AI**, 100% coverage. See
[Memory Writer](docs/MEMORY_WRITER.md).

**Phase 3.8.5 — Memory Intelligence Engine** adds a memory-**quality** layer
(`backend/app/orchestra/intelligence/`): evidence-backed confidence (signup 1.0 →
explicit 0.99 → implied 0.80 → casual 0.40), configurable thresholds
(`memory_intelligence.json`, per-type overrides), sources, mandatory evidence,
version history that is never lost, evolution/conflict resolution, confidence
decay (never deletes), verification prep, and **user-correction learning** —
corrections permanently replace outdated values, raise confidence, and never
resurface; frequently corrected types require stronger evidence. Deterministic,
**no AI**, 100% coverage. See
[Memory Intelligence Engine](docs/MEMORY_INTELLIGENCE_ENGINE.md).

**Phase 3.9 — Conversation Composer** builds the **tenth and final node**
(`backend/app/orchestra/composer/`): the **single gateway between the Orchestra
and the frontend**. Only approved responses are delivered — with the candidate
text exactly as approved (never rewritten); rejected / needs-retry become
structured failure packages that never reach the user. Packages memory updates +
frontend events; attachment/action/notification/citation architecture prepared as
typed placeholders. Assemble only, **no AI**, 100% coverage. **All 10 Orchestra
nodes now exist.** See [Conversation Composer](docs/CONVERSATION_COMPOSER.md).

## 🗺️ Future Roadmap

Auth → Diary storage → Reflection engine → Semantic memory → Analytics &
charts → SoulLibrary → Safety hardening → Realtime streaming.

See [`docs/PHASES.md`](docs/PHASES.md).

## 📄 License

Proprietary — © Mini SoulSpace. All rights reserved.
