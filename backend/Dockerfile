# Mini SoulSpace backend — Railway / production image.
#
# Railway's Dockerfile builder uses this file with the backend/ directory as the
# build context (set the service "Root Directory" to `backend`). The container
# binds to Railway's injected $PORT (falling back to 8000 locally).

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application source.
COPY . .

EXPOSE 8000

# Shell form so ${PORT} is expanded at runtime by the platform.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
