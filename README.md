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

## 🗺️ Future Roadmap

Auth → Diary storage → Reflection engine → Semantic memory → Analytics &
charts → SoulLibrary → Safety hardening → Realtime streaming.

See [`docs/PHASES.md`](docs/PHASES.md).

## 📄 License

Proprietary — © Mini SoulSpace. All rights reserved.
