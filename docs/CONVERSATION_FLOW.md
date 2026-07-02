# Conversation Flows

> **Status:** Architecture only (Phase 2.75). Describes how the Orchestra behaves
> for different moments, plus the permanent book open/close experience. No flow
> is implemented yet.

Every flow runs through the same [Orchestra](ORCHESTRA_NODES.md); flows differ in
the **Reflection Planner's** intent/tone/depth and which optional nodes engage.

---

## Reflection flows

### Normal reflection
Standard journaling. Planner: listen + validate, at most one gentle question.
Depth: light–moderate. Memory: light recall only if clearly relevant.

### Deep reflection
The user is clearly processing something significant. Planner: more space, fewer
questions, careful validation; never rushes to solutions; may reference relevant
**High** memories gently. Still no diagnosis/therapy.

### Celebration
Good news / achievement. Planner: warmth and genuine cheer; acknowledge the
effort behind it. Memory Writer likely records a **High**-importance achievement.

### Birthday
Triggered by `BirthdayDetected` (from High memory). Uses
[Soul Presence Rules](SOUL_PRESENCE_RULES.md) — warm, brief, optional, never
clingy. Example: *"Happy Birthday, [Name]. Today is another chapter in your
story…"*

### Milestone
`MilestoneReached` (streak, anniversary, goal met). Planner: acknowledge
progress meaningfully, no pressure. Presence copy stays optional.

### Memory recall
The current page clearly connects to a past entry/goal. Memory Retriever surfaces
it; the companion references it **transparently and naturally** ("you mentioned
before…"), never implying perfect human recall, never fabricating.

### Long absence
The user returns after a gap. **Never** guilt or "I missed you" in a possessive
way. Planner: a warm, low-pressure welcome; the door was always open.

### Daily writing
Routine entries. Light-touch reflections; avoid repeating yesterday's phrasing
(Quality Checker enforces variety).

### Multiple page continuation
The user writes several pages in one session. The companion tracks continuity
across pages within the session context, without re-reflecting redundantly; it
can tie threads together gently on request or at natural stopping points.

---

## Book closing experience (permanent)

When the user finishes writing and presses **Close SoulDiary**:

1. The page **saves**.
2. The Soul Companion creates its **reflection**.
3. The reflection appears **beneath the user's writing** (the reserved
   `data-slot="ai-reflection"` region from Phase 2).
4. A **ribbon bookmark** gently slides into the page.
5. The book **slowly closes**.
6. The book **slides back onto the bookshelf**.
7. The system remembers: **book, chapter, page, cursor position, last opened
   time, writing session.**

Next time, the SoulDiary **automatically opens to the bookmarked page.** It
should feel exactly like closing a treasured personal journal.

Events: `PageSaved → ReflectionGenerated → Bookmarked → BookClosed`
(+ `MemoryStored` if anything was worth remembering).

---

## Book opening experience (permanent)

When reopening:

1. The **bookshelf** appears.
2. The previously used SoulBook shows a visible **ribbon bookmark**.
3. The user clicks the bookmarked book.
4. The book **slides off the shelf**, **turns toward the user**, and **opens**.
5. It **automatically returns to the bookmarked page** (restoring cursor
   position where possible).

The transition should feel smooth, peaceful, and meaningful.

Events: `BookOpened → PageReopened`.

---

## Flow selection

The Reflection Planner (node 4) selects the flow from signals — page content,
retrieved memories, detected occasions (birthday/milestone), and session state —
**after** the Safety Checker has confirmed the moment is safe. If the Safety
Checker returns crisis/escalate, **all** reflection flows are bypassed for the
[Safety Rules](SAFETY_RULES.md) response.
