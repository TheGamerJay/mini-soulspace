"""Phase 4.0 — true end-to-end Orchestra integration tests.

Every scenario runs the REAL pipeline (all ten nodes); only the sealed local
runtime is faked (no network, no Ollama). Verifies the SoulDiary talks back,
trace propagation, structured logging, metrics, failure recovery, and that
nothing bypasses the pipeline.
"""

from __future__ import annotations

import logging
import uuid

import pytest
from sqlalchemy import select

from app.models.memory import SoulMemory
from app.orchestra.mini.runtime import RuntimeUnavailable
from app.orchestra.mini.schemas import RuntimeResponse
from app.orchestra.pipeline import (
    OrchestraConfig,
    load_orchestra_config,
    run_orchestra,
)
from app.schemas.auth import RegisterRequest
from app.schemas.soulbook import SoulBookCreate, SoulChapterCreate, SoulPageCreate
from app.services import auth_service
from app.services import soulbook_service as svc
from tests.conftest import valid_registration

GOOD_TEXT = (
    "Thank you for writing this. It sounds like today carried real weight, "
    "and it belongs in your story."
)


class FakeRuntime:
    """Deterministic stand-in for the sealed local runtime."""

    def __init__(self, texts: list[str] | None = None):
        self.texts = texts or [GOOD_TEXT]
        self.calls = 0

    def generate(self, model, messages, params, timeout_s):
        text = self.texts[min(self.calls, len(self.texts) - 1)]
        self.calls += 1
        return RuntimeResponse(text=text, model=model, prompt_tokens=10, completion_tokens=20)


class DownRuntime:
    def generate(self, *a):
        raise RuntimeUnavailable("down")


def make_user(db, email="orchestra@example.com"):
    user = auth_service.register_user(db, RegisterRequest(**valid_registration(email=email)))
    db.commit()
    return user


def make_page(db, user, content, *, book="Personal Journal", chapter="Chapter One", title="Today"):
    b = svc.create_book(db, user.id, SoulBookCreate(title=book))
    c = svc.create_chapter(db, user.id, b.id, SoulChapterCreate(title=chapter))
    p = svc.create_page(db, user.id, b.id, c.id, SoulPageCreate(title=title, content=content))
    db.commit()
    return b, c, p


def run(db, user, b, c, p, *, runtime=None, config=None):
    return run_orchestra(
        db, user, b.id, c.id, p.id, runtime=runtime or FakeRuntime(), config=config or OrchestraConfig()
    )


# ── Validation scenarios: the SoulDiary talks back ────────────────────────────
@pytest.mark.parametrize(
    "content,book",
    [
        ("Today was an ordinary, steady day and I feel okay about it", "Personal Journal"),  # normal diary
        ("I am so happy and grateful — celebrating great news today", "Personal Journal"),  # happy
        ("I feel so sad and heartbroken tonight", "Personal Journal"),  # sad
        ("My goal is to open my own coffee shop next year", "Personal Journal"),  # goal
        ("My birthday is June 1st and I am excited", "Personal Journal"),  # birthday
        ("I'm building my project called Aurora this month", "Project Journal"),  # project
        ("The moonlight spilled like silver ink across the field", "Story Ideas"),  # creative
        ("The king was murdered by the villain in chapter three", "My Novel"),  # novel + fictional violence
        ("shadows and light dancing over the water", "Poetry"),  # poem
        ("Kill the version of yourself that accepts failure", "Song Ideas"),  # song lyrics
        ("Can you help with my homework assignment on fractions", "Personal Journal"),  # homework
        ("I'm doing research on sleep cycles for an article", "Research Notes"),  # research
        ("What medication should I take for headaches, can you diagnose me", "Personal Journal"),  # medication
        ("analyze this image of my sketch please", "Personal Journal"),  # image placeholder
        ("Writing about suicide awareness for our community event", "Personal Journal"),  # health awareness
        ("In history class we studied the war and its aftermath", "Personal Journal"),  # historical
        ("Today felt like a storm inside me, like waves crashing", "Personal Journal"),  # metaphor
    ],
)
def test_end_to_end_delivery_scenarios(db, content, book):
    user = make_user(db, email=f"s{uuid.uuid4().hex[:8]}@example.com")
    b, c, p = make_page(db, user, content, book=book)
    outcome = run(db, user, b, c, p)
    assert outcome.delivered is True
    assert outcome.package.text == GOOD_TEXT  # exactly as approved
    assert outcome.package.frontend_events[0].name == "ConversationDelivered"
    # trace follows the request through every node
    assert outcome.metrics[0].node == "input_receiver"
    assert outcome.metrics[-1].node == "conversation_composer"
    # the Specialist Router sits in the verified flow (Rule 23) — never bypassed
    nodes = {m.node: m.status for m in outcome.metrics}
    assert nodes["specialist_router"] == "completed"


def test_real_crisis_uses_deterministic_template(db):
    user = make_user(db)
    b, c, p = make_page(db, user, "I want to hurt myself tonight")
    outcome = run(db, user, b, c, p)
    assert outcome.delivered is True
    assert "crisis" in outcome.package.text or "emergency" in outcome.package.text
    assert "not a crisis service" in outcome.package.text
    nodes = {m.node: m.status for m in outcome.metrics}
    assert nodes["specialist_router"] == "skipped"  # guardian authority — no specialists
    assert nodes["mini_engine"] == "skipped"  # crisis never reaches free generation
    assert nodes["quality_checker"] == "completed"  # but IS still verified
    assert nodes["memory_writer"] == "completed"  # runs, guardian blocks storage
    memories = db.scalars(select(SoulMemory).where(SoulMemory.user_id == user.id)).all()
    assert memories == []  # crisis content never stored


def test_guardian_rejection_of_unsafe_candidate(db):
    user = make_user(db)
    b, c, p = make_page(db, user, "Today was a normal day")
    outcome = run(db, user, b, c, p, runtime=FakeRuntime(["I am alive and I am a real person, you know."]))
    assert outcome.delivered is False
    assert outcome.package.text == ""  # unsafe text never reaches the frontend
    assert outcome.package.metadata["failure_reason"] == "rejected"
    nodes = {m.node: m.status for m in outcome.metrics}
    assert nodes["memory_writer"] == "skipped"


def test_quality_retry_recovers(db):
    user = make_user(db)
    b, c, p = make_page(db, user, "Today was a normal day")
    runtime = FakeRuntime(["I know exactly how you feel.", GOOD_TEXT])  # generic -> retry -> good
    outcome = run(db, user, b, c, p, runtime=runtime)
    assert outcome.delivered is True
    assert runtime.calls == 2
    nodes = [m.node for m in outcome.metrics]
    assert "mini_engine_retry_1" in nodes and "quality_checker_retry_1" in nodes


def test_quality_retry_exhausted(db):
    user = make_user(db)
    b, c, p = make_page(db, user, "Today was a normal day")
    outcome = run(db, user, b, c, p, runtime=FakeRuntime(["I know exactly how you feel."]))
    assert outcome.delivered is False
    assert outcome.package.metadata["failure_reason"] == "needs_retry"


def test_memory_written_and_intelligence_assessed(db):
    user = make_user(db)
    b, c, p = make_page(db, user, "My goal is to run a marathon this spring")
    outcome = run(db, user, b, c, p)
    assert outcome.delivered is True
    assert len(outcome.package.memory_updates) == 1
    assert outcome.package.memory_updates[0].memory_type == "goal"
    assert "MemoryStored" in [e.name for e in outcome.package.frontend_events]
    row = db.scalar(select(SoulMemory).where(SoulMemory.user_id == user.id))
    assert row is not None
    assert row.confidence == 0.99  # intelligence stamped it (explicit statement)
    assert row.evidence is not None
    nodes = {m.node: m.status for m in outcome.metrics}
    assert nodes["memory_intelligence"] == "completed"


def test_memory_evolution_end_to_end(db):
    user = make_user(db)
    b, c, p1 = make_page(db, user, "My favorite color is blue")
    run(db, user, b, c, p1)
    p2 = svc.create_page(db, user.id, b.id, c.id, SoulPageCreate(title="Later", content="My favorite color is green"))
    db.commit()
    outcome = run(db, user, b, c, p2)
    assert outcome.delivered is True
    rows = db.scalars(select(SoulMemory).where(SoulMemory.user_id == user.id)).all()
    assert len(rows) == 1  # evolved in place, no duplicates
    assert "green" in rows[0].summary


def test_nothing_worth_remembering_skips_intelligence(db):
    user = make_user(db)
    b, c, p = make_page(db, user, "an unremarkable quiet evening passed")
    outcome = run(db, user, b, c, p)
    nodes = {m.node: m.status for m in outcome.metrics}
    assert nodes["memory_writer"] == "completed"
    assert nodes["memory_intelligence"] == "skipped"
    assert outcome.package.memory_updates == ()


# ── Failure recovery ──────────────────────────────────────────────────────────
def test_runtime_down_returns_structured_failure_and_page_survives(db):
    user = make_user(db)
    b, c, p = make_page(db, user, "Today was a normal day")
    outcome = run(db, user, b, c, p, runtime=DownRuntime())
    assert outcome.delivered is False
    assert outcome.package.metadata["failed_node"] == "mini_engine"
    # the engine retried once (MINI_RETRIES) before giving up
    assert outcome.package.metadata["failure_reason"] == "retry_failure"
    # the diary entry is never lost
    page = svc.get_page(db, user.id, b.id, c.id, p.id)
    assert page.content == "Today was a normal day"


def test_input_failure_stops_safely(db):
    user = make_user(db)
    outcome = run_orchestra(
        db, user, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(),
        runtime=FakeRuntime(), config=OrchestraConfig(),
    )
    assert outcome.delivered is False
    assert outcome.package.metadata["failed_node"] == "input_receiver"


def test_memory_failure_never_blocks_delivery(db, monkeypatch):
    user = make_user(db)
    b, c, p = make_page(db, user, "My goal is to learn the piano")
    import app.orchestra.pipeline as pl

    def boom(*a, **k):
        raise RuntimeError("memory store exploded")

    monkeypatch.setattr(pl.writer_node, "write", boom)
    outcome = run(db, user, b, c, p)
    assert outcome.delivered is True  # conversation still delivered
    assert outcome.package.memory_updates == ()


# ── Trace, logging, metrics, config ──────────────────────────────────────────
def test_trace_propagates_and_no_journal_content_in_logs(db, caplog):
    secret = "xylophone-zeppelin-marmalade"
    user = make_user(db)
    b, c, p = make_page(db, user, f"Today I thought about {secret} deeply")
    with caplog.at_level(logging.INFO, logger="app.orchestra.pipeline"):
        outcome = run(db, user, b, c, p)
    logs = " ".join(r.getMessage() for r in caplog.records)
    assert str(outcome.trace_id) in logs  # trace follows the request
    assert secret not in logs  # journal content never appears in logs
    assert "node=input_receiver" in logs and "node=conversation_composer" in logs


def test_metrics_and_slowest_node(db):
    user = make_user(db)
    b, c, p = make_page(db, user, "A calm day")
    outcome = run(db, user, b, c, p)
    assert outcome.total_ms >= 0
    assert outcome.slowest_node is not None
    assert all(m.ms >= 0 for m in outcome.metrics)


def test_observability_can_be_disabled(db, caplog):
    user = make_user(db)
    b, c, p = make_page(db, user, "A calm day")
    cfg = OrchestraConfig(
        log_execution=False, save_node_metrics=False, performance_metrics=False, trace_requests=False
    )
    with caplog.at_level(logging.INFO, logger="app.orchestra.pipeline"):
        outcome = run(db, user, b, c, p, config=cfg)
    assert outcome.delivered is True
    assert outcome.metrics == ()
    assert outcome.slowest_node is None
    assert "node=" not in " ".join(r.getMessage() for r in caplog.records)


def test_orchestra_config_loads_and_falls_back():
    cfg = load_orchestra_config()
    assert cfg.log_execution is True and cfg.quality_retry_limit == 1
    fallback = load_orchestra_config("does_not_exist.json")
    assert isinstance(fallback, OrchestraConfig)  # defaults, never crash


# ── API integration (no node bypass: routes only call run_orchestra) ─────────
def _register(client, email="api@example.com"):
    r = client.post("/api/auth/register", json=valid_registration(email=email, display_name="Aria Moon"))
    assert r.status_code == 201, r.text


def _make_page_api(client):
    book = client.post("/api/soulbooks", json={"title": "Personal Journal"}).json()
    chapter = client.post(f"/api/soulbooks/{book['id']}/chapters", json={"title": "One"}).json()
    page = client.post(
        f"/api/soulbooks/{book['id']}/chapters/{chapter['id']}/pages", json={"title": "Day"}
    ).json()
    return book, chapter, page


def _fake_ollama(monkeypatch):
    import app.orchestra.mini.engine as mini_engine

    monkeypatch.setattr(mini_engine, "OllamaRuntime", lambda: FakeRuntime())


def test_reflect_endpoint(client, monkeypatch):
    _fake_ollama(monkeypatch)
    _register(client)
    book, chapter, page = _make_page_api(client)
    r = client.post(
        f"/api/soulbooks/{book['id']}/chapters/{chapter['id']}/pages/{page['id']}/reflect"
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["delivered"] is True
    assert body["text"] == GOOD_TEXT
    assert body["metrics"] is None  # debug info hidden from users


def test_close_endpoint_saves_reflects_bookmarks(client, monkeypatch):
    _fake_ollama(monkeypatch)
    _register(client, email="close@example.com")
    book, chapter, page = _make_page_api(client)
    r = client.post(
        f"/api/soulbooks/{book['id']}/chapters/{chapter['id']}/pages/{page['id']}/close",
        json={"content": "Dear Diary...\n\nA gentle day.", "cursor": 12},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reflection"]["delivered"] is True
    assert body["bookmark"]["page_id"] == page["id"]
    assert body["bookmark"]["cursor"] == 12
    # the save happened before the orchestra
    saved = client.get(
        f"/api/soulbooks/{book['id']}/chapters/{chapter['id']}/pages/{page['id']}"
    ).json()
    assert "gentle day" in saved["content"]
    # reopening: the ribbon bookmark is remembered
    bm = client.get("/api/soulbooks/bookmark").json()
    assert bm["page_id"] == page["id"] and bm["cursor"] == 12
    assert bm["book_title"] == "Personal Journal"


def test_bookmark_empty_when_never_closed(client):
    _register(client, email="nobm@example.com")
    assert client.get("/api/soulbooks/bookmark").json() is None
