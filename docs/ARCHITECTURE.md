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

## Configuration

Every runtime value is environment-driven through `app.core.config.Settings`.
See `.env.example` for the full list.
