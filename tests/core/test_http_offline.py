"""The shared network access of source clients (#86): one user agent, and retries only
for transient failures."""

from __future__ import annotations

import ast
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
