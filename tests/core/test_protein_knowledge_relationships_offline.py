"""GO annotations, classifications and interactions as typed relationships.

uibcdf/sabueso#21, part 2a: protein-centric knowledge stated by UniProt becomes
relationships of the protein instead of protein-typed cards of annotation concepts.
"""

from collections import Counter

from sabueso import resolve_protein_card
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.uniprot import create_protein_card_from_file


def _card(accession):
    return create_protein_card_from_file(
        f"temp_data/{accession}.json", retrieved_at="2026-02-01"
    )


def _one(card, object_ref):
    (rel,) = card.relationships(object_ref=object_ref)
    return rel, card.source_assertion_store.get(rel["source_assertion_ids"][0])


def test_go_annotations_keep_aspect_term_and_go_code():
    card = _card("P60174")
    assert len(card.relationships(predicate="annotated_with")) == 13

    rel, assertion = _one(card, "go:GO:0005829")
    assert rel["predicate"] == "annotated_with"
    assert rel["qualifiers"] == {
        "aspect": "cellular_component",
        "term": "cytosol",
        "go_code": "IBA",
        "assigned_by": "GO_Central",
    }
    # The source's own property names are kept verbatim in the assertion.
    assert (
        assertion["asserted_value"]["properties"]["GoEvidenceType"] == "IBA:GO_Central"
    )
    assert assertion["subject_ref"] == "uniprot:P60174"

    _, exosome = _one(card, "go:GO:0070062")
    assert exosome["source_metadata"]["eco"][0] == {
        "code": "ECO:0007005",
        "source": "PubMed",
        "id": "19056867",
    }


def test_go_codes_expose_how_well_each_tim_is_characterized():
    human = Counter(
        r["qualifiers"]["go_code"]
        for r in _card("P60174").relationships("annotated_with")
    )
    parasite = Counter(
        r["qualifiers"]["go_code"]
        for r in _card("P52270").relationships("annotated_with")
    )
    assert human["IDA"] == 3 and human["IPI"] == 1  # experimental annotations
    assert parasite == Counter({"IEA": 7})  # electronic inference only


def test_classifications_use_the_namespace_of_each_resource():
    card = _card("P52270")
    classified = {
        r["object_ref"]: r["qualifiers"] for r in card.relationships("classified_in")
    }
    assert len(classified) == 13
    assert classified["pfam:PF00121"]["name"] == "TIM"
    assert classified["cath:3.20.20.70"]["classification"] == "Gene3D"
    assert classified["supfam:SSF51351"]["name"] == "Triosephosphate isomerase (TIM)"
    assert classified["interpro:IPR000652"]["name"] == "Triosephosphate_isomerase"


def test_curated_interactions_become_interacts_with():
    card = _card("P60174")
    interactions = {
        r["object_ref"]: r["qualifiers"] for r in card.relationships("interacts_with")
    }
    assert interactions["uniprot:P42858"]["partner_gene"] == "HTT"
    assert interactions["uniprot:P42858"]["experiments"] == 6
    assert interactions["uniprot:P42858"]["curated_by"] == "IntAct"
    assert _card("P52270").relationships("interacts_with") == []


def test_resolved_cards_carry_the_knowledge_relationships():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    card, _ = resolve_protein_card("P52270", resolver)
    counts = Counter(r["predicate"] for r in card.relationships())
    assert counts == Counter(
        {"classified_in": 13, "has_structure": 7, "annotated_with": 7}
    )
