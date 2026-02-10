import json
from pathlib import Path
import pytest

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.merge import merge_mapping_results
from sabueso.mappings.chembl import map_molecule as map_chembl_compound
from sabueso.mappings.pubchem import map_compound as map_pubchem_compound
from sabueso.mappings.uniprot import map_protein as map_uniprot_protein
from sabueso.resolver import load_selection_rules


def _load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_end_to_end_small_molecule_offline():
    chembl_path = Path("temp_data/CHEMBL90555.json")
    pubchem_path = Path("temp_data/66414.json")
    if not chembl_path.exists() or not pubchem_path.exists():
        pytest.skip("Missing temp_data for small molecule end-to-end test.")

    chembl = _load(str(chembl_path))
    pubchem = _load(str(pubchem_path))
    rules = load_selection_rules()

    chembl_map = map_chembl_compound(chembl, retrieved_at="2026-02-01")
    pubchem_map = map_pubchem_compound(pubchem, retrieved_at="2026-02-02")

    merged = merge_mapping_results([chembl_map, pubchem_map])
    card = build_card_from_mapping(merged, meta={"entity_type": "small_molecule"}, selection_rules=rules)

    assert card.get("identifiers.smiles") is not None
    assert card.get("properties.physchem.molecular_weight") is not None


def test_end_to_end_protein_offline():
    uniprot = _load("temp_data/P52789.json")
    rules = load_selection_rules()

    uni_map = map_uniprot_protein(uniprot, retrieved_at="2026-02-01")
    merged = merge_mapping_results([uni_map])
    card = build_card_from_mapping(merged, meta={"entity_type": "protein"}, selection_rules=rules)

    assert card.get("identifiers.uniprot") is not None
