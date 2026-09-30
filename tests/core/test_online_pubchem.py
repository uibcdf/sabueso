import pytest

import sabueso


@pytest.mark.online
def test_online_pubchem_card():
    card = sabueso.create_compound_card_online("66414", retrieved_at="2026-02-04")
    assert card.get("identifiers.pubchem") is not None


@pytest.mark.online
def test_online_structure_lookups_read_as_the_frozen_ones():
    # PubChem states which compound a structure is (#93); an absent structure is CID 0,
    # an unreadable one HTTP 400.
    from sabueso.tools.db.pubchem import OnlinePubChemClient

    client = OnlinePubChemClient()
    assert client.structure("smiles", "CC(=O)OC1=CC=CC=C1C(=O)O")["cids"] == ["2244"]
    assert client.structure("smiles", "C1CC1[Xe]C1CC1CC(=O)OCCCCCCCCCCN")["cids"] == []
    assert client.structure("smiles", "C1CC(")["fault"]


@pytest.mark.online
def test_online_chebi_entries_in_one_request():
    from sabueso.tools.db.chebi import OnlineChEBIClient

    answer = OnlineChEBIClient().compounds(["CHEBI:28445", "15365", "CHEBI:0"])
    assert set(answer["compounds"]) == {"CHEBI:28445", "CHEBI:15365"}
    vincristine = answer["compounds"]["CHEBI:28445"]["data"]
    assert vincristine["default_structure"]["standard_inchi_key"] == (
        "OGWKCGZFUXNPDA-XQKSVPLYSA-N"
    )
