from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.scope import map_scope_domains


def test_scope_mapping_offline():
    scope_json = {"sunid": 1234, "name": "Mock SCOPe"}
    mapping = map_scope_domains(scope_json, retrieved_at="2026-02-04")
    card = build_card_from_mapping(mapping, meta={"entity_type": "protein"})

    assert card.get("annotations.domains") is not None
