"""Specialist Router — decides WHO helps; the Orchestra decides HOW.

Deterministic, registry-driven, never keywords alone, never bypasses the
Guardian. See docs/SPECIALIST_ROUTER.md and docs/MINI_SERVICES.md.
"""

from app.orchestra.router.errors import RouterError
from app.orchestra.router.registry import (
    DEFAULT_SPECIALISTS_PATH,
    find_by_capability,
    future_specialists,
    load_specialists,
)
from app.orchestra.router.router import route
from app.orchestra.router.schemas import (
    SCHEMA_VERSION,
    Availability,
    Complexity,
    RoutingPlan,
    SpecialistCard,
)

__all__ = [
    "route",
    "load_specialists",
    "future_specialists",
    "find_by_capability",
    "DEFAULT_SPECIALISTS_PATH",
    "RouterError",
    "RoutingPlan",
    "SpecialistCard",
    "Availability",
    "Complexity",
    "SCHEMA_VERSION",
]
