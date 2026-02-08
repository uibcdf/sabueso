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
        },
        "rcsb_accession_info": {
            "deposit_date": "2006-11-25T00:00:00+0000",
            "initial_release_date": "2006-12-05T00:00:00+0000",
        },
        "rcsb_primary_citation": {
            "pdbx_database_id_doi": "10.1234/example",
            "pdbx_database_id_pub_med": "12345678",
            "title": "Mock citation",
        },
    }
    mapping = map_structure(pdb_json, pdb_id=pdb_id, retrieved_at="2026-02-04")
    card = build_card_from_mapping(mapping, meta={"entity_type": "protein"})

    assert card.get("structure.entry_metadata.title") is not None
    assert card.get("structure.entry_metadata.experimental_method") is not None
    assert card.get("structure.entry_metadata.resolution") is not None
    assert card.get("structure.entry_metadata.deposition_date") is not None
    assert card.get("structure.entry_metadata.release_date") is not None
    assert card.get("structure.entry_metadata.primary_citation.doi") is not None

    # evidence exists
    title = card.get("structure.entry_metadata.title")
    for ev_id in title.get("evidence_ids", []):
        assert card.evidence_store.get(ev_id) is not None
