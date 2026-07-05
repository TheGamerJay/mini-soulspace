"""Mini Engine — Orchestra node 7 (first node with local model access).

The Orchestra addresses Mini Services by name; this node maps them to local
models and returns an immutable CandidateResponse. The runtime (Ollama) is sealed
inside `runtime.py`. See docs/MINI_ENGINE.md.
"""

from app.orchestra.mini.engine import generate
from app.orchestra.mini.errors import MiniEngineError
from app.orchestra.mini.registry import ROLE_TO_SERVICE, load_registry, resolve_service
from app.orchestra.mini.runtime import OllamaRuntime, RuntimeTimeout, RuntimeUnavailable
from app.orchestra.mini.schemas import (
    SCHEMA_VERSION,
    CandidateResponse,
    MiniService,
    RuntimeResponse,
    TokenCounts,
)

__all__ = [
    "generate",
    "MiniEngineError",
    "CandidateResponse",
    "RuntimeResponse",
    "TokenCounts",
    "MiniService",
    "load_registry",
    "resolve_service",
    "ROLE_TO_SERVICE",
    "OllamaRuntime",
    "RuntimeTimeout",
    "RuntimeUnavailable",
    "SCHEMA_VERSION",
]
