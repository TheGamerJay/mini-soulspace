"""Router brain — decides which brain(s) should handle an incoming request.

In later phases this brain inspects the user's input and dispatches to the
appropriate specialist brain(s). Phase 0 provides the stable interface only.
"""

from __future__ import annotations

from app.brains.base import Brain, BrainContext, BrainResult


class RouterBrain(Brain):
    name = "router_brain"

    def process(self, context: BrainContext) -> BrainResult:
        return BrainResult(brain=self.name, output={"route": "emotional_brain"})


__all__ = ["RouterBrain"]
