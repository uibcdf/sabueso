"""Readable original chain context; public fixtures and explicit protocol cases."""

import gzip
import hashlib
import importlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from pyunitwizard import QuantityRecord

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_access import CardAccess
from sabueso.core.card_structure_reading_v1 import RULE, reading
from sabueso.core.snapshot import canonical_json
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient


def forbidden(*args, **kwargs):
    raise AssertionError("No acquisition, recapture or scientific reevaluation")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def public_original():
    card, _ = sabueso.resolve(
        "P52270",
        resolver=EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=FixtureRCSBClient("temp_data"),
        ),
        structures=["1SUX"],
    )
    card.relationship_store.store = {
        row["id"]: row
        for row in card.relationships("has_structure")
        if row["object_ref"] == "pdb:1SUX"
    }
    return card.to_dict()


@pytest.fixture
def card(public_original):
    return Card.from_dict(deepcopy(public_original))


def region(explorer, positions=(96, 168)):
    return explorer.answer(
        "region_coverage",
        options={"sequence_ref": "uniprot:P52270", "region": list(positions)},
    )


def scalar_list(access, location):
    """Use the public bounded agent protocol for original missing-position lists."""
    selection = access.read(location)
    values, cursor = [], None
    while True:
        page = selection.page(limit=1, max_bytes=8192, cursor=cursor)
        assert len(canonical_json(page).encode()) <= 8192
        assert page["page"]["values_complete"]
        values.extend(item["value"] for item in page["items"])
        cursor = page["page"]["next_cursor"]
        if cursor is None:
            return values


@pytest.mark.parametrize(
    "positions,complete,gaps", [([96, 168], ["A", "B"], []), ([1, 96], [], [1])]
)
def test_original_region_complete_and_missing_chains_remain_distinct(
    card, positions, complete, gaps
):
    before = card.to_dict()
    explorer = card.explore()
    selected = region(explorer, positions)
    detail = selected.items()[0].open()
    native = detail.native_payload
    result = detail.regional_reading
    assert result["rule"] == RULE
    assert result["status"] == "recorded"
    assert result["sequence_ref"] == "uniprot:P52270"
    assert result["region"] == positions
    assert result["complete_chains"] == native["complete_chains"] == complete
    assert result["coordinate_basis"]["status"] == "comparable"
    assert result["coordinate_basis"]["structure_reference_revision"] == "not_stated"
    assert result["relationship_ref"] == native["relationship_id"]
    for row in result["chains"]:
        assert row["missing_count"] == len(gaps)
        assert scalar_list(explorer.access, row["missing_positions_location"]) == gaps
        assert (
            explorer.inspect(locator=row["numbering_location"]).native_payload
            == native["author_numbering"][row["chain"]]
        )
    assert (
        explorer.inspect(locator=result["assembly_context"]["location"]).native_payload
        == card.relationships("has_structure")[0]["qualifiers"]["assemblies"]
    )
    text = repr(detail)
    assert f"Chain A: {len(gaps)} requested positions without coordinates" in text
    assert "agreement of structure/reference revisions is not established" in text
    assert "Chain/contact membership of an assembly is not computed" in text
    assert detail.back() is selected
    assert card.to_dict() == before and detail.native_payload == native


def test_optional_human_reading_keeps_compact_agent_frames_unchanged(card):
    explorer = card.explore()
    view = region(explorer)
    selection = explorer.access.select(
        "structures", fields=[], options={"region": [96, 168]}
    )
    before = selection.page(max_bytes=8192)
    assert before["page"]["values_complete"]
    detail = view.items()[0].open()
    context = detail.regional_reading
    repr(detail)
    assert selection.page(max_bytes=8192) == before
    assert "regional_reading" not in before["items"][0]
    assert context["result_ref"] == selection.result_ref == view.result_ref
    literal = explorer.inspect(locator=context["item_location"]).native_payload
    assert literal["relationship_id"] == context["relationship_ref"]
    assert literal["complete_chains"] == detail.native_payload["complete_chains"]
    assert literal["missing_in_region"] == detail.native_payload["missing_in_region"]
    assert (
        QuantityRecord.from_dict(literal["resolution"]).to_quantity(
            field="relationships.has_structure.resolution", unit="angstrom"
        )
        == detail.native_payload["resolution"]
    )
    assert explorer.access.read(context["source_relationship_location"]).count > 0


def test_reading_is_detached_without_current_readers_or_copying_native_body(
    card, monkeypatch
):
    view = region(card.explore())
    detail = view.items()[0].open()
    original = canonical_json(view._selection._scientific.wire)
    for module, names in {
        "structures": ("structures_view", "structure_inventory"),
        "structure_explanation": ("explain_structure_inventory",),
        "card_scientific_access": ("materialize",),
    }.items():
        for name in names:
            monkeypatch.setattr(
                importlib.import_module("sabueso.core." + module), name, forbidden
            )
    monkeypatch.setattr(Card, "from_dict", forbidden)
    detached = detail.regional_reading
    detached["complete_chains"].clear()
    detached["chains"][0]["chain"] = "SYNTHETIC_REPLACEMENT"
    detached["region"].clear()
    assert detail.regional_reading["complete_chains"] == ["A", "B"]
    monkeypatch.setattr(type(detail), "native_payload", property(forbidden))
    assert "Chain A: 0 requested positions" in repr(detail)
    assert "Chain A: 0 requested positions" in detail._repr_html_()
    assert canonical_json(view._selection._scientific.wire) == original


def test_unverified_original_coordinates_stay_unknown_not_zero():
    card = Card.from_dict(
        json.loads(Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text())
    )
    detail = (
        region(card.explore())
        .filter("structure_ref", equals="pdb:1SUX")
        .items()[0]
        .open()
    )
    context = detail.regional_reading
    assert context["status"] == "not_computed"
    assert context["complete_chains"] is None and context["chains"] == []
    assert (
        context["coordinate_basis"]["reason"] == "original_polymer_inputs_unavailable"
    )
    assert "not computed" in repr(detail)
    assert "unknown coordinates are not missing residues" in repr(detail)


def test_no_region_or_focused_scientific_item_never_fabricates_context(card):
    explorer = card.explore()
    assert explorer.overview().regional_reading is None
    assert explorer.view("structures").items()[0].open().regional_reading is None
    assert region(explorer).regional_reading is None
    assert (
        explorer._metadata(
            {"complete_chains": ["SYNTHETIC"], "missing_in_region": {}},
            "Structure lookalike",
        ).regional_reading
        is None
    )


@pytest.mark.parametrize(
    "value,state",
    [([], "retained_empty"), (None, "retained_null"), ({}, "unrecognized_shape")],
)
def test_original_assembly_shapes_are_inspectable_not_membership(card, value, state):
    # Synthetic qualifier changes test presentation scope, not source knowledge.
    card.relationships("has_structure")[0]["qualifiers"]["assemblies"] = value
    explorer = card.explore()
    context = region(explorer).items()[0].open().regional_reading
    assert context["assembly_context"]["state"] == state
    assert (
        explorer.inspect(locator=context["assembly_context"]["location"]).native_payload
        == value
    )


def test_duplicate_pdb_labels_keep_the_exact_parent_and_captured_scope(card):
    first = card.relationships("has_structure")[0]
    second = deepcopy(first)
    second["id"] += "_SYNTHETIC_SECOND"
    second["qualifiers"].pop("assemblies")
    card.relationship_store.add(second)
    explorer = card.explore()
    view = region(explorer)
    card.relationship_store.store.clear()
    assert len(view.items()) == 2
    for item in view.items():
        context = item.open().regional_reading
        parent = explorer.inspect(
            locator=context["source_relationship_location"]
        ).native_payload
        assert parent["id"] == context["relationship_ref"]
        assert context["assembly_context"]["state"] == (
            "retained" if parent["id"] == first["id"] else "not_retained"
        )


def test_saved_region_reopens_inertly_with_original_chains_and_resolvable_locations(
    card, tmp_path
):
    view = region(card.explore(), [1, 96])
    detail = view.items()[0].open()
    expected = detail.regional_reading
    path = tmp_path / "region.json"
    detail.save(path)
    before = path.read_bytes()
    code = r"""
import importlib,json,socket,sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a,**k):raise AssertionError('No science, Card reconstruction, acquisition or new credit')
Card.__init__=Card.from_dict=forbidden
socket.socket.connect=socket.create_connection=forbidden
for module,names in {'card_scientific_access':['materialize'],'structures':['structures_view','structure_inventory'],'structure_explanation':['explain_structure_inventory'],'knowledge_state':['knowledge_state']}.items():
 for name in names:setattr(importlib.import_module('sabueso.core.'+module),name,forbidden)
import ackredit
ackredit.register_item=ackredit.track_item=forbidden
def audit(event,args):
 if event=='open' and 'temp_data' in str(args[0]):forbidden()
sys.addaudithook(audit)
v=sabueso.read_exploration(sys.argv[1]);context=v.regional_reading
def values(value):
 if isinstance(value,list):return [values(item) for item in value]
 if isinstance(value,dict):return {k:values(item) for k,item in value.items() if k!='location_ref'}
 return value
# Current delivery uses session-local lookup handles; original science and the
# exact result/relationship binding stay equal across independent readers.
assert values(context)==values(json.loads(sys.argv[2]))
assert 'Chain A: 1 requested positions' in repr(v)
for chain in context['chains']:
 assert v.explorer.inspect(locator=chain['missing_positions_location']).native_payload==[1]
assert v.back().items()[0].open().regional_reading==context
"""
    with TemporaryDirectory(prefix="sabueso-regional-reader-") as working:
        result = subprocess.run(
            [sys.executable, "-c", code, str(path.resolve()), json.dumps(expected)],
            cwd=working,
            capture_output=True,
            text=True,
            check=False,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    assert path.read_bytes() == before


def test_genuine_old_regional_result_keeps_its_original_reported_values(
    tmp_path, monkeypatch
):
    raw = gzip.decompress(
        Path("tests/core/data/card_agent_selection_v1.json.gz").read_bytes()
    )
    assert (
        hashlib.sha256(raw).hexdigest()
        == "4f88069416426c4b32cab97d8029dd061d167bac7769831da7aad0b4dd89a81d"
    )
    path = tmp_path / "original.json"
    path.write_bytes(raw)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_scientific_access"),
        "materialize",
        forbidden,
    )
    saved = sabueso.read_exploration(path)
    access = saved.explorer.access
    # Exercise current presentation over a genuinely retained old regional result,
    # without claiming an unrecorded human request or changing the original file.
    result = next(
        selection._scientific
        for selection in access._selections.values()
        if selection._scientific is not None
        and selection._scientific.options.get("region") is not None
    )
    key = result.entries[0].key
    original = canonical_json(result.wire)
    context = reading(access, result, key)
    assert context["coordinate_basis"]["status"] == "not_retained"
    assert context["complete_chains"] == result.wire["items"][key]["complete_chains"]
    assert context["region"] == result.options["region"]
    assert canonical_json(result.wire) == original and path.read_bytes() == raw


def test_preview_is_explicitly_bounded_and_html_escaped(card, monkeypatch):
    detail = region(card.explore()).items()[0].open()
    # Synthetic presentation rows exercise prefix work, never source knowledge.
    row = detail._selection._scientific.wire["items"][detail._focus]
    row["missing_in_region"] = {
        f"<script>SYNTHETIC_{index}</script>": [96] for index in range(9)
    }
    row["author_numbering"] = {}
    original, calls = CardAccess._location, []

    def counted(self, location):
        segments = location.get("segments", [])
        if len(segments) >= 4 and segments[-2] == {
            "type": "Key",
            "value": "missing_in_region",
        }:
            calls.append(location)
        return original(self, location)

    with monkeypatch.context() as patch:
        patch.setattr(CardAccess, "_location", counted)
        assert "Showing 6 of 9 chain records" in repr(detail)
        assert len(calls) == 6
        html = detail._repr_html_()
        assert len(calls) == 12
    assert "<script>" not in html and "&lt;script&gt;" in html
    complete = detail.regional_reading
    assert complete["chain_count"] == len(complete["chains"]) == 9
    assert complete["chains_complete"]
