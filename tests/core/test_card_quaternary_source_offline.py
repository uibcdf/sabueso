"""Readable original quaternary declarations; modified cases are synthetic."""

import gzip
import importlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_exploration_storage import _seal
from sabueso.core.errors import ArgumentError, StorageError

TOPIC = "quaternary_structure"


def forbidden(*args, **kwargs):
    raise AssertionError("No acquisition, native classification or recapture")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def card():
    return Card.from_dict(
        json.loads(
            Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text(
                encoding="utf-8"
            )
        )
    )


@pytest.fixture
def synthetic(card):
    # Deliberately reduced captured test state, not an original source response.
    card.relationship_store.store = {
        key: row
        for key, row in card.relationship_store.store.items()
        if (row["predicate"] == "has_structure" and row["object_ref"] == "pdb:1SUX")
        or (
            row["predicate"] == "has_interface_with"
            and row["object_ref"] == "uniprot:P52270"
        )
    }
    return card


def structure(card):
    return next(
        row
        for row in card.relationship_store.store.values()
        if row["predicate"] == "has_structure" and row["object_ref"] == "pdb:1SUX"
    )


def test_public_rows_keep_original_grain_source_context_and_complete_access(
    card, monkeypatch
):
    original = card.to_dict()
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.oligomer"), "oligomer_view", forbidden
    )
    explorer = card.explore()
    view = explorer.answer(TOPIC)
    assert view.result_ref == explorer.view(TOPIC).result_ref
    assert len(view.items()) == 11
    assert {item.kind for item in view.items()} == {
        "subunit_annotation",
        "assembly",
        "interface",
    }
    assert "Homodimer" in repr(view)
    assert "Stoichiometry: A2" in repr(view)
    assert "Source method: PISA" in repr(view)
    assert "Assembly IDs are local" in repr(view)
    assemblies = view.filter("kind", equals="assembly").filter(
        "structure_ref", equals="pdb:1SUX"
    )
    item = assemblies.items()[0]
    assert item.cells["assembly_id"].value == "1"
    assert item.open().native_payload == structure(card)["qualifiers"]["assemblies"][0]
    assert item.support[0]["basis"] == "relationship_level"
    assert item.explain().back() is assemblies
    sources = item.related().filter("role", equals="source")
    assert (
        sources.items()[0].open().native_payload["id"]
        in structure(card)["source_assertion_ids"]
    )
    assert sources.back().back().back() is assemblies
    original_structure = (
        item.related().filter("role", equals="structure_context").items()[0].open()
    )
    assert original_structure.native_payload == structure(card)
    assert original_structure.back().back().back().back() is assemblies
    interface = view.filter("partner_ref", equals="uniprot:P52270").items()[0]
    assert interface.kind == "interface"
    assert "Recorded numbering: uniprot" in repr(
        interface.back().filter("kind", equals="interface")
    )
    assert card.to_dict() == original
    page = explorer.access.read(item.payload_location).page(max_bytes=8192)
    assert page["page"]["returned"] > 0
    # Nested values retain typed follow-up locations instead of a false full-value claim.
    assert any(row["key"] == "stoichiometry" for row in page["items"])


@pytest.mark.parametrize("mode", ["missing", "wrong", "conflicting"])
def test_inconsistent_identity_is_a_prerequisite_gap(card, mode):
    if mode == "missing":
        card.meta.pop("card_id")
    elif mode == "wrong":
        card.get("identifiers.uniprot")["value"] = "P60174"
    else:
        card.quality.setdefault("conflicts", []).append(
            {"field": "identifiers.uniprot"}
        )
    view = card.explore().view(TOPIC)
    assert view.outcome["status"] == "missing_prerequisite"
    assert not view.items()


def test_missing_empty_malformed_and_duplicate_ids_preserve_original_indices(synthetic):
    row = structure(synthetic)
    row["qualifiers"]["assemblies"] = [{"id": "1"}, None, {"id": "1"}, {}, {"id": 1}]
    view = synthetic.explore().view(TOPIC)
    assemblies = view.filter("kind", equals="assembly")
    assert len(assemblies.items()) == 4
    assert len({item.item_ref for item in assemblies.items()}) == 4
    assert len(assemblies.filter("assembly_id", equals="1").items()) == 2
    assert [
        item.payload_location["segments"][-1]["value"] for item in assemblies.items()
    ] == [0, 2, 3, 4]
    assert "unknown" in repr(assemblies)
    assert any(
        gap["state"] == "unrecognized_shape"
        for gap in view.native_payload["field_gaps"]
    )
    with pytest.raises(ArgumentError):
        assemblies.filter("assembly_id", equals=1)


@pytest.mark.parametrize(
    "value,state",
    [(None, "not_retained"), ([], "retained_empty"), ("bad", "unrecognized_shape")],
)
def test_missing_assembly_declarations_are_not_source_absence(synthetic, value, state):
    structure(synthetic)["qualifiers"]["assemblies"] = value
    view = synthetic.explore().view(TOPIC)
    assert not view.filter("kind", equals="assembly").items()
    assert any(gap["state"] == state for gap in view.native_payload["field_gaps"])
    assert "Missing declarations are not absence" in repr(view)


def test_foreign_relationships_are_excluded_and_capture_is_isolated(synthetic):
    original = structure(synthetic)
    foreign = deepcopy(original)
    foreign["id"] += "_SYNTHETIC_FOREIGN"
    foreign["subject_ref"] = "uniprot:P60174"
    synthetic.relationship_store.add(foreign)
    explorer = synthetic.explore()
    original["qualifiers"]["assemblies"].clear()
    view = explorer.view(TOPIC)
    assert len(view.filter("kind", equals="assembly").items()) == 1
    item = view.filter("kind", equals="assembly").items()[0]
    item.cells["value"].value["id"] = "mutated copy"
    assert item.cells["assembly_id"].value == "1"


@pytest.mark.parametrize("nature", ["small_molecule", "disease"])
def test_other_natures_are_explicitly_not_applicable(synthetic, nature):
    synthetic.meta["entity_type"] = nature
    view = synthetic.explore().view(TOPIC)
    assert view.outcome["status"] == "not_applicable"


def test_saved_reading_sources_back_and_repeated_save(synthetic, tmp_path, monkeypatch):
    view = (
        synthetic.explore()
        .answer(TOPIC)
        .filter("structure_ref", equals="pdb:1SUX")
        .table()
    )
    path = tmp_path / "original.json"
    view.save(path)
    expected = view.rows()
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_exploration_profiles"),
        "field_entries",
        forbidden,
    )
    saved = sabueso.read_exploration(path)
    assert saved.rows() == expected
    assert saved.items()[0].explain().back().view_ref == saved.view_ref
    assert (
        saved.items()[0]
        .related()
        .filter("role", equals="source")
        .items()[0]
        .open()
        .native_payload["id"]
    )
    again = tmp_path / "again.json"
    saved.save(again)
    assert sabueso.read_exploration(again).view_ref == saved.view_ref


@pytest.mark.parametrize(
    "change", ["scope", "adapter", "ordinal", "membership", "kind", "assembly_id"]
)
def test_rehashed_profile_or_typed_membership_changes_are_rejected(
    synthetic, tmp_path, change
):
    view = synthetic.explore().view(TOPIC)
    path = tmp_path / "original.json"
    view.save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if change in ("scope", "adapter"):
        native = next(
            value
            for value in bundle["objects"].values()
            if isinstance(value, dict)
            and value.get("adapter") == "quaternary_structure_fields@1"
        )
        native[change] = "SYNTHETIC_CHANGED"
    else:
        record = bundle["views"][bundle["root_navigation_ref"]]
        if change == "membership":
            record["selection"]["entries"].pop()
        elif change == "ordinal":
            next(
                row
                for row in record["selection"]["entries"]
                if row["ordinal"] is not None
            )["ordinal"] = 99
        else:
            state = next(
                row
                for row in record["state"]["items"].values()
                if row["kind"] == "assembly"
            )
            if change == "kind":
                state["kind"] = "interface"
            else:
                state["cells"]["assembly_id"]["value"] = "other"
    path.write_text(json.dumps(_seal(bundle)))
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_genuine_older_capsules_remain_readable(tmp_path):
    folder = Path(__file__).parent / "data"
    for name in (
        "card_exploration_science_v2.json.gz",
        "card_exploration_sites_v1.json.gz",
    ):
        path = tmp_path / name.removesuffix(".gz")
        path.write_bytes(gzip.decompress((folder / name).read_bytes()))
        assert sabueso.read_exploration(path).validation["integrity"] == "verified"


def test_independent_reader_never_uses_live_profiles_native_science_or_sources(
    synthetic, tmp_path
):
    path = tmp_path / "original.json"
    synthetic.explore().answer(TOPIC).save(path)
    script = r"""
import importlib, socket, sys
import sabueso
from sabueso.core.card import Card
from sabueso.core.card_exploration import CardExplorer
def forbidden(*a, **k): raise AssertionError('No current producer, Card construction, fixture access or network')
Card.from_dict = forbidden
CardExplorer._field_view = forbidden
socket.socket.connect = forbidden
socket.create_connection = forbidden
importlib.import_module('sabueso.core.card_exploration_profiles').field_entries = forbidden
importlib.import_module('sabueso.core.oligomer').oligomer_view = forbidden
def audit(event,args):
 if event=='open' and isinstance(args[0],str) and 'temp_data' in args[0].replace(chr(92), '/').split('/'): forbidden()
sys.addaudithook(audit)
view=sabueso.read_exploration(sys.argv[1])
assert view.validation['integrity']=='verified'
assert view.explorer.view('quaternary_structure').result_ref == view.result_ref
assert view.explorer.answer('quaternary_structure').view_ref == view.view_ref
assembly=view.filter('kind',equals='assembly').items()[0]
assert assembly.cells['structure_ref'].value=='pdb:1SUX'
assert assembly.open().native_payload['stoichiometry']==['A2']
assert assembly.related().filter('role',equals='source').items()[0].open().native_payload['id']
page=view.explorer.access.read(assembly.payload_location).page(max_bytes=8192)
assert page['page']['returned']>0
print('PASS independent original quaternary source reading')
"""
    with TemporaryDirectory(prefix="sabueso-quaternary-reader-") as cwd:
        result = subprocess.run(
            [sys.executable, "-c", script, str(path.resolve())],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
    assert result.returncode == 0, result.stdout + result.stderr


def test_conflicts_full_raw_values_and_bounded_escaped_preview(synthetic, tmp_path):
    row = structure(synthetic)
    row.setdefault("qualifier_conflicts", {})["assemblies"] = [{"id": "other"}]
    row["qualifiers"]["assemblies"][0]["id"] = "<script>unsafe</script>"
    synthetic.get("annotations.subunit")["value"] = ["<script>" + "x" * 10000] * 100
    view = synthetic.explore().view(TOPIC)
    assert len(repr(view)) < 16000
    html = view._repr_html_()
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "Unresolved qualifier conflicts" in repr(view)
    item = view.filter("kind", equals="assembly").items()[0]
    original = deepcopy(item.open().native_payload)
    path = tmp_path / "original.json"
    view.save(path)
    saved = sabueso.read_exploration(path)
    assert (
        saved.filter("kind", equals="assembly").items()[0].open().native_payload
        == original
    )


def test_rehashed_original_structure_destination_swap_is_rejected(synthetic, tmp_path):
    view = synthetic.explore().view(TOPIC)
    path = tmp_path / "original.json"
    view.save(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for obj in data["objects"].values():
        if isinstance(obj, dict) and obj.get("rule") == "quaternary_context_links@1":
            for link in obj["links"]:
                if link["role"] == "structure_context":
                    link["candidates"][0]["location"]["segments"] = [
                        {"type": "Key", "value": "quality"}
                    ]
                    changed = True
    assert changed
    path.write_text(json.dumps(_seal(data)))
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)
