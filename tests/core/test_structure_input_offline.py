"""Molecules given as a structure, a SMILES or an InChI (#93): PubChem states which
compound the structure is, and the card is that compound's. Sabueso never computes a
key from a structure.

Vincristine: PubChem CID 5978, InChIKey OGWKCGZFUXNPDA-XQKSVPLYSA-N. Lookups frozen
from PubChem PUG REST on 2026-09-29 (temp_data/pubchem/structures.json).
"""

import json

import pytest

import sabueso
from sabueso.core.errors import ArgumentError
from sabueso.tools.db import pubchem
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.pubchem import FixturePubChemClient
from sabueso.tools.db.unichem import FixtureUniChemClient

VCR = "sabueso:small_molecule:inchikey:OGWKCGZFUXNPDA-XQKSVPLYSA-N"
LOOKUPS = json.loads(
    open("temp_data/pubchem/structures.json", encoding="utf-8").read()
)["lookups"]
VCR_SMILES, FLAT_SMILES, VCR_INCHI, ABSENT, UNREADABLE = (
    lookup["query"] for lookup in LOOKUPS
)


def _clients(**options):
    return dict(
        chembl_client=FixtureChEMBLClient("temp_data"),
        ccd_client=FixtureCCDClient("temp_data"),
        unichem_client=FixtureUniChemClient("temp_data"),
        pubchem_client=FixturePubChemClient("temp_data"),
        **options,
    )


@pytest.mark.parametrize(
    "query",
    [f"smiles:{VCR_SMILES}", f"inchi:{VCR_INCHI}", VCR_INCHI],
)
def test_a_structure_resolves_to_the_compound_pubchem_states(query):
    card, resolution = sabueso.resolve(query, **_clients())
    assert (resolution.status, card.id) == ("resolved", VCR)
    structure = resolution.decision["structure"]
    assert structure["basis"] == "pubchem_structure_lookup"
    assert structure["cids"] == ["5978"]
    assert structure["given"] == query.removeprefix("smiles:").removeprefix("inchi:")
    assert "pubchem_structure_lookup" in resolution.decision["rules"]
    # The same card as from the CID: UniChem links ChEMBL's record of the structure.
    assert "chembl:CHEMBL90555" in {
        r["subject_ref"] for r in card.relationships("same_as")
    }
    assert card.quality["entity_resolution"]["decision"]["structure"] == structure


def test_stereochemistry_is_as_pubchem_handles_it():
    # Without stereocentres, PubChem matches the compound whose stereochemistry is
    # undefined, which is not vincristine. Sabueso does not normalize the structure.
    card, resolution = sabueso.resolve(f"smiles:{FLAT_SMILES}", **_clients())
    assert resolution.decision["structure"]["cids"] == ["3717450"]
    assert card.id != VCR
    assert card.get("identifiers.pubchem")["value"] == "3717450"


def test_a_structure_pubchem_does_not_hold_is_not_found():
    card, resolution = sabueso.resolve(f"smiles:{ABSENT}", **_clients())
    assert card is None
    assert resolution.status == "not_found"
    assert resolution.decision["rules"][-1] == "structure_not_in_pubchem"
    # Never a computed key.
    assert resolution.entity_ref is None


def test_a_structure_pubchem_cannot_read_is_reported():
    card, resolution = sabueso.resolve(f"smiles:{UNREADABLE}", **_clients())
    assert card is None
    assert resolution.status == "unsupported"
    assert resolution.decision["rules"][-1] == "structure_not_readable_by_pubchem"
    assert "standardize" in resolution.decision["structure"]["fault"]


def test_several_compounds_for_one_structure_are_ambiguous():
    class Several(FixturePubChemClient):
        def structure(self, notation, structure):
            return {"retrieved_at": "fixture", "cids": ["1", "2"], "fault": None}

    card, resolution = sabueso.resolve(
        f"smiles:{VCR_SMILES}", **{**_clients(), "pubchem_client": Several()}
    )
    assert card is None and resolution.status == "ambiguous"
    assert resolution.decision["candidates"] == ["pubchem:1", "pubchem:2"]


def test_an_inchi_must_be_one():
    _, resolution = sabueso.resolve("inchi:1S/C9H8O4", **_clients())
    assert resolution.decision["rules"] == ["not_an_inchi"]


def test_a_profile_that_excludes_pubchem_does_not_ask_it(monkeypatch):
    from sabueso.core import terms as terms_module

    stated = {k: v for k, v in terms_module.source_terms().items() if k != "PubChem"}
    monkeypatch.setattr(terms_module, "source_terms", lambda: stated)
    card, resolution = sabueso.resolve(
        f"smiles:{VCR_SMILES}", terms="commercial", **_clients()
    )
    assert card is None
    assert resolution.decision["rules"] == ["excluded_by_terms_profile"]


def test_the_lookup_is_public_source_access():
    record = pubchem.get_structure_match(
        VCR_INCHI, notation="inchi", client=FixturePubChemClient("temp_data")
    )
    assert record["source"] == "PubChem" and record["kind"] == "structure_match"
    assert record["record"] == {"cids": ["5978"], "fault": None}
    with pytest.raises(ArgumentError):
        pubchem.get_structure_match(VCR_SMILES, notation="mol2")
