"""GPCRdb: a receptor's classification, segments, generic numbers and structures (#83).

Fixtures: GPR52 (Q9Y2T5), an orphan class A receptor, with its GPCRdb residues and its
seven structures (inactive and active, apo and with an allosteric agonist, with a G
protein or an arrestin).
"""

import collections

import pytest

import sabueso
from sabueso._private.smonitor.warnings import (
    EnrichmentFailedWarning,
    EnrichmentTruncatedWarning,
)
from sabueso.mappings.gpcrdb import map_receptor, segments
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.gpcrdb import FixtureGPCRdbClient

CLASSIFICATION = "annotations.gpcr_classification"
SEGMENTS = "annotations.gpcr_segments"
RESIDUES = "annotations.gpcr_residues"
STRUCTURES = "annotations.gpcr_structures"


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(FixtureUniProtClient("temp_data"))


def _card(resolver, accession="Q9Y2T5", gpcrdb=None, client=None):
    card, _ = sabueso.resolve(
        accession,
        resolver=resolver,
        gpcrdb={} if gpcrdb is None else gpcrdb,
        gpcrdb_client=client or FixtureGPCRdbClient("temp_data"),
    )
    return card


def _record(card):
    (record,) = [e for e in card.quality["enrichments"] if e["source"] == "GPCRdb"]
    return record


@pytest.fixture(scope="module")
def card(resolver):
    return _card(resolver)


def test_a_receptor_joins_through_the_accession_gpcrdb_states(card):
    assert card.get(CLASSIFICATION)["value"] == [
        {
            "entry_name": "gpr52_human",
            "name": "GPR52",
            "receptor_class": "Class A (Rhodopsin)",
            "family": "Orphan receptors",
            "numbering_scheme": "GPCRdb(A)",
        }
    ]


def test_residues_are_in_uniprot_numbering_when_the_sequences_are_the_same(card):
    residues = card.get(RESIDUES)["value"]
    assert len(residues) == 270
    assert {r["numbering"] for r in residues} == {"uniprot"}
    tm2 = next(r for r in residues if r["generic_number"] == "2.43x43")
    assert (tm2["residue"], tm2["segment"], tm2["location"]) == (
        "I",
        "TM2",
        {"start": 80, "end": 80},
    )
    assert tm2["placed_via"] == {"rule": "gpcrdb_sequence_numbering@1"}
    assert {"scheme": "BW", "label": "2.43"} in tm2["generic_numbers"]
    record = _record(card)
    assert (record["sequence_matches"], record["residues_placed"]) == (True, 270)


def test_segments_are_runs_of_the_residues_gpcrdb_assigns(card):
    runs = card.get(SEGMENTS)["value"]
    assert [r["segment"] for r in runs[:4]] == ["N-term", "TM1", "ICL1", "TM2"]
    assert runs[1]["location"] == {"start": 40, "end": 68}
    assert segments(
        [
            {"sequence_number": 1, "protein_segment": "TM1"},
            {"sequence_number": 2, "protein_segment": "TM1"},
            {"sequence_number": 4, "protein_segment": "TM1"},
        ]
    ) == [
        {"segment": "TM1", "start": 1, "end": 2},
        {"segment": "TM1", "start": 4, "end": 4},
    ]


def test_structures_keep_state_ligands_and_signalling_protein(card):
    structures = {s["structure"]: s for s in card.get(STRUCTURES)["value"]}
    assert collections.Counter(s["state"] for s in structures.values()) == {
        "Active": 4,
        "Inactive": 3,
    }
    inactive = structures["pdb:6LI0"]
    assert inactive["ligands"] == [
        {
            "name": "derivative 17 [Nakahata et al., 2018]",
            "pdb_ccd": "EN6",
            "type": "Small molecule",
            "function": "Allosteric agonist",
        }
    ]
    assert inactive["resolution"] == {"value": 2.2, "unit": "angstrom"}
    # GPCRdb writes "Apo (no ligand)" as a ligand; the card says apo instead.
    assert structures["pdb:6LI1"]["apo"] is True
    assert "ligands" not in structures["pdb:6LI1"]
    assert structures["pdb:6LI3"]["signalling_protein"] == {
        "type": "G protein",
        "partners": ["gbb1_human", "gbg2_human", "gnas2_human"],
    }
    assert structures["pdb:9IJR"]["signalling_protein"]["type"] == "Arrestin"


def test_a_different_sequence_keeps_gpcrdbs_numbering():
    receptor = {"entry_name": "x_human", "sequence": "MAGK"}
    residues = [
        {
            "sequence_number": 2,
            "amino_acid": "A",
            "protein_segment": "TM1",
            "display_generic_number": "1.50x50",
            "alternative_generic_numbers": [],
        }
    ]
    mapping, outcome = map_receptor(
        receptor, residues, [], "X", "MAGKL", "fixture", 5000
    )
    (residue,) = mapping["fields"][RESIDUES]
    assert (residue["not_placed"], residue["numbering"]) == (
        "sequence_differs",
        "gpcrdb",
    )
    assert "location" not in residue
    assert mapping["fields"][SEGMENTS][0]["not_placed"] == "sequence_differs"
    assert outcome["sequence_matches"] is False


def test_a_protein_gpcrdb_has_no_receptor_for_is_not_found(resolver):
    card = _card(resolver, accession="P60174")
    record = _record(card)
    assert record["status"] == "not_found"
    assert "GPCRdb has no receptor for P60174" in record["detail"]


def test_a_failing_source_is_an_error_not_an_absence(resolver):
    with pytest.warns(EnrichmentFailedWarning):
        card = _card(
            resolver,
            client=FixtureGPCRdbClient("temp_data", failing={"receptor_Q9Y2T5"}),
        )
    assert _record(card)["status"] == "error"


def test_the_structure_ceiling_is_reported(resolver):
    with pytest.warns(EnrichmentTruncatedWarning):
        card = _card(resolver, gpcrdb={"limit": 2})
    record = _record(card)
    assert (record["count"], record["total_count"], record["truncated"]) == (2, 7, True)
