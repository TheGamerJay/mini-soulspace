# Soul Companion Experience (Phase 4.1)

> **Status:** Implemented. No new AI capabilities — this phase makes the
> SoulDiary feel beautiful, calm, personal, immersive, and emotionally natural.
> **The SoulDiary is not a chat application** (Constitution **Rule 22**): the
> user's writing is primary; Mini's reflections are secondary.

## Writing experience

While writing, the diary is **completely quiet**: no interruptions, no early
reflections, no typing indicators, no AI chat bubbles, no distractions. Writing
always belongs to the user.

## Book closing experience

Pressing **Save & Close**:

1. The page saves (always first — the entry can never be lost).
2. The writing controls fade.
3. A soft page-turn plays on the journal.
4. The page enters a reflection state: a **subtle companion glow** breathes
   around the page and a small flourish (❧) rests where the reflection will
   appear — never a spinner, never a typing indicator.
5. The reflection **writes itself in ink**: words gradually appear, blurred to
   sharp, as though an invisible fountain pen is writing in the journal
   (`InkText`; paced to finish within ~8s).
6. The reflection ends with a companion seal (✒) beneath a soft divider (❦).
7. The **ribbon bookmark** — in the book's own ribbon color — slides onto the page.
8. "Return to the shelf": the book slowly closes (perspective rotation), fades,
   and the Soul Library settles back in.

Failures stay gentle: *"Your words are safely kept in your SoulDiary."*

## Book opening experience

The Soul Library shows the ribboned book and a **"Continue your story"** card;
opening returns to the bookmarked book → chapter → page (cursor remembered). No
loading flashes, no blank screens.

## Reflection presentation

Reflections are **journal writing, never chat messages**: soft divider,
handwriting-inspired font stack (`--font-reflection`, no webfont dependency),
themed ink color (`--soul-ink`), decorative flourish, companion seal, generous
margins and loose leading, on the page's paper (`--soul-paper`).

## Bookshelf experience

- **Covers**: each book shows its own cover color spine, material sheen, icon,
  and category chip.
- **Favorite pin** (⭐): toggles per book; favorites always float to the top of
  every sort (server-side).
- **Recent glow**: books opened in the last 24h glow softly.
- **Archived shelf**: archived books live on their own dimmed shelf.
- **Shelf depth**: a themed shelf bar (`--soul-shelf`) grounds each row.
- **Default keepsakes**: Daily (leather brown), Dream (blue 🌙), Travel (green
  🧭), Project (gray 🗂️), Creative (purple 🎨), Prayer 🕊️, Gratitude 🌻,
  Health 🌿, Learning 📚.

## SoulBook personalization

Per-book, persisted (migration 0005): **cover color · cover material (leather /
cloth / hardcover / vintage / modern) · icon · title · description · category ·
ribbon color · shelf position · favorite · archive** — edited in the
**Customize** dialog ("Save keepsake"). Future-ready: custom cover artwork,
uploaded covers, corner designs, gold-foil titles, embossed leather, fantasy
tomes — new `cover_material`/`cover_style` values plug in without redesign.

## Bookmark experience

The single active reading ribbon per user is **visual**: it takes the book's
`ribbon_color` on the page and on the shelf. Future: custom bookmark icons,
favorite bookmarks, bookmark notes.

## Companion Themes

Themes affect **appearance only** — never Mini's personality, memory, safety, or
behavior. Implemented: **Midnight**, **Classic Parchment**, **Galaxy**.
Architecture-ready (registry entries awaiting variable blocks): Morning Light,
Autumn, Winter, Spring, Rainy Day.

- Everything renders through CSS variables (`--soul-bg/surface/primary/accent/
  muted/ink/paper/glow/shelf`), so a theme is one variable block in
  `globals.css` + one registry entry in `lib/themes.ts`.
- User-selectable (🎨 switcher), persisted in `localStorage`, applied before
  first paint (no flash). Server persistence can later hook into the existing
  `user_preferences.preferred_theme` column.

## Accessibility

- **Reduced motion**: `prefers-reduced-motion` disables the glow, ink animation
  (text appears instantly), page-turn, and shortens transitions globally.
- Screen readers: the reflection paragraph carries the full text as its label;
  the reflecting state announces via `role="status"`; ribbon/favorite/customize
  controls are labelled.
- Keyboard: all controls are buttons/selects with visible `:focus-visible`
  outlines. High contrast: themed ink colors keep strong contrast per theme.

## Prepared for the future (architecture only)

Voice reflections (Composer attachments: `voice`), illustrated pages / photo
memories (`image` attachments), memory timeline (view_timeline action), mood
colors + seasonal themes (theme registry), animated page backgrounds (theme
`--soul-*` ambience), interactive decorations (flourish slots).

## Testing

Backend: personalization create/defaults/customize/favorite + favorites-first
sort (full suite green). Frontend: ink text (full text accessible + staggered
delays), theme switcher (applies/persists/falls back/only implemented), Save &
Close flow (ink reflection + ribbon + return button), gentle fallback, library
+ bookmark flows — 29 vitest green; production build green.
