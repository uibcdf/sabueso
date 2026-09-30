"""The shared network access of source clients (#86): one user agent, and retries only
for transient failures."""

from __future__ import annotations

import ast
import io
import zlib
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from sabueso.tools.db import _http

DB = Path(_http.__file__).parent


def _http_error(code, retry_after=None):
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return HTTPError("https://example.org", code, "status", headers, None)


def _opener(outcomes, seen):
    def fake(request, timeout):
        seen.append(request)
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    return fake


def test_every_client_reaches_the_network_through_http():
    for path in DB.glob("*.py"):
        if path.name == "_http.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "urllib.request":
                names = {alias.name for alias in node.names}
                assert "urlopen" not in names, path.name


def test_requests_name_sabueso(monkeypatch):
    seen = []
    monkeypatch.setattr(_http, "_urlopen", _opener(["ok"], seen))
    assert _http.urlopen("https://example.org/x") == "ok"
    assert seen[0].get_header("User-agent").startswith("Sabueso/")


def test_transient_failures_are_retried_with_backoff(monkeypatch):
    seen, waits = [], []
    outcomes = [_http_error(503), _http_error(429, "3"), "ok"]
    monkeypatch.setattr(_http, "_urlopen", _opener(outcomes, seen))
    assert _http.urlopen("https://example.org/x", sleep=waits.append) == "ok"
    assert len(seen) == 3
    assert waits == [_http.BACKOFF, 3.0]  # Retry-After is honoured


def test_retries_are_bounded(monkeypatch):
    seen = []
    outcomes = [_http_error(502)] * (_http.RETRIES + 1)
    monkeypatch.setattr(_http, "_urlopen", _opener(outcomes, seen))
    with pytest.raises(HTTPError):
        _http.urlopen("https://example.org/x", sleep=lambda s: None)
    assert len(seen) == _http.RETRIES + 1


@pytest.mark.parametrize(
    "error",
    [_http_error(404), _http_error(400), URLError(TimeoutError("timed out"))],
    ids=["not-found", "bad-request", "timeout"],
)
def test_other_failures_reach_the_client_at_once(monkeypatch, error):
    seen = []
    monkeypatch.setattr(_http, "_urlopen", _opener([error], seen))
    with pytest.raises(URLError):
        _http.urlopen("https://example.org/x", sleep=lambda s: None)
    assert len(seen) == 1


def test_a_refused_connection_is_retried(monkeypatch):
    seen = []
    outcomes = [URLError(ConnectionRefusedError("refused")), "ok"]
    monkeypatch.setattr(_http, "_urlopen", _opener(outcomes, seen))
    assert _http.urlopen("https://example.org/x", sleep=lambda s: None) == "ok"


# --- Many requests to one service (#98) ------------------------------------------------


def test_gather_keeps_the_order_and_each_failure_is_its_own():
    from sabueso.core.errors import ConnectorError, RecordNotFoundError

    def call(item):
        if item == "missing":
            raise RecordNotFoundError("no such record")
        if item == "broken":
            raise ConnectorError("down")
        return item.upper()

    items = ["a", "missing", "b", "broken", "c"]
    answers = _http.gather(
        call, items, workers=3, expected=(RecordNotFoundError, ConnectorError)
    )
    assert [item for item, _ in answers] == items
    assert [a for _, a in answers][::2] == ["A", "B", "C"]
    assert isinstance(answers[1][1], RecordNotFoundError)
    assert isinstance(answers[3][1], ConnectorError)


def test_gather_raises_a_fault_that_is_not_a_source_answer():
    def call(item):
        raise KeyError(item)

    with pytest.raises(KeyError):
        _http.gather(call, ["a", "b"], workers=2, expected=(ValueError,))


def test_pace_spaces_the_start_of_requests():
    now, slept = [0.0], []

    def sleep(seconds):
        slept.append(round(seconds, 6))
        now[0] += seconds

    pace = _http.Pace(5.0, sleep=sleep, clock=lambda: now[0])
    for _ in range(4):
        pace.wait()
    assert slept == [0.2, 0.2, 0.2]


# --- What was downloaded: the retrieval archive (#100) ---------------------------------


class _Response:
    def __init__(self, body, status=200, headers=None):
        self.body, self.status = body, status
        self.headers = Message()
        for k, v in (headers or {}).items():
            self.headers[k] = v

    def read(self, *_):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None


def test_nothing_is_archived_unless_asked(tmp_path, monkeypatch):
    monkeypatch.setattr(_http, "_urlopen", lambda r, timeout: _Response(b"{}"))
    with _http.urlopen("https://example.org/a") as resp:
        assert resp.read() == b"{}"
    assert not list(tmp_path.iterdir())


def test_an_answer_is_archived_once_and_read_back_verified(tmp_path, monkeypatch):
    import sabueso
    from sabueso.core.errors import StorageError
    from sabueso.tools.db import _archive

    monkeypatch.setattr(
        _http,
        "_urlopen",
        lambda r, timeout: _Response(b'{"x": 1}', headers={"X-UniProt-Release": "7"}),
    )
    archive = sabueso.RetrievalArchive(tmp_path / "a.db")
    with archive.recording(), _archive.collecting() as made:
        for _ in range(2):
            with _http.urlopen("https://example.org/a") as resp:
                assert resp.read() == b'{"x": 1}'
                assert resp.headers.get("X-UniProt-Release") == "7"
    assert len(made) == 2
    assert archive.stats()["contents"] == 1  # the same content, stored once
    record = archive.get(made[0]["ref"])
    assert record["content"] == b'{"x": 1}' and record["headers"] == {
        "X-UniProt-Release": "7"
    }
    import sqlite3

    with sqlite3.connect(tmp_path / "a.db") as conn:
        conn.execute("UPDATE contents SET body = ?", (zlib.compress(b"tampered"),))
    with pytest.raises(StorageError, match="changed outside Sabueso"):
        archive.get(made[0]["ref"])


def test_a_not_found_is_an_answer_and_is_archived(tmp_path, monkeypatch):
    import sabueso

    def not_found(request, timeout):
        raise HTTPError(
            "https://example.org/b", 404, "no", Message(), io.BytesIO(b"nope")
        )

    monkeypatch.setattr(_http, "_urlopen", not_found)
    archive = sabueso.RetrievalArchive(tmp_path / "a.db")
    with archive.recording():
        with pytest.raises(HTTPError) as caught:
            _http.urlopen("https://example.org/b")
    assert caught.value.code == 404 and caught.value.read() == b"nope"
    assert archive.stats()["records"] == 1


def test_requests_made_by_threads_are_archived_too(tmp_path, monkeypatch):
    import sabueso
    from sabueso.tools.db import _archive

    monkeypatch.setattr(
        _http, "_urlopen", lambda r, timeout: _Response(r.full_url.encode())
    )
    archive = sabueso.RetrievalArchive(tmp_path / "a.db")

    def get(i):
        with _http.urlopen(f"https://example.org/{i}") as resp:
            return resp.read()

    with archive.recording(), _archive.collecting() as made:
        answers = _http.gather(get, range(5), workers=3)
    assert [a for _, a in answers][0] == b"https://example.org/0"
    assert len(made) == 5 and archive.stats()["records"] == 5
