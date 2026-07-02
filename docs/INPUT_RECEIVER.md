# Input Receiver (Orchestra Node 1)

> **Status:** Implemented (Phase 3.0). The first working Orchestra node. It does
> **no** AI, memory, safety, prompt, or model work — it only collects,
> validates, and packages application state into an immutable `OrchestraRequest`.
> Source: `backend/app/orchestra/`.

## Purpose

Be the eyes and ears of the Soul Companion. Convert raw application data into one
structured, immutable, versioned `OrchestraRequest` that every downstream node
will consume. **Single responsibility** — nothing else.

## Responsibilities

- Gather facts about the authenticated user, SoulBook, chapter, page, content,
  statistics, timestamps, language, timezone and session.
- Validate that everything exists, is owned by the user, and is internally
  consistent.
- Package it into an immutable `OrchestraRequest`.
- **Never** modify source data; **never** generate, retrieve, reflect, or call a
  model.

It reuses the Phase 2 `soulbook_service` for ownership-scoped reads and its
`count_words` / `count_characters` helpers — no data access is duplicated.

## Inputs (API contract)

```
build_orchestra_request(
  db, user, book_id, chapter_id, page_id,
  *, session_id=None, metadata=None
) -> OrchestraRequest
```

- **Application state:** a DB session, the authenticated `User`, and the target
  `book_id` / `chapter_id` / `page_id`.
- Optional `session_id` and extra `metadata`.

## Output: `OrchestraRequest` (schema v1.0)

Immutable (`frozen`) and versioned. Facts only — no AI-specific fields.

| Field | Contents |
| --- | --- |
| `schema_version` | `"1.0"` |
| `request_id` | generated UUID |
| `created_at` | build time (UTC) |
| `user` | id, display_name, timezone, preferred_language |
| `book` | id, title, cover_style, book_type, last_opened_at |
| `chapter` | id, title, chapter_number |
| `page` | id, title, page_number, content_format, timezone, cursor_position* |
| `page_content` | the page text (plain_text/markdown) |
| `statistics` | word_count, character_count (recomputed from content) |
| `timestamps` | page_created_at, page_updated_at, book_last_opened_at |
| `language` | user's preferred language |
| `timezone` | page timezone, else user timezone |
| `session` | session_id*, started_at, last_opened_at |
| `metadata` | `{ book_type, … }` |
| `future_reserved` | reserved for backwards-compatible additions |

`*` future-ready fields.

## Validation rules

Fails fast — the node **never** continues with invalid data.

1. Authenticated **user exists** (non-null) → else `missing_user`.
2. **Book belongs to user** → else `book_not_found`.
3. **Chapter belongs to book** → else `chapter_not_found`.
4. **Page belongs to chapter** → else `page_not_found`.
5. **Relationship integrity** (chapter↔book, page↔book, page↔chapter) →
   `corrupted_relationship`.
6. **Content exists** → else `missing_content`.
7. **Language exists** → else `missing_language`.
8. **Timezone resolvable** (page or user) → else `missing_timezone`.
9. **Statistics** computed from content.

Ownership failures (missing vs. foreign) are deliberately indistinguishable
(both surface as `*_not_found`) so the node never leaks whether another user's
record exists.

## Error handling

On any failure the node raises `InputValidationError`, carrying a structured
`errors` list of `{ field, code, message }`. Callers/tests inspect codes without
parsing strings. No partial or invalid `OrchestraRequest` is ever returned.

## Immutability

`OrchestraRequest` (and its nested value objects) are Pydantic **frozen** models.
Once built, attributes cannot be reassigned — downstream nodes produce their own
outputs rather than editing the input.

## Versioning & future compatibility

- `schema_version` starts at `"1.0"`.
- Additions must be **backwards compatible**: add **optional** fields (or use
  `future_reserved`), then bump the minor version. Consumers must ignore unknown
  fields.
- No AI-specific fields will be added here — those belong to later nodes' outputs.

## Testing

`backend/tests/test_input_receiver.py` — **100% coverage** of `app.orchestra`
(measured via `pytest-cov`): happy path, immutability, default "Dear Diary…"
content + stats, missing user/book/chapter/page, wrong ownership, missing
language, missing timezone, relationship-integrity and fact validators, and
schema versioning.

## Where it sits

Node **1 of 10** in the [Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md).
Its output flows to the Safety Checker (node 2) next. See
[Orchestra Nodes](ORCHESTRA_NODES.md) and [Future API Contracts](FUTURE_API_CONTRACTS.md).
