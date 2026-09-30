"""Transmembrane segments per chain, as RCSB states them, in UniProt numbering (#83).

Frozen RCSB entry 6LI0 (GPR52, inactive, with an allosteric agonist), fetched
2026-09-30. RCSB integrates the segments OPM and PDBTM assign to its chain A.
"""

import pytest

import sabueso
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _qualifiers(card, structure):
    (rel,) = card.relationships("has_structure", object_ref=structure)
    return rel["qualifiers"]


def test_each_resource_keeps_its_own_segments(resolver):
    card, _ = sabueso.resolve("Q9Y2T5", resolver=resolver, structures=["6LI0"])
    (opm, pdbtm) = _qualifiers(card, "pdb:6LI0")["membrane_segments"]["A"]
    assert (opm["assigned_by"], pdbtm["assigned_by"]) == ("OPM", "PDBTM")
    assert len(opm["segments"]) == len(pdbtm["segments"]) == 7
    # They agree on TM1 and differ by a residue or two elsewhere; neither is chosen.
    assert opm["segments"][0] == pdbtm["segments"][0] == [40, 61]
    assert (opm["segments"][1], pdbtm["segments"][1]) == ([78, 102], [79, 103])
    # What RCSB stated is in the statement, for this entry only.
    (statement,) = [
        sa
        for sa in card.source_assertion_store.find_by_field(
            "relationships.has_structure"
        )
        if sa["source"]["name"] == "RCSB PDB" and sa["source"]["record_id"] == "6LI0"
    ]
    assert set(statement["asserted_value"]["membrane_segments"]) == {"A"}


def test_a_soluble_protein_has_no_membrane_segments(resolver):
    card, _ = sabueso.resolve("P52270", resolver=resolver, structures=["1TCD"])
    qualifiers = _qualifiers(card, "pdb:1TCD")
    assert "membrane_segments" not in qualifiers
    (statement,) = [
        sa
        for sa in card.source_assertion_store.find_by_field(
            "relationships.has_structure"
        )
        if sa["source"]["name"] == "RCSB PDB"
    ]
    # Entries without segments keep the statement they always had.
    assert "membrane_segments" not in statement["asserted_value"]
