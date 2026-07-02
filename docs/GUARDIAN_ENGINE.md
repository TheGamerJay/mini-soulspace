# Guardian Engine (Orchestra Node 2)

> **Status:** Implemented (Phase 3.1). The protector of the User, the SoulDiary,
> the Soul Companion, and the Orchestra. It **classifies and protects only** —
> it never generates prose, never calls an LLM, never reflects, and never touches
> memory. Deterministic and rule-based. Source: `backend/app/orchestra/guardian/`.

## Responsibilities (single responsibility)

Evaluate the incoming immutable `OrchestraRequest` and produce one immutable
`GuardianResult` of **structured decisions** for the next node. Its four missions:

1. Protect the **User**.
2. Protect the **SoulDiary** experience.
3. Protect the **Soul Companion** identity.
4. Protect the **Orchestra**.

## Inputs / Outputs (API contract)

```
evaluate(request: OrchestraRequest) -> GuardianResult
```

- **Input:** the immutable `OrchestraRequest` (never modified).
- **Output:** an immutable `GuardianResult` (structured data only, never
  user-facing text). Malformed input raises a structured `GuardianError`
  (`{ field, code, message }`) — never an unstructured exception.

## GuardianResult schema (v1.0, immutable)

| Field | Meaning |
| --- | --- |
| `schema_version`, `result_id`, `created_at`, `request_id` | metadata + traceability link |
| `category` | one primary `GuardianCategory` |
| `emotional_tone` | one `EmotionalTone` (descriptive, never a diagnosis) |
| `allow_reflection` | may the diary talk back at all? |
| `allow_memory_storage` / `allow_memory_retrieval` | memory permissions |
| `allow_questions`, `max_questions` (0–2) | question policy (never > 2) |
| `reflection_depth` | `None` / `Light` / `Medium` / `Deep` (recommendation) |
| `allow_identity_override` / `allow_roleplay_override` | **permanently `false`** |
| `needs_human_referral` | encourage real-world/qualified help |
| `needs_crisis_template` | route to a deterministic safety response |
| `recommended_action` | `RecommendedAction` for the next node |
| `confidence` | 0.0–1.0 |
| `reason`, `signals` | structured reasoning (internal/debug only) |

## Classification system

Exactly one primary category, chosen in **safety-first priority order**:
`SELF_HARM_RISK → HARM_TO_OTHERS → EMERGENCY → HIGH_EMOTIONAL_DISTRESS →
MEDICAL_INFORMATION → LEGAL_INFORMATION → ACADEMIC_HELP → PROJECT_ASSISTANCE →
IMAGE_ANALYSIS → RESEARCH → EMOTIONAL_SUPPORT → LOW_CONCERN → SAFE`
(`UNKNOWN` reserved). The Guardian **classifies only — it never answers.**

## Emotional intensity

One descriptive `EmotionalTone`: Neutral, Positive, Reflective, Joyful, Hopeful,
Frustrated, Angry, Anxious, Sad, Grieving, Overwhelmed, **Mixed** (both positive
and negative present), **Uncertain** (empty/unreadable). Descriptive only —
never diagnostic.

## Protection rules

- **Identity:** `allow_identity_override` / `allow_roleplay_override` are
  **always false**. Detected identity/roleplay/safety-override attempts →
  `recommended_action = decline_override` and the attempt is not stored to memory.
- **SoulDiary / Safety:** crisis categories short-circuit reflection
  (`allow_reflection=false`, `reflection_depth=None`, `needs_crisis_template=true`,
  `needs_human_referral=true`) — **safety always wins**, even when an override
  attempt is also present.
- **Memory:** sensitive/crisis/override content is not eligible for long-term
  storage (`allow_memory_storage=false`); crisis also blocks retrieval.

## Decision model & flow

```
detect_signals(text)  →  classify_category  →  classify_tone
   → base policy per category
   → modifiers:  celebrate (positive) · listen-only (grieving)
                 · decline-override (injection) · safer-path (low confidence)
   → GuardianResult
```

**Guardian Principle:** *when uncertain, choose the safer path.* Low-confidence,
non-crisis results drop questions and cap reflection depth. Safety overrides
intelligence at every step.

## Error handling

Structured `GuardianError` only, and only for malformed **input** (e.g. a
non-request object). Ordinary uncertain content is never an error — it is
classified conservatively instead.

## Versioning & compatibility

`GuardianResult` is schema **v1.0**. Additions must be backwards compatible
(optional fields; bump minor). No AI-specific fields belong here.

## Testing

`backend/tests/test_guardian.py` — **100% coverage** of
`app.orchestra.guardian` (`pytest-cov`), fully **without the rest of the
Orchestra** (Constitution Rule 3): safe/happy/sad/grieving/angry/overwhelmed/
anxious/mixed entries, high distress, self-harm / harm-to-others / emergency
crises, crisis-beats-injection, medical/legal/academic/project/research/image
requests, identity/roleplay/safety override attempts, confidence bounds,
immutability, structured reasoning, empty-content edge, and failure cases.

## Constitution compliance

Single responsibility (classify/protect only), structured versioned I/O, model
agnostic (no LLM), never guesses (structured decisions/errors), safety before
intelligence, immutability, backward-compatible versioning, and the SoulDiary
stays the hero. See [Orchestra Engineering Rules](ORCHESTRA_ENGINEERING_RULES.md).

## Where it sits

Node **2 of 10** in the [Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md).
Consumes the [Input Receiver](INPUT_RECEIVER.md)'s `OrchestraRequest`; its
`GuardianResult` guides the Memory Retriever (node 3) and every node after.
