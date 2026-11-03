"""Original nonpolymer identifiers are retained, without assembly reinterpretation."""

import hashlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.knowledge_store import KnowledgeStore
from sabueso.core.migration import SCHEMA_CHANGES
from sabueso.mappings.rcsb_structures import map_structure_entities
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import rcsb

DATA = Path("temp_data/rcsb_nonpolymer_instances")
ALIAS = "assembly_nonpolymer_entities"


def forbidden(*args, **kwargs):
    raise AssertionError("No source acquisition or live saved interpretation")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def entry(identifier="1HTI"):
    return json.loads((DATA / "rcsb" / f"{identifier}.json").read_text())


def build(identifier="1HTI", root=DATA):
    return sabueso.resolve(
        "P60174" if identifier == "1HTI" else "P52270",
        resolver=EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=rcsb.FixtureRCSBClient(str(root)),
        ),
        structures=[identifier],
    )[0]


def assertion(card):
    return next(
        row
        for row in card.source_assertion_store.store.values()
        if row["source"]["name"] == "RCSB PDB"
    )


@pytest.mark.parametrize("identifier", ["1SUX", "2V5B", "1HTI"])
def test_complete_original_capture_and_declared_query_scope(identifier):
    capture = json.loads((DATA / "capture.json").read_text())
    record = next(r for r in capture["records"] if r["pdb_id"] == identifier)
    request = (DATA / "wire" / f"{identifier}.request.json").read_bytes()
    raw = (DATA / "wire" / f"{identifier}.graphql.json").read_bytes()
    decoded = (DATA / "rcsb" / f"{identifier}.json").read_bytes()
    receipt = record["receipt"]
    assert hashlib.sha256(request).hexdigest() == receipt["request_sha256"]
    assert hashlib.sha256(raw).hexdigest() == receipt["sha256"]
    assert len(raw) == receipt["bytes"] and receipt["complete_within_budget"]
    assert hashlib.sha256(decoded).hexdigest() == record["decoded_sha256"]
    assert (
        hashlib.sha256(json.loads(request)["query"].encode()).hexdigest()
        == capture["scope"]["sha256"]
    )
    wire = json.loads(raw)
    assert not wire.get("errors") and wire["data"]["entry"] == json.loads(decoded)
    assert record["acquisition_trace"]["records"][0]["network_attempts"] == 1


@pytest.mark.parametrize("identifier", ["1SUX", "2V5B", "1HTI"])
def test_original_record_identity_order_revision_and_null_survive_mapping(identifier):
    original = entry(identifier)
    before = deepcopy(original)
    mapped = map_structure_entities(original, "2026-11-03")
    source = mapped["source_assertions"][0]
    assert source["asserted_value"]["assembly_component_inputs"] == {
        "nonpolymer_entities": before[ALIAS]
    }
    assert source["asserted_value"]["accession_info"] == before["rcsb_accession_info"]
    assert source["id"] in mapped["relationships"][0]["source_assertion_ids"]
    assert original == before
    original[ALIAS] = "synthetic caller mutation"
    assert (
        source["asserted_value"]["assembly_component_inputs"]["nonpolymer_entities"]
        == before[ALIAS]
    )
    if identifier == "1HTI":
        ids = before[ALIAS][0]["nonpolymer_entity_instances"][0][
            "rcsb_nonpolymer_entity_instance_container_identifiers"
        ]
        assert ids["asym_id"] == "C" and ids["auth_asym_id"] == "B"
        assert ids["comp_id"] == "PGA" and ids["auth_seq_id"] == "549"
    elif identifier == "2V5B":
        assert before[ALIAS] is None  # Not a declaration of an empty assembly.


@pytest.mark.parametrize(
    "value", [None, [], {}, "synthetic malformed", False, 0, [None], [{"x": 1}]]
)
def test_unsupported_alias_values_remain_literal_and_do_not_replace_ligands(value):
    original = entry()
    original[ALIAS] = deepcopy(value)
    legacy = deepcopy(original)
    del legacy[ALIAS]
    mapped = map_structure_entities(original, "fixed retrieval")
    prior = map_structure_entities(legacy, "fixed retrieval")
    source = mapped["source_assertions"][0]
    assert source["asserted_value"]["assembly_component_inputs"] == {
        "nonpolymer_entities": value
    }
    assert (
        mapped["relationships"][0]["qualifiers"]
        == prior["relationships"][0]["qualifiers"]
    )
    assert (
        "assembly_component_inputs"
        not in prior["source_assertions"][0]["asserted_value"]
    )


@pytest.mark.parametrize(
    "query", [rcsb.STRUCTURE_QUERY, rcsb.BATCH_QUERY, rcsb.PARTIAL_QUERY]
)
def test_single_batch_and_partial_query_keep_separate_native_instance_scope(query):
    assert "assembly_nonpolymer_entities: nonpolymer_entities" in query
    assert "rcsb_nonpolymer_entity_instance_container_identifiers" in query
    assert "entry_id entity_id asym_id auth_asym_id comp_id auth_seq_id" in query
    assert "matrix" not in query and "vector" not in query


def test_instance_feature_fallback_keeps_the_nonpolymer_capture():
    class ScriptedClient(rcsb.OnlineRCSBClient):
        def __init__(self):
            super().__init__()
            self.queries = []

        def _post(self, query, pdb_id, variables=None):
            self.queries.append(query)
            if len(self.queries) == 1:
                return {"errors": [{"path": ["entry", "polymer_entity_instances"]}]}
            return {"data": {"entry": entry()}}

    client = ScriptedClient()
    result, _ = client.fetch_structure("1HTI")
    assert client.queries == [rcsb.STRUCTURE_QUERY, rcsb.PARTIAL_QUERY]
    assert result[ALIAS] == entry()[ALIAS]
    mapped = map_structure_entities(result, "fixed retrieval")
    assert mapped["source_assertions"][0]["asserted_value"]["assembly_component_inputs"]


def test_current_native_rule_does_not_turn_new_inputs_into_physical_membership():
    card = build()
    before = card.to_dict()
    result = card.assembly_generation()
    component = next(
        row
        for row in result["sources"][0]["component_registry"]
        if row["asym_id"] == "C"
    )
    assert component["binding_state"] == "referenced"
    assert result["rule"] == "rcsb_assembly_generation@4"
    assert result["physical_membership"] == "not_computed"
    assert card.to_dict() == before


def test_refresh_is_a_new_source_basis_and_migration_never_fills_old_inputs(tmp_path):
    card = build(root=Path("temp_data/rcsb_assembly_generation"))
    original, pin = card.to_dict(), card.pinned_ref()
    assert "assembly_component_inputs" not in assertion(card)["asserted_value"]
    migrated = sabueso.migrate_card(original)
    assert "assembly_component_inputs" not in assertion(migrated)["asserted_value"]
    change = next(
        row
        for row in SCHEMA_CHANGES["0.3.14"]
        if row["path"].endswith("assembly_component_inputs")
    )
    assert change["explicit_only"] is True
    store = KnowledgeStore(tmp_path / "cards.db")
    refreshed, _ = sabueso.refresh_card(
        card,
        resolver=EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=rcsb.FixtureRCSBClient(str(DATA)),
        ),
        store=store,
    )
    assert assertion(refreshed)["id"] != assertion(card)["id"]
    assert assertion(refreshed)["asserted_value"]["assembly_component_inputs"]
    assert store.load(pin).to_dict() == original
    assert card.to_dict() == original and card.pinned_ref() == pin


def test_human_compact_and_independent_saved_access_preserve_original_ids(tmp_path):
    card = build()
    source = assertion(card)
    original = card.to_dict()
    explorer = card.explore()
    location = {
        "format": "card_access_location@1",
        "kind": "card",
        "card_ref": explorer.context["card_ref"],
        "snapshot_id": explorer.context["snapshot_id"],
        "segments": [
            {"type": "Key", "value": "source_assertion_store"},
            {"type": "Record", "value": source["id"]},
            {"type": "Key", "value": "asserted_value"},
            {"type": "Key", "value": "assembly_component_inputs"},
        ],
    }
    view = explorer.inspect(locator=location)
    assert view.native_payload == {"nonpolymer_entities": entry()[ALIAS]}
    assert explorer.access.read(location).page(max_bytes=16384)["items"]
    card_path = tmp_path / "card.json"
    card.to_json(card_path)
    assert Card.from_json(card_path).to_dict() == original
    path = tmp_path / "reading.json"
    receipt = view.save(path)
    code = r"""
import socket,sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a,**k):raise AssertionError('No Card, mapper or network during original reading')
Card.__init__=Card.from_dict=Card.entities=forbidden
socket.socket.connect=socket.create_connection=forbidden
v=sabueso.read_exploration(sys.argv[1],expected_digest=sys.argv[2])
node=v.native_payload['nonpolymer_entities'][0]['nonpolymer_entity_instances'][0]
assert node['rcsb_id']=='1HTI.C'
ids=node['rcsb_nonpolymer_entity_instance_container_identifiers']
assert ids['asym_id']=='C' and ids['auth_asym_id']=='B'
assert ids['comp_id']=='PGA' and ids['auth_seq_id']=='549'
assert v.validation['integrity']=='verified'
"""
    completed = subprocess.run(
        [sys.executable, "-c", code, str(path.resolve()), receipt["bundle_digest"]],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert card.to_dict() == original
