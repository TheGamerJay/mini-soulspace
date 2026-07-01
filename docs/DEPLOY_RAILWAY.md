# Deploying Mini SoulSpace to Railway

Mini SoulSpace deploys as a **single unified service**: one container that builds
the Next.js frontend into a static export and serves it from the FastAPI
backend, alongside the API and (future) WebSockets. One image, one domain, no
CORS.

```
┌──────────────────── one container ────────────────────┐
│  FastAPI (uvicorn on $PORT)                            │
│   ├── /            → Next.js static build (served)     │
│   ├── /api         → service metadata                 │
│   ├── /api/health  → liveness                          │
│   ├── /api/health/ready → DB + Redis readiness         │
│   └── /api/...     → application API                   │
└───────────────────────────────────────────────────────┘
        │                         │
   ┌────────┐                ┌────────┐
   │Postgres│                │ Redis  │   (Railway-managed)
   └────────┘                └────────┘
```

The root `Dockerfile` is multi-stage: a Node stage runs `next build` (static
export → `out/`), then a Python stage installs the backend and copies that build
to `./static`, which FastAPI mounts at `/`.

---

## Service configuration (one service)

### Settings → Source
- **Root Directory:** *empty* (the repository **root**).
  If it currently says `/backend`, clear it back to root — the unified build
  needs both `frontend/` and `backend/` in the build context.

### Settings → Build
- **Builder:** `Dockerfile` (auto via root `railway.json`).
- **Dockerfile Path:** `Dockerfile` (the root one).

`railway.json` sets the health check to `/api/health`.

### Add datastores
- **Postgres** and **Redis** (New → Database) — both in the same project.

### Settings → Variables
| Variable       | Value                        |
| -------------- | ---------------------------- |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `REDIS_URL`    | `${{Redis.REDIS_URL}}`       |
| `SECRET_KEY`   | *(a strong random string)*   |

> `NEXT_PUBLIC_API_URL` is **not needed** — the frontend calls the API on the
> same origin (`/api`). The backend also auto-rewrites Railway's `postgresql://`
> URL to the `postgresql+psycopg://` SQLAlchemy driver.

### Networking
Generate a public domain. Everything is served from it:
- `/`                     → landing page (SoulDiary UI)
- `/api`                  → `{"app":"Mini SoulSpace","status":"running","phase":"0"}`
- `/api/health`           → `{"status":"healthy"}`
- `/api/health/ready`     → `{"status":"ready","checks":{"database":"ok","redis":"ok"}}`

`/api/health/ready` is the end-to-end proof the backend reaches **Postgres and
Redis** (HTTP 503 + `degraded` naming any dependency that is not connected).

---

## Local development

Local dev stays **split** for hot reload (no single-container needed):

```powershell
# terminal 1 — backend (API at /api)
cd backend; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload

# terminal 2 — frontend (Next dev server, proxies to backend via NEXT_PUBLIC_API_URL)
cd frontend; npm run dev
```

To reproduce the unified production container locally:

```powershell
docker build -t mini-soulspace .
docker run -p 8000:8000 --env-file .env mini-soulspace
# open http://localhost:8000
```

---

## Troubleshooting

| Symptom                                   | Cause / Fix                                                        |
| ----------------------------------------- | ----------------------------------------------------------------- |
| *Failed to build an image* at root        | Builder not on Dockerfile, or Root Directory pointed at a subfolder — use repo **root** + `Dockerfile`. |
| `"/requirements.txt": not found`          | Root Directory set to a subfolder / wrong Dockerfile path. Use root `Dockerfile`. |
| Frontend 404 at `/`                        | `next build` didn't emit `out/` — ensure `output: "export"` in `next.config.mjs`. |
| App builds but crashes / restarts         | Not binding `$PORT` — the root Dockerfile already handles it.      |
| `/api/health/ready` → `database: error`   | `DATABASE_URL` not referencing `${{Postgres.DATABASE_URL}}`.       |
| `/api/health/ready` → `redis: error`      | Redis service not added or `REDIS_URL` not referenced.            |
