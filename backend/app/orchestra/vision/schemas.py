"""Mini Vision schemas — structured visual facts, never conclusions.

Rule 25: Mini Vision observes. It never concludes, never advises, never
identifies people. Only structured output for the Orchestra — no user-facing
language.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class VisionConfig(_Frozen):
    """Loaded from vision.json — nothing hardcoded."""

    ocr_enabled: bool = True
    objects_enabled: bool = True
    charts_enabled: bool = True
    handwriting_enabled: bool = True
    language_detection_enabled: bool = True
    max_image_bytes: int = 10 * 1024 * 1024
    min_width: int = 32
    min_height: int = 32
    allowed_formats: tuple[str, ...] = ("png", "jpeg", "webp")
    quality_penalty: float = 0.15
    future_models: dict[str, Any] = Field(default_factory=dict)


class VisionImage(_Frozen):
    """A raw image handed to Mini Vision (photo, screenshot, scan, page…)."""

    filename: str
    content_type: str
    data: bytes


class ImageMetadata(_Frozen):
    filename: str
    content_type: str
    detected_format: str  # png | jpeg | webp | unknown
    width: int | None = None
    height: int | None = None
    size_bytes: int = 0


class ImageQuality(_Frozen):
    """Quality flags: blurry, dark, low_resolution, rotated, partially_visible,
    overexposed, underexposed, unreadable, dimensions_unknown…"""

    flags: tuple[str, ...] = Field(default_factory=tuple)
    score: float = Field(ge=0.0, le=1.0, default=1.0)


class DetectedObject(_Frozen):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    box: tuple[int, int, int, int] | None = None  # x, y, w, h


class LayoutRegion(_Frozen):
    kind: str  # heading | paragraph | table | figure | caption | panel | ui_element
    text: str = ""
    box: tuple[int, int, int, int] | None = None


class Handwriting(_Frozen):
    present: bool = False
    readability: float = Field(ge=0.0, le=1.0, default=0.0)
    text: str = ""


class VisionResult(_Frozen):
    """Immutable structured visual facts for the Orchestra."""

    schema_version: str = SCHEMA_VERSION
    vision_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    trace_id: uuid.UUID

    image_metadata: ImageMetadata
    image_quality: ImageQuality
    detected_language: str | None = None
    ocr_text: str = ""
    objects: tuple[DetectedObject, ...] = Field(default_factory=tuple)
    layout: tuple[LayoutRegion, ...] = Field(default_factory=tuple)
    tables: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    charts: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    diagrams: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    handwriting: Handwriting = Field(default_factory=Handwriting)
    document_type: str = "unknown"
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


#: Object detection taxonomy — future objects extend naturally.
OBJECT_TAXONOMY: tuple[str, ...] = (
    "medication", "bottle", "book", "computer", "phone", "monitor", "paper",
    "graph", "chart", "table", "receipt", "homework", "plant", "animal",
    "food", "vehicle", "tool", "person",
)

#: Document understanding taxonomy.
DOCUMENT_TYPES: tuple[str, ...] = (
    "homework", "medical_paper", "medication_label", "letter", "invoice",
    "receipt", "form", "business_card", "pdf_image", "notebook_page",
    "journal_page", "screenshot", "chart", "diagram", "comic_page", "map",
    "unknown",
)

#: UI screenshot kinds (screenshot analysis).
UI_KINDS: tuple[str, ...] = (
    "desktop_software", "website", "mobile_app", "settings_page",
    "error_dialog", "dashboard", "game", "developer_tools",
)

#: Future capabilities — architecture placeholders only, not implemented.
FUTURE_CAPABILITIES: tuple[str, ...] = (
    "barcode", "qr_code", "depth", "segmentation", "3d", "video",
    "live_camera", "ar", "multi_image_comparison", "image_similarity",
    "image_search",
)

#: Identity protection: observations Mini Vision must never produce.
FORBIDDEN_OBSERVATIONS: frozenset[str] = frozenset({
    "identity", "person_identity", "face", "face_match", "face_recognition",
    "age", "race", "ethnicity", "religion", "political_affiliation",
    "sexuality", "gender", "demographics", "medical_condition",
})
