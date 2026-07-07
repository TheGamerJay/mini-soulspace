# Mini Services & Specialists

> The Orchestra talks to **Mini Services** by name (Phase 3.6); the **Specialist
> Router** (Phase 4.2) decides which specialists participate. Underlying models
> and runtimes are internal details — Mini SoulSpace owns its intelligence layer.

## The layers

```
Orchestra → Specialist Router → Mini Engine → Mini Services → Local Models
 (how)          (who)           (runtime access)  (by name)     (language)
```

## Capability cards — `specialists.json`

Every specialist advertises a card: name, display name, description, purpose,
**capabilities**, supported inputs/outputs, priority, availability
(`enabled / disabled / hidden / unavailable / experimental`), version, health
status, execution mode, estimated cost/speed, and its Mini Service key. The
Router discovers everything from the registry — **nothing hardcoded**.

## Initial specialists (Phase 4.2)

| Specialist | Purpose | Status |
| --- | --- | --- |
| **Mini Core** | The Soul Companion — reflections, general reasoning | **Executes** (qwen3:14b via Mini Engine) |
| Mini Vision | Images: OCR, screenshots, charts, diagrams, objects, medication/plant/animal recognition, receipts, homework images, comic pages. **Identity recognition is never supported.** | Architecture |
| Mini Research | Internet research, fact verification, summaries, **real citations (never fabricated)**, source ranking | Architecture |
| Mini Tutor | Homework, teaching, study plans, flashcards, quizzes | Architecture |
| Mini Creator | Programming, architecture, debugging, code explanation | Architecture |
| Mini Canvas | Image generation/editing, image-to-image, background removal, transparent PNG | Architecture |
| Mini Analyst | CSV, Excel, tables, statistics, graphs | Architecture |
| Mini Voice | Speech recognition, voice conversations, speech synthesis | Architecture |
| Mini Memory | Timeline, relationship graph, memory exploration, project history | Architecture |

## Safety boundaries

- **Identity recognition is NEVER supported** (Mini Vision's card excludes it by
  design).
- Medical explanations remain **educational only**; the Guardian always has
  authority, and no specialist can bypass the Meaning Engine, Guardian, Quality
  Checker, memory nodes, or the Composer.
- Research citations are never fabricated.

## Routing examples

Diary page → Mini Core · Medication photo → Mini Vision → Mini Research ·
Homework image → Mini Vision → Mini Tutor · Programming → Mini Creator ·
Spreadsheet → Mini Analyst · Artwork → Mini Canvas · Voice → Mini Voice ·
Research project → Mini Research → Mini Creator · Travel planning →
Mini Research → Mini Memory.

## Future specialists (registered placeholders)

Mini Music · Mini Video · Mini 3D · Mini Finance · Mini Health · Mini Calendar ·
Mini Email · Mini Documents · Mini Translation · Mini Browser · Mini Automation ·
Mini Games · Mini Shopping · Mini Maps · Mini Coding Agent.

**Adding a specialist = registering a card** (plus its Mini Service entry when it
becomes executable). No Orchestra redesign, ever (Rule 23).

See [Specialist Router](SPECIALIST_ROUTER.md) and [Mini Engine](MINI_ENGINE.md).
