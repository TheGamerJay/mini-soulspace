# Conversation Composer (Orchestra Node 10 — the Frontend Gateway)

> **Status:** Implemented (Phase 3.9). The tenth and **final** Orchestra node —
> formerly planned as "Final Responder", renamed the **Conversation Composer**.
> It is the **ONLY** node permitted to communicate with the frontend
> (Constitution **Rule 20**). Assemble-only — **no AI, no generation, no
> modification.** Source: `backend/app/orchestra/composer/`.
>
> This completes the first fully operational Orchestra: all 10 nodes exist.

## Purpose (single responsibility)

Assemble the final user experience from approved Orchestra results. It never
generates AI responses, touches memory, plans, or re-judges safety/quality — and
it never modifies previous Orchestra results.

## Inputs / Outputs (API contract)

```
compose(request, quality, candidate=None, *,
        memory_decision=None, memory_intelligence=None) -> ConversationPackage
```

- **Inputs:** the `OrchestraRequest` and `QualityResult` (required); the
  `CandidateResponse` (required for approved delivery); optional
  `MemoryDecision` + `MemoryIntelligenceResult` for memory packaging. Upstream
  results (Meaning/Guardian/Retrieval/Planner/Context/Prompt) inform earlier
  nodes; the Composer consumes their downstream products. Nothing is modified.
- **Output:** an immutable `ConversationPackage` — the only payload the frontend
  ever receives. Structurally invalid input raises a structured `ComposerError`.

## ConversationPackage (v1.0, immutable)

`schema_version · package_id · created_at · request_id · status · text ·
attachments · actions · memory_updates · notifications · citations · sources ·
frontend_events · metadata`.

## Delivery rules

- **Only approved** `QualityResult`s are delivered. The Quality Checker is never
  bypassed.
- **Text is exact**: `CandidateResponse.response_text` verbatim — never
  rewritten, paraphrased, regenerated, or modified.
- **Rejected / needs_retry →** a structured **failure package**:
  `status = not_delivered`, empty text, a `ConversationNotDelivered` event, and
  internal metadata (failure reason, violation codes, retry_allowed). An unsafe
  response never reaches the frontend.

## Memory packaging

When the Memory Writer stored/updated something, the package carries structured
`MemoryUpdate` entries (op, type, importance, title, confidence, verification
status — confidence from the Intelligence Engine when available) and emits
`MemoryStored` / `MemoryUpdated` events. **Memory notifications** ("I'll remember
that.", "Your birthday has been saved.") are **prepared** as templates — not
displayed yet.

## Prepared architecture (not implemented)

- **Attachments:** image, generated_image, document, pdf, audio, voice, video,
  research_report, code_file, model_3d.
- **Actions:** open_souldiary, open_project, create_reminder, generate_image,
  start_voice_chat, view_memory, view_timeline.
- **Notifications:** birthday, milestone, memory_updated, goal_achieved,
  project_progress, streak, anniversary, reminder.
- **Citations:** research / document / memory / knowledge references.

All are typed schemas shipped as empty tuples today — future specialists fill
them without redesign.

## Frontend events

Structured `FrontendEvent {name, payload}`. Known names:
`ConversationDelivered · ConversationNotDelivered · MemoryStored · MemoryUpdated ·
BirthdayDetected · MilestoneReached · AttachmentReady · ImageGenerated ·
ResearchCompleted · VoiceReady` — future events extend naturally.

## Frontend ownership

Every previous node communicates only with the Orchestra. **All** user-facing
communication passes through the Composer. No exceptions (Rule 20).

## Testing

`backend/tests/test_conversation_composer.py` — **100% coverage** of
`app.orchestra.composer`: exact-text approved delivery, empty placeholders,
memory create/update packaging (+ intelligence fallback), no-store packaging,
rejected + needs_retry failure packages (with violation codes), failure without
candidate, immutability + versioning, prepared event names + notification
templates, and structured errors (invalid request/quality, approved-without-
candidate).

## Where it sits

Node **10 of 10** — the end of the pipeline in the
[Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md):
`… → Quality Checker → Memory Writer → Conversation Composer → frontend`.
Governed by the [Orchestra Constitution](ORCHESTRA_ENGINEERING_RULES.md)
(esp. Rules 17 and 20). Next: **Phase 4.0 — Orchestra Integration & Validation**
wires all ten nodes into one flow.
