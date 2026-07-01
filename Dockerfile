# Mini SoulSpace — unified single-container image (frontend + backend).
#
# Stage 1 builds the Next.js static export; stage 2 runs the FastAPI backend and
# serves that static build. Deployed as ONE Railway service with the repository
# root as the build context (Root Directory = empty/`/`).

# ── Stage 1: build the frontend (Next.js static export) ──────────────────────
FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build          # emits ./out (static site)

# ── Stage 2: backend runtime that also serves the static frontend ────────────
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install backend dependencies first for better layer caching.
COPY backend/requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Backend source.
COPY backend/ ./

# Built frontend -> ./static, which FastAPI mounts at "/".
COPY --from=frontend /frontend/out ./static

# Railway routes to port 8080 by default; bind there unless $PORT overrides.
EXPOSE 8080

# Shell form so ${PORT} is expanded at runtime by the platform.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
