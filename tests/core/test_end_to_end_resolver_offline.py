import json
from pathlib import Path

import pytest

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.errors import SchemaError
from sabueso.core.merge import merge_mapping_results
from sabueso.mappings.chembl import map_molecule as map_chembl_compound
from sabueso.mappings.pubchem import map_compound as map_pubchem_compound
from sabueso.mappings.uniprot import map_protein as map_uniprot_protein
from sabueso.resolver import load_selection_rules
from sabueso.tools.card.small_molecule import single_molecule_card


def _load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_end_to_end_small_molecule_offline():
    # Same molecule in both sources: vincristine (InChIKey OGWKCGZFUXNPDA-XQKSVPLYSA-N).
    # They are merged because their identity is resolved first: both records state the
    # same standard InChIKey, the card's anchor (#25).
    chembl = _load("temp_data/CHEMBL90555.json")
    pubchem = _load("temp_data/5978.json")
    card = single_molecule_card(
        chembl={"retrieved_at": "2026-02-01", "molecules": {"CHEMBL90555": chembl}},
        pubchem={"retrieved_at": "2026-02-02", "compounds": {"5978": pubchem}},
    )

    assert card.id == "sabueso:small_molecule:inchikey:OGWKCGZFUXNPDA-XQKSVPLYSA-N"
    assert {r["subject_ref"] for r in card.relationships("same_as")} == {
        "chembl:CHEMBL90555",
        "pubchem:5978",
    }
    assert card.get("identifiers.smiles") is not None
    assert card.get("properties.physchem.molecular_weight") is not None
    assert card.get("identifiers.inchikey")["value"] == "OGWKCGZFUXNPDA-XQKSVPLYSA-N"
    conflicting = {c["field"] for c in card.quality.get("conflicts", [])}
    assert "identifiers.inchikey" not in conflicting


def test_records_of_several_subjects_are_not_merged_unresolved():
    # The same two records, merged without resolving their identity: refused (#21).
    chembl_map = map_chembl_compound(_load("temp_data/CHEMBL90555.json"), "2026-02-01")
    pubchem_map = map_pubchem_compound(_load("temp_data/5978.json"), "2026-02-02")
    merged = merge_mapping_results([chembl_map, pubchem_map])
    with pytest.raises(SchemaError, match="several subjects"):
        build_card_from_mapping(merged, meta={"entity_type": "small_molecule"})


def test_records_of_different_molecules_never_make_one_card():
    other = _load("temp_data/66414.json")  # PubChem CID 66414: a different molecule
    with pytest.raises(SchemaError, match="2 molecules"):
        single_molecule_card(
            pubchem={
                "retrieved_at": "x",
                "compounds": {"5978": _load("temp_data/5978.json"), "66414": other},
            }
        )


def test_end_to_end_protein_offline():
    uniprot = _load("temp_data/P52789.json")
    rules = load_selection_rules()

    uni_map = map_uniprot_protein(uniprot, retrieved_at="2026-02-01")
    merged = merge_mapping_results([uni_map])
    card = build_card_from_mapping(
        merged, meta={"entity_type": "protein"}, selection_rules=rules
    )

    assert card.get("identifiers.uniprot") is not None
