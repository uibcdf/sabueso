"""Opaque qualifier parents remain literal; only interpretable context enriches entities."""

import hashlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import smonitor

from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import SchemaError
from sabueso.core.knowledge_store import KnowledgeStore


def forbidden(*args, **kwargs):
    raise AssertionError("No acquisition, live interpretation or Card construction")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def card():
    card = Card.from_dict(
        json.loads(Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text())
    )
    card.relationship_store.store = {
        key: row
        for key, row in card.relationship_store.store.items()
        if row["predicate"] == "has_structure" and row["object_ref"] == "pdb:1SUX"
    }
    return card


def relationship(card):
    return next(iter(card.relationship_store.store.values()))


def literal(card, row):
    explorer = card.explore()
    location = {
        "format": "card_access_location@1",
        "kind": "card",
        "card_ref": explorer.context["card_ref"],
        "snapshot_id": explorer.context["snapshot_id"],
        "segments": [
            {"type": "Key", "value": "relationship_store"},
            {"type": "Record", "value": row["id"]},
            {"type": "Key", "value": "qualifiers"},
        ],
    }
    return explorer, explorer.inspect(locator=location), location


@pytest.mark.parametrize(
    "value",
    [None, False, True, 0, 1, "", "synthetic invalid parent", [], ["synthetic"], {}],
)
def test_serialization_pinning_capture_and_roundtrip_preserve_exact_original_parent(
    card, value
):
    row = relationship(card)
    row["qualifiers"] = value
    original_row = deepcopy(row)
    sources = deepcopy(card.source_assertion_store.to_list())
    stored = card.to_dict()
    assert stored["relationship_store"][0] == original_row
    assert stored["source_assertion_store"] == sources
    assert "pdb.ligand:BTS" not in stored["entities"]
    pin = card.pinned_ref()
    restored = Card.from_dict(stored)
    assert restored.to_dict() == stored and restored.pinned_ref() == pin
    explorer, view, location = literal(card, row)
    assert view.native_payload == value
    parent = explorer.inspect(
        locator={**location, "segments": location["segments"][:2]}
    )
    assert parent.native_payload == original_row
    assert parent.items()[0].explain().items()
    # Both stored literal values and an actual original support record survive.
    page = explorer.access.read(location).page(limit=1, max_bytes=8192)
    assert page["page"]["values_complete"]
    assert card.relationships()[0] == original_row
    assert card.to_dict() == stored


@pytest.mark.parametrize(
    "predicate,obj",
    [
        ("has_ligand_site", "pdb.ligand:BTS"),
        ("has_bioactivity", "chembl:CHEMBL_TEST"),
        ("engages", "pdb.ligand:BTS"),
        ("interacts_with", "uniprot:SYNTHETIC_PARTNER"),
        ("functionally_associated_with", "string:SYNTHETIC_PARTNER"),
        ("has_interface_with", "pdbe_kb.partner:SYNTHETIC"),
    ],
)
def test_other_predicates_keep_explicit_records_without_parsing_opaque_qualifier_aliases(
    predicate, obj
):
    raw = '{"chembl_id":"SYNTHETIC_ALIAS","molecule_ref":"inchikey:SYNTHETIC","partner_name":"invented"}'
    row = {
        "id": "REL_SYNTHETIC",
        "subject_ref": "uniprot:SYNTHETIC",
        "predicate": predicate,
        "object_ref": obj,
        "qualifiers": raw,
    }
    card = Card(
        meta={"card_id": "sabueso:protein:uniprot:SYNTHETIC", "entity_type": "protein"},
        relationship_store=[row],
    )
    entries = card.entities()
    assert obj in entries and entries[obj]["names"] == []
    assert "inchikey:SYNTHETIC" not in entries
    assert not any("SYNTHETIC_ALIAS" in k for k in entries)
    assert card.to_dict()["relationship_store"][0]["qualifiers"] == raw


def test_source_stated_same_as_keeps_its_explicit_identity_without_qualifier_names():
    row = {
        "id": "REL_SYNTHETIC_IDENTITY",
        "subject_ref": "chembl:SYNTHETIC",
        "predicate": "same_as",
        "object_ref": "inchikey:SYNTHETIC",
        "qualifiers": "unreadable names",
    }
    card = Card(
        meta={
            "card_id": "sabueso:small_molecule:inchikey:SYNTHETIC",
            "entity_type": "small_molecule",
        },
        relationship_store=[row],
    )
    entries = card.entities()
    assert entries["inchikey:SYNTHETIC"]["records"] == ["chembl:SYNTHETIC"]
    assert entries["inchikey:SYNTHETIC"]["names"] == []
    assert card.to_dict()["relationship_store"][0] == row


def test_independent_registered_identity_is_not_lost_with_opaque_structure_context(
    card,
):
    card.register_identity(
        "inchikey:SYNTHETIC",
        ["pdb.ligand:BTS"],
        "small_molecule",
        {"source": "explicit synthetic identity"},
    )
    relationship(card)["qualifiers"] = "unreadable structure context"
    entries = card.entities()
    assert entries["inchikey:SYNTHETIC"]["records"] == ["pdb.ligand:BTS"]
    assert entries["inchikey:SYNTHETIC"]["identity"] == {
        "source": "explicit synthetic identity"
    }


@pytest.mark.parametrize("route", ["card", "deck", "human", "agent"])
def test_structural_receiving_refuses_unknown_parent_after_literal_capture(card, route):
    row = relationship(card)
    row["qualifiers"] = "synthetic malformed parent"
    explorer = card.explore()
    with pytest.raises(SchemaError) as caught:
        if route == "card":
            card.structures()
        elif route == "deck":
            Deck(cards=[card]).structure_inventory()
        elif route == "human":
            explorer.answer(
                "region_coverage",
                options={"sequence_ref": "uniprot:P52270", "region": [96]},
            )
        else:
            explorer.access.select("structures", options={"region": [96]})
    error = caught.value
    assert error.extra["reason"] == "malformed_structure_qualifier_inputs"
    assert error.extra["problem"] == "qualifiers_not_mapping"
    assert error.extra["field"] == "has_structure.qualifiers"
    assert (
        explorer.inspect(locator=error.extra["location"]).native_payload
        == row["qualifiers"]
    )


def test_missing_and_empty_mapping_still_support_original_unknown_state(card):
    row = relationship(card)
    del row["qualifiers"]
    assert card.structures()["items"][0]["state"]["ligands"] is None
    row["qualifiers"] = {}
    assert card.structures()["items"][0]["state"]["ligands"] is None


@pytest.mark.parametrize("value", [None, False, [], 0])
def test_retained_unknown_parent_is_not_classified_as_an_empty_mapping(card, value):
    row = relationship(card)
    row["qualifiers"] = value
    explorer = card.explore()
    with pytest.raises(SchemaError) as caught:
        card.structures()
    assert caught.value.extra["reason"] == "malformed_structure_qualifier_inputs"
    assert (
        explorer.inspect(locator=caught.value.extra["location"]).native_payload == value
    )


def test_foreign_malformed_parent_remains_unplaced_and_inspectable(card):
    other = deepcopy(relationship(card))
    other.update(
        id="REL_SYNTHETIC_FOREIGN",
        subject_ref="uniprot:P60174",
        qualifiers="malformed foreign context",
    )
    card.relationship_store.add(other)
    result = card.structures()
    assert len(result["items"]) == 1 and result["unplaced"][0]["relationship"] == other


def test_restricted_parent_diagnostic_does_not_expose_original_value_or_identity(card):
    relationship(card)["qualifiers"] = "SYNTHETIC_PRIVATE_VALUE"
    with smonitor.diagnostic_scope():
        with pytest.raises(SchemaError) as caught:
            card.structures()
    assert caught.value.extra["problem"] == "qualifiers_not_mapping"
    assert "SYNTHETIC_PRIVATE_VALUE" not in str(caught.value)
    assert "location" not in caught.value.extra


def test_storage_and_inert_saved_inspection_keep_the_unsupported_original(
    card, tmp_path
):
    row = relationship(card)
    row["qualifiers"] = "synthetic malformed parent"
    stored = card.to_dict()
    path = tmp_path / "card.json"
    card.to_json(path)
    assert Card.from_json(path).to_dict() == stored
    store = KnowledgeStore(tmp_path / "cards.db")
    pin = store.save(card)
    assert pin == card.pinned_ref()
    assert store.load(pin).to_dict() == stored
    explorer, view, _ = literal(card, row)
    snapshot = tmp_path / "literal.json"
    receipt = view.save(snapshot)
    digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    code = r"""
import json,socket,sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a,**k):raise AssertionError('No live Card, source acquisition or entities rebuilding')
Card.__init__=Card.from_dict=Card.entities=forbidden
socket.socket.connect=socket.create_connection=forbidden
v=sabueso.read_exploration(sys.argv[1],expected_digest=sys.argv[2])
assert v.native_payload=='synthetic malformed parent'
assert v.validation['integrity']=='verified'
assert 'synthetic malformed parent' in repr(v)
"""
    with TemporaryDirectory(prefix="sabueso-opaque-qualifier-reader-") as working:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                code,
                str(snapshot.resolve()),
                receipt["bundle_digest"],
            ],
            cwd=working,
            capture_output=True,
            text=True,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == digest
    assert card.to_dict() == stored
