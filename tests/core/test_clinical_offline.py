"""The clinical layer of a molecule: ChEMBL indications and the trials they cite (#81).

Benznidazole (CHEMBL110): ChEMBL_37 indications, and the 16 ClinicalTrials.gov studies
they cite (API v2 data of 2026-09-25).
"""

import json
from pathlib import Path

import pytest

import sabueso
from sabueso._private.smonitor.warnings import (
    EnrichmentFailedWarning,
    EnrichmentTruncatedWarning,
)
from sabueso.core.migration import within_line_gaps
from sabueso.mappings.clinical import map_indications, map_trials
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.clinicaltrials import FixtureClinicalTrialsClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.unichem import FixtureUniChemClient

CLIENTS = dict(
    chembl_client=FixtureChEMBLClient("temp_data"),
    ccd_client=FixtureCCDClient("temp_data"),
    unichem_client=FixtureUniChemClient("temp_data"),
    clinicaltrials_client=FixtureClinicalTrialsClient("temp_data"),
)


def _card(**options):
    card, _ = sabueso.resolve("chembl:CHEMBL110", **CLIENTS, **options)
    return card


def test_indications_keep_each_term_as_chembl_states_it():
    view = _card(indications=True).clinical()
    assert view["max_phase"] == 4.0
    diseases = [i["disease"] for i in view["indications"]]
    # Chagas disease is stated twice, under two terms with one MeSH heading: two rows.
    assert {"efo:EFO:0008559", "mondo:MONDO:0001444"} <= set(diseases)
    chagas = [i for i in view["indications"] if i["mesh_heading"] == "Chagas Disease"]
    assert len(chagas) == 2
    assert {i["max_phase"] for i in view["indications"]} == {4.0}
    leish = next(i for i in view["indications"] if i["disease_term"] == "Leishmaniasis")
    assert (leish["trials"], leish["reference_types"]) == ([], ["ATC"])
    # Without trials, the cited trials are listed as not fetched, never as absent.
    assert view["trials"] == []
    assert len(view["not_fetched"]) == 16


def test_a_trial_is_linked_through_the_indication_that_cites_it():
    card = _card(trials={})
    view = card.clinical()
    assert len(view["trials"]) == 16 and view["not_fetched"] == []
    benefit = next(t for t in view["trials"] if t["trial"] == "nct:NCT00123916")
    assert benefit["cited_for"] == ["doid:DOID:10113", "mondo:MONDO:0001444"]
    assert (benefit["status"], benefit["phases"]) == ("COMPLETED", ["PHASE3"])
    # The intervention is kept as written; it is not what links the trial.
    assert benefit["interventions"][0]["name"] == "Benznidazole"
    (rel,) = card.relationships("tested_in", object_ref="nct:NCT00123916")
    assert rel["qualifiers"]["basis"] == "chembl_drug_indication"
    sources = {
        card.source_assertion_store.get(i)["source"]["name"]
        for i in rel["source_assertion_ids"]
    }
    assert sources == {"ChEMBL", "ClinicalTrials.gov"}


def test_a_trial_the_registry_does_not_hold_keeps_chembls_statement():
    records = json.loads(Path("temp_data/chembl/indications.json").read_text())
    mapped = map_indications(records["indications"], "t", "ChEMBL_37")
    linked = map_trials(mapped["citations"], {}, ["NCT00123916"], "t", None)
    (rel,) = linked["relationships"]
    assert rel["qualifiers"]["registry"] == "not_found"
    assert linked["source_assertions"] == []  # ChEMBL's citations are the only support


def test_the_trial_limit_is_reported():
    with pytest.warns(EnrichmentTruncatedWarning):
        card = _card(trials={"limit": 10})
    view = card.clinical()
    assert (len(view["trials"]), len(view["not_fetched"])) == (10, 6)


def test_a_failed_registry_leaves_the_indications():
    clients = {
        **CLIENTS,
        "clinicaltrials_client": FixtureClinicalTrialsClient(
            "temp_data", failing={"NCT00123916"}
        ),
    }
    with pytest.warns(EnrichmentFailedWarning):
        card, _ = sabueso.resolve("chembl:CHEMBL110", trials={}, **clients)
    assert len(card.clinical()["indications"]) == 4
    assert card.clinical()["trials"] == []


def test_migration_proposes_only_what_applies_to_the_entity():
    molecule = _card().to_dict()
    gaps = {g["path"] for g in within_line_gaps(molecule, "0.3.5", "0.3.6")}
    assert "relationships.investigated_for" in gaps
    assert "annotations.pathogen_phenotypes" not in gaps
    protein = json.loads(
        Path("temp_data/frozen_cards/schema_0.3.5__P60174.json").read_text()
    )
    gaps = {g["path"] for g in within_line_gaps(protein, "0.3.5", "0.3.6")}
    assert "annotations.pathogen_phenotypes" in gaps
    assert "relationships.investigated_for" not in gaps
