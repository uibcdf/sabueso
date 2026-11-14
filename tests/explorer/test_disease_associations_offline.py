"""Native disease statements retain scope, source roles and exact GUI return."""

import socket
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError
from sabueso.explorer._deck_session import _DeckSession
from sabueso.explorer._service import _Service
from sabueso.explorer._session import _Session
from sabueso.explorer._workspace import read_workspace, save_workspace

DATA = Path(__file__).resolve().parents[2] / "temp_data"


def forbidden(*args, **kwargs):
    pytest.fail("Retained disease navigation must not acquire sources")


@pytest.fixture(scope="module")
def originals():
    from devtools.prepare_disease_walkthrough import cards
    from sabueso.tools.db import _http

    with pytest.MonkeyPatch.context() as guard:
        guard.setattr(socket.socket, "connect", forbidden)
        guard.setattr(_http, "_urlopen", forbidden)
        return {key: card.to_dict() for key, card in cards(DATA).items()}


@pytest.fixture(autouse=True)
def no_queries(monkeypatch, originals):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    for name in ("resolve", "disease_targets", "disease_drugs", "refresh_card"):
        monkeypatch.setattr(sabueso, name, forbidden)


def card(originals, name):
    return Card.from_dict(deepcopy(originals[name]))


def session(originals, tmp_path, *, disease="disease"):
    names = [disease, "protein", "molecule", "chagas", disease]
    return _DeckSession(
        Deck(
            [card(originals, name) for name in names],
            meta={
                "purpose": "Public retained disease controls",
                "membership": {
                    originals[disease]["meta"]["card_id"]: {
                        "basis": "Explicit demonstration input, not inferred association"
                    }
                },
            },
        ),
        tmp_path,
    )


def act(s, name, **extra):
    return s.dispatch({"name": name, "revision": s.revision, **extra})


def disease_view(s):
    selection = act(s, "search", text="MONDO:0014221")
    act(s, "open", item_ref=selection["items"][1]["ref"])
    act(s, "topic", topic="associations")
    return selection


def test_public_native_scope_graph_and_all_support_cells(originals, tmp_path):
    s = session(originals, tmp_path)
    before = [deepcopy(raw) for raw in originals.values()]
    disease_view(s)
    view = s.card_session.current
    native = view.native_payload
    panel = s.panel()
    summary = panel["association_scope"]
    assert summary["matched_occurrences"] == native["matched_occurrences"] > 0
    assert summary["context_count"] == len(native["contexts"])
    assert summary["exclusion_count"] == len(native["exclusions"]) > 0
    assert summary["input_occurrences"] == len(native["input_occurrences"])
    assert summary["outcome"] == view.outcome
    assert summary["selection_rows"] == panel["count"]
    for row in panel["items"]:
        fields = {cell["column"] for cell in row["preview"]["cells"]}
        assert {
            "source",
            "channel",
            "identity_basis",
            "support_state",
            "state",
        } <= fields
        assert row["preview"]["complete"]
    graph = panel["graph"]
    assert graph["rule"] == "retained_disease_association_graph@1"
    assert graph["edges"]
    for edge in graph["edges"]:
        item = view.item(edge["item_ref"])
        assert item.kind != "association_context"
        assert {
            key: edge[key] for key in ("subject_ref", "predicate", "object_ref")
        } == {
            key: item.cells[key].value
            for key in ("subject_ref", "predicate", "object_ref")
        }
        assert {"source", "channel", "identity_basis", "support_state"} <= edge.keys()
    assert list(originals.values()) == before


def test_support_and_related_original_card_keep_exact_deck_entry(originals, tmp_path):
    s = session(originals, tmp_path)
    selected = disease_view(s)
    view = s.card_session.current
    row = next(i for i in view.items() if i.kind != "association_context")
    expected = row.explain().native_payload
    parent = s.panel()["view_ref"]
    act(s, "explain", item_ref=row.item_ref)
    assert s.card_session.current.native_payload == expected
    assert act(s, "back")["view_ref"] == parent
    act(s, "related", item_ref=row.item_ref)
    item = next(
        i
        for i in s.card_session.current.items()
        if i._entry.value["role"] == "whole_card_context"
    )
    exact = item._entry.value["candidates"][0]["location"]["card_ref"]
    act(s, "open", item_ref=item.item_ref)
    assert s.panel()["deck_context"]["current_card"]["card_ref"] == exact
    assert s.panel()["deck_context"]["entry_position"] == 4
    act(s, "overview")
    assert s.panel()["profile"] == "protein"
    restored = act(s, "deck")
    assert (
        restored["view_ref"] == selected["view_ref"]
        and restored["items"] == selected["items"]
    )


def test_exact_source_filter_does_not_rewrite_captured_scope(originals, tmp_path):
    s = session(originals, tmp_path)
    disease_view(s)
    original = s.panel()
    row = next(
        i
        for i in s.card_session.current.items()
        if i.kind != "association_context" and isinstance(i.cells["source"].value, str)
    )
    wanted = row.cells["source"].value
    panel = act(s, "filter_cell", item_ref=row.item_ref, column="source")
    assert (
        panel["association_scope"]["matched_occurrences"]
        == original["association_scope"]["matched_occurrences"]
    )
    assert panel["association_scope"]["selection_rows"] == panel["count"]
    assert all(
        i.cells["source"].value == wanted for i in s.card_session.current.items()
    )
    assert act(s, "back")["view_ref"] == original["view_ref"]


def test_chagas_indications_are_original_statements_not_efficacy(originals, tmp_path):
    d = card(originals, "chagas")
    m = card(originals, "molecule")
    s = _Session(d.explore(related_cards=[m]).view("associations"), tmp_path)
    assert s.panel()["association_scope"]["matched_occurrences"] > 0
    rows = [i for i in s.current.items() if i.kind != "association_context"]
    assert rows and all(i.kind == "indication_statement" for i in rows)
    assert all(i.cells["object_ref"].value == "mondo:MONDO:0001444" for i in rows)
    assert "efficacy" in s.panel()["graph"]["scope"]


def test_missing_inputs_and_lookalikes_do_not_become_association_results(
    originals, tmp_path
):
    s = _Session.from_card(card(originals, "disease"), tmp_path)
    panel = act(s, "topic", topic="associations")
    assert panel["association_scope"]["matched_occurrences"] == 0
    assert (
        panel["outcome"]["status"] == "missing_prerequisite" and panel["graph"] is None
    )
    other = Card()
    other.unknown_stored["associations"] = {
        "adapter": "disease_association_exploration@1",
        "contexts": [],
        "matched_occurrences": 1,
    }
    s = _Session.from_card(other, tmp_path)
    assert act(s, "topic", topic="content")["association_scope"] is None


def test_independent_original_workspace_keeps_support_and_filtered_association_scope(
    originals, tmp_path, monkeypatch
):
    s = session(originals, tmp_path)
    selected = disease_view(s)
    row = next(
        i
        for i in s.card_session.current.items()
        if i.kind != "association_context" and isinstance(i.cells["source"].value, str)
    )
    act(s, "filter_cell", item_ref=row.item_ref, column="source")
    original = s.panel()
    item = next(
        i for i in s.card_session.current.items() if i.kind != "association_context"
    )
    act(s, "explain", item_ref=item.item_ref)
    source = s.card_session.current.native_payload
    service = _Service(tmp_path, s)
    path = tmp_path / "association-workspace.json.gz"
    save_workspace(service, path, compression="gzip")
    monkeypatch.setattr(Card, "__init__", forbidden)
    received, report, history = read_workspace(path, tmp_path)
    assert report is None and not history
    assert received.card_session.current.native_payload == source
    restored = act(received, "back")
    assert (
        restored["view_ref"] == original["view_ref"]
        and restored["association_scope"] == original["association_scope"]
    )
    assert restored["graph"] == original["graph"]
    result = act(received, "deck")
    assert (
        result["view_ref"] == selected["view_ref"]
        and result["items"] == selected["items"]
    )


def test_compact_member_labels_and_membership_keep_original_pins_occurrences_and_types(
    originals, tmp_path
):
    d = card(originals, "disease")
    basis = {
        "boolean": False,
        "nothing": None,
        "float": 33.0,
        "integer": 9007199254740993,
        "long": "x" * 2500,
    }
    s = _DeckSession(Deck([d, d], meta={"membership": {d.id: basis}}), tmp_path)
    panel = s.panel()
    for row in panel["items"]:
        assert row["label"] == d.pinned_ref()
        assert row["display_label"] == "disease · mondo:MONDO:0014221"
        assert (
            row["membership_preview"]["state"] == "recorded"
            and not row["membership_preview"]["complete"]
        )
        assert len(row["membership_preview"]["text"]) == 2048
        assert (
            "no occurrence-specific support inferred"
            in row["membership_preview"]["scope"]
        )
    assert panel["items"][0]["ref"] != panel["items"][1]["ref"]
    missing = _DeckSession(Deck([d]), tmp_path).panel()["items"][0]
    assert missing["membership_preview"]["state"] == "not_stated"


def test_support_requires_exact_current_visible_item(originals, tmp_path):
    s = session(originals, tmp_path)
    disease_view(s)
    stale = s.revision
    item = s.panel()["items"][0]["ref"]
    act(s, "back")
    with pytest.raises(ArgumentError):
        s.dispatch({"name": "explain", "revision": stale, "item_ref": item})
    with pytest.raises(ArgumentError):
        act(s, "explain", item_ref=item)


def test_explicit_synthetic_phenotype_graph_preserves_source_direction(tmp_path):
    from devtools.prepare_disease_walkthrough import synthetic_phenotype_control

    card = synthetic_phenotype_control()
    before = card.to_dict()
    s = _Session.from_card(card, tmp_path)
    panel = act(s, "topic", topic="associations")
    (edge,) = panel["graph"]["edges"]
    assert edge["subject_ref"] == "mondo:MONDO:9999999"
    assert edge["predicate"] == "associated_with"
    assert edge["object_ref"] == "hpo:HP:9999999"
    assert edge["source"] == "Synthetic phenotype control"
    assert card.to_dict() == before


def test_unvisited_disease_associations_remain_not_saved_after_original_reopen(
    originals, tmp_path, monkeypatch
):
    s = session(originals, tmp_path)
    disease_view(s)
    service = _Service(tmp_path, s)
    path = tmp_path / "unvisited.json.gz"
    save_workspace(service, path, compression="gzip")
    monkeypatch.setattr(Card, "__init__", forbidden)
    received, _, _ = read_workspace(path, tmp_path)
    act(received, "deck")
    act(received, "overview")
    selected = act(received, "search", text="MONDO:0001444")
    act(received, "open", item_ref=selected["items"][0]["ref"])
    panel = act(received, "topic", topic="associations")
    assert panel["outcome"]["status"] == "not_saved"
    assert panel["association_scope"] is None and panel["graph"] is None
