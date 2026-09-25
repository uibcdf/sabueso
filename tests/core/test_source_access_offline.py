"""Source access as a public layer (uibcdf/sabueso#49).

Every source module offers ``get_*`` functions returning the raw record in a provenance
envelope: ``{source, kind, query, retrieved_at, version, record}``. They take the same
clients card building uses, so there is one way to query each source.
"""

import pytest

from sabueso._private.smonitor.warnings import DeprecatedUsageWarning
from sabueso.core.errors import ArgumentError, RecordNotFoundError
from sabueso.tools.db import (
    alphafold,
    chembl,
    interpro,
    pdb_ccd,
    pdbe_kb,
    pubchem,
    rcsb,
    stringdb,
    unichem,
    uniprot,
)

ENVELOPE = {"source", "kind", "query", "retrieved_at", "version", "record"}
BTS_KEY = "XBNHRNFODJOFRU-UHFFFAOYSA-N"

CALLS = {
    "alphafold.get_prediction": lambda: alphafold.get_prediction(
        "P52270", client=alphafold.FixtureAlphaFoldClient("temp_data")
    ),
    "uniprot.get_entry": lambda: uniprot.get_entry(
        "P60174", client=uniprot.FixtureUniProtClient("temp_data")
    ),
    "uniprot.search": lambda: uniprot.search(
        "triosephosphate isomerase",
        9606,
        client=uniprot.FixtureUniProtClient("temp_data"),
    ),
    "rcsb.get_entry": lambda: rcsb.get_entry(
        "1sux", client=rcsb.FixtureRCSBClient("temp_data")
    ),
    "chembl.get_bioactivities": lambda: chembl.get_bioactivities(
        "CHEMBL4880", limit=10, client=chembl.FixtureChEMBLClient("temp_data")
    ),
    "chembl.get_molecules": lambda: chembl.get_molecules(
        ["CHEMBL1161789"], client=chembl.FixtureChEMBLClient("temp_data")
    ),
    "pubchem.get_compound": lambda: pubchem.get_compound(
        "5978", client=pubchem.FixturePubChemClient("temp_data")
    ),
    "interpro.get_site_residues": lambda: interpro.get_site_residues(
        "P52270", client=interpro.FixtureInterProClient("temp_data")
    ),
    "pdbe_kb.get_ligand_sites": lambda: pdbe_kb.get_ligand_sites(
        "P52270", client=pdbe_kb.FixturePDBeKBClient("temp_data")
    ),
    "pdbe_kb.get_interface_residues": lambda: pdbe_kb.get_interface_residues(
        "P52270", client=pdbe_kb.FixturePDBeKBClient("temp_data")
    ),
    "pdb_ccd.get_components": lambda: pdb_ccd.get_components(
        ["BTS", "PGA"], client=pdb_ccd.FixtureCCDClient("temp_data")
    ),
    "unichem.get_compound": lambda: unichem.get_compound(
        BTS_KEY, client=unichem.FixtureUniChemClient("temp_data")
    ),
    "stringdb.get_partners": lambda: stringdb.get_partners(
        "P60174", 9606, client=stringdb.FixtureStringClient("temp_data")
    ),
}


@pytest.mark.parametrize("name", sorted(CALLS))
def test_every_source_returns_its_record_in_the_envelope(name):
    result = CALLS[name]()
    assert set(result) == ENVELOPE
    assert result["record"]
    assert result["retrieved_at"]
    assert result["query"]


def test_the_envelope_carries_the_release_where_the_source_states_it():
    entry = CALLS["uniprot.get_entry"]()
    assert (entry["source"], entry["kind"], entry["version"]) == (
        "UniProt",
        "entry",
        "212",
    )
    assert entry["record"]["primaryAccession"] == "P60174"
    assert CALLS["chembl.get_bioactivities"]()["version"] == "ChEMBL_37"
    assert CALLS["rcsb.get_entry"]()["query"] == {"pdb_id": "1SUX"}


def test_the_same_clients_build_cards_and_answer_queries():
    # One way to query each source: the resolver's clients are tools.db's.
    from sabueso.resolver import FixtureRCSBClient, FixtureUniProtClient

    assert FixtureUniProtClient is uniprot.FixtureUniProtClient
    assert FixtureRCSBClient is rcsb.FixtureRCSBClient


def test_not_found_is_an_answer_not_a_failure():
    with pytest.raises(RecordNotFoundError):
        uniprot.get_entry("Q99999", client=uniprot.FixtureUniProtClient("temp_data"))
    with pytest.raises(RecordNotFoundError):
        pubchem.get_compound("1", client=pubchem.FixturePubChemClient("temp_data"))


@pytest.mark.parametrize(
    "call",
    [
        lambda: uniprot.get_entry(""),
        lambda: uniprot.get_entry("P60174", client="https://rest.uniprot.org"),
        lambda: uniprot.search("", 9606),
        lambda: uniprot.search("tim", True),
        lambda: chembl.get_bioactivities("CHEMBL4880", limit=0),
        lambda: chembl.get_molecules([]),
        lambda: stringdb.get_partners("P60174", 9606, required_score=2000),
    ],
)
def test_wrong_arguments_are_refused(call):
    with pytest.raises(ArgumentError):
        call()


# --- deprecated routes -----------------------------------------------------------------


@pytest.fixture
def offline_uniprot(monkeypatch):
    monkeypatch.setattr(
        uniprot,
        "OnlineUniProtClient",
        lambda: uniprot.FixtureUniProtClient("temp_data"),
    )


def test_fetch_uniprot_json_warns_and_still_works(offline_uniprot):
    with pytest.warns(DeprecatedUsageWarning, match="get_entry"):
        entry = uniprot.fetch_uniprot_json("P60174")
    assert entry["primaryAccession"] == "P60174"


def test_create_protein_card_online_points_to_resolve(offline_uniprot):
    with pytest.warns(DeprecatedUsageWarning, match="sabueso.resolve"):
        card = uniprot.create_protein_card_online("P60174")
    assert card.id == "sabueso:protein:uniprot:P60174"


def test_the_deprecation_warning_is_a_future_warning():
    # Python shows FutureWarning to end users by default; DeprecationWarning it hides.
    assert issubclass(DeprecatedUsageWarning, FutureWarning)
