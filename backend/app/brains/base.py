"""Shared foundation for every SoulSpace "brain".

A *brain* is a focused, single-responsibility reasoning unit. Each brain owns
one cognitive concern (routing, emotion, reflection, memory, building,
analytics, safety) and exposes a small, well-defined interface. Concrete
behaviour is implemented in later phases; Phase 0 establishes the contract so
the rest of the system can depend on stable seams.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BrainContext:
    """Input passed to a brain for a single reasoning turn."""

    user_id: str | None = None
    text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrainResult:
    """Output produced by a brain for a single reasoning turn."""

    brain: str
    output: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Brain(ABC):
    """Abstract base class all brains inherit from."""

    #: Stable identifier used in routing, logging and analytics.
    name: str = "brain"

    @abstractmethod
    def process(self, context: BrainContext) -> BrainResult:
        """Process a single context and return a result."""

    def describe(self) -> dict[str, str]:
        """Return a short self-description (used by the router brain)."""

        return {"name": self.name, "doc": (self.__doc__ or "").strip()}
