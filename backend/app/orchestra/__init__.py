"""The Soul Orchestra — the reasoning pipeline (Phase 3+).

Phase 3.0 implements only the first node, the Input Receiver, which packages
application state into an immutable ``OrchestraRequest``. No AI, memory, safety,
prompt, or model logic lives here.
"""

from app.orchestra.errors import InputValidationError
from app.orchestra.input_receiver import build_orchestra_request
from app.orchestra.schemas import SCHEMA_VERSION, OrchestraRequest

__all__ = [
    "build_orchestra_request",
    "OrchestraRequest",
    "InputValidationError",
    "SCHEMA_VERSION",
]
