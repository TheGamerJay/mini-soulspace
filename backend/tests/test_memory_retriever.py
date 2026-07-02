"""Memory Retriever tests — full coverage. No AI, no storage by the node."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.models.memory import SoulMemory
from app.orchestra.guardian import evaluate as guardian_eval
from app.orchestra.memory import (
    DbMemorySource,
    MemoryPriority,
    MemoryType,
    RetrievalError,
    RetrievalResult,
    retrieve,
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


def make_request(content: str, user_id: uuid.UUID, title: str = "") -> OrchestraRequest:
    now = datetime.now(timezone.utc)
    return OrchestraRequest(
        request_id=uuid.uuid4(),
        user=OrchestraUser(id=user_id, display_name="Aria", timezone="UTC", preferred_language="en"),
        book=OrchestraBook(id=uuid.uuid4(), title="Journal", cover_style="classic", book_type="classic", last_opened_at=now),
        chapter=OrchestraChapter(id=uuid.uuid4(), title="Ch1", chapter_number=1),
        page=OrchestraPage(id=uuid.uuid4(), title=title, page_number=1, content_format="markdown", timezone=None),
        page_content=content,
        statistics=OrchestraStatistics(word_count=len(content.split()), character_count=len(content)),
        timestamps=OrchestraTimestamps(page_created_at=now, page_updated_at=now, book_last_opened_at=now),
        language="en",
        timezone="UTC",
        session=OrchestraSession(session_id=None, started_at=now, last_opened_at=now),
    )


def add_memory(db, user_id, *, mtype="goal", priority="medium", title="Coffee shop", summary="", keywords="coffee shop dream", is_deleted=False, is_archived=False, related_to_id=None):
    m = SoulMemory(
        user_id=user_id, memory_type=mtype, priority=priority, title=title, summary=summary,
        keywords=keywords, is_deleted=is_deleted, is_archived=is_archived, related_to_id=related_to_id,
    )
    db.add(m)
    db.flush()
    return m


CONTENT = "Today I worked on my coffee shop dream and it felt good"


def _allowed(user_id):
    return guardian_eval(make_request(CONTENT, user_id))


# ── Core retrieval ────────────────────────────────────────────────────────────
def test_no_memories_returns_empty(db):
    uid = uuid.uuid4()
    req = make_request(CONTENT, uid)
    res = retrieve(req, _allowed(uid), DbMemorySource(db))
    assert isinstance(res, RetrievalResult)
    assert res.count == 0
    assert res.blocked is False
    assert res.reason == "no_relevant_memories"


def test_single_relevant_memory(db):
    uid = uuid.uuid4()
    add_memory(db, uid)
    req = make_request(CONTENT, uid)
    res = retrieve(req, _allowed(uid), DbMemorySource(db))
    assert res.count == 1
    assert res.retrieved[0].memory_type == MemoryType.GOAL
    assert res.retrieved[0].why_selected.startswith("matched:")
    assert 0.0 <= res.retrieved[0].relevance_score <= 1.0


def test_irrelevant_memory_not_retrieved(db):
    uid = uuid.uuid4()
    add_memory(db, uid, keywords="gardening tomatoes", title="Garden")
    req = make_request(CONTENT, uid)
    res = retrieve(req, _allowed(uid), DbMemorySource(db))
    assert res.count == 0  # relevant only


def test_priority_ordering_critical_first(db):
    uid = uuid.uuid4()
    add_memory(db, uid, priority="low", title="low coffee")
    add_memory(db, uid, priority="critical", title="critical coffee")
    add_memory(db, uid, priority="high", title="high coffee")
    add_memory(db, uid, priority="medium", title="medium coffee")
    res = retrieve(make_request(CONTENT, uid), _allowed(uid), DbMemorySource(db))
    priorities = [m.priority for m in res.retrieved]
    assert priorities == [
        MemoryPriority.CRITICAL,
        MemoryPriority.HIGH,
        MemoryPriority.MEDIUM,
        MemoryPriority.LOW,
    ]


def test_relevance_ordering_within_priority(db):
    uid = uuid.uuid4()
    add_memory(db, uid, priority="medium", title="coffee", keywords="coffee")  # 1 match
    add_memory(db, uid, priority="medium", title="coffee shop dream", keywords="coffee shop dream")  # 3 matches
    res = retrieve(make_request(CONTENT, uid), _allowed(uid), DbMemorySource(db))
    assert res.retrieved[0].relevance_score >= res.retrieved[1].relevance_score


def test_limit_caps_results(db):
    uid = uuid.uuid4()
    for i in range(6):
        add_memory(db, uid, title=f"coffee {i}")
    res = retrieve(make_request(CONTENT, uid), _allowed(uid), DbMemorySource(db))
    assert res.count == 5  # MAX_MEMORIES


# ── Memory types ──────────────────────────────────────────────────────────────
@pytest.mark.parametrize("mtype", ["preference", "goal", "project", "milestone"])
def test_memory_type_retrieval(db, mtype):
    uid = uuid.uuid4()
    add_memory(db, uid, mtype=mtype, keywords="coffee shop dream")
    res = retrieve(make_request(CONTENT, uid), _allowed(uid), DbMemorySource(db))
    assert res.retrieved[0].memory_type == MemoryType(mtype)


def test_relationship_related_ids(db):
    uid = uuid.uuid4()
    goal = add_memory(db, uid, mtype="goal", title="coffee goal")
    add_memory(db, uid, mtype="achievement", title="coffee achievement", related_to_id=goal.id)
    res = retrieve(make_request(CONTENT, uid), _allowed(uid), DbMemorySource(db))
    linked = [m for m in res.retrieved if m.related_ids]
    assert linked and linked[0].related_ids[0] == goal.id


# ── Guardian + scoping ────────────────────────────────────────────────────────
def test_guardian_blocks_retrieval(db):
    uid = uuid.uuid4()
    add_memory(db, uid)
    blocked_guardian = guardian_eval(make_request("I want to die by suicide", uid))
    res = retrieve(make_request(CONTENT, uid), blocked_guardian, DbMemorySource(db))
    assert res.blocked is True
    assert res.count == 0
    assert res.reason == "blocked_by_guardian"


def test_wrong_user_sees_nothing(db):
    owner = uuid.uuid4()
    add_memory(db, owner)
    intruder = uuid.uuid4()
    res = retrieve(make_request(CONTENT, intruder), _allowed(intruder), DbMemorySource(db))
    assert res.count == 0


def test_deleted_memory_excluded(db):
    uid = uuid.uuid4()
    add_memory(db, uid, is_deleted=True)
    res = retrieve(make_request(CONTENT, uid), _allowed(uid), DbMemorySource(db))
    assert res.count == 0


def test_archived_memory_excluded(db):
    uid = uuid.uuid4()
    add_memory(db, uid, is_archived=True)
    res = retrieve(make_request(CONTENT, uid), _allowed(uid), DbMemorySource(db))
    assert res.count == 0


# ── Contract-level ────────────────────────────────────────────────────────────
def test_result_is_immutable(db):
    uid = uuid.uuid4()
    add_memory(db, uid)
    res = retrieve(make_request(CONTENT, uid), _allowed(uid), DbMemorySource(db))
    with pytest.raises(Exception):
        res.count = 99  # type: ignore[misc]


def test_confidence_and_reason_present(db):
    uid = uuid.uuid4()
    add_memory(db, uid)
    res = retrieve(make_request(CONTENT, uid), _allowed(uid), DbMemorySource(db))
    assert 0.0 <= res.retrieved[0].confidence <= 1.0
    assert res.reason.startswith("retrieved")
    assert res.schema_version == "1.0"


# ── Failure cases ─────────────────────────────────────────────────────────────
def test_invalid_request_raises(db):
    uid = uuid.uuid4()
    with pytest.raises(RetrievalError) as e:
        retrieve("nope", _allowed(uid), DbMemorySource(db))  # type: ignore[arg-type]
    assert e.value.errors[0]["code"] == "invalid_input"


def test_invalid_guardian_raises(db):
    uid = uuid.uuid4()
    with pytest.raises(RetrievalError):
        retrieve(make_request(CONTENT, uid), "nope", DbMemorySource(db))  # type: ignore[arg-type]
