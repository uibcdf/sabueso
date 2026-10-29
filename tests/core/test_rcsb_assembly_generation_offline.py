"""Original public assembly declarations; modified inputs are synthetic cases."""

import hashlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.snapshot import canonical_json
from sabueso.mappings.rcsb_structures import map_structure_entities
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import rcsb

DATA = Path("temp_data/rcsb_assembly_generation")
KEYS = ("pdbx_struct_assembly_gen", "pdbx_struct_oper_list")
LEGACY_PINS = {
    "1SUX": "9ca26aeff2b18b96093f0a6eb69477301a0f078d704fcc35660b686af5211a61",
    "2V5B": "743e8f0c31af372f573d04d1e2ba0db3b084ace417433728992b55f35f5b9eae",
    "1HTI": "1bf0bea1894f890bf85057142a8a08b596dd2d1c6bf18c322eb12f3a83441e1f",
}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No network acquisition")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


def entry(identifier="2V5B"):
    return json.loads((DATA / "rcsb" / f"{identifier}.json").read_text())


@pytest.mark.parametrize("identifier", LEGACY_PINS)
def test_complete_wire_originals_and_decoded_entries_are_distinguished(identifier):
    capture = json.loads((DATA / "capture.json").read_text())
    record = next(row for row in capture["records"] if row["pdb_id"] == identifier)
    raw = (DATA / "wire" / f"{identifier}.graphql.json").read_bytes()
    request = (DATA / "wire" / f"{identifier}.request.json").read_bytes()
    decoded = (DATA / "rcsb" / f"{identifier}.json").read_bytes()
    receipt = record["receipt"]
    assert hashlib.sha256(raw).hexdigest() == receipt["sha256"]
    assert hashlib.sha256(request).hexdigest() == receipt["request_sha256"]
    assert hashlib.sha256(decoded).hexdigest() == record["decoded_sha256"]
    assert len(raw) == receipt["bytes"]
    assert receipt["response_status"] == 200 and receipt["complete_within_budget"]
    wire = json.loads(raw)
    assert not wire.get("errors")
    assert wire["data"]["entry"] == json.loads(decoded)
    assert json.loads(request)["query"].strip() == rcsb.STRUCTURE_QUERY.strip()
    assert record["acquisition_trace"]["records"][0]["network_attempts"] == 1


@pytest.mark.parametrize("identifier", LEGACY_PINS)
def test_native_parent_revision_order_and_support_survive_mapping(identifier):
    original = entry(identifier)
    before = deepcopy(original)
    mapped = map_structure_entities(original, "2026-10-29")
    assertion = mapped["source_assertions"][0]
    value = assertion["asserted_value"]
    assert value["assembly_generation_inputs"] == {"assemblies": before["assemblies"]}
    assert value["accession_info"] == before["rcsb_accession_info"]
    relation = mapped["relationships"][0]
    assert assertion["id"] in relation["source_assertion_ids"]
    for projected, native in zip(
        relation["qualifiers"]["assemblies"], before["assemblies"], strict=True
    ):
        assert projected["generation"] == {key: native[key] for key in KEYS}
        assert (
            projected["id"]
            == native["rcsb_assembly_container_identifiers"]["assembly_id"]
        )
    assert original == before
    original["assemblies"].clear()
    assert value["assembly_generation_inputs"]["assemblies"] == before["assemblies"]
    assert relation["qualifiers"]["assemblies"][0]["generation"]


def test_alternative_generators_are_not_resolved_from_descriptive_polymer_counts():
    mapped = map_structure_entities(entry(), "2026-10-29")
    first, second = mapped["relationships"][0]["qualifiers"]["assemblies"]
    assert first["oligomeric_count"] == 2 and second["oligomeric_count"] == 1
    a, b = (row["generation"][KEYS[0]][0] for row in (first, second))
    assert (a["ordinal"], a["oper_expression"]) == (1, "1,2")
    assert (b["ordinal"], b["oper_expression"]) == (2, "1")
    assert a["asym_id_list"] == b["asym_id_list"] == ["A", "B"]
    assert set(first["generation"]) == set(KEYS)
    # Source descriptors and raw generation declarations assert no reconciled
    # physical membership, no assembly-specific contacts and no coordinates.
    assert "members" not in first and "contacts" not in first


@pytest.mark.parametrize("value", [None, [], {}, "malformed", [None, {"ordinal": 1}]])
def test_null_empty_malformed_and_unknown_context_remain_verbatim(value):
    original = entry()
    original["assemblies"][0][KEYS[0]] = deepcopy(value)
    del original["assemblies"][0][KEYS[1]]
    mapped = map_structure_entities(original, "synthetic retrieval")
    assert mapped["relationships"][0]["qualifiers"]["assemblies"][0]["generation"] == {
        KEYS[0]: value
    }
    assert mapped["source_assertions"][0]["asserted_value"][
        "assembly_generation_inputs"
    ] == {"assemblies": original["assemblies"]}


def test_duplicates_foreign_identity_and_unexpanded_products_keep_original_locations():
    original = entry()
    row = original["assemblies"][0]
    row[KEYS[0]][0].update(
        assembly_id="foreign",
        asym_id_list=["A", "A", "unknown"],
        oper_expression="(1-1000000000)(1-1000000000)",
    )
    row[KEYS[0]].append(deepcopy(row[KEYS[0]][0]))
    row[KEYS[1]].append(deepcopy(row[KEYS[1]][0]))
    original["assemblies"] = [original["assemblies"][1], row, deepcopy(row)]
    mapped = map_structure_entities(original, "synthetic retrieval")
    value = mapped["source_assertions"][0]["asserted_value"]
    assert value["assembly_generation_inputs"]["assemblies"] == original["assemblies"]
    assert len(mapped["relationships"][0]["qualifiers"]["assemblies"]) == 3
    assert (
        value["assembly_generation_inputs"]["assemblies"][1][KEYS[0]][0]["assembly_id"]
        == "foreign"
    )


@pytest.mark.parametrize("identifier", LEGACY_PINS)
def test_legacy_assertions_keep_exact_original_pins_without_backfill(identifier):
    legacy = json.loads(Path(f"temp_data/rcsb/{identifier}.json").read_text())
    mapped = map_structure_entities(legacy, "fixed legacy retrieval")
    assert (
        hashlib.sha256(canonical_json(mapped["source_assertions"]).encode()).hexdigest()
        == LEGACY_PINS[identifier]
    )
    assert all(
        "assembly_generation_inputs" not in row["asserted_value"]
        for row in mapped["source_assertions"]
    )
    assert all(
        "generation" not in row
        for row in mapped["relationships"][0]["qualifiers"]["assemblies"]
    )


@pytest.mark.parametrize(
    "query", [rcsb.STRUCTURE_QUERY, rcsb.PARTIAL_QUERY, rcsb.BATCH_QUERY]
)
def test_single_batch_and_instance_fallback_all_request_native_generation(query):
    assert (
        "pdbx_struct_assembly_gen { assembly_id ordinal asym_id_list oper_expression }"
        in query
    )
    assert "pdbx_struct_oper_list { id name type symmetry_operation }" in query
    assert "matrix" not in query and "vector" not in query


def test_human_agent_and_inert_saved_reading_reach_original_generation(
    tmp_path, monkeypatch
):
    card, _ = sabueso.resolve(
        "P52270",
        resolver=EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=rcsb.FixtureRCSBClient(str(DATA)),
        ),
        structures=["2V5B"],
    )
    original = card.to_dict()
    explorer = card.explore()
    view = explorer.view("quaternary_structure").filter("kind", equals="assembly")
    assert len(view.items()) == 2
    native = view.items()[0].open().native_payload
    assert native["generation"][KEYS[0]][0]["oper_expression"] == "1,2"
    page = explorer.access.read(view.items()[0].payload_location).page(max_bytes=8192)
    assert any(row["key"] == "generation" for row in page["items"])
    path = tmp_path / "original.json"
    view.save(path)

    def forbidden(*args, **kwargs):
        raise AssertionError("Saved reading must not remap or acquire source records")

    monkeypatch.setattr(rcsb.FixtureRCSBClient, "fetch_structure", forbidden)
    monkeypatch.setattr(
        "sabueso.mappings.rcsb_structures.map_structure_entities", forbidden
    )
    saved = sabueso.read_exploration(path)
    assert saved.items()[0].open().native_payload == native
    sources = [
        item.open().native_payload
        for item in saved.items()[0].related().filter("role", equals="source").items()
    ]
    source = next(row for row in sources if row["source"]["name"] == "RCSB PDB")
    assert (
        source["asserted_value"]["assembly_generation_inputs"]["assemblies"]
        == entry()["assemblies"]
    )
    assert card.to_dict() == original
