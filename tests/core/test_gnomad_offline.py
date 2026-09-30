"""gnomAD: population frequencies of a human gene's variants (#83).

Fixtures: 18 of the 1,668 gnomAD (gnomad_r4) variants of TPI1, as gnomAD states them for
the gene: protein changes on the canonical transcript ENST00000396705, on
ENST00000229270 (UniProt's isoform 3) and on ENST00000462761 (a transcript UniProt does
not state), and non-coding ones; and what gnomAD states for the same variants on the
canonical transcript (#85).
"""

import collections

import pytest

import sabueso
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.gnomad import FixtureGnomADClient

FIELD = "annotations.population_variants"


@pytest.fixture(scope="module")
def card():
    resolver = EntityResolver(FixtureUniProtClient("temp_data"))
    card, _ = sabueso.resolve(
        "P60174",
        resolver=resolver,
        gnomad={},
        gnomad_client=FixtureGnomADClient("temp_data"),
    )
    return card


def test_frequencies_are_kept_as_gnomad_states_them(card):
    e105d = next(v for v in card.get(FIELD)["value"] if v["hgvs_p"] == "p.Glu105Asp")
    assert e105d["exome"] == {
        "ac": 393,
        "an": 1461876,
        "af": pytest.approx(2.688e-4, rel=1e-3),
    }
    assert e105d["genome"]["ac"] == 16
    assert (e105d["location"], e105d["numbering"]) == (
        {"start": 105, "end": 105},
        "uniprot",
    )


def test_the_consequence_on_the_canonical_transcript_comes_first(card):
    variants = card.get(FIELD)["value"]
    counts = collections.Counter(v.get("not_placed", "placed") for v in variants)
    assert counts == {
        "placed": 7,
        "isoform_specific_position": 6,
        "not_coding_on_canonical": 2,
    }
    # For the gene, gnomAD states this change on a transcript UniProt does not state
    # (p.Met1?); on the canonical transcript it states p.Met83Val.
    m83v = next(v for v in variants if v["variant_id"] == "12-6869106-A-G")
    assert (m83v["transcript"], m83v["transcript_version"], m83v["hgvs_p"]) == (
        "ENST00000396705",
        "10",
        "p.Met83Val",
    )
    assert m83v["location"] == {"start": 83, "end": 83}
    assert "placed_via" not in m83v
    (record,) = [e for e in card.quality["enrichments"] if e["source"] == "gnomAD"]
    assert (record["count"], record["without_protein_change"]) == (15, 3)
    assert record["canonical_transcripts"] == [
        {"transcript": "ENST00000396705", "version": "10"}
    ]


def test_a_change_that_is_not_coding_on_the_canonical_transcript_is_not_placed(card):
    # A frameshift at Pro40 of isoform 3 lies where UniProt's isoform map would put
    # canonical Pro3; on the canonical transcript gnomAD states the same insertion is a
    # 5' UTR variant. The isoform map is not applied to it.
    variants = card.get(FIELD)["value"]
    frameshift = next(v for v in variants if v["hgvs_p"] == "p.Pro40ThrfsTer24")
    assert frameshift["not_placed"] == "not_coding_on_canonical"
    assert "location" not in frameshift
    assert frameshift["canonical_consequence"] == {
        "transcript": "ENST00000396705",
        "transcript_version": "10",
        "consequence": "5_prime_UTR_variant",
        "hgvs_c": "c.-26_6dup",
    }
    assert frameshift["numbering"] == "ENST00000229270"


def test_without_the_canonical_answer_uniprots_isoform_map_places_changes():
    from sabueso.mappings._hgvs import transcript_context
    from sabueso.mappings.gnomad import map_variants
    from sabueso.resolver import FixtureUniProtClient

    entry, _ = FixtureUniProtClient("temp_data").fetch_entry("P60174")
    saved = FixtureGnomADClient("temp_data").variants("ENSG00000111669")
    mapped = map_variants(
        [v for v in saved["record"]["variants"] if v.get("hgvsp")],
        "P60174",
        transcript_context(entry),
        "fixture",
        "gnomad_r4",
    )
    frameshift = next(
        v for v in mapped["fields"][FIELD] if v["hgvs_p"] == "p.Pro40ThrfsTer24"
    )
    assert frameshift["location"] == {"start": 3, "end": 3}
    assert frameshift["placed_via"] == {
        "rule": "uniprot_isoform_map@1",
        "isoform": "P60174-3",
        "isoform_position": 40,
    }


def test_merging_keeps_one_item_per_variant():
    from sabueso.mappings.gnomad import merged

    gene = [
        {"variant_id": "a", "hgvsp": "p.Ala2Thr", "transcript_id": "T2"},
        {"variant_id": "b", "hgvsp": "p.Gly5Ser", "transcript_id": "T2"},
        {"variant_id": "c", "transcript_id": "T2"},
        {"variant_id": "d", "transcript_id": "T2"},
    ]
    canonical = [
        {
            "variants": [
                {"variant_id": "a", "hgvsp": "p.Ala7Thr", "transcript_id": "T1"},
                {"variant_id": "b", "hgvsc": "c.10+3G>A", "transcript_id": "T1"},
                {"variant_id": "d", "hgvsp": "p.Leu9Pro", "transcript_id": "T1"},
            ]
        }
    ]
    kept, without = merged(gene, canonical)
    assert [(v["variant_id"], v["transcript_id"]) for v in kept] == [
        ("a", "T1"),
        ("b", "T2"),
        ("d", "T1"),
    ]
    assert kept[1]["canonical_consequence"]["hgvs_c"] == "c.10+3G>A"
    assert without == 1


def test_gnomad_does_not_cover_a_parasite_protein():
    resolver = EntityResolver(FixtureUniProtClient("temp_data"))
    card, _ = sabueso.resolve(
        "P52270",
        resolver=resolver,
        gnomad={},
        gnomad_client=FixtureGnomADClient("temp_data"),
    )
    states = {
        (r["area"], r["source"]): r["state"] for r in card.knowledge_state()["rows"]
    }
    assert states[(FIELD, "gnomAD")] == "not_queried"
