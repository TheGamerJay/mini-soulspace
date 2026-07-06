"""Memory Intelligence Engine — memory quality over time (Phase 3.8.5).

Confidence, evidence, sources, version history, evolution, conflict resolution,
decay, verification prep, and user-correction learning. No AI, no retrieval, no
generation. See docs/MEMORY_INTELLIGENCE_ENGINE.md.
"""

from app.orchestra.intelligence.engine import (
    DEFAULT_CONFIG_PATH,
    apply_correction,
    apply_decay,
    assess,
    load_config,
    needs_verification,
    required_confidence,
    score_confidence,
    would_resurface,
)
from app.orchestra.intelligence.errors import MemoryIntelligenceError
from app.orchestra.intelligence.schemas import (
    ANALYTICS_EVENTS,
    SCHEMA_VERSION,
    IntelligenceConfig,
    MemoryIntelligenceResult,
    MemorySource,
    NextAction,
    VerificationStatus,
)
from app.orchestra.intelligence.store import DbIntelligenceStore, IntelligenceStore

__all__ = [
    "assess",
    "apply_decay",
    "apply_correction",
    "needs_verification",
    "would_resurface",
    "required_confidence",
    "score_confidence",
    "load_config",
    "DEFAULT_CONFIG_PATH",
    "MemoryIntelligenceError",
    "MemoryIntelligenceResult",
    "IntelligenceConfig",
    "MemorySource",
    "VerificationStatus",
    "NextAction",
    "IntelligenceStore",
    "DbIntelligenceStore",
    "ANALYTICS_EVENTS",
    "SCHEMA_VERSION",
]
