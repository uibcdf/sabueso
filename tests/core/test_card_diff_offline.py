"""Comparing the knowledge of two cards (uibcdf/sabueso#59).

TcTIM (P52270) and HsTIM (P60174): UniProt places the active sites at 96 and 168 in the
parasite, and at 96 and 166 in human, and the substrate binding sites at 12 and 14 in
both. The residue mapping below is constructed for the test; in practice it comes from
an alignment (MolSysMT).
"""

import pytest

import sabueso
from sabueso.core.errors import ArgumentError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

MAPPING = {12: 12, 14: 14, 96: 96, 168: 166}


@pytest.fixture(scope="module")
def tims():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    return [sabueso.resolve(a, resolver=resolver)[0] for a in ("P52270", "P60174")]


def test_what_both_state_and_what_only_one_states(tims):
    tc, hs = tims
    diff = tc.compare_knowledge(hs)
    assert (diff["self"], diff["other"]) == (tc.id, hs.id)
    assert diff["rule"]["rule"] == "card_knowledge_diff@1"
    fields = diff["fields"]
    assert fields["annotations.function"]["status"] == "only_other"
    assert fields["annotations.taxon_id"] == {
        "status": "differs",
        "self": 5693,
        "other": 9606,
    }
    lineage = fields["annotations.lineage"]
    assert {"self": "Eukaryota", "other": "Eukaryota"} in lineage["both"]
    assert "Trypanosomatida" in lineage["only_self"]
    # Free text is never compared without reading it.
    assert fields["annotations.subunit"] == {
        "status": "not_compared",
        "reason": "free text",
    }
    assert fields["sequence.primary"]["lengths"] == [251, 249]


def test_positions_are_compared_only_through_a_residue_mapping(tims):
    tc, hs = tims
    unmapped = tc.compare_knowledge(hs)["fields"]["features_positional.active_site"]
    assert unmapped == {"status": "not_compared", "reason": "no residue mapping"}
    mapped = tc.compare_knowledge(hs, residue_map=MAPPING)["fields"]
    active = mapped["features_positional.active_site"]
    assert active["status"] == "same" and len(active["both"]) == 2
    assert mapped["features_positional.binding_site"]["status"] == "same"
    # A position the mapping does not cover cannot be compared.
    partial = tc.compare_knowledge(hs, residue_map={12: 12, 14: 14, 96: 96})["fields"]
    active = partial["features_positional.active_site"]
    assert len(active["not_comparable"]) == 1 and active["status"] == "differs"


def test_relationships_and_knowledge_states(tims):
    tc, hs = tims
    diff = tc.compare_knowledge(hs)
    classified = diff["relationships"]["classified_in"]
    assert "interpro:IPR000652" in classified["both"]
    assert "orthodb:9472880at2759" in classified["only_other"]
    states = {(r["area"], r["source"]): r for r in diff["knowledge_states"]}
    # "Only HsTIM states a function" is backed by UniProt stating none for TcTIM.
    assert states[("annotations.function", "UniProt")]["self"] == "not_stated"
    assert states[("annotations.function", "UniProt")]["other"] == "known"


def test_arguments_are_checked(tims):
    tc, hs = tims
    with pytest.raises(ArgumentError):
        tc.compare_knowledge(hs, residue_map={0: 1})
    with pytest.raises(ArgumentError):
        tc.compare_knowledge("P60174")
