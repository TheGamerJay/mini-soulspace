"""Safety brain — screens content for risk and crisis signals.

Later phases detect self-harm / crisis language and route to supportive,
resource-aware responses. Phase 0 provides the stable interface only.
"""

from __future__ import annotations

from app.brains.base import Brain, BrainContext, BrainResult


class SafetyBrain(Brain):
    name = "safety_brain"

    def process(self, context: BrainContext) -> BrainResult:
        return BrainResult(brain=self.name, output={"flagged": False, "level": "none"})


__all__ = ["SafetyBrain"]
