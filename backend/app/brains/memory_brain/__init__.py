"""Memory brain — stores and retrieves long-term semantic memory.

Later phases embed entries with pgvector and recall relevant context. Phase 0
provides the stable interface only.
"""

from __future__ import annotations

from app.brains.base import Brain, BrainContext, BrainResult


class MemoryBrain(Brain):
    name = "memory_brain"

    def process(self, context: BrainContext) -> BrainResult:
        return BrainResult(brain=self.name, output={"memories": []})


__all__ = ["MemoryBrain"]
