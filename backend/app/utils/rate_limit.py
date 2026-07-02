"""Redis-backed fixed-window rate limiter.

Fails open: if Redis is unreachable the limiter allows the request rather than
locking users out of the whole service. Rate limiting is a mitigation, not a
correctness guarantee.
"""

from __future__ import annotations

import redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: redis.Redis | None = None


def _get_client() -> redis.Redis | None:
    global _client
    if _client is None:
        try:
            _client = redis.from_url(
                settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Could not create Redis client for rate limiting: %s", exc)
            return None
    return _client


def check_rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """Return ``True`` if the action is allowed, ``False`` if the limit is hit.

    Uses a fixed window keyed by ``key``. The first hit sets an expiry so the
    window resets automatically.
    """

    if not settings.RATE_LIMIT_ENABLED:
        return True

    client = _get_client()
    if client is None:
        return True  # fail open

    redis_key = f"ratelimit:{key}"
    try:
        current = client.incr(redis_key)
        if current == 1:
            client.expire(redis_key, window_seconds)
        return int(current) <= limit
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Rate limit check failed (allowing request): %s", exc)
        return True


def reset_rate_limit(key: str) -> None:
    """Clear a rate-limit counter (e.g. after a successful login)."""

    client = _get_client()
    if client is None:
        return
    try:
        client.delete(f"ratelimit:{key}")
    except Exception:  # pragma: no cover - defensive
        pass
