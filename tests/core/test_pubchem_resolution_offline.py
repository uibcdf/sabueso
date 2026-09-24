"""Small molecules resolved from PubChem CIDs (uibcdf/sabueso#50).

Vincristine: PubChem CID 5978, ChEMBL CHEMBL90555, standard InChIKey
OGWKCGZFUXNPDA-XQKSVPLYSA-N. Frozen public responses; UniChem retrieved 2026-09-24.
"""

import pytest

import sabueso
from sabueso._private.smonitor.warnings import DeprecatedUsageWarning
from sabueso.tools.card.small_molecule import resolve_molecule_card
from sabueso.tools.db import pubchem
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.pubchem import FixturePubChemClient
from sabueso.tools.db.unichem import FixtureUniChemClient

VCR_KEY = "OGWKCGZFUXNPDA-XQKSVPLYSA-N"
VCR = f"sabueso:small_molecule:inchikey:{VCR_KEY}"


def _clients(**failing):
    return dict(
        chembl_client=FixtureChEMBLClient("temp_data"),
        ccd_client=FixtureCCDClient("temp_data"),
        unichem_client=FixtureUniChemClient("temp_data"),
        pubchem_client=FixturePubChemClient(
            "temp_data", failing=failing.get("pubchem")
        ),
    )


def _links(card):
    return {r["subject_ref"] for r in card.relationships("same_as")}


def test_a_pubchem_cid_resolves_to_the_inchikey_anchored_card():
    card, resolution = sabueso.resolve("pubchem:5978", **_clients())
    assert (resolution.status, card.id) == ("resolved", VCR)
    assert resolution.decision["route"]["basis"] == "namespace:pubchem"
    # UniChem links the ChEMBL record of the same structure.
    assert {"pubchem:5978", "chembl:CHEMBL90555"} <= _links(card)
    stated_by = {
        card.source_assertion_store.get(i)["source"]["name"]
        for i in card.get("identifiers.inchikey")["source_assertion_ids"]
    }
    assert {"PubChem", "ChEMBL"} <= stated_by


def _stated_by(card, ref):
    (link,) = [r for r in card.relationships("same_as") if r["subject_ref"] == ref]
    return {
        card.source_assertion_store.get(i)["source"]["name"]
        for i in link["source_assertion_ids"]
    }


def test_the_chembl_route_reaches_the_same_card_and_can_bring_pubchem():
    card, _ = sabueso.resolve("chembl:CHEMBL90555", **_clients())
    assert card.id == VCR
    # UniChem states that CID 5978 is this structure; PubChem itself is not consulted.
    assert _stated_by(card, "pubchem:5978") == {"UniChem"}
    card, _ = sabueso.resolve("chembl:CHEMBL90555", pubchem=True, **_clients())
    assert _stated_by(card, "pubchem:5978") == {"UniChem", "PubChem"}
    (outcome,) = [e for e in card.quality["enrichments"] if e["source"] == "PubChem"]
    assert (outcome["status"], outcome["records"]) == ("added", ["5978"])


def test_without_unichem_the_card_holds_the_compound_alone():
    card, _ = resolve_molecule_card("pubchem:5978", unichem=False, **_clients())
    assert card.id == VCR
    assert _links(card) == {"pubchem:5978"}


def test_an_unknown_cid_is_not_found_and_a_failure_is_an_error():
    _, resolution = resolve_molecule_card("pubchem:1", unichem=False, **_clients())
    assert resolution.status == "not_found"
    _, resolution = resolve_molecule_card(
        "pubchem:5978", unichem=False, **_clients(pubchem={"5978"})
    )
    assert resolution.status == "error"


@pytest.mark.parametrize("identifier", ["pubchem:abc", "5978", "pubchem:"])
def test_a_cid_needs_its_prefix_and_digits(identifier):
    _, resolution = resolve_molecule_card(identifier, unichem=False, **_clients())
    assert resolution.status == "unsupported"


def test_create_compound_card_online_now_points_to_resolve(monkeypatch):
    monkeypatch.setattr(
        pubchem, "OnlinePubChemClient", lambda: FixturePubChemClient("temp_data")
    )
    with pytest.warns(DeprecatedUsageWarning, match="pubchem:<cid>"):
        card = pubchem.create_compound_card_online("5978", retrieved_at="2026-09-24")
    assert card.id == VCR
