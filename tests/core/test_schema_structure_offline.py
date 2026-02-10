from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.merge import merge_mapping_results
from sabueso.mappings.uniprot import map_protein


def test_card_sections_have_value_and_evidence_ids():
    mapping = map_protein({"primaryAccession": "P00000"}, retrieved_at="2026-02-01")
    merged = merge_mapping_results([mapping])
    card = build_card_from_mapping(merged, meta={"entity_type": "protein"})

    node = card.get("identifiers.uniprot")
    assert isinstance(node, dict)
    assert "value" in node
    assert "evidence_ids" in node
