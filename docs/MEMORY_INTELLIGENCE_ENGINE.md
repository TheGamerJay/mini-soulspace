# Memory Intelligence Engine (Phase 3.8.5)

> **Status:** Implemented. Manages memory **quality over time** — it does NOT
> decide what memories should exist (that is the [Memory Writer](MEMORY_WRITER.md)'s
> job). Deterministic, rule-based — **no AI**, no retrieval, no generation, no
> delivery. Source: `backend/app/orchestra/intelligence/`.

## Purpose (single responsibility)

Ensure every stored memory remains **accurate, trustworthy, explainable,
verifiable, and capable of evolving**. Mini becomes more reliable the longer
someone uses it (Constitution **Rule 19**: if Mini cannot explain why a memory
exists, that memory should not exist).

## Inputs / Outputs

Consumes a `MemoryDecision` + existing memory records. Produces an immutable
**`MemoryIntelligenceResult`** (v1.0): `schema_version · result_id · created_at ·
memory_id · confidence · confidence_reason · memory_source · evidence ·
verification_status · last_verified_at · last_updated_at · previous_version ·
next_action · metadata`.

## Confidence system

Deterministic, evidence-backed — **never guessed** (the reason names the tier):

| Evidence | Confidence |
| --- | --- |
| Entered during signup / manual user entry | **1.00** (verified) |
| Explicit statement ("My favorite color is blue.") | **0.99** |
| Strong implication ("I usually like blue.") | **0.80** |
| Casual mention ("Blue looks nice.") | **0.40** |
| Unclassified statement strength | 0.60 |

## Configurable thresholds — `memory_intelligence.json`

Bundled at `backend/app/orchestra/intelligence/memory_intelligence.json`.
**No thresholds are hardcoded**: `auto_store_threshold` (0.90),
`needs_verification_threshold` (0.70), `low_confidence_threshold` (0.50),
`minimum_confidence`, `confidence_decay_enabled`, `verification_enabled`,
`decay_per_day`, correction-pattern settings, and **`type_overrides`** —
per-memory-type thresholds, future-ready.

## Memory sources

`signup_form · souldiary · conversation · voice_conversation · image_analysis ·
document_analysis · calendar · manual_user_entry · imported_data ·
system_generated` — every memory records where it came from; new sources extend
the enum naturally.

## Evidence

Every memory stores an evidence blob (page id / signup field / conversation id /
timestamp / reason stored). **No memory exists without evidence** — `assess` and
`apply_correction` raise a structured `MemoryIntelligenceError` on empty evidence.

## Version history

`soul_memory_versions` (migration 0004): every change writes an immutable row —
version, previous title/summary/confidence, `reason_changed`, `author`
(user/system), `is_outdated`, timestamp. **History is never lost.**

## Evolution & conflict resolution

When a memory evolves or conflicts (favorite food pizza → sushi): the existing
memory is **updated in place**, the previous value is **archived as an outdated
version** with the reason recorded, and no conflicting active memories remain.

## Confidence decay

`apply_decay` slowly lowers confidence with age (configurable rate, floored at
`minimum_confidence`; can be disabled). **The memory itself is never deleted —
only confidence changes.** Dropping below the verification threshold marks it
`needs_verification`.

## Memory verification (prepared)

`needs_verification(memory)` flags candidates; a future phase asks naturally —
*"I remember you used to enjoy painting. Is that still something you enjoy?"* —
never interrogating, never repeatedly asking.

## User correction learning

The user is the **final authority**. `apply_correction`:
1. archives the old value as an **outdated** version (author = `user`),
2. updates the memory in place (version + 1),
3. **raises confidence to 0.99** (explicit correction) and marks it verified,
4. records correction evidence,
5. `would_resurface(versions, candidate)` prevents the corrected-away value from
   ever coming back. Never argues; never requires repeat corrections.

## Correction pattern learning

`required_confidence(memory_type, corrections_by_type, config)`: types the user
frequently corrects require **stronger evidence** before storing (threshold +
penalty per correction past the pattern threshold, capped at 0.99). Uses explicit
correction history + configurable thresholds only — **no model retraining, no
hidden prompt changes.**

## Provenance

Every memory permanently tracks: created/updated/verified timestamps, confidence,
evidence, source, version, author — the full explainability contract of Rule 19.

## Future analytics (prepared, not implemented)

`ANALYTICS_EVENTS`: MemoryCreated, MemoryUpdated, UserCorrectionApplied,
DuplicateMemoryPrevented, ConfidenceAdjusted, VerificationScheduled,
VerificationSucceeded.

## Testing

`backend/tests/test_memory_intelligence.py` — **100% coverage** of
`app.orchestra.intelligence`: config loading + missing config, all confidence
tiers, assess (stamping, provenance, history, signup-verified, update op,
casual→monitor, unclassified→schedule-verification, verification-disabled,
missing evidence, invalid inputs), decay (applies/disabled/floor/naive-datetime),
verification threshold, corrections (archive + raise confidence + evidence +
version history + resurface prevention + repeat corrections), pattern learning
(+ type overrides + counts by type), immutability, analytics prep.

## Where it sits

A memory-quality layer alongside node 9: the [Memory Writer](MEMORY_WRITER.md)
decides *what* exists; the Intelligence Engine keeps it *trustworthy*. The
[Memory Retriever](MEMORY_RETRIEVER.md) reads the same store. Governed by the
[Memory Rules](MEMORY_RULES.md) and the
[Orchestra Constitution](ORCHESTRA_ENGINEERING_RULES.md) (esp. Rules 9, 18, 19).
