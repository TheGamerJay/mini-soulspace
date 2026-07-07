"""Specialist Registry — discoverable, configuration-driven.

The Router never knows specialists in advance and never hardcodes specialist
logic: everything is discovered from ``specialists.json``. Future specialists
are added simply by registering them — no Orchestra redesign.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.orchestra.router.errors import RouterError
from app.orchestra.router.schemas import SpecialistCard

DEFAULT_SPECIALISTS_PATH = Path(__file__).with_name("specialists.json")


def load_specialists(path: Path | str = DEFAULT_SPECIALISTS_PATH) -> dict[str, SpecialistCard]:
    """Load capability cards from the registry file."""

    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise RouterError(
            [{"field": "registry", "code": "missing_registry", "message": "specialists.json could not be loaded."}]
        )
    return {
        name: SpecialistCard(
            name=name,
            display_name=cfg["display_name"],
            description=cfg["description"],
            purpose=cfg["purpose"],
            capabilities=tuple(cfg["capabilities"]),
            supported_inputs=tuple(cfg["supported_inputs"]),
            supported_outputs=tuple(cfg["supported_outputs"]),
            priority=cfg["priority"],
            availability=cfg["availability"],
            version=cfg["version"],
            health_status=cfg["health_status"],
            execution_mode=cfg["execution_mode"],
            estimated_cost=cfg["estimated_cost"],
            estimated_speed=cfg["estimated_speed"],
            service=cfg["service"],
        )
        for name, cfg in raw["specialists"].items()
    }


def future_specialists(path: Path | str = DEFAULT_SPECIALISTS_PATH) -> tuple[str, ...]:
    """Names reserved for future specialists (architecture placeholders)."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return tuple(raw.get("future_specialists", []))


def find_by_capability(
    registry: dict[str, SpecialistCard], capabilities: set[str]
) -> list[SpecialistCard]:
    """All specialists advertising any of the requested capabilities,
    highest priority first (deterministic tie-break by name)."""

    matches = [c for c in registry.values() if capabilities & set(c.capabilities)]
    return sorted(matches, key=lambda c: (-c.priority, c.name))
