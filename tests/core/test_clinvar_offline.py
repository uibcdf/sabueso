"""ClinVar: variants of a human gene and their classification (#83).

Fixture: 21 of the 249 ClinVar variation summaries of TPI1 (GeneID 7167), build
Build260924-0125.1: canonical-transcript missense, nonsense and frameshift changes,
intronic and UTR changes, a copy-number variant, and conflicting classifications.
"""

import collections

import pytest

import sabueso
from sabueso._private.smonitor.warnings import EnrichmentTruncatedWarning
from sabueso.mappings._hgvs import place
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.clinvar import FixtureClinVarClient

FIELD = "annotations.clinical_variants"


@pytest.fixture(scope="module")
def card():
    resolver = EntityResolver(FixtureUniProtClient("temp_data"))
    with pytest.warns(EnrichmentTruncatedWarning):  # 21 saved records of 249
        card, _ = sabueso.resolve(
            "P60174",
            resolver=resolver,
            clinvar={},
            clinvar_client=FixtureClinVarClient("temp_data"),
        )
    return card


def _by_accession(card):
    return {v["accession"]: v for v in card.get(FIELD)["value"]}


def test_classifications_are_kept_as_clinvar_states_them(card):
    variants = _by_accession(card)
    e105d = variants["VCV000012468"]
    assert e105d["classification"] == "Pathogenic/Likely pathogenic"
    assert e105d["review_status"] == (
        "criteria provided, multiple submitters, no conflicts"
    )
    assert "Triosephosphate isomerase deficiency" in {
        c["name"] for c in e105d["conditions"]
    }
    # A disagreement among submitters is ClinVar's own statement, never resolved.
    assert variants["VCV001685182"]["classification"] == (
        "Conflicting classifications of pathogenicity"
    )


def test_a_variant_is_placed_only_through_the_canonical_transcript(card):
    variants = _by_accession(card)
    e105d = variants["VCV000012468"]
    # ClinVar's protein_change lists every isoform ("E142D, E105D, E23D"); the title's
    # transcript, which UniProt states for the canonical isoform, places it.
    assert (e105d["transcript"], e105d["numbering"]) == ("NM_000365.6", "uniprot")
    assert e105d["location"] == {"start": 105, "end": 105}
    assert e105d["substitution"] == {"original": "E", "change": "D"}
    assert variants["VCV000012473"]["substitution"]["change"] == "*"  # p.Glu146Ter
    counts = collections.Counter(
        v.get("not_placed", "placed") for v in variants.values()
    )
    assert counts == {"placed": 15, "no_protein_change": 6}
    # The placed positions include the natural variants UniProt states.
    natural = {
        i["location"]["sequence"]["start"]
        for i in card.get("features_positional.natural_variant")["value"]
    }
    placed = {v["location"]["start"] for v in variants.values() if "location" in v}
    assert {42, 105, 171, 241} <= placed & natural


@pytest.mark.parametrize(
    "hgvs_p, transcript, reason",
    [
        (None, "NM_000365.6", "no_protein_change"),
        ("p.Lys105Asp", "NM_000365.6", "residue_mismatch"),  # E at 105, not K
        ("p.Glu999Asp", "NM_000365.6", "residue_mismatch"),  # past the sequence
        ("p.Ter250Cysext*55", "NM_000365.6", "stop_codon"),  # one past 249 residues
        ("p.AspGly4_?9", "NM_000365.6", "unparsed_protein_change"),
        ("p.Glu105Asp", "NM_999999.1", "transcript_not_canonical"),
    ],
)
def test_what_cannot_be_placed_says_why(card, hgvs_p, transcript, reason):
    sequence = card.get("sequence.primary")["value"]
    assert place(hgvs_p, transcript, ["NM_000365.6"], sequence) == {
        "not_placed": reason
    }


def test_clinvar_does_not_cover_a_parasite_protein():
    resolver = EntityResolver(FixtureUniProtClient("temp_data"))
    card, _ = sabueso.resolve(
        "P52270",
        resolver=resolver,
        clinvar={},
        clinvar_client=FixtureClinVarClient("temp_data"),
    )
    states = {
        (r["area"], r["source"]): r["state"] for r in card.knowledge_state()["rows"]
    }
    assert states[(FIELD, "ClinVar")] == "not_queried"


def test_uniprots_isoform_edits_give_a_position_map():
    import json
    from pathlib import Path

    from sabueso.mappings._hgvs import isoform_map, transcript_context

    # A deletion of canonical 1-82 (isoform 3 of P60174) and a replacement of Met1 by
    # 38 residues (isoform 2).
    assert isoform_map(249, [(1, 82, "")])[23] == 105
    extended = isoform_map(249, [(1, 1, "M" * 38)])
    assert (extended.get(38), extended[142]) == (None, 105)
    context = transcript_context(json.loads(Path("temp_data/P60174.json").read_text()))
    assert context["canonical"] == {"NM_000365.6", "ENST00000396705"}
    assert context["isoform_of"]["NM_001159287.1"] == "P60174-3"
    # ClinVar's "E142D, E105D, E23D": one change, three numberings, one position.
    sequence = context["sequence"]
    for transcript, stated in (("NM_001159287.1", 142), ("NM_001258026.2", 23)):
        placed = place(
            f"p.Glu{stated}Asp",
            transcript,
            context["canonical"],
            sequence,
            context["isoform_of"],
            context["maps"],
        )
        assert placed["location"] == {"start": 105, "end": 105}
