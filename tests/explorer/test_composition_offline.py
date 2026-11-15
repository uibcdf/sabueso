"""Native packet composition keeps mandatory final admission and original bytes."""

import json
import socket

import pytest

from sabueso.core import card_exploration_storage as card_storage
from sabueso.core import deck_exploration_storage as deck_storage
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import StorageError
from sabueso.explorer import _workspace
from sabueso.explorer._deck_session import _DeckSession
from sabueso.explorer._service import _Service
from sabueso.explorer._session import _Session


@pytest.fixture(autouse=True)
def no_sources(monkeypatch):
    monkeypatch.setattr(
        socket.socket,
        "connect",
        lambda *a, **k: pytest.fail("Composition cannot acquire sources"),
    )


def context(tmp_path, deck):
    card = Card()
    card.unknown_stored["synthetic"] = {
        "false": False,
        "missing": None,
        "float": 33.0,
        "integer": 9007199254740993,
        "quantity": {"value": [1.0, 2.0], "unit": "nanometer"},
    }
    if deck:
        return _DeckSession(
            Deck([card, Card(), card], {"purpose": "Synthetic composition control"}),
            tmp_path,
        )
    session = _Session.from_card(card, tmp_path)
    session.dispatch(
        {"name": "topic", "topic": "content", "revision": session.revision}
    )
    return session


@pytest.mark.parametrize("deck", [False, True])
def test_workspace_embeds_the_same_native_packets_as_independent_saving(tmp_path, deck):
    session = context(tmp_path, deck)
    native_path, workspace_path = tmp_path / "native", tmp_path / "workspace"
    if deck:
        session._save(native_path)
        expected = _workspace._decode(native_path.read_bytes())
        # A live Deck save visits fresh overview nodes. Reopen the literal
        # original when checking byte preservation, not a second live capture.
        session = _DeckSession.from_saved(native_path, tmp_path)
    else:
        card_storage.save_exploration(session.current, native_path)
        expected = json.loads(native_path.read_bytes())
    service = _Service(tmp_path, session)
    _workspace.save_workspace(service, workspace_path, compression="none")
    saved = json.loads(workspace_path.read_bytes())
    components = saved["decks" if deck else "cards"]
    assert list(components.values()) == [expected]
    restored, _, _ = _workspace.read_workspace(workspace_path, tmp_path)
    assert restored.panel()["view_ref"] == session.panel()["view_ref"]
    assert restored.panel()["items"] == session.panel()["items"]


@pytest.mark.parametrize("writer", ["card", "deck", "workspace_card", "workspace_deck"])
def test_final_admission_rejects_resealed_bad_native_components_before_publication(
    tmp_path, monkeypatch, writer
):
    session = context(tmp_path, writer in ("deck", "workspace_deck"))
    service = _Service(tmp_path, session)
    path = tmp_path / "caller-owned"
    path.write_bytes(b"original caller bytes")
    before = service.panel()
    prepare = card_storage._prepare_bundle

    def forged(*args, **kwargs):
        bundle = prepare(*args, **kwargs)
        bundle["foreign_component_declaration"] = "Synthetic resealed substitution"
        return card_storage._seal(bundle)

    monkeypatch.setattr(card_storage, "_prepare_bundle", forged)
    monkeypatch.setattr(deck_storage, "_prepare_card_bundle", forged)
    monkeypatch.setattr(_workspace, "prepare_card_bundle", forged)
    with pytest.raises(StorageError):
        if writer == "card":
            card_storage.save_exploration(session.current, path, overwrite=True)
        elif writer == "deck":
            deck_storage.save_deck_exploration(session.current, path, overwrite=True)
        else:
            _workspace.save_workspace(service, path, overwrite=True)
    assert path.read_bytes() == b"original caller bytes"
    assert service.panel() == before
    assert not list(tmp_path.glob(".sabueso-*"))
