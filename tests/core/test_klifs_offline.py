"""KLIFS: a kinase's classification, structures and pocket (#83).

Fixtures: STK16 (O75716, KLIFS's MPSK1), its two KLIFS structures (2BUJ chains A and
B), and the pocket residues KLIFS states in chain B's author numbering.
"""

import collections

import pytest

import sabueso
from sabueso._private.smonitor.warnings import (
    EnrichmentFailedWarning,
    EnrichmentTruncatedWarning,
)
from sabueso.mappings.klifs import map_kinases, reference
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.klifs import FixtureKLIFSClient

CLASSIFICATION = "annotations.kinase_classification"
STRUCTURES = "annotations.kinase_structures"
POCKET = "annotations.kinase_pocket"


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _card(resolver, accession="O75716", structures=("2BUJ",), klifs=None, client=None):
    card, _ = sabueso.resolve(
        accession,
        resolver=resolver,
        structures=list(structures),
        klifs={} if klifs is None else klifs,
        klifs_client=client or FixtureKLIFSClient("temp_data"),
    )
    return card


def _record(card):
    (record,) = [e for e in card.quality["enrichments"] if e["source"] == "KLIFS"]
    return record


def test_a_kinase_joins_through_the_accession_klifs_states(resolver):
    card = _card(resolver)
    (kinase,) = card.get(CLASSIFICATION)["value"]
    assert kinase == {
        "kinase_id": 280,
        "name": "MPSK1",
        "group": "Other",
        "family": "NAK",
        "subfamily": "MPSK",
        "pocket_sequence": (
            "QKLGEGGFSYVDLYALKRIEAQREADMHRLFNPNILRLVAYWLLLPFFKRGTLWNEIERAIHAKGYAHRDLK"
            "PTNILLLMDLGSM"
        ),
    }


def test_structures_keep_the_conformation_klifs_assigns(resolver):
    card = _card(resolver)
    structures = card.get(STRUCTURES)["value"]
    assert [(s["structure"], s["chain"]) for s in structures] == [
        ("pdb:2BUJ", "A"),
        ("pdb:2BUJ", "B"),
    ]
    b = structures[1]
    assert (b["dfg"], b["ac_helix"], b["ligand"]) == ("in", "in", "STU")
    assert "allosteric_ligand" not in b  # KLIFS writes 0
    assert b["quality_score"] == 9.2
    assert b["resolution"] == {"value": 2.6, "unit": "angstrom"}
    # Chain A states the same staurosporine as allosteric too, as KLIFS has it.
    assert structures[0]["allosteric_ligand"] == "STU"


def test_the_pocket_is_placed_through_the_reference_structures_numbering(resolver):
    card = _card(resolver)
    pocket = card.get(POCKET)["value"]
    assert len(pocket) == 85
    assert collections.Counter(p.get("not_placed", "placed") for p in pocket) == {
        "placed": 85
    }
    by_label = {p["klifs_position"]: p for p in pocket}
    assert [
        (label, by_label[label]["residue"], by_label[label]["location"]["start"])
        for label in ("III.17", "GK.45", "hinge.46", "xDFG.81")
    ] == [
        ("III.17", "K", 49),
        ("GK.45", "L", 98),
        ("hinge.46", "P", 99),
        ("xDFG.81", "D", 166),
    ]
    # Chain B: its pocket is the kinase's (chain A has two gaps), quality 9.2.
    assert by_label["GK.45"]["placed_via"] == {
        "rule": "rcsb_author_numbering@1",
        "reference_rule": "klifs_pocket_reference@1",
        "structure": "pdb:2BUJ",
        "chain": "B",
        "author_position": "98",
    }
    record = _record(card)
    assert record["pocket_placed"] == 85
    assert record["pocket_references"] == [
        {
            "kinase_id": 280,
            "structure": "pdb:2BUJ",
            "chain": "B",
            "klifs_structure_id": 2230,
        }
    ]


def test_without_a_structure_on_the_card_the_pocket_is_not_placed(resolver):
    class Counting(FixtureKLIFSClient):
        asked = []

        def pocket(self, structure_id):
            self.asked.append(structure_id)
            return super().pocket(structure_id)

    client = Counting("temp_data")
    card = _card(resolver, structures=(), client=client)
    pocket = card.get(POCKET)["value"]
    assert {p["not_placed"] for p in pocket} == {"no_structure_loaded"}
    assert all(p["numbering"] == "klifs" for p in pocket)
    assert client.asked == []
    assert _record(card)["pocket_references"] == []


def test_a_protein_klifs_states_no_kinase_for_is_not_found(resolver):
    card = _card(resolver, accession="P60174", structures=())
    record = _record(card)
    assert record["status"] == "not_found"
    assert "KLIFS states no kinase for P60174" in record["detail"]
    assert card.get(POCKET) is None


def test_a_failing_source_is_an_error_not_an_absence(resolver):
    with pytest.warns(EnrichmentFailedWarning):
        card = _card(
            resolver, client=FixtureKLIFSClient("temp_data", failing={"kinase_names"})
        )
    assert _record(card)["status"] == "error"


def test_the_structure_ceiling_is_reported(resolver):
    with pytest.warns(EnrichmentTruncatedWarning):
        card = _card(resolver, klifs={"limit": 1})
    assert len(card.get(STRUCTURES)["value"]) == 1
    record = _record(card)
    assert (record["count"], record["total_count"], record["truncated"]) == (
        1,
        2,
        True,
    )


def _row(sid, pdb, chain, pocket, quality, missing=0, resolution="2.0"):
    return {
        "structure_ID": sid,
        "pdb": pdb,
        "chain": chain,
        "pocket": pocket,
        "quality_score": quality,
        "missing_residues": missing,
        "missing_atoms": 0,
        "resolution": resolution,
    }


def test_the_reference_prefers_the_kinases_own_pocket_then_quality():
    entry = {
        "uniProtKBCrossReferences": [
            {
                "database": "PDB",
                "id": pdb,
                "properties": [{"key": "Chains", "value": "A=1-10"}],
            }
            for pdb in ("1AAA", "2BBB", "3CCC")
        ]
    }
    numbering = {pdb: {"A": [[1, 10, 1]]} for pdb in ("1AAA", "2BBB", "3CCC")}
    kinase = {"pocket": "KLG"}
    rows = [
        _row(1, "1aaa", "A", "KMG", 9.9),  # a mutant pocket
        _row(2, "2bbb", "A", "KLG", 8.0),
        _row(3, "3ccc", "A", "KLG", 8.5),
        _row(4, "4ddd", "A", "KLG", 10.0),  # not on the card
    ]
    assert reference(kinase, rows, entry, numbering)["structure_ID"] == 3
    assert reference(kinase, rows[:1], entry, numbering)["structure_ID"] == 1
    assert reference(kinase, rows[3:], entry, numbering) is None


def test_a_protein_with_two_kinase_domains_holds_both():
    kinases = [
        {
            "kinase": {"kinase_ID": kid, "name": name, "group": "TK", "pocket": "K_G"},
            "structures": [],
            "reference": None,
            "pocket": None,
        }
        for kid, name in ((435, "JAK1"), (438, "JAK1-b"))
    ]
    mapping, outcome = map_kinases(
        kinases, "P23458", {"sequence": {"value": "MKLG"}}, {}, "fixture", 5000
    )
    names = [k["name"] for k in mapping["fields"][CLASSIFICATION]]
    assert names == ["JAK1", "JAK1-b"]
    pocket = mapping["fields"][POCKET]
    assert [(p["kinase_id"], p["index"], p["not_placed"]) for p in pocket] == [
        (435, 1, "no_structure_loaded"),
        (435, 2, "gap"),
        (435, 3, "no_structure_loaded"),
        (438, 1, "no_structure_loaded"),
        (438, 2, "gap"),
        (438, 3, "no_structure_loaded"),
    ]
    assert outcome["kinases"] == [435, 438]
