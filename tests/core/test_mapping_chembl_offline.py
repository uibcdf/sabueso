from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.chembl import map_molecule


def test_chembl_mapping_offline():
    chembl_json = {
        "molecule_chembl_id": "CHEMBL1",
        "molecule_properties": {"alogp": 2.3},
        "molecule_structures": {"canonical_smiles": "CCO"},
    }
    mapping = map_molecule(chembl_json, retrieved_at="2026-02-04")
    card = build_card_from_mapping(mapping, meta={"entity_type": "small_molecule"})

    assert card.get("identifiers.chembl") is not None
    assert card.get("properties.physchem.logp") is not None
    assert card.get("identifiers.smiles") is not None

    logp = card.get("properties.physchem.logp")
    for ev_id in logp.get("evidence_ids", []):
        assert card.evidence_store.get(ev_id) is not None
