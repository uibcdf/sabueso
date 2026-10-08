"""Recovered chemical descriptions do not establish or merge molecular identity."""

import copy
import json
from pathlib import Path

import pytest

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.errors import ConnectorError
from sabueso.core.merge import merge_mapping_results
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.chebi import map_chebi_identity

ORIGINALS = json.loads(
    Path("temp_data/chebi/compounds.json").read_text(encoding="utf-8")
)["compounds"]


@pytest.mark.parametrize("identifier", sorted(ORIGINALS))
def test_native_names_and_formulas_have_independent_original_source_support(identifier):
    record = copy.deepcopy(ORIGINALS[identifier])
    before = copy.deepcopy(record)
    data = record.get("data", record)
    mapping, key = map_chebi_identity(record, "2026-09-30")
    for path, native in (
        ("names.canonical_name", data["name"]),
        ("properties.physchem.formula", data["chemical_data"]["formula"]),
    ):
        assert mapping["fields"][path] == native
        (reference,) = mapping["field_source_assertions"][path]
        assertion = next(
            a for a in mapping["source_assertions"] if a["id"] == reference
        )
        assert assertion["asserted_value"] == native
        assert assertion["source"]["name"] == "ChEBI"
        assert assertion["source"]["record_id"] == identifier
        assert assertion["source"].get("version") is None
        assert assertion["subject_ref"] == "chebi:" + identifier.split(":")[1]
        assert assertion["retrieved_at"] == "2026-09-30"
        assert assertion["source_metadata"]["stars"] == data["stars"]
        assert "knowledge_class" not in assertion and "evidence_class" not in assertion
    assert key == data["default_structure"]["standard_inchi_key"]
    assert mapping["relationships"][0]["object_ref"] == "inchikey:" + key
    assert record == before


@pytest.mark.parametrize("value", [None, ""])
def test_missing_descriptions_do_not_become_empty_assertions(value):
    record = copy.deepcopy(ORIGINALS["CHEBI:28445"])
    record["data"]["name"] = value
    record["data"]["chemical_data"]["formula"] = value
    mapping, key = map_chebi_identity(record, "fixture")
    assert key and "names.canonical_name" not in mapping["fields"]
    assert "properties.physchem.formula" not in mapping["fields"]
    assert not any(
        a["field_path"] in {"names.canonical_name", "properties.physchem.formula"}
        for a in mapping["source_assertions"]
    )


@pytest.mark.parametrize("chemical", [None, {}])
def test_unstated_chemical_data_keeps_the_source_name_without_inventing_formula(
    chemical,
):
    record = copy.deepcopy(ORIGINALS["CHEBI:28445"])
    record["data"]["chemical_data"] = chemical
    mapping, _ = map_chebi_identity(record, "fixture")
    assert mapping["fields"]["names.canonical_name"] == "vincristine"
    assert "properties.physchem.formula" not in mapping["fields"]


@pytest.mark.parametrize("path", ["name", "formula"])
@pytest.mark.parametrize("invalid", [False, 0, [], {}, "   "])
def test_malformed_descriptive_fields_fail_without_silently_skipping_them(
    path, invalid
):
    record = copy.deepcopy(ORIGINALS["CHEBI:28445"])
    data = record["data"] if path == "name" else record["data"]["chemical_data"]
    data[path] = invalid
    with pytest.raises(ConnectorError, match="native text"):
        map_chebi_identity(record, "fixture")


@pytest.mark.parametrize("chemical", [[], "bad", True])
def test_foreign_chemical_shape_is_not_treated_as_missing_data(chemical):
    record = copy.deepcopy(ORIGINALS["CHEBI:28445"])
    record["data"]["chemical_data"] = chemical
    with pytest.raises(ConnectorError, match="chemical_data"):
        map_chebi_identity(record, "fixture")


def test_name_and_formula_never_supply_a_missing_or_nonstandard_identity_key():
    record = copy.deepcopy(ORIGINALS["CHEBI:28445"])
    record["data"]["default_structure"] = None
    mapping, key = map_chebi_identity(record, "fixture")
    assert key is None and not mapping["fields"] and not mapping["relationships"]


def test_conflicting_formula_stays_supported_beside_the_selected_value_after_merge():
    record = copy.deepcopy(ORIGINALS["CHEBI:28445"])
    mapping, key = map_chebi_identity(record, "fixture")
    subject = "chebi:28445"
    path = "properties.physchem.formula"
    # Synthetic second declaration exercises selection, not provider qualification.
    alternative = make_source_assertion(
        path, "C46H56N4O11", "PubChem", "1", "fixture", subject_ref=subject
    )
    other = {
        "fields": {path: alternative["asserted_value"]},
        "source_assertions": [alternative],
        "field_source_assertions": {path: [alternative["id"]]},
    }
    merged = merge_mapping_results([mapping, other])
    merged["fields"]["identifiers.inchikey"] = key
    card = build_card_from_mapping(merged, meta={"entity_type": "small_molecule"})
    assert card.get(path)["value"] == "C46H56N4O11"
    assert any(c["field"] == path for c in card.quality["conflicts"])
    assertions = card.source_assertion_store.find_by_field(path)
    assert {a["asserted_value"] for a in assertions} == {"C46H56N4O10", "C46H56N4O11"}
    assert card.get(path)["source_assertion_ids"] == [alternative["id"]]
    (conflict,) = [c for c in card.quality["conflicts"] if c["field"] == path]
    assert {a["id"] for a in assertions} == {
        identifier for group in conflict["source_assertion_ids"] for identifier in group
    }
    assert {a["source"]["name"] for a in assertions} == {"ChEBI", "PubChem"}
