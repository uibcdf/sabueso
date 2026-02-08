from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.go import map_go_terms


def test_go_mapping_offline():
    go_json = {
        "terms": [
            {"id": "GO:0008150", "name": "biological_process"},
            {"id": "GO:0003674", "name": "molecular_function"},
        ]
    }
    mapping = map_go_terms(go_json, retrieved_at="2026-02-04")
    card = build_card_from_mapping(mapping, meta={"entity_type": "protein"})

    assert card.get("annotations.go_terms") is not None
    terms = card.get("annotations.go_terms")
    for ev_id in terms.get("evidence_ids", []):
        assert card.evidence_store.get(ev_id) is not None
