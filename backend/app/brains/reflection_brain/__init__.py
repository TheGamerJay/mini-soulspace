"""Reflection brain — generates the diary's "talking back" responses.

Later phases synthesise supportive, context-aware reflections from an entry and
the user's memory. Phase 0 provides the stable interface only.
"""

from __future__ import annotations

from app.brains.base import Brain, BrainContext, BrainResult


class ReflectionBrain(Brain):
    name = "reflection_brain"

    def process(self, context: BrainContext) -> BrainResult:
        return BrainResult(brain=self.name, output={"reflection": ""})


__all__ = ["ReflectionBrain"]
