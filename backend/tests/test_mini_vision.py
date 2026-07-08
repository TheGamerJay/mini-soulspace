"""Mini Vision tests — full coverage. Observes, never concludes, never invents."""

from __future__ import annotations

import struct
import uuid

import pytest

from app.orchestra.orchestrator import OrchestrationStatus, orchestrate, OrchestratorConfig
from app.orchestra.router.schemas import RoutingPlan
from app.orchestra.vision import (
    DOCUMENT_TYPES,
    FORBIDDEN_OBSERVATIONS,
    FUTURE_CAPABILITIES,
    OBJECT_TAXONOMY,
    NullPerceptionBackend,
    VisionConfig,
    VisionError,
    VisionImage,
    analyze,
    detect_format,
    image_dimensions,
    load_vision_config,
    make_vision_executor,
    sanitize_identity,
)

TRACE = uuid.uuid4()
CFG = VisionConfig()


def png_bytes(w: int = 640, h: int = 480) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR"
        + struct.pack(">II", w, h) + b"\x00" * 30
    )


def jpeg_bytes(w: int = 800, h: int = 600) -> bytes:
    return (
        b"\xff\xd8"
        + b"\xff\xe0" + struct.pack(">H", 4) + b"\x00\x00"
        + b"\xff\xc0" + struct.pack(">H", 11) + b"\x08" + struct.pack(">HH", h, w)
        + b"\x00" * 12
    )


def webp_bytes() -> bytes:
    return b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 16


def img(data: bytes, name: str = "photo.png") -> VisionImage:
    return VisionImage(filename=name, content_type="image/png", data=data)


class FakeBackend:
    def __init__(self, raw: dict):
        self.raw = raw

    def perceive(self, image, config):
        return self.raw


class BoomBackend:
    def perceive(self, image, config):
        raise RuntimeError("model exploded")


# ── Config + format detection ─────────────────────────────────────────────────
def test_config_loads_and_missing_raises():
    cfg = load_vision_config()
    assert cfg.ocr_enabled is True and "png" in cfg.allowed_formats
    with pytest.raises(VisionError) as e:
        load_vision_config("nope.json")
    assert e.value.code == "missing_config"


@pytest.mark.parametrize(
    "data,expected",
    [(png_bytes(), "png"), (jpeg_bytes(), "jpeg"), (webp_bytes(), "webp"), (b"hello world!", "unknown")],
)
def test_detect_format(data, expected):
    assert detect_format(data) == expected


def test_dimensions_png_and_jpeg():
    assert image_dimensions(png_bytes(1024, 768), "png") == (1024, 768)
    assert image_dimensions(jpeg_bytes(800, 600), "jpeg") == (800, 600)
    assert image_dimensions(webp_bytes(), "webp") == (None, None)
    assert image_dimensions(b"\xff\xd8\x00bad", "jpeg") == (None, None)
    # corrupt stream: a valid first segment followed by non-marker garbage
    corrupt = b"\xff\xd8" + b"\xff\xe0" + struct.pack(">H", 4) + b"\x00\x00" + b"garbage-not-a-marker"
    assert image_dimensions(corrupt, "jpeg") == (None, None)


# ── Honest degradation (never hallucinate) ────────────────────────────────────
def test_unsupported_format_is_unreadable_not_invented():
    res = analyze(img(b"not an image", "note.txt"), trace_id=TRACE, config=CFG)
    assert res.confidence == 0.0
    assert "unsupported_format" in res.warnings
    assert res.ocr_text == "" and res.objects == ()


def test_oversized_image_rejected_honestly():
    cfg = VisionConfig(max_image_bytes=10)
    res = analyze(img(png_bytes()), trace_id=TRACE, config=cfg)
    assert "image_too_large" in res.warnings
    assert res.confidence == 0.0


def test_null_backend_observes_nothing():
    res = analyze(img(png_bytes()), trace_id=TRACE, backend=NullPerceptionBackend(), config=CFG)
    assert res.ocr_text == ""  # unreadable stays unreadable
    assert "no_perception_available" in res.warnings
    assert res.confidence <= 0.1
    assert res.metadata["backend"] == "NullPerceptionBackend"


def test_backend_failure_degrades_never_crashes():
    res = analyze(img(png_bytes()), trace_id=TRACE, backend=BoomBackend(), config=CFG)
    assert any(w.startswith("backend_failed") for w in res.warnings)
    assert res.ocr_text == ""


def test_low_resolution_flagged():
    res = analyze(img(png_bytes(10, 10)), trace_id=TRACE, config=CFG)
    assert "low_resolution" in res.image_quality.flags


def test_webp_dimensions_unknown_flagged():
    res = analyze(img(webp_bytes(), "pic.webp"), trace_id=TRACE, config=CFG)
    assert "dimensions_unknown" in res.image_quality.flags


# ── Perception via backend ────────────────────────────────────────────────────
RICH = {
    "ocr_text": "Take one tablet daily\nASPIRIN 100mg",
    "detected_language": "en",
    "objects": [
        {"label": "medication", "confidence": 0.92, "box": [10, 10, 50, 80]},
        {"label": "bottle", "confidence": 0.8},
    ],
    "layout": [{"kind": "heading", "text": "ASPIRIN 100mg"}],
    "tables": [{"rows": 2}],
    "charts": [{"kind": "bar"}],
    "diagrams": [{"kind": "flow"}],
    "handwriting": {"present": True, "readability": 0.7, "text": "refill friday"},
    "document_type": "medication_label",
    "confidence": 0.9,
    "quality_flags": ["blurry"],
}


def test_rich_perception_structured():
    res = analyze(img(png_bytes()), trace_id=TRACE, backend=FakeBackend(RICH), config=CFG)
    assert "ASPIRIN 100mg" in res.ocr_text  # layout-preserving text
    assert res.detected_language == "en"
    assert res.objects[0].label == "medication" and res.objects[0].box == (10, 10, 50, 80)
    assert res.layout[0].kind == "heading"
    assert res.tables and res.charts and res.diagrams
    assert res.handwriting.present is True and res.handwriting.text == "refill friday"
    assert res.document_type == "medication_label"
    assert "blurry" in res.image_quality.flags
    assert res.confidence < 0.9  # quality reduces confidence


def test_medication_safety_label_only():
    res = analyze(img(png_bytes()), trace_id=TRACE, backend=FakeBackend(RICH), config=CFG)
    assert any("no medical advice" in w for w in res.warnings)
    # structured facts only — no advice, no diagnosis fields exist
    assert "advice" not in res.model_dump()


@pytest.mark.parametrize("doc", ["homework", "screenshot", "receipt", "chart", "form", "comic_page"])
def test_document_types_pass_through(doc):
    res = analyze(img(png_bytes()), trace_id=TRACE, backend=FakeBackend({"document_type": doc, "ocr_text": "x"}), config=CFG)
    assert res.document_type == doc
    assert doc in DOCUMENT_TYPES


# ── Feature toggles (nothing hardcoded) ───────────────────────────────────────
def test_ocr_disabled():
    cfg = VisionConfig(ocr_enabled=False)
    res = analyze(img(png_bytes()), trace_id=TRACE, backend=FakeBackend(RICH), config=cfg)
    assert res.ocr_text == "" and "ocr_disabled" in res.warnings


def test_toggles_disable_objects_charts_handwriting_language():
    cfg = VisionConfig(objects_enabled=False, charts_enabled=False, handwriting_enabled=False, language_detection_enabled=False)
    res = analyze(img(png_bytes()), trace_id=TRACE, backend=FakeBackend(RICH), config=cfg)
    assert res.objects == () and res.charts == ()
    assert res.handwriting.present is False
    assert res.detected_language is None


# ── Identity protection ───────────────────────────────────────────────────────
def test_identity_observations_stripped():
    raw = {
        "ocr_text": "hello",
        "objects": [
            {"label": "person", "confidence": 0.9},
            {"label": "face", "confidence": 0.9},
            {"label": "face_recognition", "confidence": 0.9},
            {"label": "age", "confidence": 0.9},
        ],
        "identity": "someone",
        "demographics": {"age": 30},
    }
    res = analyze(img(png_bytes()), trace_id=TRACE, backend=FakeBackend(raw), config=CFG)
    labels = [o.label for o in res.objects]
    assert labels == ["person"]  # generic object stays; identity never does
    assert any(w.startswith("identity_protection") for w in res.warnings)


def test_sanitize_identity_pure():
    cleaned, warnings = sanitize_identity({"race": "x", "objects": [{"label": "book"}]})
    assert "race" not in cleaned
    assert cleaned["objects"] == [{"label": "book"}]
    assert warnings and "identity_protection" in warnings[0]
    assert "race" in FORBIDDEN_OBSERVATIONS


# ── Contract + future architecture ────────────────────────────────────────────
def test_result_immutable_and_versioned():
    res = analyze(img(png_bytes()), trace_id=TRACE, config=CFG)
    assert res.schema_version == "1.0"
    assert res.trace_id == TRACE
    with pytest.raises(Exception):
        res.confidence = 1.0  # type: ignore[misc]


def test_invalid_input_raises():
    with pytest.raises(VisionError) as e:
        analyze("not an image", trace_id=TRACE, config=CFG)  # type: ignore[arg-type]
    assert e.value.code == "invalid_input"


def test_taxonomies_and_future_capabilities():
    assert "medication" in OBJECT_TAXONOMY and "plant" in OBJECT_TAXONOMY
    assert "barcode" in FUTURE_CAPABILITIES and "live_camera" in FUTURE_CAPABILITIES


# ── First multi-specialist flow: Vision → Core via the Orchestrator ───────────
def test_vision_to_core_orchestrated_flow():
    routing = RoutingPlan(
        request_id=uuid.uuid4(),
        primary_specialist="mini_core",
        primary_service="mini_core",
        secondary_specialists=("mini_vision",),
        fallback_specialist="mini_core",
        execution_order=("mini_vision", "mini_core"),
        reasoning="test", confidence=0.9,
    )
    executors = {
        "mini_vision": make_vision_executor(
            img(png_bytes()), backend=FakeBackend(RICH), config=CFG, trace_id=TRACE
        ),
        "mini_core": lambda task, inputs: {
            "reflection": f"I read the label: {inputs['mini_vision']['ocr_text'].splitlines()[-1]}"
        },
    }
    cfg = OrchestratorConfig(dependencies={"mini_core": ("mini_vision",)})
    res = orchestrate(routing, executors, trace_id=TRACE, config=cfg)
    assert res.status == OrchestrationStatus.COMPLETED
    assert res.merged_result["evidence"]["mini_vision"]["document_type"] == "medication_label"
    assert "ASPIRIN 100mg" in res.merged_result["primary"]["reflection"]
