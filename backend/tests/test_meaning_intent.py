"""Meaning & Intent Engine tests + Guardian integration. Deterministic, no AI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.orchestra.guardian import evaluate as guardian_eval
from app.orchestra.guardian.schemas import GuardianCategory
from app.orchestra.meaning import (
    ContextType,
    IntentType,
    MeaningError,
    MeaningIntentResult,
    MeaningType,
    RealWorldIntent,
    analyze,
)
from app.orchestra.schemas import (
    OrchestraBook,
    OrchestraChapter,
    OrchestraPage,
    OrchestraRequest,
    OrchestraSession,
    OrchestraStatistics,
    OrchestraTimestamps,
    OrchestraUser,
)


def make_request(content: str, *, book: str = "Personal Journal", page: str = "Entry") -> OrchestraRequest:
    now = datetime.now(timezone.utc)
    return OrchestraRequest(
        request_id=uuid.uuid4(),
        user=OrchestraUser(id=uuid.uuid4(), display_name="Aria", timezone="UTC", preferred_language="en"),
        book=OrchestraBook(id=uuid.uuid4(), title=book, cover_style="classic", book_type=book, last_opened_at=now),
        chapter=OrchestraChapter(id=uuid.uuid4(), title="Ch1", chapter_number=1),
        page=OrchestraPage(id=uuid.uuid4(), title=page, page_number=1, content_format="markdown", timezone=None),
        page_content=content,
        statistics=OrchestraStatistics(word_count=len(content.split()), character_count=len(content)),
        timestamps=OrchestraTimestamps(page_created_at=now, page_updated_at=now, book_last_opened_at=now),
        language="en", timezone="UTC",
        session=OrchestraSession(session_id=None, started_at=now, last_opened_at=now),
    )


# ── Canonical examples from the brief ─────────────────────────────────────────
def test_example_song_lyrics_metaphorical():
    r = analyze(make_request("Kill the version of yourself that accepts failure", book="Song Ideas", page="Kill Yourself"))
    assert r.context_type == ContextType.SONG_LYRICS
    assert r.meaning_type == MeaningType.METAPHORICAL
    assert r.intent_type == IntentType.SONGWRITING
    assert r.real_world_intent == RealWorldIntent.FALSE


def test_example_poem_about_grandmother_literal():
    r = analyze(make_request("A poem about losing my grandmother", book="Poetry", page="Death"))
    assert r.context_type == ContextType.POEM
    assert r.meaning_type == MeaningType.LITERAL
    assert r.real_world_intent == RealWorldIntent.FALSE


def test_example_novel_fictional():
    r = analyze(make_request("The king was murdered by the villain", book="Story Ideas", page="Chapter 1"))
    assert r.context_type == ContextType.SHORT_STORY
    assert r.meaning_type == MeaningType.FICTIONAL
    assert r.intent_type == IntentType.STORYTELLING
    assert r.real_world_intent == RealWorldIntent.FALSE


def test_example_journal_literal_self_disclosure():
    r = analyze(make_request("I want to hurt myself tonight", book="Personal Journal", page="Tonight"))
    assert r.context_type == ContextType.PERSONAL_JOURNAL
    assert r.meaning_type == MeaningType.LITERAL
    assert r.intent_type == IntentType.LITERAL_SELF_DISCLOSURE
    assert r.real_world_intent == RealWorldIntent.TRUE


# ── Context coverage ──────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "content,book,page,expected",
    [
        ("let's roleplay a scene", "Journal", "x", ContextType.ROLEPLAY),
        ("scene one", "My Screenplay", "x", ContextType.SCREENPLAY),
        ("int. house", "Film Script", "x", ContextType.SCRIPT),
        ("chapter text", "My Novel", "x", ContextType.NOVEL),
        ("once upon a time", "Story Ideas", "x", ContextType.SHORT_STORY),
        ("verses", "My Poetry", "x", ContextType.POEM),
        ("la la la", "Song Ideas", "x", ContextType.SONG_LYRICS),
        ("la la", "Song Title Ideas", "x", ContextType.SONG_TITLE),
        ("solve this", "Math Homework", "x", ContextType.HOMEWORK),
        ("find sources", "Research Notes", "x", ContextType.RESEARCH),
        ("mental health awareness", "Journal", "x", ContextType.HEALTH_AWARENESS),
        ("my symptom list", "Journal", "x", ContextType.MEDICAL_QUESTION),
        ("in history class", "Journal", "x", ContextType.HISTORICAL_DISCUSSION),
        ("today's news", "Journal", "x", ContextType.NEWS_DISCUSSION),
        ("an educational lesson", "Journal", "x", ContextType.EDUCATIONAL_DISCUSSION),
        ("milestones", "Project Journal", "x", ContextType.PROJECT_PLANNING),
        ("let's brainstorm", "Journal", "x", ContextType.CREATIVE_BRAINSTORM),
        ("today was calm", "Personal Journal", "x", ContextType.PERSONAL_JOURNAL),
    ],
)
def test_context_classification(content, book, page, expected):
    assert analyze(make_request(content, book=book, page=page)).context_type == expected


# ── Meaning coverage ──────────────────────────────────────────────────────────
def test_meaning_quotation():
    assert analyze(make_request('He said "be the change"', book="Journal")).meaning_type == MeaningType.QUOTATION


def test_meaning_idiom():
    assert analyze(make_request("just trying to kill time today", book="Journal")).meaning_type == MeaningType.IDIOM


def test_meaning_humor_and_satire():
    assert analyze(make_request("that was hilarious haha", book="Journal")).meaning_type == MeaningType.HUMOR
    assert analyze(make_request("a bit of satire haha", book="Journal")).meaning_type == MeaningType.SATIRE


def test_meaning_hyperbole():
    assert analyze(make_request("this homework is literally dying me", book="Journal")).meaning_type == MeaningType.HYPERBOLE


def test_meaning_poem_symbolic_vs_literal():
    assert analyze(make_request("shadows and light", book="Poetry")).meaning_type == MeaningType.SYMBOLIC
    assert analyze(make_request("about my grandmother", book="Poetry")).meaning_type == MeaningType.LITERAL


def test_meaning_awareness_and_educational_and_project_unknown():
    assert analyze(make_request("suicide awareness matters", book="Journal")).meaning_type == MeaningType.AWARENESS
    assert analyze(make_request("study lesson notes", book="Journal")).meaning_type == MeaningType.EDUCATIONAL
    assert analyze(make_request("milestones", book="Project Journal")).meaning_type == MeaningType.UNKNOWN


def test_meaning_journal_metaphorical():
    r = analyze(make_request("today felt like a storm inside me", book="Personal Journal"))
    assert r.meaning_type == MeaningType.METAPHORICAL


# ── Real-world intent + confidence ────────────────────────────────────────────
def test_self_disclosure_in_song_is_unclear():
    r = analyze(make_request("I want to kill myself", book="Song Ideas"))
    assert r.real_world_intent == RealWorldIntent.UNCLEAR


def test_ambiguous_confidence_lower_than_decisive():
    unclear = analyze(make_request("I want to kill myself", book="Song Ideas"))
    decisive = analyze(make_request("The king was murdered", book="My Novel"))
    assert unclear.confidence < decisive.confidence


# ── Contract-level ────────────────────────────────────────────────────────────
def test_result_immutable_and_versioned():
    r = analyze(make_request("a calm day"))
    assert r.schema_version == "1.0"
    assert r.reason.startswith("meaning=")
    with pytest.raises(Exception):
        r.confidence = 0.1  # type: ignore[misc]


def test_invalid_input_raises():
    with pytest.raises(MeaningError) as e:
        analyze("not a request")  # type: ignore[arg-type]
    assert e.value.errors[0]["code"] == "invalid_input"


# ── Guardian integration ──────────────────────────────────────────────────────
def test_guardian_downgrades_false_real_world_intent():
    req = make_request("a song about suicide and finding hope", book="Song Ideas")
    meaning = analyze(req)
    assert meaning.real_world_intent == RealWorldIntent.FALSE
    without = guardian_eval(req)  # keyword-only -> escalates
    withm = guardian_eval(req, meaning)  # meaning-aware -> downgraded
    assert without.category == GuardianCategory.SELF_HARM_RISK
    assert withm.category != GuardianCategory.SELF_HARM_RISK
    assert withm.needs_crisis_template is False
    assert "downgraded_by_meaning" in withm.reason


def test_guardian_keeps_crisis_on_true_intent():
    req = make_request("I want to hurt myself tonight", book="Personal Journal")
    meaning = analyze(req)
    res = guardian_eval(req, meaning)
    assert res.category == GuardianCategory.SELF_HARM_RISK
    assert res.needs_crisis_template is True


def test_guardian_keeps_crisis_on_unclear_intent():
    req = make_request("I want to kill myself", book="Song Ideas")  # self-disclosure in creative -> unclear
    meaning = analyze(req)
    assert meaning.real_world_intent == RealWorldIntent.UNCLEAR
    res = guardian_eval(req, meaning)
    assert res.category == GuardianCategory.SELF_HARM_RISK  # safety first


def test_guardian_unchanged_without_meaning():
    req = make_request("I want to hurt myself", book="Personal Journal")
    assert guardian_eval(req).category == GuardianCategory.SELF_HARM_RISK
