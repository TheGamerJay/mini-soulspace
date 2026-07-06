"""Meaning & Intent Engine — runs before the Guardian.

Determines meaning, context, intent, and real-world intent so safety decisions
are never based on isolated words. No AI. See docs/MEANING_INTENT_ENGINE.md.
"""

from app.orchestra.meaning.engine import analyze
from app.orchestra.meaning.errors import MeaningError
from app.orchestra.meaning.schemas import (
    SCHEMA_VERSION,
    ContextType,
    IntentType,
    MeaningIntentResult,
    MeaningType,
    RealWorldIntent,
)

__all__ = [
    "analyze",
    "MeaningError",
    "MeaningIntentResult",
    "MeaningType",
    "ContextType",
    "IntentType",
    "RealWorldIntent",
    "SCHEMA_VERSION",
]
