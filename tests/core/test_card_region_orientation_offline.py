"""Orient regional reading without promoting declared spans to coordinates."""

import gzip
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.snapshot import canonical_json


def forbidden(*args, **kwargs):
    raise AssertionError("No provider query, rebuilding or current regional science")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def original():
    # Actual original public source capture, shared with existing assembly gates.
    path = Path(__file__).parent / "data/assembly_nonpolymer_live_v2.json.gz"
    return json.loads(gzip.decompress(path.read_bytes()))["cases"]["1SUX"]["card"]


@pytest.fixture
def card(original):
    return Card.from_dict(deepcopy(original))


def region(explorer, positions):
    return explorer.answer(
        "region_coverage",
        options={
            "sequence_ref": "uniprot:P52270",
            "region": positions,
            "include_fragments": True,
        },
    )


@pytest.mark.parametrize(
    "positions,expected",
    [
        ([96], "96 (1 position)"),
        ([96, 168], "96, 168 (2 positions)"),
        (list(range(90, 101)), "90–100 (11 positions)"),
        ([*range(1, 13), 200], "1–12 … (13 positions)"),
    ],
)
def test_requested_positions_are_compact_exact_and_explicitly_bounded(
    card, positions, expected
):
    view = region(card.explore(), positions)
    request = view.request
    text, html = str(view), view._repr_html_()
    assert "Positions: " + expected in text
    assert expected in html
    assert view.request == request


def test_original_declared_spans_and_coordinate_status_stay_separate(card):
    before = card.to_dict()
    explorer = card.explore()
    view = region(explorer, [96, 168])
    selection = explorer.access.select(
        "structures",
        fields=[],
        options={"region": [96, 168], "include_fragments": True},
    )
    native = view.native_payload
    rows = view.rows()
    frame = selection.page(limit=1, max_bytes=16384)
    text = str(view.table())
    html = view.table()._repr_html_()
    assert "Declared ranges | Requested region" in text
    assert "3–18, 44–100, 123–251" in text
    assert "Declared ranges retain source statements" in text
    assert "original mapping inputs" in html
    assert "complete chains in retained coordinate annotations" in text
    assert view.native_payload == native and view.rows() == rows
    assert selection.page(limit=1, max_bytes=16384) == frame
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, "not retained"),
        ([], "empty retained list"),
        ("<script>source</script>", "retained value: <script>source</script>"),
        ([[1, 2], [4, 5], [7, 8], [10, 11], [13, 14]], "5 retained ranges;"),
        ([[9, 3]], "9–3"),
        ([["unknown", 3]], "retained value: 2 items"),
    ],
)
def test_synthetic_unverified_qualifiers_remain_literal_bounded_and_inert(
    card, value, expected
):
    # Deliberately changed qualifiers do not claim a genuine source observation.
    row = next(
        r
        for r in card.relationship_store.store.values()
        if r["object_ref"] == "pdb:1SUX"
    )
    row["qualifiers"]["ranges"] = deepcopy(value)
    view = region(card.explore(), [96, 168]).filter("structure_ref", equals="pdb:1SUX")
    native = view.native_payload
    assert expected in str(view)
    assert view.native_payload == native
    assert "<script>" not in view._repr_html_()
    if isinstance(value, str):
        assert "&lt;script&gt;" in view._repr_html_()
    if isinstance(value, list) and len(value) > 4:
        assert "13–14" not in str(view)
        support = view._selection._scientific.wire["support"][row["id"]]
        original = view.explorer.inspect(locator=support["relationship_location"])
        assert original.native_payload["qualifiers"]["ranges"] == value


def test_conflicting_declared_spans_never_select_one_silently(card):
    row = next(
        r
        for r in card.relationship_store.store.values()
        if r["object_ref"] == "pdb:1SUX"
    )
    row["qualifier_conflicts"] = {
        "ranges": [{"value": [[1, 50]]}, {"value": [[100, 150]]}]
    }
    view = region(card.explore(), [96]).filter("structure_ref", equals="pdb:1SUX")
    assert "conflicting declarations; inspect explain()" in str(view)
    support = view._selection._scientific.wire["support"][row["id"]]
    original = view.explorer.inspect(locator=support["relationship_location"])
    assert len(original.native_payload["qualifier_conflicts"]["ranges"]) == 2


def test_nonregional_inventory_keeps_its_existing_columns(card):
    text = str(card.explore().view("structures").table())
    assert "Declared ranges" not in text and "Requested region" not in text


def test_saved_orientation_preserves_exact_wire_sources_and_machine_request(
    card, tmp_path, monkeypatch
):
    view = region(card.explore(), list(range(90, 101))).table()
    native = view.native_payload
    wire = canonical_json(view._selection._scientific.wire)
    request = view.request
    path = tmp_path / "region.json.gz"
    receipt = view.save(path, compression="gzip")
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(Card, "__init__", forbidden)
    import sabueso.core.card_protein_exploration as current

    monkeypatch.setattr(current, "region_request", forbidden)
    saved = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert "90–100 (11 positions)" in str(saved)
    assert "3–18, 44–100, 123–251" in saved._repr_html_()
    assert saved.native_payload == native and saved.request == request
    assert canonical_json(saved._selection._scientific.wire) == wire
    again = tmp_path / "again.json.gz"
    saved.save(again, compression="gzip")
    assert sabueso.read_exploration(again).native_payload == native
