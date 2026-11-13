"""Application navigation must retain the original readers, quantities and scope."""

import copy
import json
import socket

import pytest
import pyunitwizard as puw

from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.explorer._session import PAGE_SIZE, _Session


@pytest.fixture(autouse=True)
def no_source_queries(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Exploration must not acquire source data")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


def session(tmp_path, nature="protein"):
    card = Card(meta={"entity_type": nature})
    card.unknown_stored["synthetic"] = {
        "<script>alert(1)</script>": "literal text",
        "quantity": {"value": 3, "unit": "nanometer"},
        "false": False,
        "missing": None,
        "many": list(range(PAGE_SIZE + 7)),
    }
    return card, _Session.from_card(card, tmp_path)


def act(s, name, **args):
    return s.dispatch({"name": name, "revision": s.revision, **args})


@pytest.mark.parametrize("nature", ["protein", "small_molecule", "disease", "other"])
def test_generic_topics_and_exact_return_without_mutation(tmp_path, nature):
    card, s = session(tmp_path, nature)
    before = copy.deepcopy(card.to_dict())
    opening = s.panel()
    assert opening["format"] == "sabueso.explorer_panel@1"
    json.dumps(opening)
    content = act(s, "topic", topic="content")
    original_ref = s.current.result_ref
    item = next(i for i in content["items"] if i["label"] == "synthetic")
    act(s, "open", item_ref=item["ref"])
    assert act(s, "back")["result_ref"] == original_ref
    assert act(s, "back")["view_ref"] == opening["view_ref"]
    assert card.to_dict() == before


def test_search_quantity_save_inert_reopen_and_original_return(tmp_path):
    card, s = session(tmp_path)
    before = card.to_dict()
    result = act(s, "search", text="quantity")
    act(s, "open", item_ref=result["items"][0]["ref"])
    original = s.current
    value = original.native_payload
    assert (
        puw.get_value(puw.quantity(value["value"], value["unit"]), to_unit="angstrom")
        == 30
    )
    act(s, "save")
    reopened = act(s, "reopen")
    assert reopened["mode"] == "saved"
    assert s.current.result_ref == original.result_ref
    assert s.current.rows() == original.rows()
    assert s.current.native_payload == {"value": 3, "unit": "nanometer"}
    assert act(s, "back")["view_ref"] == original.view_ref
    fresh = _Session.from_saved(s.saved[0], tmp_path)
    assert fresh.current.native_payload == original.native_payload
    assert card.to_dict() == before


def test_paging_is_bound_to_current_view_and_preserved_by_back(tmp_path):
    _, s = session(tmp_path)
    result = act(s, "search", text="many")
    act(s, "open", item_ref=result["items"][0]["ref"])
    first = s.panel()
    assert len(first["items"]) == PAGE_SIZE and first["has_next"]
    second = act(s, "page", offset=PAGE_SIZE)
    assert len(second["items"]) == 7 and not second["has_next"]
    with pytest.raises(ArgumentError):
        act(s, "open", item_ref=first["items"][0]["ref"])
    act(s, "open", item_ref=second["items"][0]["ref"])
    assert act(s, "back")["offset"] == PAGE_SIZE


@pytest.mark.parametrize(
    "action",
    [
        {"name": "open", "item_ref": "foreign"},
        {"name": "topic", "topic": "unknown"},
        {"name": "page", "offset": True},
        {"name": "page", "offset": -1},
        {"name": "page", "offset": PAGE_SIZE * 100},
        {"name": "search", "text": ""},
        {"name": "search", "text": []},
        {"name": "back", "extra": "ignored?"},
        {"name": "__getattribute__"},
        {"name": []},
        {"name": "reopen"},
    ],
)
def test_refused_action_preserves_reading(tmp_path, action):
    _, s = session(tmp_path)
    before = s.panel()
    with pytest.raises(ArgumentError):
        s.dispatch({"revision": s.revision, **action})
    assert s.panel() == before


def test_stale_request_and_tampered_saved_reading_are_refused(tmp_path):
    _, s = session(tmp_path)
    old = s.revision
    act(s, "topic", topic="content")
    with pytest.raises(ArgumentError):
        s.dispatch({"name": "overview", "revision": old})
    act(s, "save")
    s.saved[0].write_bytes(b"not the captured reading")
    before = s.current
    with pytest.raises(StorageError):
        act(s, "reopen")
    assert s.current is before


def test_history_limit_refuses_navigation_without_discarding_return_context(tmp_path):
    from sabueso.explorer._session import HISTORY_LIMIT

    _, s = session(tmp_path)
    s.history = [(s.current, 0, 0)] * HISTORY_LIMIT
    before = s.panel()
    with pytest.raises(ArgumentError):
        act(s, "overview")
    assert s.panel() == before and len(s.history) == HISTORY_LIMIT
    assert act(s, "back")["can_back"]


def test_complete_unicode_text_is_readable_in_bound_pages(tmp_path):
    from sabueso.explorer._session import TEXT_SIZE

    card = Card()
    text = "<script>literal</script> α🧬" * 400
    card.unknown_stored["long"] = text
    s = _Session.from_card(card, tmp_path)
    result = act(s, "search", text="long")
    first = act(s, "open", item_ref=result["items"][0]["ref"])
    complete = first["full_text"]["text"]
    offset = TEXT_SIZE
    while offset < len(text):
        page = act(s, "text_page", offset=offset)
        complete += page["full_text"]["text"]
        offset += TEXT_SIZE
    assert complete == text
    act(s, "save")
    assert act(s, "reopen")["full_text"]["text"] == text[:TEXT_SIZE]
    assert act(s, "back")["full_text"]["offset"] == offset - TEXT_SIZE
