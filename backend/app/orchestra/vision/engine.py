"""Mini Vision engine — the visual perception system of Mini SoulSpace.

Single responsibility: understand visual information and return structured
``VisionResult``s. It never talks to the user, never generates final responses,
never interprets user intent, never diagnoses, never identifies people, never
stores memories, and never bypasses the Orchestra (Rule 25).

Perception models are injectable ``VisionBackend``s (like the sealed local
runtime in the Mini Engine): the engine validates and measures the actual image
bytes, delegates raw perception, then sanitizes and structures the outcome.
Without a backend the result is honestly empty — **unreadable stays unreadable;
nothing is ever hallucinated.**
"""

from __future__ import annotations

import json
import struct
import uuid
from pathlib import Path
from typing import Any, Protocol

from app.orchestra.vision.errors import VisionError
from app.orchestra.vision.schemas import (
    FORBIDDEN_OBSERVATIONS,
    DetectedObject,
    Handwriting,
    ImageMetadata,
    ImageQuality,
    LayoutRegion,
    VisionConfig,
    VisionImage,
    VisionResult,
)

DEFAULT_VISION_CONFIG_PATH = Path(__file__).with_name("vision.json")


class VisionBackend(Protocol):
    """A perception model. Returns raw observations as a dict; the engine
    sanitizes and structures them. Future models plug in without redesign."""

    def perceive(self, image: VisionImage, config: VisionConfig) -> dict[str, Any]: ...


class NullPerceptionBackend:
    """No model deployed: observes nothing, invents nothing."""

    def perceive(self, image: VisionImage, config: VisionConfig) -> dict[str, Any]:
        return {}


def load_vision_config(path: Path | str = DEFAULT_VISION_CONFIG_PATH) -> VisionConfig:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise VisionError(
            [{"field": "config", "code": "missing_config", "message": "vision.json could not be loaded."}]
        )
    raw["allowed_formats"] = tuple(raw.get("allowed_formats", ()))
    return VisionConfig(**raw)


# ── Deterministic image inspection (real bytes, no model) ────────────────────
def detect_format(data: bytes) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return "unknown"


def image_dimensions(data: bytes, fmt: str) -> tuple[int | None, int | None]:
    """Parse dimensions from the actual header bytes. Unknown stays unknown."""

    if fmt == "png" and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return width, height
    if fmt == "jpeg":
        # Walk JPEG markers to a start-of-frame segment.
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                break
            marker = data[i + 1]
            length = struct.unpack(">H", data[i + 2:i + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                height, width = struct.unpack(">HH", data[i + 5:i + 9])
                return width, height
            i += 2 + length
    return None, None


def _quality(meta: ImageMetadata, config: VisionConfig, backend_flags: list[str]) -> ImageQuality:
    flags = list(backend_flags)
    if meta.width is None or meta.height is None:
        flags.append("dimensions_unknown")
    elif meta.width < config.min_width or meta.height < config.min_height:
        flags.append("low_resolution")
    score = max(0.0, 1.0 - config.quality_penalty * len(flags))
    return ImageQuality(flags=tuple(dict.fromkeys(flags)), score=score)


# ── Identity protection ──────────────────────────────────────────────────────
def _is_forbidden(label: str) -> bool:
    low = label.lower()
    return low in FORBIDDEN_OBSERVATIONS or "face" in low or "identity" in low


def sanitize_identity(raw: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Strip any observation that could identify or profile a person.

    A generic "person" object may remain; identity, faces, and demographic
    inferences never do."""

    warnings: list[str] = []
    cleaned = dict(raw)
    removed = 0

    objects = []
    for obj in cleaned.get("objects", []):
        if _is_forbidden(str(obj.get("label", ""))):
            removed += 1
            continue
        objects.append(obj)
    cleaned["objects"] = objects

    for key in list(cleaned):
        if _is_forbidden(key):
            cleaned.pop(key)
            removed += 1

    if removed:
        warnings.append(f"identity_protection: removed {removed} forbidden observation(s)")
    return cleaned, warnings


# ── The engine ───────────────────────────────────────────────────────────────
def analyze(
    image: VisionImage,
    *,
    trace_id: uuid.UUID,
    backend: VisionBackend | None = None,
    config: VisionConfig | None = None,
) -> VisionResult:
    """Analyze one image into structured visual facts."""

    if not isinstance(image, VisionImage):
        raise VisionError([{"field": "image", "code": "invalid_input", "message": "Expected a VisionImage."}])
    config = config or load_vision_config()
    backend = backend or NullPerceptionBackend()

    fmt = detect_format(image.data)
    width, height = image_dimensions(image.data, fmt)
    meta = ImageMetadata(
        filename=image.filename, content_type=image.content_type,
        detected_format=fmt, width=width, height=height, size_bytes=len(image.data),
    )

    warnings: list[str] = []

    # Content problems degrade honestly — they never crash the Orchestra.
    if fmt not in config.allowed_formats:
        return VisionResult(
            trace_id=trace_id, image_metadata=meta,
            image_quality=ImageQuality(flags=("unreadable",), score=0.0),
            confidence=0.0, warnings=("unsupported_format",),
        )
    if meta.size_bytes > config.max_image_bytes:
        return VisionResult(
            trace_id=trace_id, image_metadata=meta,
            image_quality=ImageQuality(flags=("unreadable",), score=0.0),
            confidence=0.0, warnings=("image_too_large",),
        )

    try:
        raw = backend.perceive(image, config) or {}
    except Exception as exc:  # noqa: BLE001 — perception failure degrades, never crashes
        raw = {}
        warnings.append(f"backend_failed: {type(exc).__name__}")

    raw, identity_warnings = sanitize_identity(raw)
    warnings.extend(identity_warnings)

    quality = _quality(meta, config, list(raw.get("quality_flags", [])))

    ocr_text = str(raw.get("ocr_text", "")) if config.ocr_enabled else ""
    if not config.ocr_enabled:
        warnings.append("ocr_disabled")
    language = raw.get("detected_language") if config.language_detection_enabled else None

    objects = (
        tuple(
            DetectedObject(
                label=str(o["label"]),
                confidence=float(o.get("confidence", 0.5)),
                box=tuple(o["box"]) if o.get("box") else None,
            )
            for o in raw.get("objects", [])
        )
        if config.objects_enabled
        else ()
    )
    layout = tuple(
        LayoutRegion(kind=str(r.get("kind", "paragraph")), text=str(r.get("text", "")),
                     box=tuple(r["box"]) if r.get("box") else None)
        for r in raw.get("layout", [])
    )
    charts = tuple(raw.get("charts", [])) if config.charts_enabled else ()
    hw_raw = raw.get("handwriting") or {}
    handwriting = (
        Handwriting(
            present=bool(hw_raw.get("present", False)),
            readability=float(hw_raw.get("readability", 0.0)),
            text=str(hw_raw.get("text", "")),
        )
        if config.handwriting_enabled
        else Handwriting()
    )

    document_type = str(raw.get("document_type", "unknown"))
    perceived = bool(raw.get("ocr_text") or raw.get("objects") or raw.get("document_type"))
    if not perceived:
        # Nothing was observed — say so plainly. Never invent missing words.
        warnings.append("no_perception_available")

    # Medication safety: Mini Vision reads the label only — no medical advice.
    if document_type == "medication_label" or any(o.label == "medication" for o in objects):
        warnings.append("medication: label reading only — no medical advice")

    base = float(raw.get("confidence", 0.9 if perceived else 0.1))
    confidence = round(max(0.0, min(1.0, base * quality.score)), 3)

    return VisionResult(
        trace_id=trace_id,
        image_metadata=meta,
        image_quality=quality,
        detected_language=language,
        ocr_text=ocr_text,
        objects=objects,
        layout=layout,
        tables=tuple(raw.get("tables", [])),
        charts=charts,
        diagrams=tuple(raw.get("diagrams", [])),
        handwriting=handwriting,
        document_type=document_type,
        confidence=confidence,
        warnings=tuple(warnings),
        metadata={"backend": type(backend).__name__},
    )


def make_vision_executor(
    image: VisionImage,
    *,
    backend: VisionBackend | None = None,
    config: VisionConfig | None = None,
    trace_id: uuid.UUID,
):
    """Adapt Mini Vision to the Specialist Orchestrator's executor contract.

    The executor performs exactly its assigned task and returns structured
    evidence for the workspace — never a user-facing response."""

    def executor(task, inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
        result = analyze(image, trace_id=trace_id, backend=backend, config=config)
        return {
            "vision_result": result.model_dump(mode="json"),
            "ocr_text": result.ocr_text,
            "document_type": result.document_type,
            "confidence": result.confidence,
        }

    return executor
