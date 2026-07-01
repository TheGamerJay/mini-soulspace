# Mini SoulSpace — AI Layer

This directory holds the model-facing assets that power the SoulDiary's
intelligence. It is intentionally decoupled from the backend so prompts,
model routing and embedding strategies can evolve independently of API code.

## Structure

| Folder        | Responsibility                                                        |
| ------------- | --------------------------------------------------------------------- |
| `prompts/`    | System and task prompt templates.                                     |
| `configs/`    | Model configuration (see `configs/models.json`).                      |
| `builders/`   | Prompt/response builders that assemble structured artefacts.          |
| `memory/`     | Long-term semantic memory strategies (pgvector-backed).               |
| `reflection/` | Reflection generation logic ("the diary that talks back").            |
| `routing/`    | Model/brain routing rules and heuristics.                             |
| `summaries/`  | Summarisation prompts and pipelines.                                  |
| `tags/`       | Tagging and classification prompts.                                   |
| `embeddings/` | Embedding generation and vector utilities.                            |
| `safety/`     | Safety, moderation and crisis-detection prompts.                      |

## Models (Ollama)

| Role  | Model              |
| ----- | ------------------ |
| Main  | `qwen3:14b`        |
| Fast  | `llama3.1:8b`      |
| Tag   | `gemma3:4b`        |
| Coder | `qwen2.5-coder:14b`|

Ollama endpoint: `http://localhost:11434`

Pull the models with `scripts/pull_ollama_models.ps1`.
