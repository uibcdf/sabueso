from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.pubchem import map_compound


def test_pubchem_mapping_offline():
    pubchem_json = {
        "PropertyTable": {
            "Properties": [
                {"CID": 66414, "MolecularWeight": 302.36, "CanonicalSMILES": "CC"}
            ]
        }
    }
    mapping = map_compound(pubchem_json, retrieved_at="2026-02-04")
    card = build_card_from_mapping(mapping, meta={"entity_type": "small_molecule"})

    assert card.get("properties.physchem.molecular_weight") is not None
    assert card.get("identifiers.smiles") is not None
    assert card.get("identifiers.secondary_ids.pubchem") is not None

    mw = card.get("properties.physchem.molecular_weight")
    for ev_id in mw.get("evidence_ids", []):
        assert card.evidence_store.get(ev_id) is not None
