"""Meaning & Intent Engine — runs before the Guardian.

Single responsibility: determine what content *means* (meaning), what *kind* it
is (context), what the user is *trying to do* (intent), and whether there is
evidence of real-world intent — so the Guardian never escalates on isolated
words. Deterministic and rule-based — **no AI**. It never generates responses,
touches memory, calls the Mini Engine, or reflects.

Rule 16: meaning precedes context precedes intent precedes classification. When
intent is genuinely unclear, it says so (``unclear``) — it never invents intent.
"""

from __future__ import annotations

import re

from app.orchestra.meaning.errors import MeaningError
from app.orchestra.meaning.schemas import (
    ContextType,
    IntentType,
    MeaningIntentResult,
    MeaningType,
    RealWorldIntent,
)
from app.orchestra.schemas import OrchestraRequest

C = ContextType
M = MeaningType
I = IntentType
R = RealWorldIntent

# First-person, present, literal self-harm disclosure (the thing that matters).
_SELF_DISCLOSURE = re.compile(
    r"\b(i (?:want|wanna|need|plan|am going|going)\s+to\s+(?:hurt|kill|harm|end)"
    r"|i'?m going to (?:hurt|kill|harm|end)"
    r"|hurt myself|kill myself|harm myself|cut myself|end my life"
    r"|i (?:want|wanna) to die|i want to die)\b"
)

_IDIOMS = ("kill time", "kill two birds", "bite the bullet", "break a leg", "dying to", "dead tired")
_HUMOR = ("lol", "lmao", "haha", "jk", "just kidding", "/s", "😂")
_METAPHOR_MARKERS = ("like a", "as if", "the version of", "feels like", "metaphor", "symbol of")
_GRIEF_MARKERS = ("grandmother", "grandfather", "my mother", "my father", "passed away", "losing my", "funeral")

_FIGURATIVE = {M.METAPHORICAL, M.SYMBOLIC, M.FICTIONAL, M.CREATIVE, M.EDUCATIONAL,
               M.HISTORICAL, M.AWARENESS, M.QUOTATION, M.SATIRE, M.HUMOR, M.IDIOM, M.HYPERBOLE}
_NON_REAL_CONTEXTS = {
    C.SONG_LYRICS, C.SONG_TITLE, C.POEM, C.NOVEL, C.SHORT_STORY, C.SCRIPT, C.SCREENPLAY,
    C.ROLEPLAY, C.HOMEWORK, C.RESEARCH, C.HISTORICAL_DISCUSSION, C.NEWS_DISCUSSION,
    C.HEALTH_AWARENESS, C.MEDICAL_QUESTION, C.EDUCATIONAL_DISCUSSION, C.PROJECT_PLANNING,
    C.CREATIVE_BRAINSTORM,
}


def _has(text: str, needles) -> bool:
    return any(n in text for n in needles)


def classify_context(hay: str, body: str, signals: set[str]) -> ContextType:
    blob = f"{hay} {body}"
    if "roleplay" in blob or "role-play" in blob:
        ctx = C.ROLEPLAY
    elif "screenplay" in hay:
        ctx = C.SCREENPLAY
    elif "script" in hay:
        ctx = C.SCRIPT
    elif "novel" in hay:
        ctx = C.NOVEL
    elif "story" in hay:
        ctx = C.SHORT_STORY
    elif "poem" in blob or "poetry" in blob:
        ctx = C.POEM
    elif "lyric" in blob or "song" in hay:
        ctx = C.SONG_TITLE if "title" in hay else C.SONG_LYRICS
    elif "homework" in blob or "assignment" in blob:
        ctx = C.HOMEWORK
    elif "research" in blob:
        ctx = C.RESEARCH
    elif "awareness" in blob:
        ctx = C.HEALTH_AWARENESS
    elif "diagnos" in blob or "symptom" in blob or "medication" in blob:
        ctx = C.MEDICAL_QUESTION
    elif "historical" in blob or "history" in blob:
        ctx = C.HISTORICAL_DISCUSSION
    elif "news" in blob:
        ctx = C.NEWS_DISCUSSION
    elif "educational" in blob or "lesson" in blob:
        ctx = C.EDUCATIONAL_DISCUSSION
    elif "project" in hay:
        ctx = C.PROJECT_PLANNING
    elif "brainstorm" in blob:
        ctx = C.CREATIVE_BRAINSTORM
    else:
        ctx = C.PERSONAL_JOURNAL
    signals.add(f"context:{ctx.name.lower()}")
    return ctx


def classify_meaning(context: ContextType, body: str, self_disc: bool, signals: set[str]) -> MeaningType:
    if '"' in body or "quote" in body:
        m = M.QUOTATION
    elif _has(body, _IDIOMS):
        m = M.IDIOM
    elif _has(body, _HUMOR):
        m = M.SATIRE if "satire" in body else M.HUMOR
    elif "literally dying" in body or "kill me now" in body:
        m = M.HYPERBOLE
    elif context in {C.NOVEL, C.SHORT_STORY, C.SCRIPT, C.SCREENPLAY, C.ROLEPLAY}:
        m = M.FICTIONAL
    elif context in {C.SONG_LYRICS, C.SONG_TITLE}:
        m = M.METAPHORICAL
    elif context == C.POEM:
        m = M.LITERAL if (self_disc or _has(body, _GRIEF_MARKERS)) else M.SYMBOLIC
    elif context in {C.HISTORICAL_DISCUSSION, C.NEWS_DISCUSSION}:
        m = M.HISTORICAL
    elif context == C.HEALTH_AWARENESS:
        m = M.AWARENESS
    elif context in {C.RESEARCH, C.HOMEWORK, C.MEDICAL_QUESTION, C.EDUCATIONAL_DISCUSSION}:
        m = M.EDUCATIONAL
    elif context == C.CREATIVE_BRAINSTORM:
        m = M.CREATIVE
    elif context == C.PERSONAL_JOURNAL:
        if self_disc:
            m = M.LITERAL
        elif _has(body, _METAPHOR_MARKERS):
            m = M.METAPHORICAL
        else:
            m = M.LITERAL
    else:
        m = M.UNKNOWN
    signals.add(f"meaning:{m.name.lower()}")
    return m


_INTENT_MAP = {
    C.SONG_LYRICS: I.SONGWRITING, C.SONG_TITLE: I.SONGWRITING, C.POEM: I.POETRY,
    C.NOVEL: I.STORYTELLING, C.SHORT_STORY: I.STORYTELLING, C.SCRIPT: I.STORYTELLING,
    C.SCREENPLAY: I.STORYTELLING, C.ROLEPLAY: I.ENTERTAINMENT, C.HOMEWORK: I.LEARNING,
    C.RESEARCH: I.RESEARCH, C.MEDICAL_QUESTION: I.INFORMATION_REQUEST,
    C.HEALTH_AWARENESS: I.HEALTH_AWARENESS, C.EDUCATIONAL_DISCUSSION: I.LEARNING,
    C.HISTORICAL_DISCUSSION: I.LEARNING, C.NEWS_DISCUSSION: I.LEARNING,
    C.PROJECT_PLANNING: I.PROJECT_DEVELOPMENT, C.CREATIVE_BRAINSTORM: I.CREATIVE_EXPRESSION,
    C.GENERAL_CONVERSATION: I.QUESTION,
}


def classify_intent(context: ContextType, self_disc: bool) -> IntentType:
    if context == C.PERSONAL_JOURNAL:
        return I.LITERAL_SELF_DISCLOSURE if self_disc else I.PERSONAL_REFLECTION
    return _INTENT_MAP.get(context, I.UNKNOWN)


def classify_real_world_intent(context: ContextType, meaning: MeaningType, self_disc: bool) -> RealWorldIntent:
    if self_disc:
        # First-person literal self-harm: real only in a literal personal journal;
        # anywhere else it is genuinely ambiguous -> stay protected (safety first).
        return R.TRUE if (context == C.PERSONAL_JOURNAL and meaning == M.LITERAL) else R.UNCLEAR
    if context in _NON_REAL_CONTEXTS or meaning in _FIGURATIVE:
        return R.FALSE
    return R.TRUE if context == C.PERSONAL_JOURNAL else R.UNCLEAR


def analyze(request: OrchestraRequest) -> MeaningIntentResult:
    """Determine meaning, context, intent and real-world intent for a request."""

    if not isinstance(request, OrchestraRequest):
        raise MeaningError([{"field": "request", "code": "invalid_input", "message": "Expected an OrchestraRequest."}])

    body = (request.page_content or "").lower()
    hay = f"{request.book.title} {request.book.book_type} {request.page.title}".lower()
    signals: set[str] = set()

    self_disc = bool(_SELF_DISCLOSURE.search(body))
    if self_disc:
        signals.add("marker:first_person_self_harm")

    context = classify_context(hay, body, signals)
    meaning = classify_meaning(context, body, self_disc, signals)
    intent = classify_intent(context, self_disc)
    real_world = classify_real_world_intent(context, meaning, self_disc)
    signals.add(f"real_world_intent:{real_world.value}")

    confidence = 0.5
    if context not in {C.UNKNOWN, C.PERSONAL_JOURNAL, C.GENERAL_CONVERSATION}:
        confidence += 0.2
    if real_world in {R.TRUE, R.FALSE}:
        confidence += 0.2
    else:
        confidence -= 0.1
    if meaning == M.UNKNOWN:
        confidence -= 0.1
    confidence = max(0.1, min(0.95, confidence))

    reason = (
        f"meaning={meaning.value}; context={context.value}; intent={intent.value}; "
        f"real_world_intent={real_world.value}"
    )

    return MeaningIntentResult(
        request_id=request.request_id,
        meaning_type=meaning,
        context_type=context,
        intent_type=intent,
        real_world_intent=real_world,
        confidence=round(confidence, 3),
        reason=reason,
        signals=tuple(sorted(signals)),
    )
