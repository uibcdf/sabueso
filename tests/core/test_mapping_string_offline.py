from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.stringdb import map_string_interactions


def test_string_mapping_offline():
    string_json = [
        {"preferredName_A": "TP53", "preferredName_B": "MDM2"},
        {"preferredName_A": "TP53", "preferredName_B": "BAX"},
    ]
    mapping = map_string_interactions(string_json, query_name="TP53", retrieved_at="2026-02-04")
    card = build_card_from_mapping(mapping, meta={"entity_type": "protein"})

    assert card.get("interactions.binding_partners") is not None
