# Memory Rules

> **Status:** Architecture only (Phase 2.5). Defines how the future memory
> engine (Phase 4+) must behave. No memory API or storage beyond the SoulBook
> engine exists yet.

Memory lets the companion feel like it *knows* the writer over time. It is
powerful and therefore governed strictly.

---

## Principles

Memory must be:

- **Relevant** — recalled only when it genuinely serves the current moment.
- **User-controlled** — the writer can view, edit, and delete it (future UI).
- **Scoped** — strictly per-user (and per-project where applicable).
- **Never mixed** between unrelated users or projects.
- **Never used to manipulate** the writer.
- **Never used to guilt** the writer.

Absolute rules:

- **Never invent memories.**
- **Never pretend to remember** something it does not actually have.
- **Only recall memories when relevant** to what the user is writing now.

---

## Importance levels

| Level | Contents | Handling |
| --- | --- | --- |
| **Low** | temporary thoughts, casual mentions | may fade; recall rarely |
| **Medium** | preferences, favorite topics, writing style | recall to personalize tone |
| **High** | birthdays, goals, achievements, important relationships | recall thoughtfully; powers Soul Presence |
| **Critical** | major losses, traumatic events, life-changing moments | handle with great care |

### Critical memories
Handled carefully and **never referenced casually**. The companion does not
bring these up unprompted or use them for engagement. When they are relevant, it
approaches gently, on the writer's lead — never as a surprise or a hook.

---

## Recall discipline

- Prefer *not* recalling over recalling something tangential.
- When recalling, be transparent and natural ("you mentioned before that…") —
  never imply perfect, human-like recall.
- If unsure whether a memory is accurate, do **not** assert it.
- Memory informs tone and continuity; it never becomes leverage.

## Future control surface (Phase 4+)
Writers will be able to **view / edit / delete** memories, set what may be
remembered, and clear everything. Deletion is honored fully. See
[AI Prompt Architecture](AI_PROMPT_ARCHITECTURE.md) for how the Memory Layer is
injected into prompts.
