"""Mini Service Registry.

The Orchestra addresses model roles; the Mini Engine maps role -> Mini Service ->
local model. The Orchestra never learns which underlying model is used. Future
services can be added by editing ``mini_services.json`` — no Orchestra redesign.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.orchestra.mini.schemas import MiniService
from app.orchestra.prompt.schemas import ModelRole

DEFAULT_SERVICES_PATH = Path(__file__).with_name("mini_services.json")

# Orchestra-facing role -> internal Mini Service name.
ROLE_TO_SERVICE: dict[ModelRole, str] = {
    ModelRole.MAIN: "mini_core",
    ModelRole.FAST: "mini_swift",
    ModelRole.SUMMARY: "mini_insight",
    ModelRole.CODING: "mini_creator",
    ModelRole.VISION: "mini_vision",
    ModelRole.RESEARCH: "mini_research",
    ModelRole.IMAGE: "mini_canvas",
}


def load_registry(path: Path | str = DEFAULT_SERVICES_PATH) -> dict[str, MiniService]:
    """Load the service registry. Raises OSError/JSONDecodeError on failure."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        key: MiniService(
            key=key,
            display_name=cfg["display_name"],
            purpose=cfg["purpose"],
            runtime=cfg["runtime"],
            model=cfg["model"],
        )
        for key, cfg in raw.items()
    }


def resolve_service(role: ModelRole, registry: dict[str, MiniService]) -> MiniService:
    """Resolve a model role to a configured Mini Service. Raises KeyError if none."""

    key = ROLE_TO_SERVICE.get(role)
    if key not in registry:
        raise KeyError(f"No Mini Service configured for role '{role.value}'.")
    return registry[key]
