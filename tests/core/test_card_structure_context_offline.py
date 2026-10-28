"""Original structure declarations, never PDB-label or assembly joins."""

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
from sabueso.core.errors import StorageError


def forbidden(*args, **kwargs):
    raise AssertionError("No acquisition, recapture or new scientific interpretation")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def card():
    card = Card.from_dict(
        json.loads(
            Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text(
                encoding="utf-8"
            )
        )
    )
    card.relationship_store.store = {
        key: row
        for key, row in card.relationship_store.store.items()
        if row["predicate"] == "has_structure" and row["object_ref"] == "pdb:1SUX"
    }
    return card


def link(view, role):
    return view.filter("role", equals=role).items()[0]


def structure(card):
    return card.explore().view("structures").items()[0]


def parent_item(explorer):
    return explorer.inspect(
        locator={
            **explorer._location("relationship_store"),
            "segments": [{"type": "Key", "value": "relationship_store"}],
        }
    ).items()[0]


def test_native_original_fields_support_and_separate_object_card(card, monkeypatch):
    original = deepcopy(next(iter(card.relationship_store.store.values())))
    item = structure(card)
    monkeypatch.setattr(Card, "structures", forbidden)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.structures"),
        "structure_inventory",
        forbidden,
    )
    card.relationship_store.store.clear()
    links = item.related()
    assert links.native_payload["rule"] == "structure_declaration_context_links@1"
    assert link(links, "structure_context").open().native_payload == original
    for role, field in (
        ("ligand_context", "ligands"),
        ("assembly_context", "assemblies"),
        ("chain_context", "chains"),
        ("numbering_context", "author_numbering"),
    ):
        field_link = link(links, role)
        destination = field_link.open()
        assert destination.native_payload == original["qualifiers"][field]
        assert destination.title == field_link.label
        assert field_link._entry.value["declaration_state"] == "retained"
        assert field_link.support
        location = field_link._entry.value["candidates"][0]["location"]
        assert (
            item._view.explorer.access.read(location).page(max_bytes=8192)["page"][
                "returned"
            ]
            > 0
        )
    assert link(links, "object").open().outcome["status"] == "context_not_supplied"
    assert "No ligand-to-assembly assignment" in links.outcome["reason"]
    assert links.filter("role", equals="source").items()


def test_instance_parent_and_qualifier_detail_offer_the_same_exact_context(card):
    explorer = card.explore()
    instance = explorer.answer("structure_ligands").items()[0]
    parent = link(instance.related(), "structure_context").open()
    qualifier = next(i for i in parent.items() if i.label == "qualifiers")
    # A record's owning array item and its qualifier node share exact field scope.
    row = next(iter(card.relationship_store.store.values()))
    record = parent_item(explorer)
    for item in (record, qualifier):
        links = item.related()
        assert link(links, "structure_context").open().native_payload == row
        assert (
            link(links, "ligand_context").open().native_payload
            == row["qualifiers"]["ligands"]
        )
        assert links.back().back() is item._view


@pytest.mark.parametrize(
    "value,state",
    [
        (None, "retained_null"),
        ([], "retained_empty"),
        (False, "unrecognized_shape"),
        ({"synthetic": "unknown"}, "unrecognized_shape"),
    ],
)
def test_existing_null_empty_and_malformed_fields_stay_inspectable(card, value, state):
    row = next(iter(card.relationship_store.store.values()))
    row["qualifiers"]["ligands"] = value
    item = parent_item(card.explore())
    field = link(item.related(), "ligand_context")
    assert field._entry.value["declaration_state"] == state
    assert field._entry.value["availability"] == "available"
    assert field.open().native_payload == value


@pytest.mark.parametrize(
    "qualifiers,state",
    [
        ({}, "not_retained"),
        (None, "unrecognized_parent_shape"),
        ([], "unrecognized_parent_shape"),
    ],
)
def test_missing_field_is_an_explicit_gap_without_card_supply_advice(
    card, qualifiers, state
):
    row = next(iter(card.relationship_store.store.values()))
    row["qualifiers"] = qualifiers
    field = link(parent_item(card.explore()).related(), "ligand_context")
    assert field._entry.value["declaration_state"] == state
    result = field.open()
    assert result.outcome["status"] == "missing_prerequisite"
    assert "missing data do not establish absence" in result.outcome["reason"]
    assert "related_cards" not in result.outcome["reason"]


def test_missing_source_guidance_does_not_offer_an_unrelated_card(card):
    row = next(iter(card.relationship_store.store.values()))
    row["source_assertion_ids"].append("SA_SYNTHETIC_NOT_RETAINED")
    links = parent_item(card.explore()).related()
    source = next(
        i
        for i in links.items()
        if i._entry.value["target_ref"] == "SA_SYNTHETIC_NOT_RETAINED"
    )
    assert source.open().outcome["status"] == "missing_prerequisite"
    assert (
        "not repaired by supplying a destination Card"
        in source.open().outcome["reason"]
    )


def test_duplicate_pdb_labels_preserve_each_original_relationship(card):
    first = next(iter(card.relationship_store.store.values()))
    second = deepcopy(first)
    second["id"] += "_SYNTHETIC_SECOND"
    second["qualifiers"]["chains"] = ["SYNTHETIC_SECOND_CHAIN"]
    card.relationship_store.add(second)
    explorer = card.explore()
    view = explorer.inspect(locator=explorer._location("relationship_store"))
    assert len(view.items()) == 2
    for item in view.items():
        links = item.related()
        parent = link(links, "structure_context").open().native_payload
        assert (
            link(links, "chain_context").open().native_payload
            == parent["qualifiers"]["chains"]
        )
        assert parent == card.relationship_store.get(parent["id"])


def test_foreign_subject_and_metadata_lookalike_are_not_native_structure_context(card):
    from sabueso.core.card_structure_context_v1 import context

    row = next(iter(card.relationship_store.store.values()))
    row["subject_ref"] = "uniprot:P60174"
    explorer = card.explore()
    assert (
        parent_item(explorer).related().native_payload["rule"]
        == "retained_context_links@2"
    )
    fake = explorer._metadata(
        {
            "context": {
                "adapter": "structure_exploration@1",
                "card_ref": explorer.access._focal.pin,
            },
            "items": {"fake": {}},
        },
        "Synthetic lookalike",
    )
    assert context(explorer, fake._selection._target["location"]) is None
    array = explorer._metadata([], "Synthetic array")
    assert context(explorer, array._selection._target["location"]) is None


@pytest.mark.parametrize("native", [False, True])
def test_independent_saved_fields_no_live_navigation_or_science(card, tmp_path, native):
    explorer = card.explore()
    view = (
        explorer.view("structures")
        if native
        else explorer.inspect(locator=explorer._location("relationship_store"))
    )
    item = view.items()[0]
    expected = link(item.related(), "ligand_context").open().native_payload
    path = tmp_path / "structure.json"
    view.save(path)
    raw = path.read_bytes()
    code = r"""
import importlib,json,socket,sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a,**k):raise AssertionError('No live reconstruction/navigation/science')
Card.__init__=Card.from_dict=forbidden
socket.socket.connect=socket.create_connection=forbidden
n=importlib.import_module('sabueso.core.card_context_navigation')
n.related=n._resolve_target=n._link=forbidden
for name in ('structures','ligand_sites','predicted_structures'):setattr(Card,name,forbidden)
def audit(event,args):
 if event=='open' and 'temp_data' in str(args[0]):forbidden()
sys.addaudithook(audit)
v=sabueso.read_exploration(sys.argv[1])
l=v.items()[0].related()
p=l.filter('role',equals='ligand_context').items()[0].open()
assert p.native_payload==json.loads(sys.argv[2])
assert not l.items()[0].related().items()
"""
    with TemporaryDirectory(prefix="sabueso-structure-reader-") as working:
        subprocess.run(
            [sys.executable, "-c", code, str(path.resolve()), json.dumps(expected)],
            cwd=working,
            check=True,
        )
    assert path.read_bytes() == raw
    again = tmp_path / "again.json"
    view.save(again)
    assert again.read_bytes() == raw


@pytest.mark.parametrize("native", [False, True])
def test_coherently_identified_other_parent_field_is_refused(card, tmp_path, native):
    from sabueso.core.card_context_navigation import _link_view

    first = next(iter(card.relationship_store.store.values()))
    second = deepcopy(first)
    second["id"] += "_SYNTHETIC_SECOND"
    if native:
        second["object_ref"] = "pdb:SYNTHETIC_OTHER"
    card.relationship_store.add(second)
    explorer = card.explore()
    view = (
        explorer.view("structures")
        if native
        else explorer.inspect(locator=explorer._location("relationship_store"))
    )
    original, other = [item.related() for item in view.items()]
    links = deepcopy(original.native_payload["links"])
    for entry in links:
        if entry["role"] == "ligand_context":
            entry["candidates"] = link(other, "ligand_context")._entry.value[
                "candidates"
            ]
    forged = _link_view(
        explorer,
        links,
        original._origin,
        "Synthetic substituted field",
        source_location=view.items()[0].payload_location,
        rule="structure_declaration_context_links@1",
    )
    with pytest.raises(StorageError, match="Original structure field/source/endpoint"):
        forged.save(tmp_path / "forged.json")


def test_supplied_object_revision_ambiguity_keeps_local_fields_unambiguous(card):
    one = Card(
        meta={"card_id": "sabueso:structure:pdb:1SUX", "entity_type": "structure"}
    )
    two = Card(
        meta={"card_id": "sabueso:structure:pdb:1SUX", "entity_type": "structure"}
    )
    two.unknown_stored["synthetic_revision"] = 2
    links = (
        card.explore(related_cards=[one, two]).view("structures").items()[0].related()
    )
    assert link(links, "object")._entry.value["availability"] == "ambiguous"
    assert link(links, "chain_context")._entry.value["availability"] == "available"
    assert link(links, "chain_context").open().native_payload == ["A", "B"]


@pytest.mark.parametrize("native", [False, True])
def test_fresh_metadata_cannot_substitute_origin_even_when_links_match(
    card, tmp_path, native
):
    from sabueso.core.card_context_navigation import _link_view

    first = next(iter(card.relationship_store.store.values()))
    second = deepcopy(first)
    second.update(id=first["id"] + "_SYNTHETIC_OTHER", object_ref="pdb:SYNTHETIC_OTHER")
    card.relationship_store.add(second)
    explorer = card.explore()
    view = (
        explorer.view("structures")
        if native
        else explorer.inspect(locator=explorer._location("relationship_store"))
    )
    original, other = [item.related() for item in view.items()]
    forged = _link_view(
        explorer,
        original.native_payload["links"],
        other._origin,
        "Synthetic wrong origin",
        source_location=view.items()[0].payload_location,
        rule="structure_declaration_context_links@1",
    )
    with pytest.raises(StorageError, match="different originating"):
        forged.save(tmp_path / "wrong-origin.json")


def test_genuine_original_codec_does_not_backfill_structure_fields(
    tmp_path, monkeypatch
):
    import gzip
    import hashlib

    packed = Path(
        "tests/core/data/card_structure_context_legacy_v1.json.gz"
    ).read_bytes()
    assert (
        hashlib.sha256(packed).hexdigest()
        == "6e521aab00fa923c3a25377b70616119bde78fb6c509aa4e861eec443f6ebe3a"
    )
    raw = gzip.decompress(packed)
    assert (
        hashlib.sha256(raw).hexdigest()
        == "04d4655a628744dd44d745f978064c0be76d0f266e3fd5caceee75ead2e52a1d"
    )
    path = tmp_path / "legacy.json"
    path.write_bytes(raw)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_structure_context_v1"),
        "links",
        forbidden,
    )
    saved = sabueso.read_exploration(path)
    original = saved.items()[0].related()
    assert original.native_payload["rule"] == "retained_context_links@2"
    assert not original.filter("role", equals="ligand_context").items()
    assert path.read_bytes() == raw
