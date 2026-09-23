"""resolve_protein_card against live UniProt, RCSB, STRING and ChEMBL (network)."""

import pytest

from sabueso import resolve_protein_card


@pytest.mark.online
def test_online_protein_card_with_structures_and_string():
    card, _ = resolve_protein_card(
        "P60174", structures=["1HTI"], string={"required_score": 900, "limit": 5}
    )
    assert card.id == "sabueso:protein:uniprot:P60174"
    outcomes = {e["source"]: e for e in card.quality["enrichments"]}
    assert outcomes["RCSB PDB"]["status"] == "added"
    assert outcomes["STRING"]["status"] == "added"
    assert outcomes["STRING"]["version"]
    assert 0 < len(card.relationships("functionally_associated_with")) <= 5


@pytest.mark.online
def test_online_protein_card_with_chembl_bioactivities():
    card, _ = resolve_protein_card("P60174", chembl={"limit": 20})
    (outcome,) = card.quality["enrichments"]
    assert (outcome["source"], outcome["target"], outcome["status"]) == (
        "ChEMBL",
        "CHEMBL4880",
        "added",
    )
    assert outcome["version"].startswith("ChEMBL_")
    assert 0 < outcome["count"] <= 20
    view = card.bioactivities(include_indirect=True)
    assert sum(len(i["measurements"]) for i in view["items"]) == outcome["count"]
