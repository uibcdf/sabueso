"""Human presentation retains native values, support and exact navigation."""

import json
import socket
from pathlib import Path

import pytest

from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.explorer._session import _Session


@pytest.fixture(autouse=True)
def no_acquisition(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Presentation must not acquire sources")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


def act(session, name, **arguments):
    return session.dispatch({"name": name, "revision": session.revision, **arguments})


def protein():
    return Card.from_dict(
        json.loads(Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text())
    )


def test_public_protein_overview_opens_original_field_and_exact_trail(tmp_path):
    card = protein()
    before = card.to_dict()
    s = _Session.from_card(card, tmp_path)
    root = s.panel()
    assert root["orientation"]["profile"] == "protein"
    name = root["orientation"]["fields"][0]
    assert name["text"] == card.sections["names"]["canonical_name"]["value"]
    result = act(s, "orientation_field", path="names.canonical_name")
    original = card.sections["names"]["canonical_name"]
    assert s.current.native_payload == original
    assert result["trail"][-1] == {"index": 0, "title": "Card overview"}
    assert act(s, "back_to", history_index=0)["view_ref"] == root["view_ref"]
    assert card.to_dict() == before


def test_sequence_text_positions_are_not_inferred_from_similar_text(tmp_path):
    card = protein()
    s = _Session.from_card(card, tmp_path)
    act(s, "topic", topic="sequence")
    item = next(i for i in s.current.items() if i.label == "Primary sequence")
    act(s, "open", item_ref=item.item_ref)
    value = next(i for i in s.current.items() if i.label == "value")
    text = act(s, "open", item_ref=value.item_ref)
    assert text["full_text"]["kind"] == "sequence"
    assert text["full_text"]["text"] == card.sections["sequence"]["primary"]["value"]
    other = Card()
    other.unknown_stored["sequence"] = text["full_text"]["text"]
    s = _Session.from_card(other, tmp_path)
    act(s, "topic", topic="content")
    item = next(i for i in s.current.items() if i.label == "sequence")
    assert act(s, "open", item_ref=item.item_ref)["full_text"]["kind"] == "text"


def test_mondo_graph_contains_only_native_relationship_rows(tmp_path):
    from sabueso.tools.card.disease import resolve_disease_card
    from sabueso.tools.db.mondo import FixtureMONDOClient

    card = resolve_disease_card(
        "MONDO:0001444", mondo_client=FixtureMONDOClient("temp_data")
    )[0]
    s = _Session.from_card(card, tmp_path)
    panel = act(s, "topic", topic="classification")
    graph = panel["graph"]
    assert graph["rule"] == "retained_relationship_graph@1"
    assert len(graph["edges"]) == len(s.current.items())
    for edge, item in zip(graph["edges"], s.current.items()):
        assert edge == {
            "item_ref": item.item_ref,
            **{
                key: item.cells[key].value
                for key in ("subject_ref", "predicate", "object_ref")
            },
        }
    row = graph["edges"][0]
    original = s.current.item(row["item_ref"]).open().native_payload
    assert act(s, "open", item_ref=row["item_ref"])["orientation"] is None
    assert s.current.native_payload == original


def test_native_filter_uses_backend_cell_and_rejects_client_operand(tmp_path):
    from sabueso.core.source_assertion_store import make_source_assertion

    card = Card()
    for i, value in enumerate([33, 33.0, 9007199254740993, False, None]):
        card.source_assertion_store.add(
            make_source_assertion(
                "unknown.synthetic", value, "Synthetic", str(i), "2026-11-13"
            )
        )
    s = _Session.from_card(card, tmp_path)
    act(s, "topic", topic="sources")
    items = s.current.items()
    # A literal native cell is filtered by its original Python operand; client
    # actions submit only the exact item/column references.
    expected = s.current.filter("label", equals=items[0].cells["label"].value)
    actual = act(s, "filter_cell", item_ref=items[0].item_ref, column="label")
    assert actual["view_ref"] == expected.view_ref
    assert s.current.native_payload == expected.native_payload
    before = s.panel()
    with pytest.raises(ArgumentError):
        act(
            s,
            "filter_cell",
            item_ref=items[0].item_ref,
            column="label",
            equals="foreign",
        )
    assert s.panel() == before


def test_saved_presentation_keeps_original_cells_with_current_construction_forbidden(
    tmp_path, monkeypatch
):
    s = _Session.from_card(protein(), tmp_path)
    act(s, "topic", topic="sequence")
    before = s.panel()
    act(s, "save")
    monkeypatch.setattr(
        Card, "__init__", lambda *a, **k: pytest.fail("No current Card construction")
    )
    reopened = act(s, "reopen")
    assert reopened["items"] == before["items"]
    json.dumps(reopened)


@pytest.mark.parametrize(
    "action",
    [
        {"name": "orientation_field", "path": "unknown.path"},
        {"name": "orientation_field", "path": []},
        {"name": "back_to", "history_index": True},
        {"name": "back_to", "history_index": -1},
        {"name": "back_to", "history_index": 1},
        {"name": "filter_cell", "item_ref": "foreign", "column": "value"},
    ],
)
def test_refused_presentation_request_keeps_exact_prior_reading(tmp_path, action):
    s = _Session.from_card(protein(), tmp_path)
    before = s.panel()
    with pytest.raises(ArgumentError):
        s.dispatch({"revision": s.revision, **action})
    assert s.panel() == before
