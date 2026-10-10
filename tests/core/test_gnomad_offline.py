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
    # The six changes in isoform 3's own segment: gnomAD, asked variant by variant,
    # states no consequence on the canonical transcript (#102).
    assert counts == {
        "placed": 7,
        "no_consequence_on_canonical": 6,
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
    assert record["consequences_checked"] == 6


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


def test_a_canonical_transcript_gnomad_does_not_annotate_is_not_asked():
    # UniProt may cross-reference Ensembl transcripts newer than the dataset's GENCODE
    # release; gnomAD's gene record lists the transcripts it annotates.
    class Older(FixtureGnomADClient):
        asked = []

        def variants(self, gene):
            saved = super().variants(gene)
            saved["record"]["gene"]["transcripts"] = [
                t
                for t in saved["record"]["gene"]["transcripts"]
                if t["transcript_id"] != "ENST00000396705"
            ]
            return saved

        def transcript_variants(self, transcript):
            self.asked.append(transcript)
            return super().transcript_variants(transcript)

    client = Older("temp_data")
    card, _ = sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        gnomad={},
        gnomad_client=client,
    )
    assert client.asked == []
    (record,) = [e for e in card.quality["enrichments"] if e["source"] == "gnomAD"]
    assert record["canonical_transcripts"] == [
        {"transcript": "ENST00000396705", "not_in_dataset": True}
    ]


def test_a_transcript_uniprot_states_no_isoform_for_is_canonical_only_without_isoforms():
    from sabueso.mappings._hgvs import transcript_context

    def entry(isoforms):
        comments = (
            [
                {
                    "commentType": "ALTERNATIVE PRODUCTS",
                    "isoforms": [
                        {"isoformIds": ["X-1"], "isoformSequenceStatus": "Displayed"},
                        {"isoformIds": ["X-2"], "sequenceIds": []},
                    ],
                }
            ]
            if isoforms
            else []
        )
        xrefs = [
            {"database": "Ensembl", "id": "ENST01.1", "isoformId": "X-1"},
            {"database": "Ensembl", "id": "ENST02.1"},
        ]
        if not isoforms:
            xrefs = [xrefs[1]]
        return {
            "sequence": {"value": "MAG"},
            "comments": comments,
            "uniProtKBCrossReferences": xrefs,
        }

    # An entry that describes isoforms names the isoform of each transcript it
    # matched; one without an isoform encodes another sequence (as CD44's
    # ENST00000442151 does).
    described = transcript_context(entry(isoforms=True))
    assert described["canonical"] == {"ENST01"}
    assert "ENST02" not in described["isoform_of"]
    assert transcript_context(entry(isoforms=False))["canonical"] == {"ENST02"}


@pytest.fixture(scope="module")
def pext_card():
    resolver = EntityResolver(FixtureUniProtClient("temp_data"))
    card, _ = sabueso.resolve(
        "P60174",
        resolver=resolver,
        gnomad={},
        exon_usage=True,
        gnomad_client=FixtureGnomADClient("temp_data"),
    )
    return card


def test_pext_is_kept_as_gnomad_states_it(pext_card):
    regions = pext_card.get("annotations.exon_usage_by_tissue")["value"]
    assert len(regions) == 12
    first = regions[0]
    assert (first["assembly"], first["chromosome"], first["start"], first["end"]) == (
        "GRCh38",
        "12",
        6867456,
        6867566,
    )
    assert len(first["tissues"]) == 49
    records = {
        e.get("data"): e
        for e in pext_card.quality["enrichments"]
        if e["source"] == "gnomAD"
    }
    assert records["pext"]["version"] == "gnomad_r4 pext (GTEx v10)"
    assert records[None]["count"] == 15  # the variants keep their own record


def test_each_variant_takes_the_pext_of_its_region(pext_card):
    view = pext_card.variant_tissue_usage()
    assert view["rule"]["rule"] == "pext_at_variant@2"
    assert (
        view["rule"]["parameters"]["coordinate_policy"]
        == "explicit_equal_assembly_and_chromosome"
    )
    by_id = {i["variant_id"]: i for i in view["items"]}
    # E105D, on the canonical isoform, lies in a region every tissue expresses.
    e105d = by_id["12-6869174-G-C"]["pext"]
    assert len(e105d["at_or_above_threshold"]) == 49
    # Isoform 3's own N-terminal segment is expressed in testis only.
    segment = by_id["12-6867456-A-G"]
    assert segment["not_placed"] == "no_consequence_on_canonical"
    assert segment["pext"]["at_or_above_threshold"] == ["testis"]
    assert segment["pext"]["max"]["tissue"] == "testis"
    assert segment["pext"]["mean"] < 0.01


def test_a_variant_outside_every_region_is_not_called_unexpressed(pext_card):
    from sabueso.core.tissue_usage import variant_tissue_usage_view

    class Card:
        def get(self, path):
            return {
                "annotations.exon_usage_by_tissue": {
                    "value": [
                        {
                            "chromosome": "12",
                            "start": 10,
                            "end": 20,
                            "mean": 0.5,
                            "tissues": [{"tissue": "liver", "value": 0.5}],
                        }
                    ]
                },
                "annotations.population_variants": {
                    "value": [{"variant_id": "12-30-A-G"}, {"variant_id": "x"}]
                },
            }.get(path)

    view = variant_tissue_usage_view(Card())
    assert [i["pext"]["basis"] for i in view["items"]] == [
        "outside_pext_regions",
        "no_position",
    ]


def test_a_change_in_an_exon_the_canonical_transcript_lacks_is_not_placed():
    # PKM's M1 exon: identical residues flank the segment UniProt marks as different,
    # so the isoform map would place a change there; gnomAD states it is intronic on
    # the canonical (M2) transcript.
    from sabueso.mappings.gnomad import merged

    gene = [
        {"variant_id": "m1", "hgvsp": "p.Ser434Phe", "transcript_id": "M1"},
        {"variant_id": "both", "hgvsp": "p.Gly5Ser", "transcript_id": "M1"},
        {"variant_id": "elsewhere", "hgvsp": "p.Ala2Thr", "transcript_id": "M1"},
    ]
    consequences = {
        "m1": [
            {"transcript_id": "M1", "hgvsp": "p.Ser434Phe"},
            {
                "transcript_id": "M2",
                "hgvsc": "c.1167+30C>T",
                "major_consequence": "intron_variant",
            },
        ],
        "both": [
            {"transcript_id": "M1", "hgvsp": "p.Gly5Ser"},
            {
                "transcript_id": "M2",
                "hgvsp": "p.Gly5Ser",
                "transcript_version": "3",
                "major_consequence": "missense_variant",
            },
        ],
        "elsewhere": [{"transcript_id": "M1", "hgvsp": "p.Ala2Thr"}],
    }
    kept, _ = merged(gene, [], consequences, {"M2"})
    by_id = {v["variant_id"]: v for v in kept}
    assert by_id["m1"]["canonical_consequence"]["consequence"] == "intron_variant"
    assert (by_id["both"]["transcript_id"], by_id["both"]["hgvsp"]) == (
        "M2",
        "p.Gly5Ser",
    )
    assert by_id["elsewhere"]["no_canonical_consequence"] is True


def test_each_isoform_takes_the_pext_of_its_own_coding_bases(pext_card):
    exons = pext_card.get("annotations.isoform_coding_exons")["value"]
    assert {e["isoform"] for e in exons} == {"P60174-1", "P60174-3", "P60174-4"}
    view = pext_card.isoform_tissue_usage()
    assert view["rule"]["rule"] == "isoform_exon_usage@3"
    # Every isoform's exons are known, so own bases are counted against all of them.
    assert view["isoforms_without_exons"] == []
    assert view["variable_regions_complete"] is True
    by_id = {i["isoform"]: i for i in view["items"]}
    # The canonical isoform shares every coding base with isoform 3.
    assert by_id["P60174-1"]["pext"] == {"basis": "no_own_coding_bases"}
    own = by_id["P60174-3"]
    assert own["own_coding_bases"] == 111
    assert own["own_bases_complete"] is True
    assert own["pext"]["at_or_above_threshold"] == ["testis"]
    (region,) = [r for r in view["variable_regions"] if r["isoforms"] == ["P60174-3"]]
    assert region["pext"]["max"]["tissue"] == "testis"


def test_variable_regions_follow_the_isoforms_that_include_them():
    # Tau-like: a constitutive exon, an exon two isoforms of three include, and one
    # only the third includes.
    from sabueso.core.tissue_usage import variable_regions

    cds = {
        "A": [[1, 10], [20, 29]],
        "B": [[1, 10], [20, 29]],
        "C": [[1, 10], [40, 49]],
    }
    assert variable_regions(cds) == [
        {"start": 20, "end": 29, "isoforms": ["A", "B"]},
        {"start": 40, "end": 49, "isoforms": ["C"]},
    ]


def test_uniprot_statements_restricted_to_an_isoform_are_kept_with_it():
    from sabueso.core.tissue_usage import isoform_tissue_usage_view

    class Store:
        def find_by_field(self, path):
            return [
                {
                    "id": "SA_1",
                    "asserted_value": "Specifically expressed in proliferating cells",
                    "source_metadata": {
                        "molecule": "Isoform M2",
                        "eco": ["ECO:0000269"],
                    },
                },
                {"id": "SA_2", "asserted_value": "Ubiquitous", "source_metadata": {}},
            ]

    class Card:
        source_assertion_store = Store()

        def get(self, path):
            return {
                "annotations.isoforms": {
                    "value": [
                        {
                            "isoform_id": "X-1",
                            "name": "M2",
                            "sequence_status": "Displayed",
                        },
                        {"isoform_id": "X-2", "name": "M1"},
                    ]
                }
            }.get(path)

    view = isoform_tissue_usage_view(Card())
    by_id = {i["isoform"]: i for i in view["items"]}
    assert [
        s["source_assertion_id"] for s in by_id["X-1"]["uniprot_tissue_specificity"]
    ] == ["SA_1"]
    assert by_id["X-2"]["uniprot_tissue_specificity"] == []
    assert [s["text"] for s in view["entry_tissue_specificity"]] == ["Ubiquitous"]
    # Built before UniProt's transcripts were recorded (schema 0.3.10).
    assert by_id["X-1"]["pext"] == {"basis": "transcripts_not_recorded"}


def test_an_isoform_without_exons_says_why_and_own_bases_say_they_may_be_shared():
    # X-1: exons from gnomAD. X-2: a transcript UniProt states, which gnomAD does not
    # annotate. X-3: no transcript UniProt states (as most of CD44's isoforms, #102).
    from sabueso.core.tissue_usage import isoform_tissue_usage_view

    class Store:
        def find_by_field(self, path):
            return []

    fields = {
        "annotations.isoforms": [
            {"isoform_id": "X-1", "name": "1", "sequence_status": "Displayed"},
            {"isoform_id": "X-2", "name": "2"},
            {"isoform_id": "X-3", "name": "3"},
        ],
        "annotations.isoform_coding_exons": [
            {"isoform": "X-1", "transcript": "ENST1", "cds": [[100, 199]]}
        ],
        "identifiers.ensembl_transcripts": [
            {"transcript": "ENST1.4", "isoform": "X-1"},
            {"transcript": "ENST2.1", "isoform": "X-2"},
        ],
    }

    class Card:
        source_assertion_store = Store()

        def get(self, path):
            return {"value": fields[path]} if path in fields else None

    view = isoform_tissue_usage_view(Card())
    by_id = {i["isoform"]: i for i in view["items"]}
    assert by_id["X-2"]["pext"] == {"basis": "transcript_not_in_gnomad"}
    assert by_id["X-2"]["transcripts"] == ["ENST2.1"]
    assert by_id["X-3"]["pext"] == {"basis": "no_transcript_stated"}
    assert view["isoforms_without_exons"] == ["X-2", "X-3"]
    # X-1's bases are its own only among the isoforms whose exons are known.
    assert by_id["X-1"]["own_coding_bases"] == 100
    assert by_id["X-1"]["own_bases_complete"] is False
    assert view["variable_regions_complete"] is False


def test_the_pext_record_counts_its_regions(pext_card):
    (record,) = [e for e in pext_card.quality["enrichments"] if e.get("data") == "pext"]
    # Until 0.9.0 the record counted nothing: the field name was shadowed.
    assert record["count"] == len(
        pext_card.get("annotations.exon_usage_by_tissue")["value"]
    )
    assert record["count"] > 0


def test_uniprot_s_ensembl_transcripts_are_recorded_with_their_isoforms(pext_card):
    # UniProt's own cross-references (schema 0.3.10, #102), versioned as it states them.
    stated = pext_card.get("identifiers.ensembl_transcripts")
    by_transcript = {x["transcript"]: x for x in stated["value"]}
    assert by_transcript["ENST00000396705.10"] == {
        "transcript": "ENST00000396705.10",
        "protein": "ENSP00000379933.4",
        "gene": "ENSG00000111669.16",
        "isoform": "P60174-1",
    }
    assert {x["isoform"] for x in stated["value"]} == {
        "P60174-1",
        "P60174-3",
        "P60174-4",
    }
    made = pext_card.source_assertion_store.get(stated["source_assertion_ids"][0])
    assert made["source"]["name"] == "UniProt"
