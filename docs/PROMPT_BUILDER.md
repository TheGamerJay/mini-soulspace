# Prompt Builder (Orchestra Node 6)

> **Status:** Implemented (Phase 3.5). Assembles the final blueprint before any
> model runs. It transforms a `ContextPackage` into a `PromptPackage` — it
> **never calls an LLM, generates a reflection, retrieves/stores memories, or
> plans.** Source: `backend/app/orchestra/prompt/`.

## Purpose

The intelligence already exists inside the Orchestra. The Prompt Builder simply
assembles it into the correct format — the complete `PromptPackage` that the
Response Generator (node 7) will send to the model. Per **Constitution Rule 14**:
templates define *structure*, the Orchestra provides *intelligence*, the LLM
provides *language* — never mixed.

## Inputs / Outputs (API contract)

```
build(context: ContextPackage, *, template_name="reflection", template_version=None)
    -> PromptPackage
```

- **Input:** the immutable `ContextPackage`. Never modified.
- **Output:** an immutable `PromptPackage`. Malformed input, an unknown template,
  or a **missing required layer** raises a structured `PromptBuilderError` — the
  builder never guesses and never silently omits a required layer.

## Schemas (v1.0, immutable)

**PromptTemplate:** `name`, `version`, `model_role`, `formatting_instructions`,
`generation` (defaults), `description`.

**PromptPackage:** `schema_version`, `package_id`, `created_at`, `request_id`,
`template_name`, `template_version`, `template_used`, `model_role`,
`system_prompt`, `conversation_blueprint` (tuple of `PromptMessage`),
`generation_parameters`, `confidence`, `reason` (internal), `statistics`,
`future_reserved`.

## Layer system

The `system_prompt` is assembled from seven ordered layers, mapped from the
ContextPackage's blocks:

1. **Identity** — the static Soul Companion identity (the builder's own text).
2. **Safety & Guardian** — the Guardian's decisions, caps, and crisis/referral
   instructions.
3. **Current Page** — the journal page and its metadata.
4. **Relevant Memories** — only the memories previous nodes selected (or "None
   selected").
5. **Reflection Plan** — the Planner's type/tone/depth/style.
6. **Response Style** — tone, depth, question limit, celebration, listening mode.
7. **Output Formatting** — the template's formatting rules (plain text / light
   markdown, never HTML; no advice-lists; at most the planned questions).

`Identity`, `Guardian`, `Current Page`, and `Reflection` are **required** —
missing any is an error. `Memory` is optional. The `conversation_blueprint` is
`[system(system_prompt), user(page content)]`.

## Template versioning

Templates are versioned (`reflection` `v1`). The registry maps
`name → {version → template}`; omitting a version selects the latest. Future
updates add new versions (`v2`, …) **without breaking previous versions**.

## Model role system

`ModelRole ∈ {main, fast, vision, research, coding, summary, image}`. The
**template** selects the role (Reflection v1 → `main`). The Prompt Builder only
records the role — it never calls the model.

## Generation parameter system

Structured, configuration-only `GenerationParameters` (`temperature`, `top_p`,
`presence_penalty`, `frequency_penalty`, `max_tokens`) come from the template,
with `max_tokens` scaled to the reflection depth (None→120, Light→250,
Medium→450, Deep→650). The builder never applies them — that is the Response
Generator's job.

## Future specialist templates

Extension points only (not implemented): Research, Homework, Vision, Image
Generation, Image Editing, Coding, Translation, Music, Project Assistant,
Medication Information, Document Analysis. Each will be a new versioned entry in
the registry with its own model role.

## Testing

`backend/tests/test_prompt_builder.py` — **100% coverage** of
`app.orchestra.prompt` (`pytest-cov`): reflection template, default + explicit +
unknown versions, unknown template name, seven-layer ordering, identity/page/
memory (with & without)/crisis/referral/celebration/listening/encourage layers,
blueprint + role selection, generation parameters by depth, structured reasoning,
immutability, invalid input, and missing-required-layer.

## Where it sits

Node **6 of 10** in the [Soul Intelligence Architecture](SOUL_INTELLIGENCE_ARCHITECTURE.md).
Consumes the [Context Builder](CONTEXT_BUILDER.md)'s package; its `PromptPackage`
is the sole input to the Response Generator (node 7) — the last assembly step
before a model is ever called. Governed by the
[AI Prompt Architecture](AI_PROMPT_ARCHITECTURE.md) and the
[Orchestra Constitution](ORCHESTRA_ENGINEERING_RULES.md) (esp. Rule 14).
