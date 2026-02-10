import json
from pathlib import Path
import pytest

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.merge import merge_mapping_results
from sabueso.mappings.uniprot import map_protein
from sabueso.mappings.pdb import map_structure as map_pdb_entry
from sabueso.mappings.interpro import map_interpro_domains
from sabueso.resolver import load_selection_rules


def _load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_end_to_end_protein_with_multiple_sources_offline():
    uniprot = _load("temp_data/P52789.json")

    pdb_path = Path("temp_data/2NZT.json")
    interpro_path = Path("temp_data/IPR000001.json")
    if not pdb_path.exists() or not interpro_path.exists():
        pytest.skip("Missing temp_data for PDB/InterPro offline test.")

    pdb = _load(str(pdb_path))
    interpro = _load(str(interpro_path))

    rules = load_selection_rules()

    uni_map = map_protein(uniprot, retrieved_at="2026-02-01")
    pdb_map = map_pdb_entry(pdb, pdb_id="2NZT", retrieved_at="2026-02-02")
    ipr_map = map_interpro_domains(interpro, retrieved_at="2026-02-03")

    merged = merge_mapping_results([uni_map, pdb_map, ipr_map])
    card = build_card_from_mapping(merged, meta={"entity_type": "protein"}, selection_rules=rules)

    assert card.get("identifiers.uniprot") is not None
    assert card.get("structure.entry_metadata.experimental_method") is not None
    assert card.get("annotations.domains") is not None
