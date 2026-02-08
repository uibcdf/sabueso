from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.cath import map_cath_domains


def test_cath_mapping_offline():
    cath_json = {"domain_id": "1abcA00", "name": "Mock domain"}
    mapping = map_cath_domains(cath_json, retrieved_at="2026-02-04")
    card = build_card_from_mapping(mapping, meta={"entity_type": "protein"})

    assert card.get("annotations.domains") is not None
