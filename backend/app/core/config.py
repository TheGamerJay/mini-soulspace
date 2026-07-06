"""Application configuration.

Uses pydantic-settings so every value can be overridden through environment
variables or a local ``.env`` file. This is the single source of truth for
runtime configuration across the whole backend.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application metadata ------------------------------------------------
    APP_NAME: str = "Mini SoulSpace"
    APP_PHASE: str = "3.8.5"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    # --- Datastores ----------------------------------------------------------
    DATABASE_URL: str = "postgresql+psycopg://soulspace:soulspace@localhost:5432/soulspace"
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- AI / Ollama ---------------------------------------------------------
    OLLAMA_URL: str = "http://localhost:11434"
    MAIN_MODEL: str = "qwen3:14b"
    FAST_MODEL: str = "llama3.1:8b"
    TAG_MODEL: str = "gemma3:4b"
    CODER_MODEL: str = "qwen2.5-coder:14b"

    # --- Mini Engine (local runtime access) ----------------------------------
    MINI_TIMEOUT_SECONDS: float = 60.0
    MINI_RETRIES: int = 1

    # --- Security / CORS -----------------------------------------------------
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # --- JWT / session -------------------------------------------------------
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_TTL_MINUTES: int = 15
    REFRESH_TOKEN_TTL_DAYS: int = 30

    # httpOnly auth cookies. COOKIE_SECURE must be True in production (HTTPS).
    ACCESS_COOKIE_NAME: str = "ss_access"
    REFRESH_COOKIE_NAME: str = "ss_refresh"
    COOKIE_SECURE: bool = False
    COOKIE_DOMAIN: str | None = None
    REFRESH_COOKIE_PATH: str = "/api/auth"

    # --- Registration policy -------------------------------------------------
    # Minimum age is configurable and can be disabled entirely by setting it to
    # 0 (or a negative value). Never hardcode a permanent age gate.
    MIN_SIGNUP_AGE: int = 13

    # --- Rate limiting (Redis-backed) ----------------------------------------
    RATE_LIMIT_ENABLED: bool = True
    LOGIN_RATE_LIMIT: int = 10  # attempts per window
    LOGIN_RATE_WINDOW_SECONDS: int = 300
    REGISTER_RATE_LIMIT: int = 5
    REGISTER_RATE_WINDOW_SECONDS: int = 3600

    @property
    def min_age_enabled(self) -> bool:
        """Whether the minimum-age gate is active."""

        return self.MIN_SIGNUP_AGE > 0

    @property
    def cookie_secure(self) -> bool:
        """Force secure cookies outside of local development."""

        return self.COOKIE_SECURE or self.ENVIRONMENT.lower() in {"production", "prod"}

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Normalise managed-provider URLs to the psycopg3 SQLAlchemy driver.

        Railway/Heroku inject ``postgres://`` or ``postgresql://`` URLs, but
        SQLAlchemy needs the explicit ``postgresql+psycopg://`` driver prefix.
        """

        if value.startswith("postgresql+"):
            return value
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance.

    Cached so the ``.env`` file is only parsed once per process.
    """

    return Settings()


settings = get_settings()
