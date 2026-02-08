from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.ted import map_ted_domains


def test_ted_mapping_offline():
    ted_json = {"id": "TED0001", "name": "Mock TED domain"}
    mapping = map_ted_domains(ted_json, retrieved_at="2026-02-04")
    card = build_card_from_mapping(mapping, meta={"entity_type": "protein"})

    assert card.get("annotations.domains") is not None
