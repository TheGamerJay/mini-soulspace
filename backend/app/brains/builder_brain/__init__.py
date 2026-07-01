"""Builder brain — assembles structured artefacts (summaries, timelines, charts).

Later phases compose higher-level views from raw entries and memory. Phase 0
provides the stable interface only.
"""

from __future__ import annotations

from app.brains.base import Brain, BrainContext, BrainResult


class BuilderBrain(Brain):
    name = "builder_brain"

    def process(self, context: BrainContext) -> BrainResult:
        return BrainResult(brain=self.name, output={"artifact": None})


__all__ = ["BuilderBrain"]
