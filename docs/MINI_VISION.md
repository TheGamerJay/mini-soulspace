# Mini Vision (Phase 4.3)

> **Status:** Implemented — the first specialist built for the Specialist Router
> and Specialist Orchestrator. **Mini Vision observes; it never concludes**
> (Constitution **Rule 25**). It never talks to the user, never generates final
> responses, never interprets intent, never bypasses the Orchestra. Source:
> `backend/app/orchestra/vision/`.

## Flow

```
User → Router → Orchestrator → Mini Vision → structured VisionResult →
next specialist (if needed) → Quality Checker → Conversation Composer
```

## Architecture

```
analyze(image, *, trace_id, backend=None, config=None) -> VisionResult
make_vision_executor(image, ...) -> Orchestrator executor
```

- The engine **validates and measures the actual image bytes** (magic-byte
  format detection for PNG/JPEG/WEBP; real PNG/JPEG header dimension parsing).
- Perception models are injectable **`VisionBackend`s** (like the sealed local
  runtime in the Mini Engine). The default `NullPerceptionBackend` observes
  nothing and invents nothing; a real vision model plugs in later by flipping
  the specialist card — no redesign.
- Backend output is **sanitized and structured** by the engine before anything
  leaves the node.

## VisionResult (v1.0, immutable)

`schema_version · vision_id · created_at · trace_id · image_metadata (filename,
content type, detected format, width/height, size) · image_quality (flags +
score) · detected_language · ocr_text · objects · layout · tables · charts ·
diagrams · handwriting (present/readability/text) · document_type · confidence ·
warnings · metadata`. **No user-facing language — structured facts only.**

## Image quality

Flags: `blurry · dark · low_resolution · rotated · partially_visible ·
overexposed · underexposed · unreadable · dimensions_unknown`. Deterministic
flags come from real header data (resolution limits, unknown dimensions);
perceptual flags come from the backend. Every flag reduces confidence by a
configurable penalty.

## OCR

Extracts text preserving layout (layout regions carry per-block text), detects
language (config-gated). **Never hallucinates missing words** — with no backend
the text is empty with a `no_perception_available` warning; unreadable remains
unreadable, honestly.

## Object detection

Taxonomy (future objects extend naturally): medication, bottle, book, computer,
phone, monitor, paper, graph, chart, table, receipt, homework, plant, animal,
food, vehicle, tool, person (generic only).

## Document understanding

`homework · medical_paper · medication_label · letter · invoice · receipt ·
form · business_card · pdf_image · notebook_page · journal_page · screenshot ·
chart · diagram · comic_page · map`. UI screenshots: desktop software, websites,
mobile apps, settings pages, error dialogs, dashboards, games, developer tools.

## Medication safety

Mini Vision **only reads the label** (OCR + `medication_label` document type)
and stamps the result with *"medication: label reading only — no medical
advice"*. Mini Research explains the medication later; Mini Core phrases it
naturally later. Mini Vision never provides medical advice or diagnoses.

## Identity protection

Mini Vision must never identify a person, recognize/compare faces, or infer
age, race, ethnicity, religion, political affiliation, sexuality, gender,
demographics, or medical conditions from appearance. The engine enforces this
structurally: `sanitize_identity` **strips any forbidden observation from any
backend output** (labels/keys matching the forbidden set or containing
"face"/"identity") and records an `identity_protection` warning. A generic
"person" object may remain; identity never does.

## Handwriting

Detected with presence, readability estimate, extracted text, and confidence —
config-gated.

## Configuration — `vision.json`

`ocr_enabled · objects_enabled · charts_enabled · handwriting_enabled ·
language_detection_enabled · max_image_bytes · min_width/min_height ·
allowed_formats · quality_penalty · future_models`. Nothing hardcoded.

## Future preparation (architecture only)

`barcode · qr_code · depth · segmentation · 3d · video · live_camera · ar ·
multi_image_comparison · image_similarity · image_search`.

## Activation

The registry card (`mini_vision`, v1.0) stays `unavailable` with health
`no_perception_backend` until a vision model deploys — then flipping the card
activates Router selection and orchestrated execution with zero code changes.
The **vision → core multi-specialist flow already runs end-to-end** through the
Specialist Orchestrator (integration-tested: Vision evidence feeds Mini Core's
reflection through the write-once workspace).

## Testing

`backend/tests/test_mini_vision.py` — **100% coverage** of
`app.orchestra.vision` (28 tests): config, format detection, PNG/JPEG/corrupt
dimension parsing, unsupported/oversized honest degradation, null backend
(no hallucination), backend failure, low-resolution + unknown-dimension flags,
rich perception structuring, medication safety, document types, feature
toggles, identity stripping (engine + pure), immutability, taxonomies/future
capabilities, invalid input, and the orchestrated Vision → Core flow.
