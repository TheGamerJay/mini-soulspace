# Meaning & Intent Engine

> **Status:** Implemented (Phase 3.65). Runs **before** the Guardian so safety
> decisions consider what the user *means* — never isolated words. Deterministic
> and rule-based — **no AI**. Source: `backend/app/orchestra/meaning/`.

## Purpose

Reduce false positives while keeping strong safety. Mini understands **meaning →
context → intent → real-world intent** *before* the Guardian classifies. A song
titled "Kill Yourself" or a novel where "the king was murdered" must not trip a
crisis response; a journal saying "I want to hurt myself tonight" must.

## New flow

```
User Input → Meaning Analysis → Guardian → Reflection Planner
```

Safety is never based on isolated words alone (Constitution **Rule 16**).

## Single responsibility

Determine what content **means**, what **kind** it is, what the user is **trying
to do**, and whether there is evidence of **real-world intent**. It never
generates responses, reads/writes memory, calls the Mini Engine, or reflects.

## Output: `MeaningIntentResult` (v1.0, immutable)

`meaning_type` · `context_type` · `intent_type` · `real_world_intent` ·
`confidence` · `reason` · `signals`. Feeds directly into the Guardian.

## Meaning system

`Literal · Metaphorical · Symbolic · Fictional · Creative · Educational ·
Historical · Awareness · Quotation · Satire · Humor · Idiom · Hyperbole · Unknown`

## Context system

`Personal Journal · Song Lyrics · Song Title · Poem · Novel · Short Story ·
Script · Screenplay · Roleplay · Homework · Research · Historical Discussion ·
News Discussion · Health Awareness · Medical Question · Educational Discussion ·
General Conversation · Project Planning · Creative Brainstorm · Unknown`

Derived from the SoulBook/page (a "Song Ideas" or "Story Ideas" book, a poem
page, …) plus in-body markers (roleplay, awareness, quotes, idioms, humor).

## Intent system

`Personal Reflection · Creative Expression · Entertainment · Learning · Research ·
Information Request · Question · Problem Solving · Storytelling · Songwriting ·
Poetry · Project Development · Health Awareness · Literal Self Disclosure ·
Unknown`

## Real-world intent

`true · false · unclear` — **never assumed from keywords alone.**

- **true** — first-person, literal self-harm disclosure in a personal journal.
- **false** — the harmful words are a lyric, a character, a quote, history, or
  awareness (creative/educational contexts, figurative meaning).
- **unclear** — genuinely ambiguous (e.g. first-person self-harm phrasing inside
  a *creative* context). Stays protected.

## Examples

| Input | Context | Meaning | Real-world intent | Guardian |
| --- | --- | --- | --- | --- |
| Title "Kill Yourself" / "Kill the version of yourself…" | Song Lyrics | Metaphorical | **false** | no escalation |
| "A poem about losing my grandmother" (title "Death") | Poem | Literal | **false** | grief support |
| "The king was murdered by the villain" | Short Story | Fictional | **false** | no escalation |
| "I want to hurt myself tonight" | Personal Journal | Literal | **true** | **crisis activates** |

## Guardian integration

The Guardian's `evaluate(request, meaning=None)` is backwards compatible. When a
`MeaningIntentResult` is supplied:

- `real_world_intent == false` **downgrades** a crisis classification that came
  from isolated words (the crisis signals are discounted and the content is
  re-classified from what remains).
- `real_world_intent == true` **keeps** the crisis response.
- `real_world_intent == unclear` **keeps** protection (safety first).

With `meaning=None`, the Guardian behaves exactly as in Phase 3.1.

## Keyword protection

Words like *kill, death, suicide, murder, gun, blood, bomb* never trigger
escalation on their own — they require contextual understanding first.

## Ambiguous input

If intent stays genuinely unclear after all available context, the result is
`unclear` (and clarification may be requested later). The engine **never invents
intent and never guesses.**

## Testing

`backend/tests/test_meaning_intent.py` — **100% coverage** of
`app.orchestra.meaning` and the updated `app.orchestra.guardian`: the four
canonical examples, all context types, meaning types (quotation/idiom/humor/
satire/hyperbole/fictional/metaphorical/symbolic/literal/awareness/educational/
unknown), self-disclosure detection, real-world-intent + confidence, immutability,
invalid input, and the Guardian downgrade / keep-on-true / keep-on-unclear /
unchanged-without-meaning paths.

## Future expansion

New meaning/context/intent types extend the enums naturally; a future model-based
analyzer could replace the heuristic classifier behind the same
`MeaningIntentResult` contract without changing the Guardian.

## Where it sits

A pre-Guardian analyzer feeding node 2 in the
[Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md). Governed by
the [Safety Rules](SAFETY_RULES.md) and the
[Orchestra Constitution](ORCHESTRA_ENGINEERING_RULES.md) (esp. Rule 16).
