# Orchestra Engineering Rules — Permanent Constitution

> **Status:** Permanent. This document is the engineering constitution of the
> Mini SoulSpace Orchestra. **Every future Orchestra node must obey these rules.**
> They **override implementation preferences.** If a future design violates one
> of these rules, the design must be revised **before** implementation.
>
> Every future phase should reference and follow this document.

---

## Rule 1 — Single Responsibility

Every Orchestra node has **exactly one** responsibility. If a node begins
performing another node's responsibility, it must be **split**. No "God Nodes."

## Rule 2 — Structured Input / Output

Every node **receives structured input** and **produces structured output**.
Never pass raw text between nodes unless explicitly required. Prefer **versioned
schemas** (e.g. `OrchestraRequest` schema v1.0).

## Rule 3 — Independent Testability

Every node must be **independently testable**, with:

- Unit tests
- Success cases
- Failure cases
- Edge cases

No node should require the full Orchestra to be tested.

## Rule 4 — No Bypassing

No node may **bypass** another node unless explicitly **documented and
approved**. The pipeline must remain **predictable and traceable**.

## Rule 5 — Model Agnostic

The **LLM is never the Orchestra** — it is one interchangeable specialist inside
it. Models may change; the Orchestra must not. Replacing Qwen (or any model) must
**not** require redesigning the Orchestra. Address models by **role**
(`main`/`fast`/`tag`/`coder`), never hard-code.

## Rule 6 — Inspect Before Acting

Before modifying existing code: **inspect** the current implementation,
**understand** dependencies, **analyze** impact, and **modify only what is
necessary.** Never edit blindly.

## Rule 7 — Never Guess

When information is missing: **do not invent, do not assume, do not
hallucinate.** Return **structured uncertainty** when necessary.

## Rule 8 — Safety Before Intelligence

**Safety always has authority** over every node. If Safety blocks a response, the
remaining pipeline must respect that decision. **No node may override Safety.**

## Rule 9 — User Control

The user **owns** their SoulDiary and their memories, and controls **deletion**
and **exports**. The Orchestra exists to **assist — not to control.**

## Rule 10 — The SoulDiary Is the Hero

Mini SoulSpace is not a chatbot and not an AI assistant — it is a **living
personal SoulDiary.**

> **Writing comes first. Reflection comes second. AI comes third.**

Every future feature must **strengthen** the SoulDiary experience rather than
distract from it.

## Rule 11 — Backward Compatibility

New nodes should **extend** the architecture without breaking existing nodes
whenever reasonably possible. Use **schema versioning** for long-term
compatibility (additive, optional fields; bump the minor version).

## Rule 12 — Quality Over Speed

The Orchestra always prioritizes **correctness, safety, consistency,
maintainability, and user trust** over speed of implementation.

## Rule 13 — Minimum Sufficient Context

Every Orchestra node should pass **only the minimum information required for the
next node to succeed.** **Quality always beats quantity.** Trim the irrelevant,
deduplicate facts, stay within budget, and record what was excluded (never
silently discard).

> Added in Phase 3.4 (the Phase 3.4 brief calls this "Rule #16"; it is the 13th
> rule and numbered sequentially to keep the constitution gap-free).

## Rule 14 — Separation of Structure, Intelligence, and Language

**Prompt templates define structure. The Orchestra provides intelligence. The
LLM provides language generation. These responsibilities must never be mixed.**

Templates never make decisions; the Orchestra nodes never format prose; the model
never sets policy. Each stays in its lane.

> Added in Phase 3.5 (matches the brief's "Rule #14").

## Rule 15 — Language Generation Makes No Decisions

**Language generation must never make architectural decisions.**

- The **Orchestra** provides intelligence.
- The **Mini Engine** provides runtime access.
- **Local models** provide language generation.

The Orchestra addresses **Mini Services** by name; the runtime (and which model
backs a service) is an internal detail of the Mini Engine that no other node may
see or depend on.

> Added in Phase 3.6 (matches the brief's "Rule #15").

## Rule 16 — Understand Meaning Before Judging

**The Orchestra must understand meaning before making safety decisions.**

> Meaning precedes context. Context precedes intent. Intent precedes
> classification. Classification precedes response.

The Orchestra must **never** classify users based solely on isolated words,
titles, or phrases. Ambiguity is reported honestly (`unclear`) and treated with
caution — never resolved by guessing.

> Added in Phase 3.65 (matches the brief's "Rule #16").

## Rule 17 — Nothing Reaches the User Unverified

**No response reaches the user until it passes quality verification.**

- The **Mini Engine** generates candidates.
- The **Quality Checker** decides whether they are safe and aligned.
- The **Final Responder** delivers only approved responses.

> Added in Phase 3.7 (matches the brief's "Rule #17").

## Rule 18 — Memory Is Earned

**Mini remembers only information that provides long-term value.**

- When uncertain, Mini chooses **not** to remember.
- Quality of memory is more important than quantity.

Nothing is fabricated, inferred, exaggerated, or duplicated; only facts supported
by the conversation are stored, and evolving facts update rather than clutter.

> Added in Phase 3.8 (matches the brief's "Rule #18").

## Rule 19 — Every Memory Must Be Explainable

Every stored memory must include:

- **Confidence**
- **Evidence**
- **Source**
- **Provenance** (created / updated / verified / version / author)

**If Mini cannot explain why a memory exists, that memory should not exist.**

The **user is the final authority** over every memory. User corrections
permanently replace outdated information and prevent the same incorrect memory
from repeatedly resurfacing.

> Added in Phase 3.8.5 (matches the brief's "Rule #19").

---

## How these rules are applied today

- **Phase 3.0 — Input Receiver** already embodies them: single responsibility
  (packaging only), structured versioned output (`OrchestraRequest` v1.0, Rule
  2/11), independently unit-tested at 100% coverage (Rule 3), never guesses —
  returns structured `InputValidationError` (Rule 7), reuses existing services
  after inspection (Rule 6), and adds no model logic (Rule 5).
- Safety (Rule 8) is reserved as node 2 with short-circuit authority over the
  whole pipeline (see [Orchestra Nodes](ORCHESTRA_NODES.md)).

## Related documents
- [Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md) — the pipeline.
- [Orchestra Nodes](ORCHESTRA_NODES.md) · [Future API Contracts](FUTURE_API_CONTRACTS.md).
- [Quality Guardrails](QUALITY_GUARDRAILS.md) · [Safety Rules](SAFETY_RULES.md) ·
  [Memory Rules](MEMORY_RULES.md) · [Soul Companion Guide](SOUL_COMPANION_GUIDE.md).
