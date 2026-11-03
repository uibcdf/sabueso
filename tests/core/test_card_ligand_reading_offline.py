"""Readable exact original ligands, with compact and independent saved access."""

import gc
import json
import socket
import subprocess
import sys
from copy import deepcopy
from tempfile import TemporaryDirectory

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_ligand_reading_v1 import RULE
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.rcsb import FixtureRCSBClient


def forbidden(*args, **kwargs):
    raise AssertionError("No acquisition, live scientific interpretation or recapture")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def original():
    card, _ = sabueso.resolve(
        "P52270",
        resolver=EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=FixtureRCSBClient("temp_data"),
        ),
        structures=["1SUX"],
    )
    # Keep the selected public declaration for bounded saved-path qualification;
    # the audit separately exercises the complete seven-declaration inventory.
    card.relationship_store.store = {
        key: row
        for key, row in card.relationship_store.store.items()
        if row["predicate"] != "has_structure" or row["object_ref"] == "pdb:1SUX"
    }
    return card.to_dict()


@pytest.fixture
def card(original):
    return Card.from_dict(deepcopy(original))


def field(view, key):
    return view.filter("label", equals=key).items()[0].open()


def journey(card):
    explorer = card.explore()
    active = explorer.view("annotated_regions").filter(
        "feature_type", equals="active_site"
    )
    annotation = active.items()[0]
    regional = annotation.related().filter("role", equals="question").items()[0].open()
    selected = regional.filter("structure_ref", equals="pdb:1SUX")
    links = selected.items()[0].related()
    ligands = links.filter("role", equals="ligand_context").items()[0].open()
    return explorer, selected, ligands


def literal_ligands(card, row):
    """Inspect malformed original literals without invoking native science."""
    explorer = card.explore()
    return explorer.inspect(
        locator={
            "format": "card_access_location@1",
            "kind": "card",
            "card_ref": explorer.context["card_ref"],
            "snapshot_id": explorer.context["snapshot_id"],
            "segments": [
                {"type": "Key", "value": "relationship_store"},
                {"type": "Record", "value": row["id"]},
                {"type": "Key", "value": "qualifiers"},
                {"type": "Key", "value": "ligands"},
            ],
        }
    )


def test_public_journey_retains_exact_components_instances_support_and_original_rows(
    card,
):
    before = card.to_dict()
    explorer, selected, ligands = journey(card)
    original_rows = ligands.rows()
    context = ligands.ligand_reading
    assert context["rule"] == RULE and context["level"] == "components"
    assert context["entry_count"] == 2 and context["entries_complete"]
    assert [e["component_id"]["value"] for e in context["entries"]] == ["BTS", "SO4"]
    assert [e["instances"]["count"] for e in context["entries"]] == [1, 7]
    assert [item.label for item in ligands.items()] == ["0", "1"]
    assert (
        context["relationship_ref"]
        == selected.items()[0].open().native_payload["relationship_id"]
    )
    assert context["source_relationship_location"]["segments"][-1] == {
        "type": "Record",
        "value": context["relationship_ref"],
    }
    assert "BTS" in repr(ligands) and "SULFATE ION" in repr(ligands)
    assert "region overlap, assembly membership" in repr(ligands)
    component = ligands.items()[1].open()
    instances = field(component, "instances")
    assert instances.back().back() is component
    assert instances.ligand_reading["entry_count"] == 7
    assert "Showing 6 of 7 original entries" in repr(instances)
    assert "instance C" in repr(instances) and "angstrom" in repr(instances)
    instance = instances.items()[0].open()
    expected = ligands.native_payload[1]["instances"][0]
    assert instance.native_payload == expected
    record = instance.ligand_reading["entries"][0]
    assert record["instance_id"]["value"] == "C"
    assert record["contacts"]["count"] == len(expected["contacts"])
    # A compact agent reads exactly these original values with the same locator.
    contacts = explorer.access.read(record["contacts"]["location"]).page(
        limit=1, max_bytes=8192
    )
    contact = contacts["items"][0]
    assert not contact["value_included"]
    original_fields = explorer.access.read(contact["value_location"]).page(
        limit=8, max_bytes=16384
    )
    assert (
        next(e for e in original_fields["items"] if e["key"] == "position")["value"]
        == expected["contacts"][0]["position"]
    )
    assert explorer.inspect(locator=record["location"]).native_payload == expected
    assert instances.items()[0].explain().items()
    context["entries"][0]["component_id"]["value"] = "caller mutation"
    assert ligands.ligand_reading["entries"][0]["component_id"]["value"] == "BTS"
    assert ligands.rows() == original_rows
    assert card.to_dict() == before
    assert explorer.view("ligand_instances").ligand_reading is None
    assert explorer.inspect().ligand_reading is None
    assert selected.items()[0].open().ligand_reading is None


@pytest.mark.parametrize(
    "value,state,count",
    [
        (None, "retained_null", None),
        ([], "retained_empty", 0),
        (False, "unrecognized_shape", None),
    ],
)
def test_null_empty_and_malformed_original_lists_are_not_absence(
    card, value, state, count
):
    row = next(
        r for r in card.relationships("has_structure") if r["object_ref"] == "pdb:1SUX"
    )
    row["qualifiers"]["ligands"] = value
    detail = literal_ligands(card, row)
    assert detail.ligand_reading["state"] == state
    assert detail.ligand_reading["entry_count"] == count
    assert detail.native_payload is value or detail.native_payload == value
    assert "not absence" in repr(detail)


def test_duplicate_structure_component_and_instance_labels_do_not_change_original_occurrences(
    card,
):
    row = next(
        r for r in card.relationships("has_structure") if r["object_ref"] == "pdb:1SUX"
    )
    second = deepcopy(row)
    second["id"] += "_SYNTHETIC_OTHER"
    second["qualifiers"]["ligands"][0]["description"] = "synthetic second declaration"
    card.relationship_store.add(second)
    explorer, selected, first = journey(card)
    assert len(selected.items()) == 2
    other = (
        selected.items()[1]
        .related()
        .filter("role", equals="ligand_context")
        .items()[0]
        .open()
    )
    assert (
        first.ligand_reading["relationship_ref"]
        != other.ligand_reading["relationship_ref"]
    )
    assert "synthetic second declaration" not in repr(first)
    assert "synthetic second declaration" in repr(other)
    # Mutating the caller Card does not replace the captured original.
    row["qualifiers"]["ligands"].clear()
    assert first.ligand_reading["entry_count"] == 2
    assert (
        explorer.inspect(
            locator=first.ligand_reading["entries"][0]["location"]
        ).native_payload["comp_id"]
        == "BTS"
    )


@pytest.mark.parametrize(
    "value,state",
    [(None, "retained_null"), ([], "retained_empty"), ({}, "unrecognized_shape")],
)
def test_missing_and_partial_instance_fields_remain_inspectable(card, value, state):
    row = next(
        r for r in card.relationships("has_structure") if r["object_ref"] == "pdb:1SUX"
    )
    ligand = row["qualifiers"]["ligands"][0]
    ligand["instances"] = value
    del ligand["description"]
    view = literal_ligands(card, row)
    record = view.ligand_reading["entries"][0]
    assert record["description"]["state"] == "not_retained"
    assert record["description"]["location"] is None
    assert record["instances"]["state"] == state


def test_unstated_instances_and_malformed_entries_keep_exact_original_locations(card):
    row = next(
        r for r in card.relationships("has_structure") if r["object_ref"] == "pdb:1SUX"
    )
    del row["qualifiers"]["ligands"][0]["instances"]
    row["qualifiers"]["ligands"].extend([None, False, {}])
    view = literal_ligands(card, row)
    reading = view.ligand_reading
    assert reading["entries"][0]["instances"] == {
        "state": "not_retained",
        "location": None,
        "count": None,
    }
    assert [r["state"] for r in reading["entries"][-3:]] == [
        "retained_null",
        "unrecognized_shape",
        "retained_empty",
    ]
    assert view.items()[2].open().native_payload is None
    assert "Original component entry 4" in repr(view)


@pytest.mark.parametrize(
    "change", ["foreign_subject", "other_predicate", "extension_lookalike"]
)
def test_only_exact_focal_structure_nodes_get_context(card, change):
    row = next(
        r for r in card.relationships("has_structure") if r["object_ref"] == "pdb:1SUX"
    )
    if change == "foreign_subject":
        row["subject_ref"] = "uniprot:SYNTHETIC_OTHER"
        view = literal_ligands(card, row)
    elif change == "other_predicate":
        row["predicate"] = "has_ligand_site"
        row["qualifiers"] = {"ligands": [{"comp_id": "BTS", "instances": []}]}
        row.pop("derivation_applications", None)
        view = literal_ligands(card, row)
    else:
        card.sections["extensions"] = {
            "synthetic_ligands": [{"comp_id": "BTS", "instances": []}]
        }
        view = card.explore().inspect("extensions.synthetic_ligands")
    assert view.ligand_reading is None
    assert "Original ligand context" not in repr(view)


def test_preview_bounds_work_and_escapes_html_without_changing_literal_labels(
    card, monkeypatch
):
    row = next(
        r for r in card.relationships("has_structure") if r["object_ref"] == "pdb:1SUX"
    )
    ligands = row["qualifiers"]["ligands"]
    ligands[:] = [deepcopy(ligands[0]) for _ in range(40)]
    for entry in ligands:
        entry["comp_id"] = "<script>SYNTHETIC</script>"
    _, _, view = journey(card)
    import sabueso.core.card_ligand_reading_v1 as policy

    calls = []
    original = policy._component

    def counted(*a):
        calls.append(1)
        return original(*a)

    monkeypatch.setattr(policy, "_component", counted)
    assert "Showing 6 of 40 original entries" in repr(view)
    assert len(calls) == 6
    html = view._repr_html_()
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert len(calls) == 12
    assert (
        view.ligand_reading["entry_count"] == len(view.ligand_reading["entries"]) == 40
    )
    assert view.items()[0].label == "0"


def test_display_filter_and_sort_preserve_selected_membership_and_original_indices(
    card,
):
    row = next(
        r for r in card.relationships("has_structure") if r["object_ref"] == "pdb:1SUX"
    )
    view = literal_ligands(card, row)
    selected = view.filter("label", equals="1")
    context = selected.ligand_reading
    assert context["entry_count"] == 1 and context["node_entry_count"] == 2
    assert context["entries_complete"]
    assert [e["component_id"]["value"] for e in context["entries"]] == ["SO4"]
    assert context["entries"][0]["index"] == 1
    assert "BTS" not in repr(selected)
    assert "Selected original entries: 1 of 2" in repr(selected)
    descending = view.sort("label", descending=True).ligand_reading
    assert [e["index"] for e in descending["entries"]] == [1, 0]
    empty = selected.filter("label", equals="SYNTHETIC_NO_MATCH").ligand_reading
    assert empty["entries"] == [] and empty["entry_count"] == 0
    assert empty["state"] == "retained" and empty["node_entry_count"] == 2


def test_saved_literal_filter_keeps_its_selection_and_complete_original_node(
    card, tmp_path
):
    row = next(
        r for r in card.relationships("has_structure") if r["object_ref"] == "pdb:1SUX"
    )
    view = literal_ligands(card, row).filter("label", equals="1")
    path = tmp_path / "selected.json"
    view.save(path)
    saved = sabueso.read_exploration(path)
    assert saved.ligand_reading == view.ligand_reading
    assert saved.ligand_reading["entries"][0]["index"] == 1
    assert len(saved.native_payload) == saved.ligand_reading["node_entry_count"] == 2
    assert "BTS" not in repr(saved)


def test_saved_journey_has_inert_current_literal_delivery_and_preserved_original_back_path(
    card, tmp_path
):
    explorer, selected, view = journey(card)
    instances = field(view.items()[0].open(), "instances")
    original = instances.items()[0].open()
    path = tmp_path / "public.json.gz"
    receipt = original.save(path, compression="gzip")
    expected_context = original.ligand_reading
    expected_payload = original.native_payload
    # Retain the expected original values, not a second complete live history,
    # while the independent receiving process validates its own reading.
    del original, instances, view, explorer, selected
    gc.collect()
    code = r"""
import importlib, json, socket, sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a, **k): raise AssertionError('No acquisition, Card construction or current science')
Card.__init__ = Card.from_dict = forbidden
socket.socket.connect = forbidden
socket.create_connection = forbidden
import sabueso.core.card_scientific_access as science
science.materialize = forbidden
for module, names in {'structures':['structures_view','structure_inventory'], 'structure_explanation':['explain_structure_inventory'], 'knowledge_state':['knowledge_state']}.items():
 for name in names: setattr(importlib.import_module('sabueso.core.' + module), name, forbidden)
def audit(event, args):
 if event == 'open' and 'temp_data' in str(args[0]): forbidden()
sys.addaudithook(audit)
saved = sabueso.read_exploration(sys.argv[1], expected_digest=sys.argv[2])
assert saved.ligand_reading == json.loads(sys.argv[3])
assert 'instance J' in repr(saved)
record = saved.ligand_reading['entries'][0]
assert saved.explorer.access.read(record['contacts']['location']).page(limit=1, max_bytes=8192)['items']
assert saved.back().items()[0].open().ligand_reading == saved.ligand_reading
assert saved.back().back().back().back().ligand_reading['level'] == 'components'
"""
    with TemporaryDirectory(prefix="sabueso-public-ligand-reader-") as working:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                code,
                str(path.resolve()),
                receipt["bundle_digest"],
                json.dumps(expected_context),
            ],
            cwd=working,
            capture_output=True,
            text=True,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    saved = sabueso.read_exploration(path)
    assert saved.native_payload == expected_payload
    assert saved.ligand_reading == expected_context
