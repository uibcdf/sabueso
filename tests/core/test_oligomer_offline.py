"""What sources state about a protein's quaternary structure (uibcdf/sabueso#40).

Frozen public responses retrieved 2026-09-24:

- PDBe-KB interface residues for TcTIM (P52270) and HsTIM (P60174);
- RCSB entries with their assemblies: 1SUX, 1TCD and 3Q37, a TcTIM/TbTIM chimera, for
  TcTIM; 1HTI and 1KLG, an HLA-DR complex with a TIM peptide, for HsTIM.
"""

import pytest

from sabueso import resolve_protein_card
from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
from sabueso.core.oligomer import AGREEMENT_RULE, PARTNER_RULE
from sabueso.mappings.pdbe_kb import map_interfaces
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.interpro import FixtureInterProClient
from sabueso.tools.db.pdbe_kb import FixturePDBeKBClient

TCTIM, HSTIM = "P52270", "P60174"


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _card(resolver, accession, structures="all", **kwargs):
    card, _ = resolve_protein_card(
        accession,
        resolver,
        structures=structures,
        interfaces=True,
        family_sites=True,
        pdbe_kb_client=kwargs.pop("pdbe_kb_client", FixturePDBeKBClient("temp_data")),
        interpro_client=FixtureInterProClient("temp_data"),
        **kwargs,
    )
    return card


@pytest.fixture(scope="module")
def tctim(resolver):
    return _card(resolver, TCTIM).oligomer()


@pytest.fixture(scope="module")
def hstim(resolver):
    return _card(resolver, HSTIM).oligomer()


def _partners(view):
    return {i["partner_ref"]: i for i in view["interfaces"]}


def test_each_partner_is_one_relationship_with_residues_and_where_they_are_seen():
    response = FixturePDBeKBClient("temp_data").interface_residues(TCTIM)
    mapped = map_interfaces(response, "2026-09-24")
    rels = {r["object_ref"]: r for r in mapped["relationships"]}
    assert sorted(rels) == ["uniprot:P04789", "uniprot:P52270"]
    homo = rels["uniprot:P52270"]["qualifiers"]
    assert homo["numbering"] == "uniprot"
    assert len(homo["residues"]) == 36
    first = homo["residues"][0]
    assert (first["start"], first["residue"]) == (12, "ASN")
    assert {"structure": "pdb:1SUX", "entity": 1, "chains": ["A", "B"]} in first[
        "observed_in"
    ]
    # Structures are where the interface is observed, not every entry of the protein.
    assert "pdb:2V5B" not in homo["structures"]
    (assertion,) = mapped["source_assertions"][:1]
    assert assertion["source"]["name"] == "PDBe-KB"


def test_a_partner_without_a_uniprot_entry_keeps_pdbe_kb_s_label():
    response = FixturePDBeKBClient("temp_data").interface_residues(HSTIM)
    refs = {r["object_ref"] for r in map_interfaces(response, "x")["relationships"]}
    assert "pdbe_kb.partner:TR-alpha light chain" in refs


def test_tctim_is_a_homodimer_by_every_source(tctim):
    assert [s["text"] for s in tctim["subunit"]] == ["Homodimer"]
    homo = _partners(tctim)["uniprot:P52270"]
    assert homo["class"] == "homomeric"
    assert len(homo["positions"]) == 36
    states = {
        a["structure_ref"]: [x["oligomeric_state"] for x in a["assemblies"]]
        for a in tctim["assemblies"]
    }
    assert states == {
        "pdb:1SUX": ["Homo 2-mer"],
        "pdb:1TCD": ["Homo 2-mer"],
        "pdb:2OMA": ["Homo 2-mer"],
        "pdb:3Q37": ["Homo 2-mer", "Homo 2-mer"],
        "pdb:4HHP": ["Homo 2-mer"],
    }


def test_a_chimera_does_not_make_its_other_half_a_partner(tctim):
    # 3Q37's single polymer entity is a TcTIM/TbTIM chimera, mapped to both proteins, so
    # PDBe-KB lists TbTIM (P04789) as an interface partner of TcTIM.
    tbtim = _partners(tctim)["uniprot:P04789"]
    assert tbtim["class"] == "chimera"
    assert tbtim["basis"] == {"pdb:3Q37": "chimera_with_partner"}


def test_peptide_complexes_are_not_heteromers_of_the_protein(hstim):
    # HsTIM peptides presented by HLA-DR (and seen by T-cell receptors) are interfaces of
    # a fragment, not complexes of the enzyme.
    others = [i for i in hstim["interfaces"] if i["class"] != "homomeric"]
    assert len(others) == 6
    assert {i["class"] for i in others} == {"fragment_complex"}
    assert set(others[0]["basis"].values()) == {"protein_as_fragment"}
    assert _partners(hstim)["uniprot:P60174"]["class"] == "homomeric"


def test_hstim_subunit_keeps_its_evidence(hstim):
    (subunit,) = hstim["subunit"]
    assert [e.get("id") for e in subunit["evidence"]] == [
        "PRU10127",
        "18562316",
        "8061610",
    ]


def test_structures_without_assembly_data_are_reported_not_dropped(tctim):
    assert tctim["without_assembly_data"] == [
        "pdb:1CI1",
        "pdb:2V5B",
    ]


def test_undetermined_when_the_structures_are_not_on_the_card(resolver):
    # Without RCSB data, 3Q37's chimeric entity cannot be told from a real complex.
    view = _card(resolver, TCTIM, structures=()).oligomer()
    tbtim = _partners(view)["uniprot:P04789"]
    assert tbtim["class"] == "undetermined"
    assert tbtim["basis"] == {"pdb:3Q37": "entity_mapping_not_retrieved"}


def test_family_dimer_interface_against_observed_interface(tctim):
    (site,) = tctim["family_interface_sites"]
    assert (site["description"], site["signature"]) == ("dimer interface", "cd00311")
    (agreement,) = tctim["agreement"]
    assert len(agreement["both"]) == 12
    assert agreement["family_only"] == [53]
    assert len(agreement["observed_only"]) == 24
    assert [r["rule"] for r in tctim["rules"]] == [PARTNER_RULE, AGREEMENT_RULE]


def test_interface_outcomes_are_recorded_and_never_block_the_card(resolver):
    with pytest.warns(EnrichmentFailedWarning):
        card = _card(
            resolver,
            TCTIM,
            structures=(),
            pdbe_kb_client=FixturePDBeKBClient("temp_data", failing={TCTIM}),
        )
    (outcome,) = [
        e for e in card.quality["enrichments"] if e.get("data") == "interface_residues"
    ]
    assert outcome["status"] == "error"
    assert card.oligomer()["interfaces"] == []
