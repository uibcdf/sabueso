import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.merge import merge_mapping_results
from sabueso.mappings.uniprot import map_protein
from validate_card import validate_card


def test_card_schema_validation_basic():
    uniprot = json.loads(Path("temp_data/P52789.json").read_text(encoding="utf-8"))
    mapping = map_protein(uniprot, retrieved_at="2026-02-01")
    merged = merge_mapping_results([mapping])
    card = build_card_from_mapping(merged, meta={"entity_type": "protein"})
    errors = validate_card(card.to_dict())
    assert errors == []
