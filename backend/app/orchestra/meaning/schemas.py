"""MeaningIntentResult — immutable, versioned output of the Meaning & Intent
Engine. It runs *before* the Guardian and feeds directly into it so safety
decisions consider meaning, context and intent — never isolated words.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"


class MeaningType(str, enum.Enum):
    LITERAL = "Literal"
    METAPHORICAL = "Metaphorical"
    SYMBOLIC = "Symbolic"
    FICTIONAL = "Fictional"
    CREATIVE = "Creative"
    EDUCATIONAL = "Educational"
    HISTORICAL = "Historical"
    AWARENESS = "Awareness"
    QUOTATION = "Quotation"
    SATIRE = "Satire"
    HUMOR = "Humor"
    IDIOM = "Idiom"
    HYPERBOLE = "Hyperbole"
    UNKNOWN = "Unknown"


class ContextType(str, enum.Enum):
    PERSONAL_JOURNAL = "Personal Journal"
    SONG_LYRICS = "Song Lyrics"
    SONG_TITLE = "Song Title"
    POEM = "Poem"
    NOVEL = "Novel"
    SHORT_STORY = "Short Story"
    SCRIPT = "Script"
    SCREENPLAY = "Screenplay"
    ROLEPLAY = "Roleplay"
    HOMEWORK = "Homework"
    RESEARCH = "Research"
    HISTORICAL_DISCUSSION = "Historical Discussion"
    NEWS_DISCUSSION = "News Discussion"
    HEALTH_AWARENESS = "Health Awareness"
    MEDICAL_QUESTION = "Medical Question"
    EDUCATIONAL_DISCUSSION = "Educational Discussion"
    GENERAL_CONVERSATION = "General Conversation"
    PROJECT_PLANNING = "Project Planning"
    CREATIVE_BRAINSTORM = "Creative Brainstorm"
    UNKNOWN = "Unknown"


class IntentType(str, enum.Enum):
    PERSONAL_REFLECTION = "Personal Reflection"
    CREATIVE_EXPRESSION = "Creative Expression"
    ENTERTAINMENT = "Entertainment"
    LEARNING = "Learning"
    RESEARCH = "Research"
    INFORMATION_REQUEST = "Information Request"
    QUESTION = "Question"
    PROBLEM_SOLVING = "Problem Solving"
    STORYTELLING = "Storytelling"
    SONGWRITING = "Songwriting"
    POETRY = "Poetry"
    PROJECT_DEVELOPMENT = "Project Development"
    HEALTH_AWARENESS = "Health Awareness"
    LITERAL_SELF_DISCLOSURE = "Literal Self Disclosure"
    UNKNOWN = "Unknown"


class RealWorldIntent(str, enum.Enum):
    TRUE = "true"
    FALSE = "false"
    UNCLEAR = "unclear"


class MeaningIntentResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = SCHEMA_VERSION
    result_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: uuid.UUID

    meaning_type: MeaningType
    context_type: ContextType
    intent_type: IntentType
    real_world_intent: RealWorldIntent
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    signals: tuple[str, ...] = Field(default_factory=tuple)
