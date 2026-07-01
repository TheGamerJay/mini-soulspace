"""Analytics brain — derives trends and metrics across a user's history.

Later phases compute mood trends, streaks and insight metrics. Phase 0 provides
the stable interface only.
"""

from __future__ import annotations

from app.brains.base import Brain, BrainContext, BrainResult


class AnalyticsBrain(Brain):
    name = "analytics_brain"

    def process(self, context: BrainContext) -> BrainResult:
        return BrainResult(brain=self.name, output={"metrics": {}})


__all__ = ["AnalyticsBrain"]
