from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.phosphositeplus import map_psp_ptm


def test_psp_mapping_offline():
    psp_json = {"ptm": [{"position": 10, "modification": "Phosphorylation"}]}
    mapping = map_psp_ptm(psp_json, retrieved_at="2026-02-04")
    card = build_card_from_mapping(mapping, meta={"entity_type": "protein"})

    assert card.get("features_positional.modified_residue") is not None
