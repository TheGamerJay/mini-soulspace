# Quality Guardrails

> **Status:** Architecture only (Phase 2.75). Defines what the Quality Checker
> (node 8) verifies before any reflection reaches the user. Not implemented.

The Quality Checker is the last gate between a generated candidate and the
writer. Nothing ships unless it passes. When in doubt, it degrades to a smaller,
safe response rather than shipping a flawed one.

## Checks (all must pass)

| Check | Fails if the candidate… |
| --- | --- |
| **No hallucinations** | asserts facts not present in context |
| **No invented memories** | claims to remember anything not in the memory set |
| **No unsafe advice** | suggests unsafe actions or harmful steps |
| **No therapy claims** | positions itself as therapy/counseling |
| **No diagnosis** | labels the user with a condition |
| **No fake certainty** | claims to *know* how the user feels, or the future |
| **No robotic repetition** | reuses stock phrases / repeats prior reflections |
| **Natural language** | sounds templated, clinical, or performative |
| **On-guide** | violates the [Soul Companion Guide](SOUL_COMPANION_GUIDE.md) or [Reflection Rules](REFLECTION_RULES.md) |

## Safety re-verification

Even though the Safety Checker (node 2) ran first, the Quality Checker
**re-confirms** the candidate contains no unsafe content and respects the
non-professional boundary. Safety is checked at both ends of the pipeline.

## Failure handling

1. **First failure →** request a single targeted revision (regenerate with the
   specific reasons).
2. **Still failing →** degrade to a minimal, honest acknowledgment (e.g., a warm
   "thank you for writing this" without risky content) — never ship the flawed
   candidate.
3. Emit the outcome as an event for auditing (see
   [Orchestration Events](ORCHESTRATION_EVENTS.md)).

## Non-negotiables
- The writing experience is never blocked by a failed reflection — the page is
  already saved; a missing/degraded reflection is acceptable, a bad one is not.
- Guardrails are rule-driven and model-agnostic, so swapping models cannot
  silently lower quality standards.
