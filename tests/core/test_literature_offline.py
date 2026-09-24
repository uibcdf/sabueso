"""Which publications support which statements on a card (uibcdf/sabueso#41, part 1).

Frozen UniProt entries (release 2026_03) of TcTIM (P52270, 3 references) and HsTIM
(P60174, 41 references), and RCSB entries with their primary citations (2026-09-24).
"""

import json
from pathlib import Path

import pytest

from sabueso import resolve_protein_card
from sabueso.mappings.uniprot import map_protein, publication_ref
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

TCTIM, HSTIM = "P52270", "P60174"


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _publications(resolver, accession):
    card, _ = resolve_protein_card(accession, resolver, structures="all")
    view = card.literature()
    return view, {p["ref"]: p for p in view["publications"]}


def test_every_reference_is_a_described_in_relationship_with_its_scope():
    entry = json.loads(Path("temp_data/P52270.json").read_text(encoding="utf-8"))
    rels = {
        r["object_ref"]: r["qualifiers"]
        for r in map_protein(entry, "2026-09-24")["relationships"]
        if r["predicate"] == "described_in"
    }
    assert sorted(rels) == ["pubmed:10468562", "pubmed:9108237", "pubmed:9761683"]
    q = rels["pubmed:9761683"]
    assert q["doi"] == "10.1006/jmbi.1998.2094"
    assert q["year"] == "1998"
    assert q["scope"] == ["X-RAY CRYSTALLOGRAPHY (1.83 ANGSTROMS)", "HOMODIMERIZATION"]
    assert q["comments"] == [{"type": "STRAIN", "value": "Ninoa"}]


@pytest.mark.parametrize(
    "citation, ref",
    [
        (
            {"citationCrossReferences": [{"database": "PubMed", "id": "1"}]},
            "pubmed:1",
        ),
        (
            {"citationCrossReferences": [{"database": "DOI", "id": "10.1/x"}]},
            "doi:10.1/x",
        ),
        ({"id": "CI-ABC"}, "uniprot.citation:CI-ABC"),
        ({}, None),
    ],
)
def test_a_publication_is_named_by_pubmed_then_doi_then_uniprot(citation, ref):
    assert publication_ref(citation) == ref


def test_structures_bring_their_primary_citation(resolver):
    _, pubs = _publications(resolver, TCTIM)
    # 1TCD's paper is also a UniProt reference: one publication, two ways in.
    paper = pubs["pubmed:9761683"]
    assert paper["primary_citation_of"] == ["pdb:1TCD"]
    assert paper["cited_by"][0]["scope"][-1] == "HOMODIMERIZATION"
    assert pubs["pubmed:15321726"]["primary_citation_of"] == ["pdb:1SUX"]
    assert pubs["pubmed:15321726"]["cited_by"] == []  # not a UniProt reference


def test_evidence_links_a_publication_to_the_statements_it_supports(resolver):
    _, pubs = _publications(resolver, HSTIM)
    supported = {s["field_path"] for s in pubs["pubmed:8061610"]["supports"]}
    assert {"annotations.subunit", "features_positional.active_site"} <= supported
    assert pubs["pubmed:8061610"]["primary_citation_of"] == ["pdb:1HTI"]


def test_a_reference_evidence_resolves_to_a_publication_without_pubmed(resolver):
    # The disease evidence "Ref.37" is a journal article UniProt holds without a PMID.
    view, pubs = _publications(resolver, HSTIM)
    paper = pubs["uniprot.citation:CI-9T5RN79Q9AJGF"]
    assert "annotations.disease" in {s["field_path"] for s in paper["supports"]}
    assert view["unresolved_eco"] == []


def test_publications_are_in_chronological_order(resolver):
    view, _ = _publications(resolver, HSTIM)
    years = [p["year"] for p in view["publications"] if p["year"]]
    assert years == sorted(years)
