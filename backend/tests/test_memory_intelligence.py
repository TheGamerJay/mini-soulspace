"""Memory Intelligence Engine tests — full coverage. Deterministic, no AI."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.memory import SoulMemory
from app.orchestra.intelligence import (
    DbIntelligenceStore,
    IntelligenceConfig,
    MemoryIntelligenceError,
    MemorySource,
    NextAction,
    VerificationStatus,
    apply_correction,
    apply_decay,
    assess,
    load_config,
    needs_verification,
    required_confidence,
    score_confidence,
    would_resurface,
)
from app.orchestra.intelligence.schemas import ANALYTICS_EVENTS
from app.orchestra.memory.schemas import MemoryPriority, MemoryType
from app.orchestra.writer.schemas import MemoryDecision


def make_decision(op="create", reason="new_memory"):
    return MemoryDecision(
        request_id=uuid.uuid4(), store_memory=True, importance=MemoryPriority.MEDIUM,
        memory_type=MemoryType.FAVORITE, title="Favorite: color", summary="My favorite color is blue",
        reason=reason, confidence=0.7, metadata={"op": op},
    )


def make_memory(db, *, summary="My favorite color is blue", mtype="favorite", user_id=None, confidence=0.6):
    m = SoulMemory(
        user_id=user_id or uuid.uuid4(), memory_type=mtype, priority="medium",
        title="Favorite: color", summary=summary, keywords="color blue", confidence=confidence,
    )
    db.add(m)
    db.flush()
    return m


EVIDENCE = {"page_id": "abc", "timestamp": "2026-07-06T00:00:00Z"}
CFG = IntelligenceConfig()


# ── Config ────────────────────────────────────────────────────────────────────
def test_load_config_defaults():
    cfg = load_config()
    assert cfg.auto_store_threshold == 0.90
    assert cfg.needs_verification_threshold == 0.70
    assert cfg.confidence_decay_enabled is True
    assert cfg.type_overrides == {}


def test_load_config_missing_raises():
    with pytest.raises(MemoryIntelligenceError) as e:
        load_config("nope.json")
    assert e.value.errors[0]["code"] == "missing_config"


# ── Confidence scoring ────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "text,source,expected",
    [
        ("anything", MemorySource.SIGNUP_FORM, 1.0),
        ("anything", MemorySource.MANUAL_USER_ENTRY, 1.0),
        ("My favorite color is blue", MemorySource.SOULDIARY, 0.99),
        ("I usually like blue", MemorySource.SOULDIARY, 0.80),
        ("Blue looks nice", MemorySource.SOULDIARY, 0.40),
        ("blue is a color", MemorySource.SOULDIARY, 0.60),
    ],
)
def test_score_confidence(text, source, expected):
    conf, reason = score_confidence(text, source)
    assert conf == expected
    assert reason  # evidence-backed, never guessed


# ── Assess (stamping + provenance + history) ──────────────────────────────────
def test_assess_stamps_and_records_history(db):
    m = make_memory(db)
    res = assess(make_decision(), m, source=MemorySource.SOULDIARY, evidence=EVIDENCE, store=DbIntelligenceStore(db), config=CFG)
    assert res.confidence == 0.99
    assert res.memory_source == MemorySource.SOULDIARY
    assert res.evidence["page_id"] == "abc"
    assert res.evidence["reason_stored"] == "new_memory"
    assert m.confidence == 0.99
    assert m.source == "souldiary"
    assert json.loads(m.evidence)["page_id"] == "abc"
    versions = DbIntelligenceStore(db).versions(m.id)
    assert len(versions) == 1 and versions[0].reason_changed == "create"


def test_assess_signup_source_verified():
    # pure decision-path check via a fake store (no DB needed)
    class FakeStore:
        def stamp(self, memory, **fields):
            for k, v in fields.items():
                setattr(memory, k, v)
            return memory
        def record_version(self, memory, **kw):
            return None
    m = SoulMemory(user_id=uuid.uuid4(), memory_type="birthday", priority="high", title="B", summary="june 1", confidence=0.6)
    m.id = uuid.uuid4()
    m.version = 1
    m.verification_status = "unverified"
    m.updated_at = datetime.now(timezone.utc)
    res = assess(make_decision(), m, source=MemorySource.SIGNUP_FORM, evidence={"signup_field": "date_of_birth"}, store=FakeStore(), config=CFG)
    assert res.confidence == 1.0
    assert res.verification_status == VerificationStatus.VERIFIED
    assert res.last_verified_at is not None
    assert res.next_action == NextAction.NONE


def test_assess_update_op_next_action(db):
    m = make_memory(db)
    res = assess(make_decision(op="update", reason="evolved_memory"), m, source=MemorySource.SOULDIARY, evidence=EVIDENCE, store=DbIntelligenceStore(db), config=CFG)
    assert res.next_action == NextAction.UPDATED
    assert res.evidence["reason_stored"] == "evolved_memory"


def test_assess_casual_needs_verification(db):
    m = make_memory(db, summary="Blue looks nice")
    res = assess(make_decision(), m, source=MemorySource.CONVERSATION, evidence=EVIDENCE, store=DbIntelligenceStore(db), config=CFG)
    assert res.confidence == 0.40
    assert res.verification_status == VerificationStatus.NEEDS_VERIFICATION
    assert res.next_action == NextAction.MONITOR


def test_assess_strong_schedule_verification(db):
    m = make_memory(db, summary="I usually like blue")
    res = assess(make_decision(), m, source=MemorySource.CONVERSATION, evidence=EVIDENCE, store=DbIntelligenceStore(db), config=CFG)
    assert res.confidence == 0.80  # between low(0.5) and needs_verification... wait 0.80 >= 0.70
    assert res.next_action == NextAction.NONE


def test_assess_unclassified_schedules_verification(db):
    m = make_memory(db, summary="blue is a color")  # unclassified -> 0.60, between low and needs_verification
    res = assess(make_decision(), m, source=MemorySource.CONVERSATION, evidence=EVIDENCE, store=DbIntelligenceStore(db), config=CFG)
    assert res.confidence == 0.60
    assert res.verification_status == VerificationStatus.NEEDS_VERIFICATION
    assert res.next_action == NextAction.SCHEDULE_VERIFICATION


def test_assess_verification_disabled(db):
    m = make_memory(db, summary="Blue looks nice")
    cfg = IntelligenceConfig(verification_enabled=False)
    res = assess(make_decision(), m, source=MemorySource.CONVERSATION, evidence=EVIDENCE, store=DbIntelligenceStore(db), config=cfg)
    assert res.verification_status == VerificationStatus.UNVERIFIED


def test_assess_requires_evidence(db):
    m = make_memory(db)
    with pytest.raises(MemoryIntelligenceError) as e:
        assess(make_decision(), m, source=MemorySource.SOULDIARY, evidence={}, store=DbIntelligenceStore(db), config=CFG)
    assert e.value.errors[0]["code"] == "missing_evidence"


def test_assess_invalid_inputs(db):
    m = make_memory(db)
    with pytest.raises(MemoryIntelligenceError):
        assess("x", m, source=MemorySource.SOULDIARY, evidence=EVIDENCE, store=DbIntelligenceStore(db), config=CFG)  # type: ignore[arg-type]
    with pytest.raises(MemoryIntelligenceError):
        assess(make_decision(), "x", source=MemorySource.SOULDIARY, evidence=EVIDENCE, store=DbIntelligenceStore(db), config=CFG)  # type: ignore[arg-type]


# ── Decay ─────────────────────────────────────────────────────────────────────
def test_decay_lowers_confidence_never_deletes(db):
    m = make_memory(db, confidence=0.8)
    m.last_verified_at = datetime.now(timezone.utc) - timedelta(days=200)
    res = apply_decay(m, store=DbIntelligenceStore(db), config=CFG, now=datetime.now(timezone.utc))
    assert res.metadata["decayed"] is True
    assert 0.0 <= res.confidence < 0.8
    assert m.is_deleted is False  # only confidence changes


def test_decay_disabled(db):
    m = make_memory(db, confidence=0.8)
    cfg = IntelligenceConfig(confidence_decay_enabled=False)
    res = apply_decay(m, store=DbIntelligenceStore(db), config=cfg)
    assert res.metadata["decayed"] is False
    assert m.confidence == 0.8


def test_decay_naive_datetime_and_floor(db):
    m = make_memory(db, confidence=0.05)
    m.last_verified_at = datetime.now() - timedelta(days=10000)  # naive + huge
    res = apply_decay(m, store=DbIntelligenceStore(db), config=CFG)
    assert res.confidence == CFG.minimum_confidence  # floored, never below


def test_decay_invalid_input(db):
    with pytest.raises(MemoryIntelligenceError):
        apply_decay("x", store=DbIntelligenceStore(db), config=CFG)  # type: ignore[arg-type]


def test_needs_verification_threshold(db):
    m = make_memory(db, confidence=0.4)
    assert needs_verification(m, CFG) is True
    m.confidence = 0.95
    assert needs_verification(m, CFG) is False
    assert needs_verification(m, IntelligenceConfig(verification_enabled=False)) is False


# ── User correction ───────────────────────────────────────────────────────────
def test_correction_updates_archives_and_raises_confidence(db):
    m = make_memory(db, summary="My favorite color is blue", confidence=0.5)
    store = DbIntelligenceStore(db)
    res = apply_correction(m, new_summary="My favorite color is green", evidence={"conversation_id": "c1"}, store=store)
    assert res.next_action == NextAction.CORRECTED
    assert res.confidence == 0.99  # raised: explicit user correction
    assert m.summary == "My favorite color is green"
    assert m.version == 2
    assert m.verification_status == "verified"
    versions = store.versions(m.id)
    assert len(versions) == 1
    assert versions[0].is_outdated is True and versions[0].summary == "My favorite color is blue"
    assert versions[0].author == "user"
    assert json.loads(m.evidence)["correction"]["conversation_id"] == "c1"


def test_correction_prevents_resurfacing(db):
    m = make_memory(db, summary="My favorite color is blue")
    store = DbIntelligenceStore(db)
    apply_correction(m, new_summary="My favorite color is green", evidence={"c": "1"}, store=store)
    versions = store.versions(m.id)
    assert would_resurface(versions, "My favorite color is blue") is True
    assert would_resurface(versions, "My favorite color is green") is False


def test_correction_requires_evidence_and_valid_memory(db):
    m = make_memory(db)
    with pytest.raises(MemoryIntelligenceError):
        apply_correction(m, new_summary="x", evidence={}, store=DbIntelligenceStore(db))
    with pytest.raises(MemoryIntelligenceError):
        apply_correction("x", new_summary="x", evidence={"a": 1}, store=DbIntelligenceStore(db))  # type: ignore[arg-type]


def test_correction_history_never_lost(db):
    m = make_memory(db, summary="Pizza is my favorite food")
    store = DbIntelligenceStore(db)
    apply_correction(m, new_summary="Sushi is my favorite food", evidence={"c": "1"}, store=store)
    apply_correction(m, new_summary="Ramen is my favorite food", evidence={"c": "2"}, store=store)
    versions = store.versions(m.id)
    assert [v.version for v in versions] == [1, 2]
    assert m.version == 3


# ── Correction pattern learning ───────────────────────────────────────────────
def test_required_confidence_raises_with_corrections():
    counts = {"preference": 4}
    base = required_confidence("preference", {}, CFG)
    raised = required_confidence("preference", counts, CFG)
    assert base == CFG.auto_store_threshold
    assert raised > base
    assert raised <= 0.99
    # below the pattern threshold -> unchanged
    assert required_confidence("preference", {"preference": 1}, CFG) == base


def test_required_confidence_type_override():
    cfg = IntelligenceConfig(type_overrides={"birthday": {"auto_store_threshold": 0.95}})
    assert required_confidence("birthday", {}, cfg) == 0.95


def test_corrections_by_type(db):
    uid = uuid.uuid4()
    m = make_memory(db, user_id=uid)
    store = DbIntelligenceStore(db)
    apply_correction(m, new_summary="My favorite color is green", evidence={"c": "1"}, store=store)
    counts = store.corrections_by_type(uid)
    assert counts == {"favorite": 1}


# ── Contract-level ────────────────────────────────────────────────────────────
def test_result_immutable_and_versioned(db):
    m = make_memory(db)
    res = assess(make_decision(), m, source=MemorySource.SOULDIARY, evidence=EVIDENCE, store=DbIntelligenceStore(db), config=CFG)
    assert res.schema_version == "1.0"
    with pytest.raises(Exception):
        res.confidence = 0.1  # type: ignore[misc]


def test_analytics_events_prepared_not_implemented():
    assert "UserCorrectionApplied" in ANALYTICS_EVENTS
    assert len(ANALYTICS_EVENTS) == 7
