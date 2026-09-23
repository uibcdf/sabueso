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

    # function field should exist or be None; if present, source assertion IDs must exist
    func = card.get("annotations.function")
    if func is not None:
        sa_ids = func.get("source_assertion_ids", [])
        assert sa_ids, "function should have source_assertion_ids"
        for sa_id in sa_ids:
            assert card.source_assertion_store.get(sa_id) is not None

    # binding site features should have source assertions
    bs = card.get("features_positional.binding_site")
    if bs is not None:
        sa_ids = bs.get("source_assertion_ids", [])
        assert sa_ids, "binding sites should have source_assertion_ids"
        for sa_id in sa_ids:
            assert card.source_assertion_store.get(sa_id) is not None
