from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.pdb import map_structure


def test_pdb_mapping_offline():
    pdb_id = "2NZT"
    pdb_json = {
        "entry": {
            "struct": {"title": "Mock structure"},
            "rcsb_entry_info": {
                "experimental_method": "X-ray",
                "resolution_combined": [2.0],
            },
        }
    }
    mapping = map_structure(pdb_json, pdb_id=pdb_id, retrieved_at="2026-02-04")
    card = build_card_from_mapping(mapping, meta={"entity_type": "protein"})

    assert card.get("structure.entry_metadata.title") is not None
    assert card.get("structure.entry_metadata.experimental_method") is not None
    assert card.get("structure.entry_metadata.resolution") is not None

    # evidence exists
    title = card.get("structure.entry_metadata.title")
    for ev_id in title.get("evidence_ids", []):
        assert card.evidence_store.get(ev_id) is not None
