# Orchestra Nodes

> **Status:** Architecture only (Phase 2.75). No node is implemented. Each node
> below defines a permanent contract: **Purpose · Inputs · Outputs ·
> Responsibilities · Failure behavior · Future API contract.** Nodes are loosely
> coupled — a node never reaches into another node's internals; it only depends
> on the documented input/output shapes.

Pipeline order: Input Receiver → Safety Checker → Memory Retriever → Reflection
Planner → Context Builder → Prompt Builder → Response Generator → Quality Checker
→ Memory Writer → Final Responder.

---

## 1. Input Receiver

- **Purpose:** Assemble the raw request into a normalized envelope.
- **Inputs:** user, book, chapter, page, page content, time, timezone, metadata.
- **Outputs:** `OrchestraRequest` (normalized, validated).
- **Responsibilities:** validate ownership context; normalize timestamps to the
  user's timezone; attach request id; strip nothing meaningful.
- **Failure behavior:** reject malformed/unauthorized input before any model
  work; emit `RequestRejected`.
- **Contract:** `receive(raw) -> OrchestraRequest`.

## 2. Safety Checker

- **Purpose:** Decide whether this is safe journaling or a crisis.
- **Inputs:** `OrchestraRequest` (page text + recent context signals).
- **Outputs:** `SafetyVerdict { level: safe | crisis | escalate, category?, template? }`.
- **Responsibilities:** detect the triggers in [Safety Rules](SAFETY_RULES.md);
  on non-safe, select a deterministic response template and **short-circuit** the
  pipeline (skip reflection).
- **Failure behavior:** **fail safe** — if uncertain, treat as needing caution and
  prefer a supportive, resource-pointing response over deep reflection.
- **Contract:** `check(request) -> SafetyVerdict`.

## 3. Memory Retriever

- **Purpose:** Fetch only memories relevant to this page.
- **Inputs:** user id, page context, planner hints (optional).
- **Outputs:** `RetrievedMemories[]` with importance + relevance score.
- **Responsibilities:** strict per-user (and per-project) scoping; relevance
  filtering; **never** returns unrelated memories; honors deletions; never
  invents (see [Memory Rules](MEMORY_RULES.md), [Memory Integration](MEMORY_INTEGRATION.md)).
- **Failure behavior:** on store error, return empty set and continue (reflection
  degrades gracefully rather than fabricating).
- **Contract:** `retrieve(userId, context) -> RetrievedMemories[]`.

## 4. Reflection Planner

- **Purpose:** Decide *how* to respond before writing anything.
- **Inputs:** request, retrieved memories, safety verdict (safe).
- **Outputs:** `ReflectionPlan { intent, tone, depth, ask_question: bool, style }`.
- **Responsibilities:** choose intent (listen / comfort / celebrate / gently
  prompt); decide whether a question helps or whether silence/space is better;
  set depth (light vs deep); never plan diagnosis or advice-dumping.
- **Failure behavior:** default to the gentlest plan (listen, no question) if
  signals are ambiguous.
- **Contract:** `plan(request, memories) -> ReflectionPlan`.

## 5. Context Builder

- **Purpose:** Build the minimal, page-relevant context.
- **Inputs:** request, retrieved memories, reflection plan.
- **Outputs:** `BuiltContext` (only what's relevant to this page).
- **Responsibilities:** include only what earns its place; trim noise; respect
  token budgets; keep the page the center of gravity (see
  [Context Strategy](CONTEXT_STRATEGY.md)).
- **Failure behavior:** prefer less context over irrelevant context.
- **Contract:** `build(request, memories, plan) -> BuiltContext`.

## 6. Prompt Builder

- **Purpose:** Compose the final prompt from the 8 layers.
- **Inputs:** identity/safety/reflection rules (static), built context, plan.
- **Outputs:** `ComposedPrompt`.
- **Responsibilities:** assemble Identity → Safety → User → Memory → Page →
  Reflection Instruction → Style → Formatting (see
  [AI Prompt Architecture](AI_PROMPT_ARCHITECTURE.md)); enforce precedence.
- **Failure behavior:** if a required layer is missing, abort rather than emit an
  unsafe/identity-less prompt.
- **Contract:** `compose(context, plan) -> ComposedPrompt`.

## 7. Response Generator

- **Purpose:** Produce a candidate reflection via the selected model.
- **Inputs:** `ComposedPrompt`, model role (default Main Reflection).
- **Outputs:** `CandidateReflection` (raw text).
- **Responsibilities:** call the role-addressed model (Ollama); enforce
  generation limits; remain model-agnostic.
- **Failure behavior:** on model error/timeout, retry once, then fall back to the
  Fast model or a graceful "saved, no reflection this time" state — never a fake
  reflection.
- **Contract:** `generate(prompt, role) -> CandidateReflection`.

## 8. Quality Checker

- **Purpose:** Gate the candidate before the user ever sees it.
- **Inputs:** `CandidateReflection`, request, retrieved memories, plan.
- **Outputs:** `QualityResult { pass: bool, reasons[], revised? }`.
- **Responsibilities:** verify no hallucinations, no invented memories, no unsafe
  advice, no therapy claims / diagnosis, no fake certainty, no robotic
  repetition, natural language, on-guide (see [Quality Guardrails](QUALITY_GUARDRAILS.md)).
- **Failure behavior:** on fail, request one revision; if still failing, degrade
  to a minimal safe acknowledgment rather than shipping a bad reflection.
- **Contract:** `verify(candidate, context) -> QualityResult`.

## 9. Memory Writer

- **Purpose:** Decide what (if anything) to remember.
- **Inputs:** request, final reflection, existing memories.
- **Outputs:** `MemoryWrite[]` (new/updated memories with importance + relations).
- **Responsibilities:** assign importance (Low/Medium/High/Critical); link
  related memories; never store manipulatively; handle conflicts/updates per
  [Memory Integration](MEMORY_INTEGRATION.md); often the right answer is "store
  nothing."
- **Failure behavior:** on store error, log and continue; never block the
  reflection from returning.
- **Contract:** `maybeWrite(request, reflection) -> MemoryWrite[]`.

## 10. Final Responder

- **Purpose:** Return the finished reflection to the SoulDiary.
- **Inputs:** approved reflection (or safety template), metadata.
- **Outputs:** `ReflectionResponse` shown beneath the user's writing.
- **Responsibilities:** attach timestamps; emit `ReflectionGenerated`; keep the
  page/writing primary.
- **Failure behavior:** always returns *something* honest — a reflection, a safety
  response, or a graceful "no reflection right now."
- **Contract:** `respond(result) -> ReflectionResponse`.

---

## Coupling rules
- A node depends only on the **shapes** in [Future API Contracts](FUTURE_API_CONTRACTS.md).
- Safety and Identity constraints are non-overridable by later nodes.
- Future models plug into nodes 3/4/6/7/8/9 by **role**, with no Orchestra
  redesign.
