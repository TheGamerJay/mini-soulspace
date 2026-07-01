"""Brain registry.

Exposes every brain and a name-keyed registry so the router brain and services
can look brains up dynamically without importing each module directly.
"""

from __future__ import annotations

from app.brains.analytics_brain import AnalyticsBrain
from app.brains.base import Brain, BrainContext, BrainResult
from app.brains.builder_brain import BuilderBrain
from app.brains.emotional_brain import EmotionalBrain
from app.brains.memory_brain import MemoryBrain
from app.brains.reflection_brain import ReflectionBrain
from app.brains.router_brain import RouterBrain
from app.brains.safety_brain import SafetyBrain

BRAIN_CLASSES: tuple[type[Brain], ...] = (
    RouterBrain,
    EmotionalBrain,
    ReflectionBrain,
    MemoryBrain,
    BuilderBrain,
    AnalyticsBrain,
    SafetyBrain,
)

#: Name -> instance registry for dynamic lookup.
REGISTRY: dict[str, Brain] = {cls.name: cls() for cls in BRAIN_CLASSES}

__all__ = [
    "Brain",
    "BrainContext",
    "BrainResult",
    "RouterBrain",
    "EmotionalBrain",
    "ReflectionBrain",
    "MemoryBrain",
    "BuilderBrain",
    "AnalyticsBrain",
    "SafetyBrain",
    "BRAIN_CLASSES",
    "REGISTRY",
]
