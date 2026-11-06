"""Retained-cell display filtering preserves scientific uncertainty and history."""

import gzip
import hashlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest
import pyunitwizard as puw

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_display_filter_v2 import FORMAT, RULE
from sabueso.core.card_exploration_storage import _restore, _seal
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.snapshot import canonical_json

ORIGINAL = Path(__file__).parent / "data/display_filter_noop_sdk187.json.gz"
ORIGINAL_SHA = "d806c3802dbfab562f1951baa62fef3aa9f9c9f5bb58ad27d97d165401d54225"


def forbidden(*args, **kwargs):
    raise AssertionError("No provider request, current science or rebuilding")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def original():
    raw = ORIGINAL.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ORIGINAL_SHA
    packet = json.loads(gzip.decompress(raw))
    assert packet["producer"]["sabueso_version"] == "0.14.0+187.g6bdac1f"
    return packet


@pytest.fixture(scope="module")
def valid_packet(tmp_path_factory):
    saved = sabueso.read_exploration(ORIGINAL)
    path = tmp_path_factory.mktemp("filter-packet") / "view.json"
    saved.filter("structure_ref", equals="pdb:1SUX").save(path)
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(params=["live", "saved"])
def view(request, original):
    if request.param == "saved":
        return sabueso.read_exploration(ORIGINAL)
    data = original["cards"][original["inputs"][0]]["data"]
    return (
        Card.from_dict(deepcopy(data))
        .explore()
        .answer(
            "region_coverage",
            options={"sequence_ref": "uniprot:P52270", "region": [96]},
        )
    )


def test_exact_filter_keeps_underlying_result_unknown_and_original_values(view):
    assert view.outcome["status"] == "not_computed" and len(view.items()) == 7
    native = view.native_payload
    wire = canonical_json(view._selection._scientific.wire)
    selected = view.filter("structure_ref", equals="pdb:1SUX")
    assert [item.label for item in selected.items()] == ["pdb:1SUX"]
    assert selected.outcome == view.outcome
    assert selected.result_ref == view.result_ref
    assert selected.native_payload == native
    assert canonical_json(selected._selection._scientific.wire) == wire
    assert selected.back() is view
    assert selected._display_request["filter_policy"] == RULE
    assert "1 matching retained items" in str(selected)
    assert "scientific status remains not_computed" in selected._repr_html_()


def test_empty_and_chained_display_selection_never_become_negative_science(view):
    selected = view.filter("structure_ref", equals="pdb:ABSENT")
    assert len(selected.items()) == 0 and len(selected.native_payload["items"]) == 7
    assert selected.outcome == view.outcome
    assert "0 matching retained items" in str(selected)
    again = selected.table().sort("structure_ref").filter("method", equals="X-ray")
    assert len(again.items()) == 0 and again.outcome == view.outcome
    assert again.back().back().back() is selected


def test_quantity_filter_uses_original_units_without_accepting_coordinates(view):
    selected = view.filter("resolution", equals=puw.quantity(0.2, "nanometer"))
    assert {item.label for item in selected.items()} == {
        "pdb:1CI1",
        "pdb:1SUX",
        "pdb:2V5B",
    }
    assert selected.outcome == view.outcome


def test_quantity_filter_roundtrip_keeps_units_and_uncertainty(view, tmp_path):
    selected = view.filter("resolution", equals=puw.quantity(0.2, "nanometer"))
    path = tmp_path / "quantity.json.gz"
    selected.save(path, compression="gzip")
    saved = sabueso.read_exploration(path)
    assert {item.label for item in saved.items()} == {
        item.label for item in selected.items()
    }
    assert saved.outcome == view.outcome
    assert puw.get_value(
        saved._display_request["equals"], to_unit="angstrom"
    ) == pytest.approx(2)


def test_shared_payload_stays_inside_one_explicit_filter_envelope(
    view, tmp_path, monkeypatch
):
    from sabueso.core import card_exploration_shared_values_v1 as shared

    pack = shared.pack
    monkeypatch.setattr(
        shared,
        "pack",
        lambda bundle, limit: pack(bundle, limit, threshold=0, min_saving=-1000000000),
    )
    selected = view.filter("structure_ref", equals="pdb:1SUX")
    path = tmp_path / "shared.json"
    selected.save(path)
    packet = json.loads(path.read_text(encoding="utf-8"))
    assert packet["format"] == FORMAT and packet["payload"]["format"] == shared.FORMAT
    saved = sabueso.read_exploration(path)
    assert len(saved.items()) == 1 and saved.outcome == view.outcome
    assert saved.validation["payload_storage_format"] == shared.FORMAT
    second = tmp_path / "second.json"
    saved.save(second)
    assert (
        json.loads(second.read_text(encoding="utf-8"))["payload"]["format"]
        == shared.FORMAT
    )
    assert len(sabueso.read_exploration(second).items()) == 1


def test_equal_structure_labels_keep_distinct_original_declarations(original):
    data = deepcopy(original["cards"][original["inputs"][0]]["data"])
    card = Card.from_dict(data)
    duplicate = deepcopy(
        next(
            r
            for r in card.relationship_store.store.values()
            if r["object_ref"] == "pdb:1SUX"
        )
    )
    duplicate["id"] += "_synthetic_separate_declaration"
    card.relationship_store.add(duplicate)
    view = card.explore().answer(
        "region_coverage",
        options={"sequence_ref": "uniprot:P52270", "region": [96]},
    )
    selected = view.filter("structure_ref", equals="pdb:1SUX")
    assert (
        len(selected.items()) == 2
        and len({item.item_ref for item in selected.items()}) == 2
    )
    assert selected.outcome == view.outcome


@pytest.mark.parametrize(
    "column,value", [("unknown", "x"), ("structure_ref", False), ("resolution", 2)]
)
def test_invalid_operands_still_fail_before_selection(view, column, value):
    with pytest.raises(ArgumentError):
        view.filter(column, equals=value)


def test_unavailable_view_without_retained_rows_refuses_explicitly():
    view = Card(meta={"entity_type": "protein"}).explore().view("structures")
    assert not view.items()
    with pytest.raises(ArgumentError, match="no retained rows"):
        view.filter("structure_ref", equals="pdb:1SUX")


def test_actual_prior_noop_keeps_original_membership_and_resaves(
    original, tmp_path, monkeypatch
):
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(Card, "__init__", forbidden)
    saved = sabueso.read_exploration(ORIGINAL, original["bundle_digest"])
    assert len(saved.items()) == 7 and saved._display_request is None
    assert saved.outcome["status"] == "not_computed"
    path = tmp_path / "original.json.gz"
    saved.save(path, compression="gzip")
    assert len(sabueso.read_exploration(path).items()) == 7
    assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == ORIGINAL_SHA
    assert len(saved.filter("structure_ref", equals="pdb:1SUX").items()) == 1


@pytest.mark.parametrize("empty", [False, True])
def test_new_selection_has_explicit_format_and_inert_read_resave(
    view, empty, tmp_path, monkeypatch
):
    selected = view.filter(
        "structure_ref", equals="pdb:ABSENT" if empty else "pdb:1SUX"
    )
    path = tmp_path / "new.json"
    receipt = selected.save(path)
    packet = json.loads(path.read_text(encoding="utf-8"))
    assert packet["format"] == FORMAT and packet["filter_policy"] == RULE
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(Card, "__init__", forbidden)
    import sabueso.core.card_scientific_access as current

    monkeypatch.setattr(current, "materialize", forbidden)
    saved = sabueso.read_exploration(path, receipt["bundle_digest"])
    assert len(saved.items()) == (0 if empty else 1)
    assert saved.outcome == view.outcome
    assert saved.validation["display_filter_policy"] == RULE
    assert saved.validation["storage_format"] == FORMAT
    assert saved.native_payload == view.native_payload
    again = tmp_path / "again.json.gz"
    saved.save(again, compression="gzip")
    restored = sabueso.read_exploration(again)
    assert restored.outcome == view.outcome and len(restored.items()) == len(
        saved.items()
    )


@pytest.mark.parametrize(
    "change",
    [
        "rule",
        "nested",
        "producer",
        "unmarked",
        "membership",
        "status",
        "reason",
        "downgrade",
    ],
)
def test_rehashed_packets_cannot_hide_policy_or_change_scientific_outcome(
    valid_packet, change
):
    packet = deepcopy(valid_packet)
    payload = packet["payload"]
    root = payload["views"][payload["root_navigation_ref"]]
    if change == "rule":
        packet["filter_policy"] = "unavailable@9"
    elif change == "nested":
        packet["payload"] = deepcopy(packet)
    elif change == "producer":
        packet["producer"]["sabueso_version"] = "another"
    elif change == "unmarked":
        root["flags"]["_display_request"].pop("filter_policy")
    elif change == "membership":
        root["selected"] = []
    elif change == "status":
        root["flags"]["_status"] = "ok"
    elif change == "reason":
        root["flags"]["_reason"] = None
    else:
        packet = payload
    _seal(payload)
    _seal(packet)
    with pytest.raises(StorageError):
        _restore(packet, packet["bundle_digest"])
    # Historical verification scope must reset even when verification fails.
    view = sabueso.read_exploration(ORIGINAL)
    assert len(view.filter("structure_ref", equals="pdb:1SUX").items()) == 1
