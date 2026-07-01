# Deploying Mini SoulSpace to Railway

Mini SoulSpace is a **monorepo** (`backend/` + `frontend/`). Railway builds one
image per service, so each app is deployed as its **own service** pointed at its
subfolder. This is why a single service building the repo **root** fails with
*"Failed to build an image"* — the root has no buildable app.

Both services use the **Dockerfile builder** (not Railpack/Nixpacks), driven by
the committed `railway.json` + `Dockerfile` in each subfolder.

---

## 1. Backend service (FastAPI)

### Settings → Build
- **Root Directory:** `backend`
- **Builder:** `Dockerfile` (auto-selected via `backend/railway.json`; if the UI
  still shows *Railpack*, switch it to **Dockerfile** manually).
- **Dockerfile Path:** `Dockerfile` (relative to the root directory).
  ⚠️ Do **not** point this at `/docker/backend.Dockerfile` — that file expects a
  different build context and will fail with `"/requirements.txt": not found`.

`backend/Dockerfile` binds to Railway's `$PORT`, and `backend/railway.json` sets
the health check to `/health`.

### Add datastores
- **Postgres:** already provisioned (New → Database → PostgreSQL).
- **Redis:** New → Database → **Redis**.

### Variables (Settings → Variables)
Add **reference variables** so the backend reads the managed datastores:

| Variable       | Value                          |
| -------------- | ------------------------------ |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}`   |
| `REDIS_URL`    | `${{Redis.REDIS_URL}}`         |
| `SECRET_KEY`   | *(a strong random string)*     |
| `CORS_ORIGINS` | `["https://<frontend-domain>"]`|

> The backend auto-rewrites Railway's `postgresql://` URL to the
> `postgresql+psycopg://` driver, so no manual URL surgery is needed.

### Verify (after deploy)
- `https://<backend-domain>/`            → `{"app":"Mini SoulSpace","status":"running","phase":"0"}`
- `https://<backend-domain>/health`      → `{"status":"healthy"}`
- `https://<backend-domain>/health/ready`→ `{"status":"ready","checks":{"database":"ok","redis":"ok"}}`

`/health/ready` is the end-to-end proof that the backend reaches **Postgres and
Redis**. It returns HTTP `503` + a `degraded` status naming any dependency that
is not yet connected.

---

## 2. Frontend service (Next.js)

### Settings → Build
- **Root Directory:** `frontend`
- **Builder:** `Dockerfile` (via `frontend/railway.json`).

### Variables
| Variable              | Value                          |
| --------------------- | ------------------------------ |
| `NEXT_PUBLIC_API_URL` | `https://<backend-domain>`     |

### Networking
Generate a public domain (Settings → Networking → Generate Domain). The landing
page is served at `/`.

---

## Troubleshooting

| Symptom                                   | Cause / Fix                                                        |
| ----------------------------------------- | ----------------------------------------------------------------- |
| *Failed to build an image* at root        | Root Directory not set — point the service at `backend`/`frontend`.|
| `"/requirements.txt": not found`          | Dockerfile Path points at `/docker/backend.Dockerfile` with root context. Set Root Directory = `backend` and Dockerfile Path = `Dockerfile`. |
| Build ignores the Dockerfile              | Builder still on Railpack — switch to **Dockerfile**.             |
| App builds but crashes / restarts         | Not binding `$PORT` — the committed Dockerfiles already handle it. |
| `/health/ready` shows `database: error`   | `DATABASE_URL` not referencing `${{Postgres.DATABASE_URL}}`.       |
| `/health/ready` shows `redis: error`      | Redis service not added or `REDIS_URL` not referenced.            |
