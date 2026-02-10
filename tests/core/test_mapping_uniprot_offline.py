import json
from pathlib import Path

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.uniprot import map_protein


def test_uniprot_mapping_offline():
    data = json.loads(Path("temp_data/P52789.json").read_text(encoding="utf-8"))
    mapping = map_protein(data, retrieved_at="2026-02-04")
    card = build_card_from_mapping(mapping, meta={"entity_type": "protein"})

    # basic fields exist
    assert card.get("identifiers.uniprot") is not None
    assert card.get("names.canonical_name") is not None

    # function field should exist or be None; if present, evidence IDs must exist
    func = card.get("uniprot_comments.function")
    if func is not None:
        ev_ids = func.get("evidence_ids", [])
        assert ev_ids, "function should have evidence_ids"
        for ev_id in ev_ids:
            assert card.evidence_store.get(ev_id) is not None

    # binding site features should have evidence
    bs = card.get("features_positional.binding_site")
    if bs is not None:
        ev_ids = bs.get("evidence_ids", [])
        assert ev_ids, "binding sites should have evidence_ids"
        for ev_id in ev_ids:
            assert card.evidence_store.get(ev_id) is not None
