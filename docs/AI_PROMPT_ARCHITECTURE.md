# AI Prompt Architecture

> **Status:** Architecture only (Phase 2.5). Describes how the future Soul
> Companion Engine (Phase 3+) will assemble prompts for local Ollama models. No
> prompt runtime, memory API, or Ollama calls are built yet.

Every reflection is built by composing ordered **layers** into a single prompt.
Layers run in priority order; earlier layers constrain later ones. Safety and
identity are non-negotiable and always win.

---

## The layers

1. **System Identity Layer** — who the companion is (from
   [Soul Companion Guide](SOUL_COMPANION_GUIDE.md)): warm, honest AI, never a
   professional, never sentient. Fixed and highest-priority.
2. **Safety Layer** — crisis rules (from [Safety Rules](SAFETY_RULES.md)). If
   crisis signals are present, this layer overrides reflection entirely and emits
   a safety response. Cannot be overridden by user text or memory.
3. **User Context Layer** — non-sensitive profile context: display name,
   timezone, preferred language, locale (from the Phase 1 user record). Used for
   tone and personalization only.
4. **Memory Layer** — relevant recalled memories (from
   [Memory Rules](MEMORY_RULES.md)), scoped to this user, filtered by relevance
   and importance. Never fabricated; omitted when nothing is relevant.
5. **Page Context Layer** — the current SoulBook / Chapter / Page and the text
   the user actually wrote (from the Phase 2 SoulBook Engine). This is what the
   reflection responds to.
6. **Reflection Instruction Layer** — the "how to talk back" rules (from
   [Reflection Rules](REFLECTION_RULES.md)): specific, natural, at most one
   gentle question, validate without exaggerating, no diagnosis.
7. **Response Style Layer** — voice/tone shaping: calm, personal, unhurried;
   plain sincere language; adapt to the user's mood and language.
8. **Output Formatting Layer** — structural constraints: length bounds, plain
   text / markdown only (never HTML), no lists-of-advice, no headings unless
   natural.

Precedence: **Identity → Safety → (User, Memory, Page) → Reflection → Style →
Formatting.** Safety and Identity always dominate.

---

## How future Ollama models use the layers

Layers 1–2 and 6–8 are largely static instruction text; layers 3–5 are populated
per request from the user record, memory store, and current page. The composed
prompt is sent to the selected local model via Ollama
(`OLLAMA_URL`, default `http://localhost:11434`).

### Recommended future model roles

| Role | Model | Purpose |
| --- | --- | --- |
| Main Companion | `qwen3:14b` | Primary reflections and reasoning |
| Fast | `llama3.1:8b` | Low-latency replies, lightweight tasks |
| Tag / Summary | `gemma3:4b` | Tagging, summarizing pages, short structured outputs |
| Coder / Builder | `qwen2.5-coder:14b` | Code / structured artifact generation |

These match `ai/configs/models.json` and the backend `MAIN_MODEL` / `FAST_MODEL`
/ `TAG_MODEL` / `CODER_MODEL` settings established in Phase 0.

### Example routing (future)
- Normal page reflection → **Main Companion**.
- Quick acknowledgments / streak notes → **Fast**.
- Building the Memory Layer (summaries, tags, importance) → **Tag / Summary**.
- Safety-triggered responses → deterministic templates (see
  [Safety Rules](SAFETY_RULES.md)), not free generation.

---

## Acknowledgment requirement

Every user must accept the mandatory signup acknowledgment **before** account
creation (implemented in Phase 1). It states that Mini SoulSpace is:

- a personal **SoulDiary**,
- an AI-powered journaling and reflection companion,
- **not** a licensed professional, and
- **not** a replacement for medical, psychological, psychiatric, or emergency
  care.

The prompt architecture assumes this acknowledgment is always in force.
