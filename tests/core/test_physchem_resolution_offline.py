"""Like is compared with like when resolving physicochemical fields (uibcdf/sabueso#10).

Vincristine in ChEMBL (CHEMBL90555) and PubChem (CID 5978), both anchored at InChIKey
OGWKCGZFUXNPDA-XQKSVPLYSA-N, used to produce five false conflicts.
"""

import json
from pathlib import Path

import pytest

from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.resolver import load_selection_rules, resolve_field
from sabueso.tools.card.small_molecule import single_molecule_card
from sabueso.tools.db.chembl import create_molecule_card_from_json

RULES = load_selection_rules()


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def vincristine():
    return single_molecule_card(
        chembl={
            "retrieved_at": "2026-02-01",
            "molecules": {"CHEMBL90555": _load("temp_data/CHEMBL90555.json")},
        },
        pubchem={
            "retrieved_at": "2026-02-02",
            "compounds": {"5978": _load("temp_data/5978.json")},
        },
    )


def _sources(card, field_path):
    return sorted(
        card.source_assertion_store.get(i)["source"]["name"]
        for i in card.get(field_path)["source_assertion_ids"]
    )


def test_no_false_conflicts_remain(vincristine):
    assert vincristine.quality.get("conflicts") is None


def test_values_agreeing_at_the_stated_precision_support_each_other(vincristine):
    # 824.97 (ChEMBL) and "825.0" (PubChem) agree at one decimal; 171.17 and 171 at zero.
    assert vincristine.get("properties.physchem.molecular_weight")["value"] == 824.97
    assert _sources(vincristine, "properties.physchem.molecular_weight") == [
        "ChEMBL",
        "PubChem",
    ]
    assert _sources(vincristine, "properties.physchem.tpsa") == ["ChEMBL", "PubChem"]


def test_method_dependent_values_are_alternatives_not_conflicts(vincristine):
    alternatives = {a["field"]: a for a in vincristine.quality["alternatives"]}
    logp = {
        v["within"]["source_metadata.method"]: v["values"]
        for v in alternatives["properties.physchem.logp"]["values"]
    }
    assert logp == {"ALogP": [3.52], "XLogP3": [2.8]}
    rotatable = alternatives["properties.physchem.rotatable_bonds"]["values"]
    assert sorted(v["values"][0] for v in rotatable) == [8, 10]
    # The selected value is supported only by the assertion that states it.
    assert _sources(vincristine, "properties.physchem.logp") == ["ChEMBL"]


def test_smiles_are_never_compared_across_sources(vincristine):
    # Both isomeric, but canonicalised by different toolkits: different strings, one
    # molecule. Identity is the InChIKey's job.
    smiles = {a["field"]: a for a in vincristine.quality["alternatives"]}[
        "identifiers.smiles"
    ]
    assert [v["within"]["source.name"] for v in smiles["values"]] == [
        "ChEMBL",
        "PubChem",
    ]
    assert _sources(vincristine, "identifiers.smiles_connectivity") == ["PubChem"]


def _sa(value, source="S"):
    sa = make_source_assertion(
        "properties.physchem.molecular_weight",
        value,
        source,
        f"{source}-{value}",
        "2026-09-23",
    )
    return sa


@pytest.mark.parametrize(
    "a, b, agree",
    [
        ("824.97", "825.0", True),  # agree at one decimal
        ("171.17", 171, True),  # agree at zero decimals
        ("2.84", 2.8, True),
        ("824.4", 825, False),  # 0.6 apart at zero decimals
        ("824.97", "830.0", False),  # a real disagreement
    ],
)
def test_stated_precision_agreement(a, b, agree):
    result = resolve_field(
        "properties.physchem.molecular_weight",
        [_sa(a, "ChEMBL"), _sa(b, "PubChem")],
        RULES,
    )
    assert (result["conflict"] is None) is agree


def test_a_real_disagreement_within_one_method_is_still_a_conflict():
    logp = [
        make_source_assertion("properties.physchem.logp", v, src, "r", "2026-09-23")
        for v, src in ((3.52, "ChEMBL"), (1.0, "PubChem"))
    ]
    for sa in logp:
        sa["source_metadata"] = {"method": "XLogP3"}
    result = resolve_field("properties.physchem.logp", logp, RULES)
    assert result["conflict"]["values"] == [3.52, 1.0]
    assert result["alternatives"] is None


def test_equal_values_of_different_methods_never_support_each_other():
    logp = [
        make_source_assertion("properties.physchem.logp", 3.0, src, "r", "2026-09-23")
        for src in ("ChEMBL", "PubChem")
    ]
    logp[0]["source_metadata"] = {"method": "ALogP"}
    logp[1]["source_metadata"] = {"method": "XLogP3"}
    result = resolve_field("properties.physchem.logp", logp, RULES)
    assert result["source_assertion_ids"] == [logp[0]["id"]]


def test_molecular_weight_is_that_of_the_anchored_structure():
    record = _load("temp_data/CHEMBL90555.json")
    salt = json.loads(json.dumps(record))
    # A salt record: the full weight is the salt's; mw_freebase is the parent's, another
    # structure with its own InChIKey and card.
    salt["molecule_properties"]["full_mwt"] = "923.04"
    card = create_molecule_card_from_json(salt, "2026-09-23")
    assert card.get("properties.physchem.molecular_weight")["value"] == 923.04
    (sa_id,) = card.get("properties.physchem.molecular_weight")["source_assertion_ids"]
    assertion = card.source_assertion_store.get(sa_id)
    assert (assertion["asserted_value"], assertion["source_metadata"]) == (
        "923.04",
        {"unit": "Da"},
    )


def test_the_card_records_the_rules_that_resolved_it(vincristine):
    assert vincristine.selection_rules["version"] == RULES["version"] == "0.2.0"


def test_mixed_retrieval_time_formats_can_be_compared():
    # Online clients stamp timezone-aware times; fixtures carry plain dates.
    aware = make_source_assertion(
        "names.canonical_name", "A", "S", "r1", "2026-09-23T19:01:07+00:00"
    )
    naive = make_source_assertion("names.canonical_name", "B", "S", "r2", "2026-02-01")
    rules = {"field_rules": {"names.canonical_name": {"strategy": "most_recent"}}}
    result = resolve_field("names.canonical_name", [naive, aware], rules)
    assert result["selected_value"] == "A"
