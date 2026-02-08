from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.biogrid import map_biogrid_interactions


def test_biogrid_mapping_offline():
    biogrid_json = {
        "1": {"OFFICIAL_SYMBOL_A": "TP53", "OFFICIAL_SYMBOL_B": "MDM2"},
        "2": {"OFFICIAL_SYMBOL_A": "TP53", "OFFICIAL_SYMBOL_B": "BAX"},
    }
    mapping = map_biogrid_interactions(biogrid_json, query_name="TP53", retrieved_at="2026-02-04")
    card = build_card_from_mapping(mapping, meta={"entity_type": "protein"})

    assert card.get("interactions.binding_partners") is not None
