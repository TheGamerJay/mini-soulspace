"""Deterministic memory-fact extractor (no AI).

Extracts at most ONE candidate memory from the user's own writing (never the AI
response — facts must be supported by the conversation). "When in doubt, don't
save": if no clear first-person fact is present, returns ``None``.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from app.orchestra.memory.schemas import MemoryPriority, MemoryType

P = MemoryPriority
M = MemoryType


class CandidateMemory(NamedTuple):
    memory_type: MemoryType
    importance: MemoryPriority
    title: str
    summary: str
    keywords: frozenset[str]


# Ordered by priority — the first matching pattern wins (one memory, not dozens).
_PATTERNS: list[tuple[tuple[str, ...], MemoryType, MemoryPriority, str]] = [
    (("passed away", "passed on", "i lost my", "she died", "he died", "they died",
      "diagnosed with", "my divorce", "funeral"), M.LIFE_EVENT, P.CRITICAL, "Life event"),
    (("my birthday is", "i was born on", "today is my birthday", "turning ", "i turn "),
     M.BIRTHDAY, P.HIGH, "Birthday"),
    (("anniversary",), M.ANNIVERSARY, P.HIGH, "Anniversary"),
    (("my son", "my daughter", "my wife", "my husband", "my partner", "my mother",
      "my father", "my mom", "my dad", "my brother", "my sister", "my fiancé",
      "my fiancee", "my boyfriend", "my girlfriend", "my best friend"),
     M.RELATIONSHIP, P.HIGH, "Relationship"),
    (("my dog", "my cat", "my puppy", "my kitten", "my pet"), M.PET, P.MEDIUM, "Pet"),
    (("i got promoted", "i graduated", "i finished", "i completed", "i achieved",
      "i won", "i passed my", "i launched", "i published", "i got the job",
      "i got accepted"), M.ACHIEVEMENT, P.HIGH, "Achievement"),
    (("milestone", "reached a milestone"), M.MILESTONE, P.HIGH, "Milestone"),
    (("my novel", "my song", "my album", "my screenplay", "my poem collection"),
     M.CREATIVE_PROJECT, P.HIGH, "Creative project"),
    (("my project", "working on", "i'm building", "i am building", "started a project"),
     M.PROJECT, P.HIGH, "Project"),
    (("my goal is", "i plan to", "i've decided to", "i aim to", "i'm determined to"),
     M.GOAL, P.HIGH, "Goal"),
    (("i've been learning", "i started learning", "learning to", "i'm practicing"),
     M.LEARNING_PROGRESS, P.MEDIUM, "Learning progress"),
    (("i traveled to", "my trip to", "trip to", "i'm visiting", "i visited"),
     M.TRAVEL, P.MEDIUM, "Travel"),
    (("every morning i", "every day i", "i started a habit", "my new routine", "my routine is"),
     M.HABIT, P.LOW, "Habit"),
    (("i want to", "i would like to"), M.GOAL, P.MEDIUM, "Goal"),
    (("my favorite", "favorite "), M.FAVORITE, P.MEDIUM, "Favorite"),
    (("i prefer", "i really like", "i love "), M.PREFERENCE, P.LOW, "Preference"),
    (("quote:", "a quote i love"), M.QUOTE, P.LOW, "Quote"),
]

_STOP = {
    "the", "and", "for", "that", "this", "with", "was", "have", "had", "not", "you",
    "are", "but", "her", "she", "him", "his", "about", "from", "into", "just", "were",
    "them", "then", "than", "your", "our", "favorite", "really", "like", "love", "want",
    "would", "started", "my", "i", "is", "a", "to", "of", "it", "on", "in", "me",
}
_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")
_SENT_RE = re.compile(r"[.!?\n]")


def _keywords(text: str) -> frozenset[str]:
    return frozenset(t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOP)


def _sentence_with(text: str, trigger: str) -> str:
    for part in _SENT_RE.split(text):
        if trigger in part.lower():
            return part.strip()
    return text.strip()[:160]


def extract(page_content: str) -> CandidateMemory | None:
    """Return the single most-important candidate memory, or None."""

    body = (page_content or "").lower()
    for triggers, mtype, importance, label in _PATTERNS:
        hit = next((t for t in triggers if t in body), None)
        if hit is None:
            continue
        summary = _sentence_with(page_content, hit)
        excerpt = " ".join(summary.split()[:8])
        return CandidateMemory(
            memory_type=mtype,
            importance=importance,
            title=f"{label}: {excerpt}"[:150],
            summary=summary[:500],
            keywords=_keywords(summary),
        )
    return None
