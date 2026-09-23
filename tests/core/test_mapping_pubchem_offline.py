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
    assert card.get("identifiers.pubchem") is not None

    mw = card.get("properties.physchem.molecular_weight")
    for sa_id in mw.get("source_assertion_ids", []):
        assert card.source_assertion_store.get(sa_id) is not None


def test_pubchem_pc_compounds_record_offline():
    from sabueso.tools.db.pubchem import create_compound_card_from_file

    card = create_compound_card_from_file(
        "temp_data/66414.json", retrieved_at="2026-02-04"
    )

    assert card.id == "sabueso:small_molecule:pubchem:66414"
    assert card.get("identifiers.pubchem")["value"] == "66414"
    assert card.get("identifiers.inchikey")["value"] == "CQOQDQWUFQDJMK-SSTWWWIQSA-N"
    assert card.get("properties.physchem.formula")["value"] == "C19H26O3"
    assert (
        card.get("identifiers.smiles")["value"]
        == "CC12CCC3C(C1CCC2O)CCC4=CC(=C(C=C34)OC)O"
    )
    for fp in (
        "properties.physchem.logp",
        "properties.physchem.tpsa",
        "properties.physchem.hbd",
        "properties.physchem.hba",
        "properties.physchem.rotatable_bonds",
        "identifiers.inchi",
    ):
        assert card.get(fp) is not None, fp

    mw = card.get("properties.physchem.molecular_weight")
    assert mw["value"] == 302.4
    assertion = card.source_assertion_store.get(mw["source_assertion_ids"][0])
    assert assertion["asserted_value"] == "302.4"
    assert assertion["normalized_value"] == 302.4


def test_pubchem_unsupported_payload_is_rejected():
    import pytest

    from sabueso.core.errors import SchemaError

    with pytest.raises(SchemaError):
        map_compound({"unexpected": []}, retrieved_at="2026-02-04")
