from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.interpro import map_interpro_domains


def test_interpro_mapping_offline():
    interpro_json = {
        "domains": [
            {"id": "IPR000001", "name": "Kringle"},
        ]
    }
    mapping = map_interpro_domains(interpro_json, retrieved_at="2026-02-04")
    card = build_card_from_mapping(mapping, meta={"entity_type": "protein"})

    assert card.get("annotations.domains") is not None
    doms = card.get("annotations.domains")
    for ev_id in doms.get("evidence_ids", []):
        assert card.evidence_store.get(ev_id) is not None
