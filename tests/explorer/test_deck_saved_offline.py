"""Independent Deck application context preserves finite history and pages."""

import json
import socket

import pytest

from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.explorer._deck_session import _DeckSession
from sabueso.explorer._service import _Service


@pytest.fixture(autouse=True)
def no_acquisition(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Opening an original Deck file cannot acquire sources")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


def make_deck():
    item = Card(meta={"card_id": "sabueso:protein:test:z", "entity_type": "protein"})
    return Deck([item] * 83, {"extension": {"value": "Synthetic original workspace"}})


def act(session, name, **args):
    return session.dispatch({"name": name, "revision": session.revision, **args})


def semantic(panel):
    return {
        k: v for k, v in panel.items() if k not in ("revision", "mode", "saved_file")
    }


def test_original_page_metadata_and_nonlinear_history_reopen_independently(
    tmp_path, monkeypatch
):
    session = _DeckSession(make_deck(), tmp_path)
    first = session.panel()
    second = act(session, "deck_next")
    ordered = act(session, "sort", column="label", descending=True)
    selected = act(session, "search", text="protein")
    # Overview is the original root; GUI history also retains a separate branch.
    overview = act(session, "overview")
    act(session, "deck_next")
    third = act(session, "deck_next")
    metadata = act(session, "metadata")
    act(session, "save")
    saved_path = session.saved[0]
    original_bytes = saved_path.read_bytes()
    monkeypatch.setattr(
        Card, "__init__", lambda *a, **k: pytest.fail("no current Card construction")
    )
    service = _Service(tmp_path)
    reopened = service.load_reading(original_bytes)
    assert reopened["mode"] == "saved" and semantic(reopened) == semantic(metadata)
    reopened = act(service.session, "back")
    assert semantic(reopened) == semantic(third)
    assert act(service.session, "deck_previous")["offset"] == 40
    assert act(service.session, "deck_previous")["items"] == overview["items"]
    assert semantic(act(service.session, "back")) == semantic(selected)
    assert semantic(act(service.session, "back")) == semantic(ordered)
    assert semantic(act(service.session, "back")) == semantic(second)
    assert act(service.session, "deck_previous")["items"] == first["items"]
    assert saved_path.read_bytes() == original_bytes


def test_save_and_reopen_then_member_reading_retains_original_outer_return(tmp_path):
    session = _DeckSession(make_deck(), tmp_path)
    selected = act(session, "search", text="protein")
    act(session, "save")
    receipt = session.saved
    assert act(session, "reopen")["mode"] == "saved"
    assert session.saved == receipt
    member = act(session, "open", item_ref=selected["items"][2]["ref"])
    assert member["mode"] == "saved" and member["deck_context"]["entry_position"] == 2
    assert act(session, "deck")["view_ref"] == selected["view_ref"]
    act(session, "save")
    other = _DeckSession.from_saved(session.saved[0], tmp_path)
    assert other.panel()["items"] == selected["items"]


@pytest.mark.parametrize("malformed", ["page", "foreign", "extra", "version", "root"])
def test_resealed_application_context_is_refused_atomically(tmp_path, malformed):
    from sabueso.core.deck_exploration_storage import save_deck_exploration

    root = make_deck().access()
    path = tmp_path / "plain.json"
    application = {
        "format": "sabueso.deck_application@1",
        "metadata_open": False,
        "current": {"view_ref": root.view_ref, "offset": 0},
        "history": [],
    }
    save_deck_exploration(root, path, application=application)
    data = json.loads(path.read_bytes())
    if malformed == "page":
        data["application"]["current"]["offset"] = 1
    elif malformed == "foreign":
        data["application"]["current"]["view_ref"] = "DV_foreign"
    elif malformed == "extra":
        data["application"]["scene"] = {"identity": "invented"}
    elif malformed == "version":
        data["application"]["format"] = "sabueso.deck_application@999"
    else:
        data["application"]["current"]["offset"] = True
    data["bundle_digest"] = digest(
        canonical_json({k: v for k, v in data.items() if k != "bundle_digest"})
    )
    raw = canonical_json(data).encode()
    service = _Service(tmp_path)
    service.session = _DeckSession(make_deck(), tmp_path)
    original = service.panel()
    with pytest.raises(StorageError):
        service.load_reading(raw)
    assert service.panel() == original


def test_native_selection_file_opens_in_application_and_invalid_action_keeps_context(
    tmp_path,
):
    path = tmp_path / "native.json.gz"
    selected = make_deck().access().sort("label").filter("protein")
    selected.save(path, compression="gzip")
    service = _Service(tmp_path)
    panel = service.load_reading(path.read_bytes())
    assert panel["workspace"] == "deck" and panel["view_ref"] == selected.view_ref
    assert act(service.session, "back")["view_ref"] == selected.back().view_ref
    before = service.panel()
    with pytest.raises(ArgumentError):
        act(service.session, "save", extra=True)
    assert service.panel() == before
