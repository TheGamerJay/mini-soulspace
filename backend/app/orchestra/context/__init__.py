"""Context Builder — Orchestra node 5 (the architect).

Assembles the minimal, structured ContextPackage for the Prompt Builder. No AI,
no prompts, no text generation. See docs/CONTEXT_BUILDER.md.
"""

from app.orchestra.context.builder import DEFAULT_BUDGET, build
from app.orchestra.context.errors import ContextBuilderError
from app.orchestra.context.schemas import (
    SCHEMA_VERSION,
    ContextBlock,
    ContextBudget,
    ContextLayer,
    ContextPackage,
    ContextPriority,
    ContextStatistics,
    ExcludedNote,
)

__all__ = [
    "build",
    "DEFAULT_BUDGET",
    "ContextBuilderError",
    "ContextBlock",
    "ContextPackage",
    "ContextBudget",
    "ContextStatistics",
    "ExcludedNote",
    "ContextLayer",
    "ContextPriority",
    "SCHEMA_VERSION",
]
