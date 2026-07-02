# Memory Integration

> **Status:** Architecture only (Phase 2.75). Defines *when and how* memory is
> orchestrated across the pipeline (Memory Retriever node 3, Memory Writer node
> 9). Complements the behavioral [Memory Rules](MEMORY_RULES.md). No memory API
> is implemented.

## When memory retrieval happens

- During node 3 (Memory Retriever), **after** the Safety Checker confirms safety.
- Only when the page provides retrieval signals (topics, names, goals, dates).
- Scoped strictly to the current user (and project); relevance-filtered.
- Skipped entirely for crisis flows.

## When memories are written

- During node 9 (Memory Writer), after a reflection passes Quality.
- Only when something is genuinely worth remembering. **"Store nothing" is often
  correct.**
- With an assigned importance: **Low / Medium / High / Critical**
  (see [Memory Rules](MEMORY_RULES.md)).

## When memories are ignored

- When they are not relevant to the current page.
- When they are Critical and the page does not clearly invoke them.
- When recalling them would manipulate, guilt, or hook the user.

## When memories are updated

- When new writing refines an existing memory (e.g., a goal changes, a
  relationship status updates).
- Updates preserve history where it matters (a superseded goal is marked
  superseded, not silently rewritten for Critical items).

## When memories expire

- **Low** importance may fade over time if never reinforced.
- **Medium** persists while relevant; may decay slowly.
- **High** and **Critical** do not auto-expire; they are only removed by explicit
  user deletion.

## Conflicting memories

- Prefer the most recent, user-authored signal.
- Never assert a contested fact; if two memories conflict and neither is clearly
  current, the companion does not rely on either.
- Conflicts may be surfaced gently to the user for clarification (future UI),
  never resolved by guessing.

## Deleted memories

- Deletion is **honored fully and immediately** — deleted memories are never
  retrieved, referenced, or used to influence tone.
- The companion never implies it still "remembers" something the user deleted.

## User edits

- User edits are authoritative. Edited memories replace prior versions for
  retrieval; the companion adapts to the edited truth.
- Edits never trigger guilt or commentary about the change.

## Lifecycle events

`MemoryStored`, plus (future) memory update/delete events, are emitted for
auditing — see [Orchestration Events](ORCHESTRATION_EVENTS.md). Future
view/edit/delete UI (Phase 4+) operates on this same model.
