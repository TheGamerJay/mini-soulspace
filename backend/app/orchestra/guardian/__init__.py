"""Guardian Engine — Orchestra node 2 (the protector).

Classifies and protects; produces an immutable GuardianResult. No AI, no Ollama,
no reflection, no memory I/O. See docs/GUARDIAN_ENGINE.md.
"""

from app.orchestra.guardian.engine import evaluate
from app.orchestra.guardian.errors import GuardianError
from app.orchestra.guardian.schemas import (
    SCHEMA_VERSION,
    EmotionalTone,
    GuardianCategory,
    GuardianResult,
    ReflectionDepth,
    RecommendedAction,
)

__all__ = [
    "evaluate",
    "GuardianError",
    "GuardianResult",
    "GuardianCategory",
    "EmotionalTone",
    "ReflectionDepth",
    "RecommendedAction",
    "SCHEMA_VERSION",
]
