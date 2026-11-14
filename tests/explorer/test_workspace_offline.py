"""Original workspace composition preserves native meaning and exact UI context."""

import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.explorer._deck_session import _DeckSession
from sabueso.explorer._service import _Service
from sabueso.explorer._session import _Session
from sabueso.explorer._workspace import read_workspace, save_workspace
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

DATA = Path(__file__).resolve().parents[2] / "temp_data"


@pytest.fixture(autouse=True)
def no_sources(monkeypatch):
    from sabueso.tools.db import _http

    monkeypatch.setattr(
        _http,
        "_urlopen",
        lambda *a, **k: pytest.fail("Original workspace cannot query live sources"),
    )
    monkeypatch.setattr(
        socket.socket,
        "connect",
        lambda *a, **k: pytest.fail(
            "Original workspace cannot open network connections"
        ),
    )


def act(session, name, **args):
    return session.dispatch({"name": name, "revision": session.revision, **args})


def fixture_service(tmp_path):
    native = EntityResolver(
        FixtureUniProtClient(DATA), rcsb_client=FixtureRCSBClient(DATA)
    )
    return _Service(
        tmp_path,
        resolver=lambda query, **options: sabueso.resolve(
            query, **options, resolver=native
        ),
    )


def query(service, kind, text):
    return service.resolve(
        {
            "kind": kind,
            "query": text,
            "revision": service.session.revision if service.session else "",
            "resolution_revision": service.resolution.revision
            if service.resolution
            else "",
        }
    )


def synthetic_session(tmp_path):
    card = Card()
    card.unknown_stored["original"] = {
        "values": list(range(90)),
        "text": "α🧬" * 5000,
        "false": False,
        "null": None,
        "float": 33.0,
        "integer": 9007199254740993,
    }
    return _Session.from_card(card, tmp_path)


def semantic(panel):
    return {
        k: v for k, v in panel.items() if k not in ("revision", "mode", "saved_file")
    }


def test_native_card_navigation_map_never_changes_original_bytes(tmp_path):
    from sabueso.core.card_exploration_storage import save_exploration

    s = synthetic_session(tmp_path)
    root = s.current
    s.dispatch({"name": "topic", "topic": "content", "revision": s.revision})
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    save_exploration(s.current, first)
    refs = {}
    save_exploration(s.current, second, _navigation_refs=refs)
    assert first.read_bytes() == second.read_bytes()
    assert id(root) in refs and id(s.current) in refs


@pytest.mark.parametrize("compression", ["none", "gzip", "zstd"])
def test_original_card_pages_and_history_restore_independently(
    tmp_path, monkeypatch, compression
):
    service = _Service(tmp_path, synthetic_session(tmp_path))
    s = service.session
    initial = s.panel()
    items = act(s, "topic", topic="content")
    act(
        s,
        "open",
        item_ref=next(i for i in items["items"] if i["label"] == "original")["ref"],
    )
    act(
        s,
        "open",
        item_ref=next(i for i in s.panel()["items"] if i["label"] == "values")["ref"],
    )
    page = act(s, "page", offset=40)
    act(s, "open", item_ref=page["items"][0]["ref"])
    prior = s.current.native_payload
    path = tmp_path / "workspace"
    receipt = save_workspace(service, path, compression=compression)
    raw = path.read_bytes()

    def forbidden(*a, **k):
        pytest.fail(
            "Original reopening cannot construct current Cards or rerun queries"
        )

    monkeypatch.setattr(Card, "__init__", forbidden)
    monkeypatch.setattr(Deck, "__init__", forbidden)
    monkeypatch.setattr(sabueso, "resolve", forbidden)
    restored, resolution, history = read_workspace(
        path, tmp_path, receipt["bundle_digest"]
    )
    assert (
        restored.current.native_payload == prior and restored.explorer.mode == "saved"
    )
    assert resolution is None and history == []
    assert act(restored, "back")["offset"] == 40
    assert act(restored, "back")["view_ref"] == s.history[-2][0].view_ref
    assert act(restored, "back_to", history_index=0)["view_ref"] == initial["view_ref"]
    assert path.read_bytes() == raw


def test_original_query_decisions_choices_and_reading_return_are_inert(
    tmp_path, monkeypatch
):
    service = fixture_service(tmp_path)
    pdb = query(service, "pdb", "1TCD")
    protein = query(service, "uniprot", "P52270")
    sources = act(service.session, "topic", topic="sources")
    act(service.session, "open", item_ref=sources["items"][0]["ref"])
    current = service.session.current.native_payload
    path = tmp_path / "query.json.gz"
    save_workspace(service, path)
    monkeypatch.setattr(
        Card, "__init__", lambda *a, **k: pytest.fail("No current construction")
    )
    restored = _Service(tmp_path)
    panel = restored.load_reading(path.read_bytes())
    assert (
        restored.session.current.native_payload == current and panel["mode"] == "saved"
    )
    assert (
        restored.resolution.panel()["original_text"]
        == protein["resolution"]["original_text"]
    )
    assert restored.resolution.panel()["mode"] == "saved"
    previous = restored.return_query(
        {
            "revision": restored.session.revision,
            "resolution_revision": restored.resolution.revision,
        }
    )
    assert previous["resolution"]["original_text"] == pdb["resolution"]["original_text"]
    assert previous["resolution"]["choices"] == pdb["resolution"]["choices"]
    assert previous["panel"] is None


def test_deck_entry_card_trail_and_outer_page_survive(tmp_path, monkeypatch):
    card = Card(meta={"card_id": "sabueso:protein:test:one", "entity_type": "protein"})
    card.unknown_stored["original"] = {"value": 33.0, "unit": "nanometer"}
    service = _Service(
        tmp_path,
        _DeckSession(Deck([card] * 83, {"extension": "Original workspace"}), tmp_path),
    )
    page = act(service.session, "deck_next")
    act(service.session, "open", item_ref=page["items"][2]["ref"])
    act(service.session, "topic", topic="content")
    item = next(
        i for i in service.session.card_session.current.items() if i.label == "original"
    )
    act(service.session, "open", item_ref=item.item_ref)
    expected = service.session.card_session.current.native_payload
    path = tmp_path / "deck-workspace.json.gz"
    save_workspace(service, path)
    monkeypatch.setattr(
        Card, "__init__", lambda *a, **k: pytest.fail("No current construction")
    )
    restored, _, _ = read_workspace(path, tmp_path)
    assert restored.card_session.current.native_payload == expected
    assert restored.entry_position == 42
    assert act(restored, "deck")["items"] == page["items"]
    assert restored.panel()["offset"] == 40
    assert act(restored, "deck_previous")["offset"] == 0


@pytest.mark.parametrize(
    "change", ["format", "component", "navigation", "page", "extra", "digest"]
)
def test_workspace_substitutions_are_refused_before_replacing_reading(tmp_path, change):
    service = _Service(tmp_path, synthetic_session(tmp_path))
    path = tmp_path / "plain.json"
    save_workspace(service, path, compression="none")
    bundle = json.loads(path.read_bytes())
    if change == "format":
        bundle["format"] = "sabueso.explorer_workspace@999"
    elif change == "component":
        bundle["current"]["session"]["current"]["component"] = "foreign"
    elif change == "navigation":
        bundle["current"]["session"]["current"]["navigation_ref"] = "missing"
    elif change == "page":
        bundle["current"]["session"]["current"]["offset"] = True
    elif change == "extra":
        bundle["model"] = {"identity": "invented"}
    else:
        bundle["bundle_digest"] = "sha256:" + "0" * 64
    if change != "digest":
        bundle["bundle_digest"] = digest(
            canonical_json({k: v for k, v in bundle.items() if k != "bundle_digest"})
        )
    before = service.panel()
    with pytest.raises(StorageError):
        service.load_reading(canonical_json(bundle).encode())
    assert service.panel() == before


def test_workspace_save_failure_preserves_original_and_leaves_no_partial_file(
    tmp_path, monkeypatch
):
    from sabueso.explorer import _workspace

    service = _Service(tmp_path, synthetic_session(tmp_path))
    path = tmp_path / "caller.json.gz"
    path.write_bytes(b"caller-owned")
    with pytest.raises(StorageError):
        save_workspace(service, path)
    assert path.read_bytes() == b"caller-owned"
    before = service.panel()

    def failed_write(*args, **kwargs):
        raise OSError("Synthetic interrupted encoder")

    monkeypatch.setattr(_workspace.transport, "write", failed_write)
    with pytest.raises(StorageError, match="Synthetic interrupted encoder"):
        save_workspace(service, path, overwrite=True)
    assert path.read_bytes() == b"caller-owned" and service.panel() == before
    assert not list(tmp_path.glob(".sabueso-workspace-*"))


def test_resealed_choice_without_original_source_basis_is_refused(tmp_path):
    service = fixture_service(tmp_path)
    query(service, "pdb", "1TCD")
    path = tmp_path / "query.json"
    save_workspace(service, path, compression="none")
    bundle = json.loads(path.read_bytes())
    bundle["current"]["resolution"]["choices"][0]["value"]["basis"] = {
        "entity_ref": "sabueso:protein:uniprot:P52270",
        "reason": "A matching label is not a source declaration",
    }
    bundle["bundle_digest"] = digest(
        canonical_json({k: v for k, v in bundle.items() if k != "bundle_digest"})
    )
    before = service.response(service.panel())
    with pytest.raises(StorageError, match="source-declared basis"):
        service.load_reading(canonical_json(bundle).encode())
    assert service.response(service.panel()) == before


def test_unavailable_destination_keeps_original_uncertainty_and_back(tmp_path):
    from sabueso.tools.db.mondo import FixtureMONDOClient

    card = sabueso.resolve_disease_card(
        "MONDO:0001444", mondo_client=FixtureMONDOClient(DATA)
    )[0]
    service = _Service(tmp_path, _Session.from_card(card, tmp_path))
    reading = act(service.session, "topic", topic="classification")
    act(service.session, "related", item_ref=reading["items"][0]["ref"])
    links = service.panel()
    target = next(i for i in links["items"] if i["label"].startswith("Object"))
    unknown = act(service.session, "open", item_ref=target["ref"])
    assert service.session.explorer is None
    assert unknown["outcome"]["status"] == "context_not_supplied"
    path = tmp_path / "unknown.json.gz"
    save_workspace(service, path)
    restored, _, _ = read_workspace(path, tmp_path)
    assert restored.explorer is None
    assert restored.panel()["outcome"] == unknown["outcome"]
    assert restored.panel()["view_ref"] == unknown["view_ref"]
    previous = act(restored, "back")
    assert previous["view_ref"] == links["view_ref"]
    assert restored.explorer is not None


def test_fresh_headless_workspace_reading_has_no_optional_gui_or_source_work(tmp_path):
    service = _Service(tmp_path, synthetic_session(tmp_path))
    path = tmp_path / "workspace.json.gz"
    save_workspace(service, path)
    code = """
import sys
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.explorer._workspace import read_workspace
def forbidden(*a,**k):raise AssertionError('current construction')
Card.__init__=Deck.__init__=forbidden
session,resolution,history=read_workspace(sys.argv[1],sys.argv[2])
assert session.explorer.mode=='saved'
assert not any(n in sys.modules for n in ('PySide6','aiohttp','molsysviewer','molsysmt'))
print('inert original workspace received')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(path), str(tmp_path)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
