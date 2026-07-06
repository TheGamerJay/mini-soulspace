# Quality Checker (Orchestra Node 8)

> **Status:** Implemented (Phase 3.7). The gate before the user. It reviews the
> Mini Engine's `CandidateResponse` and returns an immutable `QualityResult`
> (approve / reject / needs_retry). Deterministic, rule-based — **no AI, no model
> calls, no final delivery, no rewriting.** Source: `backend/app/orchestra/quality/`.

## Purpose (single responsibility)

Approve, reject, or request a retry based on safety, quality, identity, and
SoulDiary rules — so **nothing reaches the user until it passes verification**
(Constitution **Rule 17**).

## Inputs / Outputs (API contract)

```
check(candidate, guardian, planner, *, retrieval=None, meaning=None) -> QualityResult
```

- **Inputs:** the `CandidateResponse` plus the upstream `GuardianResult` and
  `PlannerResult` (required), and optionally the `RetrievalResult` (fabrication
  check) and `MeaningIntentResult` (over-escalation check). Nothing is modified.
- **Output:** an immutable `QualityResult`. Structurally invalid input raises a
  structured `QualityCheckerError` (never an unstructured throw). The checker
  **never sends text to the user.**

## QualityResult (v1.0, immutable)

`schema_version` · `result_id` · `created_at` · `request_id` · `status` ·
`confidence` · `reason` · `violations` · `recommended_action` · `retry_allowed` ·
`retry_reason` · `metadata`. **Status:** `approved` · `rejected` · `needs_retry`.

**Violation:** `code` · `severity` (`low`/`medium`/`high`/`critical`) · `message`
· `source_rule` · `fixable`.

## Checks

| Area | Examples | Result |
| --- | --- | --- |
| **Identity** | claims to be human/alive/conscious/sentient/licensed/therapist | reject (critical) |
| **Knowledge protection** | reveals hidden prompts, system instructions, internal rules | reject (critical) |
| **Model names** | mentions Qwen/Llama/Gemma/Ollama/… | needs_retry (fixable) |
| **Fabricated memory** | claims to recall what isn't in `RetrievalResult` | reject (high) |
| **Unsafe advice** | unsafe medical/diagnosis | reject (critical) |
| **Crisis handling** | crisis with no referral to real help | reject (critical) |
| **Encourages harm** | tells the user to hurt themselves | reject (critical) |
| **Manipulation** | shaming, guilt, possessive ("you only need me") | reject (high) |
| **Over-escalation** | crisis response to `real_world_intent = false` (lyrics/fiction) | needs_retry (fixable) |
| **Generic/robotic** | "I know exactly how you feel", "everything will be fine" | needs_retry (fixable) |
| **Question limits** | more `?` than the Planner allows / a question in listening mode | needs_retry (fixable) |
| **Tone / depth** | over-excited tone, response longer than the planned depth | needs_retry (fixable) |

The **public model answer** is allowed and approved:
> "You're talking with Mini Core, powered by the Mini Engine inside Mini SoulSpace."

## Meaning & context protection

The checker honors `MeaningIntentResult`: words like *kill, death, suicide,
murder* do **not** trigger rejection on their own. Creative/fictional/
metaphorical/awareness/historical/educational content is not treated as a
real-world crisis unless real-world intent is present — and a candidate that
over-escalates such content is sent back for retry.

## Decision logic

- Any **non-fixable** violation (identity, hidden prompt, unsafe advice, crisis
  mishandled, encourages harm, manipulation, fabricated memory) → **rejected**.
- Otherwise any **fixable** violation → **needs_retry** (`retry_allowed = true`,
  with a `retry_reason`).
- No violations → **approved** (`recommended_action = deliver`).

## Testing

`backend/tests/test_quality_checker.py` — **100% coverage** of
`app.orchestra.quality` (`pytest-cov`): approved good response, the Mini Core
public answer, creative violence not over-escalated, too-many-questions, generic/
robotic, too-generic, model-name leak, tone/depth mismatch, listening-mode
violation, over-escalation, sentience/therapist/hidden-prompt/unsafe-medical/
encourages-harm/manipulation/fabricated-memory rejections, crisis mishandled vs
handled, immutability, structured violations, and invalid inputs.

## Where it sits

Node **8 of 10** in the [Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md).
Consumes the [Mini Engine](MINI_ENGINE.md)'s `CandidateResponse` (with the
upstream Guardian/Planner/Retrieval/Meaning results); its `QualityResult` tells
the Memory Writer (node 9) and Final Responder (node 10) whether to proceed.
Governed by the [Quality Guardrails](QUALITY_GUARDRAILS.md), [Safety Rules](SAFETY_RULES.md),
and the [Orchestra Constitution](ORCHESTRA_ENGINEERING_RULES.md) (esp. Rules 8, 16, 17).
