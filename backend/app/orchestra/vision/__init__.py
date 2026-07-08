"""Mini Vision — the visual perception specialist (Phase 4.3).

Observes, never concludes (Rule 25). Structured VisionResults only; identity is
never inferred; nothing is hallucinated. See docs/MINI_VISION.md.
"""

from app.orchestra.vision.engine import (
    DEFAULT_VISION_CONFIG_PATH,
    NullPerceptionBackend,
    VisionBackend,
    analyze,
    detect_format,
    image_dimensions,
    load_vision_config,
    make_vision_executor,
    sanitize_identity,
)
from app.orchestra.vision.errors import VisionError
from app.orchestra.vision.schemas import (
    DOCUMENT_TYPES,
    FORBIDDEN_OBSERVATIONS,
    FUTURE_CAPABILITIES,
    OBJECT_TAXONOMY,
    SCHEMA_VERSION,
    UI_KINDS,
    DetectedObject,
    Handwriting,
    ImageMetadata,
    ImageQuality,
    LayoutRegion,
    VisionConfig,
    VisionImage,
    VisionResult,
)

__all__ = [
    "analyze",
    "make_vision_executor",
    "load_vision_config",
    "detect_format",
    "image_dimensions",
    "sanitize_identity",
    "VisionBackend",
    "NullPerceptionBackend",
    "DEFAULT_VISION_CONFIG_PATH",
    "VisionError",
    "VisionConfig",
    "VisionImage",
    "VisionResult",
    "ImageMetadata",
    "ImageQuality",
    "DetectedObject",
    "LayoutRegion",
    "Handwriting",
    "OBJECT_TAXONOMY",
    "DOCUMENT_TYPES",
    "UI_KINDS",
    "FUTURE_CAPABILITIES",
    "FORBIDDEN_OBSERVATIONS",
    "SCHEMA_VERSION",
]
