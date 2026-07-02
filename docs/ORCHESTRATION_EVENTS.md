# Orchestration Events

> **Status:** Architecture only (Phase 2.75). Defines the future internal event
> vocabulary. **No event bus or emitters are implemented.** These name the
> meaningful moments the Orchestra and app will publish so features (presence,
> analytics, memory, animations) can react without tight coupling.

## Why events

Events keep the Orchestra loosely coupled: a node or feature reacts to *what
happened* without knowing *who did it or how*. They also give every reflection an
auditable trail.

## Core events

| Event | Emitted when | Typical payload (shape only) |
| --- | --- | --- |
| `BookOpened` | a SoulBook is opened | user, book, timestamp |
| `BookClosed` | Close SoulDiary completes | user, book, chapter, page, session |
| `PageSaved` | a page is saved (manual/auto) | user, book, chapter, page, counts |
| `ReflectionGenerated` | a reflection passes Quality | user, page, reflection ref |
| `MemoryStored` | Memory Writer records something | user, memory ref, importance |
| `BirthdayDetected` | today matches the user's birthday | user, date |
| `MilestoneReached` | streak/anniversary/goal met | user, milestone type |
| `StreakUpdated` | writing streak changes | user, streak count |
| `Bookmarked` | ribbon bookmark set on close | user, book, chapter, page, cursor |
| `PageReopened` | reopening returns to bookmark | user, book, chapter, page |

## Supporting events (auditing)

- `RequestRejected` — Input Receiver rejected malformed/unauthorized input.
- `SafetyTriggered` — Safety Checker returned crisis/escalate.
- `QualityFailed` / `QualityRevised` — Quality Checker outcomes.
- `ReflectionDegraded` — a graceful fallback was returned instead of a reflection.

## Principles

- Events are **facts about the past** (named in past tense), never commands.
- Payloads carry **references and shapes**, not internal implementation detail.
- Presence features (birthday/milestone/streak) subscribe to events; they never
  poll the Orchestra directly (see [Soul Presence Rules](SOUL_PRESENCE_RULES.md)).
- The book open/close animation sequence is driven by
  `BookOpened/PageReopened` and `PageSaved → ReflectionGenerated → Bookmarked →
  BookClosed` (see [Conversation Flow](CONVERSATION_FLOW.md)).

Exact event schemas will be finalized alongside the API contracts in a future
phase — see [Future API Contracts](FUTURE_API_CONTRACTS.md).
