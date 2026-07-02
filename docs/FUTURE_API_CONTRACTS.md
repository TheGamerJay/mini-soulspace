# Future API Contracts

> **Status:** Architecture only (Phase 2.75). Describes the **interfaces between
> Orchestra nodes** — expected inputs and outputs — so future developers know
> exactly how nodes communicate. These are language-agnostic shapes, **not
> implementations**. Field names are illustrative and will be finalized in the
> implementation phase.

## Shared shapes

```
OrchestraRequest {
  request_id
  user: { id, display_name, timezone, preferred_language, locale }
  location: { book_id, chapter_id, page_id }
  page: { title, content, content_format, word_count, character_count }
  time: { now, timezone }
  metadata: { session_id, occasion_hints? }
}

SafetyVerdict {
  level: "safe" | "crisis" | "escalate"
  category?            // e.g. self_harm, abuse, medical
  template?           // deterministic response id when not safe
}

RetrievedMemory {
  id, summary, importance: "low"|"medium"|"high"|"critical",
  relevance_score, related_ids[]
}

ReflectionPlan {
  intent: "listen"|"comfort"|"celebrate"|"prompt"|"acknowledge"
  tone, depth: "light"|"moderate"|"deep"
  ask_question: boolean
  style
}

BuiltContext { page, surrounding?, memories: RetrievedMemory[], user, occasion? }
ComposedPrompt { layers[], model_role }
CandidateReflection { text, model_role }
QualityResult { pass: boolean, reasons[], revised_text? }
MemoryWrite { summary, importance, related_ids[], op: "create"|"update" }
ReflectionResponse { text?, kind: "reflection"|"safety"|"none", created_at }
```

## Node contracts

| Node | Signature |
| --- | --- |
| 1 Input Receiver | `receive(raw) -> OrchestraRequest` |
| 2 Safety Checker | `check(OrchestraRequest) -> SafetyVerdict` |
| 3 Memory Retriever | `retrieve(user_id, context) -> RetrievedMemory[]` |
| 4 Reflection Planner | `plan(OrchestraRequest, RetrievedMemory[]) -> ReflectionPlan` |
| 5 Context Builder | `build(OrchestraRequest, RetrievedMemory[], ReflectionPlan) -> BuiltContext` |
| 6 Prompt Builder | `compose(BuiltContext, ReflectionPlan) -> ComposedPrompt` |
| 7 Response Generator | `generate(ComposedPrompt, role) -> CandidateReflection` |
| 8 Quality Checker | `verify(CandidateReflection, BuiltContext) -> QualityResult` |
| 9 Memory Writer | `maybeWrite(OrchestraRequest, ReflectionResponse) -> MemoryWrite[]` |
| 10 Final Responder | `respond(QualityResult | SafetyVerdict) -> ReflectionResponse` |

## Contract rules

- **Loose coupling:** a node consumes/produces only the shapes above; it never
  reaches into another node's internals or state.
- **Safety short-circuit:** if node 2 returns non-`safe`, the orchestrator jumps
  to node 10 with the safety template; nodes 3–9 are skipped.
- **Model-agnostic:** nodes 3/4/6/7/8/9 address models by **role**
  (`main`/`fast`/`tag`/`coder`), so models are replaceable without contract
  changes.
- **Graceful degradation:** every node has a defined failure output (see
  [Orchestra Nodes](ORCHESTRA_NODES.md)); the pipeline always yields an honest
  `ReflectionResponse` (`reflection`, `safety`, or `none`) — never a fabricated one.
- **Transport-neutral:** contracts describe shapes, not HTTP/queue mechanics; a
  future implementation may run in-process or across services without changing
  them.
