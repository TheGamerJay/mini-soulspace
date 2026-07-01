"""Emotional brain — interprets the emotional tone of diary entries.

Later phases derive sentiment, mood and affect signals that feed reflections
and analytics. Phase 0 provides the stable interface only.
"""

from __future__ import annotations

from app.brains.base import Brain, BrainContext, BrainResult


class EmotionalBrain(Brain):
    name = "emotional_brain"

    def process(self, context: BrainContext) -> BrainResult:
        return BrainResult(brain=self.name, output={"mood": "neutral"})


__all__ = ["EmotionalBrain"]
