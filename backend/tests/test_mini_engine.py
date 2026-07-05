"""Mini Engine tests — full coverage. Runtime is faked; no network, no Ollama."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import httpx
import pytest

from app.orchestra.context import build as context_build
from app.orchestra.guardian import evaluate as guardian_eval
from app.orchestra.memory.schemas import RetrievalResult
from app.orchestra.mini import (
    CandidateResponse,
    MiniEngineError,
    OllamaRuntime,
    RuntimeResponse,
    RuntimeTimeout,
    RuntimeUnavailable,
    generate,
)
from app.orchestra.planner import plan
from app.orchestra.prompt import build as prompt_build
from app.orchestra.prompt.schemas import ModelRole
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

CONTENT = "pineapple lighthouse xylophone calm steady day"


def make_prompt(content: str = CONTENT):
    now = datetime.now(timezone.utc)
    req = OrchestraRequest(
        request_id=uuid.uuid4(),
        user=OrchestraUser(id=uuid.uuid4(), display_name="Aria", timezone="UTC", preferred_language="en"),
        book=OrchestraBook(id=uuid.uuid4(), title="Journal", cover_style="classic", book_type="classic", last_opened_at=now),
        chapter=OrchestraChapter(id=uuid.uuid4(), title="Ch1", chapter_number=1),
        page=OrchestraPage(id=uuid.uuid4(), title="Day", page_number=1, content_format="markdown", timezone=None),
        page_content=content,
        statistics=OrchestraStatistics(word_count=len(content.split()), character_count=len(content)),
        timestamps=OrchestraTimestamps(page_created_at=now, page_updated_at=now, book_last_opened_at=now),
        language="en", timezone="UTC",
        session=OrchestraSession(session_id=None, started_at=now, last_opened_at=now),
    )
    g = guardian_eval(req)
    retrieval = RetrievalResult(request_id=req.request_id, retrieved=(), count=0, blocked=False, reason="none")
    planner = plan(req, g, retrieval)
    ctx = context_build(req, g, retrieval, planner)
    return prompt_build(ctx)


def ok_response(model, dur=1234):
    return RuntimeResponse(text="A gentle reflection.", model=model, prompt_tokens=10, completion_tokens=5, finish_reason="stop", duration_ms=dur)


class OkRuntime:
    def __init__(self, dur=1234):
        self.dur = dur
    def generate(self, model, messages, params, timeout_s):
        return ok_response(model, self.dur)


class TimeoutRuntime:
    def generate(self, *a):
        raise RuntimeTimeout("slow")


class UnavailableRuntime:
    def generate(self, *a):
        raise RuntimeUnavailable("down")


class EmptyRuntime:
    def generate(self, model, *a):
        return RuntimeResponse(text="   ", model=model)


class MalformedRuntime:
    def generate(self, *a):
        return None


class FlakyRuntime:
    def __init__(self, fail_times):
        self.fail_times = fail_times
        self.calls = 0
    def generate(self, model, messages, params, timeout_s):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeUnavailable("temporary")
        return ok_response(model)


# ── Success + resolution ──────────────────────────────────────────────────────
def test_successful_generation_and_service_resolution():
    res = generate(make_prompt(), runtime=OkRuntime(), retries=0)
    assert isinstance(res, CandidateResponse)
    assert res.response_text == "A gentle reflection."
    assert res.service_name == "mini_core"
    assert res.service_display_name == "Mini Core"
    assert res.model_used == "qwen3:14b"
    assert res.token_counts.total == 15
    assert res.finish_reason == "stop"
    assert res.generation_time_ms == 1234
    assert res.metadata["retry_count"] == 0
    assert res.metadata["attempts"] == 1


def test_generation_time_falls_back_to_elapsed():
    res = generate(make_prompt(), runtime=OkRuntime(dur=0), retries=0)
    assert res.generation_time_ms >= 0


def test_missing_service():
    prompt = make_prompt().model_copy(update={"model_role": ModelRole.VISION})
    with pytest.raises(MiniEngineError) as e:
        generate(prompt, runtime=OkRuntime(), retries=0)
    assert e.value.code == "missing_service"


def test_missing_config():
    with pytest.raises(MiniEngineError) as e:
        generate(make_prompt(), runtime=OkRuntime(), retries=0, services_path="does_not_exist.json")
    assert e.value.code == "missing_config"


def test_invalid_input():
    with pytest.raises(MiniEngineError) as e:
        generate("not a prompt", runtime=OkRuntime())  # type: ignore[arg-type]
    assert e.value.code == "invalid_input"


# ── Failure + retry ───────────────────────────────────────────────────────────
def test_timeout_no_retry():
    with pytest.raises(MiniEngineError) as e:
        generate(make_prompt(), runtime=TimeoutRuntime(), retries=0)
    assert e.value.code == "timeout"


def test_runtime_unavailable_no_retry():
    with pytest.raises(MiniEngineError) as e:
        generate(make_prompt(), runtime=UnavailableRuntime(), retries=0)
    assert e.value.code == "runtime_unavailable"


def test_retry_success():
    flaky = FlakyRuntime(fail_times=1)
    res = generate(make_prompt(), runtime=flaky, retries=1)
    assert res.response_text == "A gentle reflection."
    assert res.metadata["retry_count"] == 1
    assert res.metadata["attempts"] == 2


def test_retry_failure():
    with pytest.raises(MiniEngineError) as e:
        generate(make_prompt(), runtime=UnavailableRuntime(), retries=2)
    assert e.value.code == "retry_failure"


def test_malformed_runtime_response():
    with pytest.raises(MiniEngineError) as e:
        generate(make_prompt(), runtime=MalformedRuntime(), retries=0)
    assert e.value.code == "malformed_runtime_response"


def test_empty_response():
    with pytest.raises(MiniEngineError) as e:
        generate(make_prompt(), runtime=EmptyRuntime(), retries=0)
    assert e.value.code == "empty_response"


# ── Contract-level ────────────────────────────────────────────────────────────
def test_candidate_is_immutable():
    res = generate(make_prompt(), runtime=OkRuntime(), retries=0)
    with pytest.raises(Exception):
        res.response_text = "hacked"  # type: ignore[misc]


def test_metrics_present():
    res = generate(make_prompt(), runtime=OkRuntime(), retries=0)
    for key in ("retry_count", "attempts", "prompt_chars", "response_chars", "timeout_ms"):
        assert key in res.metadata


def test_no_raw_payload_or_journal_leak():
    res = generate(make_prompt(CONTENT), runtime=OkRuntime(), retries=0)
    assert not hasattr(res, "raw")
    assert "raw" not in res.metadata
    # journal content must never appear in the downstream metadata
    assert "pineapple lighthouse xylophone" not in str(res.metadata)


# ── Ollama runtime (sealed connector) ─────────────────────────────────────────
class _FakeResp:
    def __init__(self, payload, status_error=False):
        self._payload = payload
        self._status_error = status_error
    def raise_for_status(self):
        if self._status_error:
            raise httpx.HTTPStatusError("500", request=None, response=None)
    def json(self):
        return self._payload


def test_ollama_runtime_success(monkeypatch):
    payload = {
        "message": {"content": "Hello from the model."}, "model": "qwen3:14b",
        "prompt_eval_count": 12, "eval_count": 7, "done_reason": "stop", "total_duration": 2_000_000,
    }
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _FakeResp(payload))
    rr = OllamaRuntime("http://localhost:11434/").generate("qwen3:14b", [{"role": "user", "content": "hi"}], {}, 5.0)
    assert rr.text == "Hello from the model."
    assert rr.prompt_tokens == 12
    assert rr.completion_tokens == 7
    assert rr.duration_ms == 2


def test_ollama_runtime_timeout(monkeypatch):
    def boom(*a, **k):
        raise httpx.TimeoutException("timed out")
    monkeypatch.setattr(httpx, "post", boom)
    with pytest.raises(RuntimeTimeout):
        OllamaRuntime().generate("m", [], {}, 1.0)


def test_ollama_runtime_unavailable(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("refused")
    monkeypatch.setattr(httpx, "post", boom)
    with pytest.raises(RuntimeUnavailable):
        OllamaRuntime().generate("m", [], {}, 1.0)


def test_ollama_runtime_http_status_error(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _FakeResp({}, status_error=True))
    with pytest.raises(RuntimeUnavailable):
        OllamaRuntime().generate("m", [], {}, 1.0)
