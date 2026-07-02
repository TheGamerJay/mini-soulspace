# Soul Intelligence Architecture

> **Status:** Architecture only (Phase 2.75). This phase does **not** build AI. It
> designs the permanent reasoning pipeline every future model must follow. No
> runtime code, no Ollama calls, no orchestration engine exist yet.

## The core idea

**The LLM is not the brain. The Orchestra is the brain.** The language model is
one specialist inside a larger reasoning pipeline. Models will change over time;
the Soul Companion — its behavior, judgment, and values — must not.

### Philosophy
- Think before speaking. Inspect before responding.
- Remember only what matters.
- Never guess. Never hallucinate. Never fake memories. Never pretend.
- Quality over speed, always.
- **The SoulDiary is always the hero. The AI is never the hero** — it quietly
  enriches the writing experience.

## What the Orchestra transforms

```
User writing  →  Thought process  →  Meaningful reflection
```

The "thought process" is the Orchestra: an ordered pipeline of loosely-coupled
**nodes**, each a specialist that does one job and hands off a clean result.

## The pipeline (permanent order)

```
1  Input Receiver      →  gather user / book / chapter / page / time / metadata
2  Safety Checker      →  safe? crisis? escalate?           (can short-circuit)
3  Memory Retriever    →  relevant memories only
4  Reflection Planner  →  intent, tone, depth, question-or-not, style
5  Context Builder     →  minimal, page-relevant context
6  Prompt Builder      →  compose the 8 prompt layers
7  Response Generator  →  call the selected LLM
8  Quality Checker     →  safety, no hallucination/fake memory, natural, on-guide
9  Memory Writer       →  should anything be remembered? at what importance?
10 Final Responder     →  return the final reflection
```

The **Safety Checker** may short-circuit the whole pipeline to a safe response
(see [Safety Rules](SAFETY_RULES.md)); safety always wins.

## Design principles

- **Loose coupling.** No node knows another node's internals — only its
  input/output contract (see [Future API Contracts](FUTURE_API_CONTRACTS.md)).
- **Replaceable models.** Any node that calls a model can swap models without
  changing the Orchestra (see the model roles below).
- **Deterministic where it matters.** Safety responses and quality gates are
  rule-driven, not left to free generation.
- **Everything auditable.** Each step emits events (see
  [Orchestration Events](ORCHESTRATION_EVENTS.md)).

## Model strategy (roles, not identities)

| Role | Current model | Notes |
| --- | --- | --- |
| Main Reflection | `qwen3:14b` | primary reflections & reasoning |
| Fast Tasks | `llama3.1:8b` | low-latency, lightweight steps |
| Summary / Tags | `gemma3:4b` | memory summaries, tagging |
| Coding | `qwen2.5-coder:14b` | structured/code generation |

Models are addressed by **role**, never hard-coded, so future models replace them
without redesigning the Orchestra. Matches `ai/configs/models.json` and the
`MAIN/FAST/TAG/CODER` settings from Phase 0.

## Related documents
- [Orchestra Nodes](ORCHESTRA_NODES.md) — every node in detail.
- [Conversation Flow](CONVERSATION_FLOW.md) — flows + book open/close experience.
- [Context Strategy](CONTEXT_STRATEGY.md) · [Quality Guardrails](QUALITY_GUARDRAILS.md).
- [Memory Integration](MEMORY_INTEGRATION.md) · [Orchestration Events](ORCHESTRATION_EVENTS.md).
- [Future API Contracts](FUTURE_API_CONTRACTS.md) · [Phase 2.75 Summary](PHASE_2_75_SUMMARY.md).
- Behavior rules: [Soul Companion Guide](SOUL_COMPANION_GUIDE.md),
  [Reflection Rules](REFLECTION_RULES.md), [Memory Rules](MEMORY_RULES.md),
  [Safety Rules](SAFETY_RULES.md), [AI Prompt Architecture](AI_PROMPT_ARCHITECTURE.md).
