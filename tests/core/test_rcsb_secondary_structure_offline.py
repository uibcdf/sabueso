"""Secondary structure per chain, as RCSB states it, in UniProt numbering (#80).

Frozen RCSB entries of TcTIM (P52270), refetched 2026-09-27 with the assigning program.
1TCD numbers its entity two residues behind UniProt.
"""

import warnings

import pytest

import sabueso
from sabueso.mappings.rcsb_structures import _secondary_structure
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient


@pytest.fixture(scope="module")
def card():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    with warnings.catch_warnings():
        # Structures without a saved RCSB response are recorded as not found.
        warnings.simplefilter("ignore")
        return sabueso.resolve("P52270", resolver=resolver, structures="all")[0]


def _qualifiers(card, structure):
    (rel,) = card.relationships("has_structure", object_ref=structure)
    return rel["qualifiers"]


def test_helices_and_strands_are_placed_in_uniprot_numbering(card):
    chain = _qualifiers(card, "pdb:1TCD")["secondary_structure"]["A"]
    assert chain["assigned_by"] == ["PROMOTIF"]
    # Entity residues 17-29 are UniProt 19-31, where UniProt also places a helix.
    assert chain["helix"][0] == [19, 31]
    assert chain["strand"][:2] == [[7, 12], [38, 43]]
    uniprot = card.get("features_positional.secondary_structure")["value"]
    assert any(
        i["element"] == "helix"
        and (i["location"]["sequence"]["start"], i["location"]["sequence"]["end"])
        == (19, 31)
        for i in uniprot
    )


def test_a_strand_shared_by_two_sheets_is_listed_once(card):
    for structure in ("pdb:1SUX", "pdb:1TCD", "pdb:2V5B"):
        for chain in _qualifiers(card, structure)["secondary_structure"].values():
            assert len(chain["strand"]) == len({tuple(s) for s in chain["strand"]})


def test_the_source_statement_keeps_rcsbs_features(card):
    (rel,) = card.relationships("has_structure", object_ref="pdb:1TCD")
    (stated,) = [
        sa["asserted_value"]
        for sa in map(card.source_assertion_store.get, rel["source_assertion_ids"])
        if sa["source"]["name"] == "RCSB PDB"
    ]
    types = {f["type"] for f in stated["secondary_structure"]["A"]}
    assert types == {"HELIX_P", "SHEET", "UNASSIGNED_SEC_STRUCT"}
    assert {f["provenance_source"] for f in stated["secondary_structure"]["A"]} == {
        "PROMOTIF"
    }


def test_a_region_shows_its_positions_in_a_helix_or_a_strand(card):
    view = card.structures(region=[[15, 35]])
    (item,) = [i for i in view["items"] if i["structure_ref"] == "pdb:1TCD"]
    assert item["secondary_structure_in_region"]["A"] == {
        "helix": list(range(19, 32)),
        "strand": [],
    }
    assert card.structures()["items"][0]["secondary_structure_in_region"] is None


def test_a_chain_without_any_assignment_is_not_stated_never_coil():
    entity = {
        "uniprot": ["P52270"],
        "regions": {"P52270": [(1, 3, 100)]},
        "instances": [
            {
                "rcsb_polymer_entity_instance_container_identifiers": {
                    "auth_asym_id": "A"
                },
                "rcsb_polymer_instance_feature": [
                    {"type": "UNOBSERVED_RESIDUE_XYZ", "feature_positions": []}
                ],
            }
        ],
    }
    assert _secondary_structure([entity], "P52270") is None
