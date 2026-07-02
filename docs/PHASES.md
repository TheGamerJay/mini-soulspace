# Mini SoulSpace — Development Phases

Mini SoulSpace is built phase by phase as a production-quality application.
Each phase must be production-ready, tested, modular, documented and
maintainable before the next begins.

## Phase 0 — Repository Foundation ✅

Backend (FastAPI, brains, config, Alembic), frontend (Next.js App Router,
landing page), AI config scaffolding, Docker, setup scripts, documentation.

## Phase 1 — Authentication & User Foundation ✅

JWT auth via httpOnly cookies (Argon2id, rotating refresh tokens with reuse
detection), Redis rate limiting, mandatory signup agreement (modal-gated),
full user profiles + preferences, protected routes, Home screen. Configurable
minimum signup age.

## Phase 2 — SoulBook Engine ✅ (current)

The permanent journal — no AI yet.

- **Data model:** `soul_books` → `soul_chapters` → `soul_pages`, plus
  `soul_bookmarks`, `soul_recent_books`, `soul_recent_chapters`. Soft delete,
  archive/restore, ordering, recency, word/character counts.
- **Storage:** pages are **plain text / markdown, never HTML** (lightweight,
  searchable, versionable, export- and AI-friendly). No rich-text dependency.
- **API:** `/api/soulbooks/**` — books, chapters, pages, autosave, search, sort;
  every record ownership-scoped to the authenticated user.
- **Frontend:** Soul Library (create/rename/archive/restore/delete, search,
  sort), immersive SoulBook cover, chapter/page navigation, and a writing engine
  with `Dear Diary...` starter, live counts, debounced auto-save + manual save.
- **Future AI slot:** each writing page reserves a layout region beneath the
  writing for the future flow (user writing → AI reflection → conversation).

## Phase 2.5 — Soul Companion Architecture ✅ (current)

Documentation & architecture only — **no AI runtime, no behavior change**.
Defines the permanent identity, behavior, memory, safety, presence and prompt
rules the future Soul Companion Engine must follow:

- [Soul Companion Guide](SOUL_COMPANION_GUIDE.md) — identity, personality, tone.
- [Reflection Rules](REFLECTION_RULES.md) — how the diary talks back (good vs bad).
- [Memory Rules](MEMORY_RULES.md) — importance levels, scoping, user control.
- [Safety Rules](SAFETY_RULES.md) — crisis-safe behavior + response templates.
- [Soul Presence Rules](SOUL_PRESENCE_RULES.md) — meaningful, optional moments.
- [AI Prompt Architecture](AI_PROMPT_ARCHITECTURE.md) — 8 prompt layers + model roles.

**Phase 3 will build the first Soul Companion Engine using these rules.**

## Future roadmap

- **Phase 3** — Reflection engine (the diary that talks back), built on the Phase 2.5 rules.
- **Phase 4** — Semantic memory (pgvector embeddings + recall).
- **Phase 5** — Conversation threads on pages.
- **Phase 6** — Emotional analytics, charts and timeline.
- **Phase 7** — Exports (PDF / DOCX / TXT), bookmarks UI, printing.
- **Phase 8** — Safety hardening + realtime (WebSocket / voice).

> The roadmap is directional and refined as the product matures.
