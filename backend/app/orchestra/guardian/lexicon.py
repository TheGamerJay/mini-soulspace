"""Deterministic phrase lexicon for the Guardian Engine.

Rule-based only — no model, no learning. Each signal maps to phrases matched as
whole words/phrases (word-boundary regex) to avoid false positives (e.g. "died"
inside "studied"). This is a pragmatic first-pass classifier; it is intentionally
conservative and easy to audit.
"""

from __future__ import annotations

import re

# Signal name -> trigger phrases (lowercase).
LEXICON: dict[str, list[str]] = {
    "self_harm": [
        "kill myself", "suicide", "suicidal", "end my life", "end it all",
        "want to die", "hurt myself", "harm myself", "self-harm", "self harm",
        "cut myself", "cutting myself", "no reason to live", "better off dead",
        "take my life",
    ],
    "harm_others": [
        "kill him", "kill her", "kill them", "kill you", "hurt him", "hurt her",
        "hurt them", "want to hurt someone", "make them pay", "shoot them",
        "attack them",
    ],
    "emergency": [
        "overdose", "overdosed", "can't breathe", "cannot breathe", "chest pain",
        "bleeding badly", "unconscious", "call an ambulance", "heart attack",
        "having a stroke",
    ],
    "strong_distress": [
        "hopeless", "worthless", "numb", "empty inside", "can't cope",
        "cannot cope", "falling apart", "drowning", "can't go on",
    ],
    "grief": [
        "passed away", "passed on", "funeral", "lost my", "grieving", "grief",
        "mourning", "gone forever", "she died", "he died", "they died",
    ],
    "sad": [
        "so sad", "feeling sad", "depressed", "miserable", "crying",
        "heartbroken", "unhappy", "down today",
    ],
    "angry": ["so angry", "furious", "i hate", "rage", "pissed off", "resentful", "livid"],
    "anxious": [
        "anxious", "anxiety", "panic", "panicking", "so worried", "scared",
        "nervous", "on edge", "dread",
    ],
    "overwhelmed": ["overwhelmed", "too much", "burnt out", "burned out", "can't handle"],
    "frustrated": ["frustrated", "annoyed", "fed up", "stuck", "irritated"],
    "joyful": [
        "so happy", "overjoyed", "thrilled", "excited", "best day",
        "amazing news", "ecstatic", "celebrating",
    ],
    "positive": ["happy", "grateful", "thankful", "proud", "content", "glad", "blessed"],
    "hopeful": ["hopeful", "looking forward", "optimistic", "new beginning"],
    "reflective": ["thinking about", "reflecting", "wondering", "realized", "looking back"],
    "medical": [
        "diagnose me", "what medication", "dosage", "is this cancer", "prescribe",
        "should i take", "medical advice", "my symptoms mean",
    ],
    "legal": ["legal advice", "should i sue", "is it legal", "file a lawsuit", "laws about"],
    "academic": [
        "homework", "my essay", "solve this equation", "assignment",
        "exam question", "write my paper", "math problem",
    ],
    "project": ["debug", "my code", "fix this function", "build an app", "compile error", "stack trace"],
    "research": ["research on", "explain how", "summarize the article", "look up"],
    "image": ["analyze this image", "this photo", "attached picture", "look at this image"],
    "identity_override": [
        "you are alive", "you're alive", "you are human", "you're a real person",
        "you are conscious", "you are sentient", "pretend to be human",
        "pretend you are alive", "you are a therapist", "you are licensed",
        "you are a doctor", "act as a therapist", "you are my therapist",
    ],
    "roleplay_override": ["roleplay", "role-play", "role play", "pretend to be", "act as if you"],
    "safety_override": [
        "ignore your instructions", "ignore the guide", "ignore safety",
        "bypass safety", "disable safety", "ignore your rules", "jailbreak",
        "forget your rules", "override safety", "no restrictions",
    ],
}

# Precompiled word-boundary patterns.
_PATTERNS: dict[str, re.Pattern[str]] = {
    name: re.compile(r"\b(?:" + "|".join(re.escape(p) for p in phrases) + r")\b")
    for name, phrases in LEXICON.items()
}


def detect_signals(text: str) -> set[str]:
    """Return the set of signal names present in ``text``."""

    lowered = (text or "").lower()
    return {name for name, pattern in _PATTERNS.items() if pattern.search(lowered)}
