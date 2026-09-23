"""EntityResolver for UniProt accessions (uibcdf/sabueso#6, step 2).

Acceptance cases A1-A5 and A12 of devguide/pending_proposals/entity_resolver.md, on
frozen public UniProt REST responses (retrieved 2026-09-23).
"""

import json
from pathlib import Path

import pytest

from sabueso.core.relationship_store import RelationshipStore
from sabueso.resolver import (
    EntityQuery,
    EntityResolver,
    FixtureUniProtClient,
    sequence_identity_link,
)

HUMAN_TIM = "sabueso:protein:uniprot:P60174"
CHIMP_TIM = "sabueso:protein:uniprot:P60175"


@pytest.fixture
def resolver():
    return EntityResolver(FixtureUniProtClient("temp_data", failing={"P12345"}))


def _entry(accession):
    return json.loads(Path(f"temp_data/{accession}.json").read_text(encoding="utf-8"))


def test_a1_active_primary_accession(resolver):
    res = resolver.resolve("P60174")
    assert (res.status, res.entity_ref) == ("resolved", HUMAN_TIM)
    assert res.decision["rules"] == ["active_primary_accession"]
    assert res.decision["sources"] == [
        {"name": "UniProt", "record": "P60174", "retrieved_at": "fixture"}
    ]


def test_a2_isoform_accession_resolves_to_the_protein_with_a_qualifier(resolver):
    res = resolver.resolve("uniprot:P60174-3")
    assert (res.status, res.entity_ref) == ("resolved", HUMAN_TIM)
    assert res.qualifiers == {"isoform": "P60174-3"}
    (link,) = res.identity_links
    assert (link["subject_ref"], link["predicate"], link["object_ref"]) == (
        "uniprot:P60174-3",
        "isoform_of",
        "uniprot:P60174",
    )
    assert link["qualifiers"]["isoform_name"] == "2"
    (assertion,) = res.source_assertions
    assert link["source_assertion_ids"] == [assertion["id"]]
    assert assertion["source"]["record_id"] == "P60174"


def test_unlisted_isoform_is_not_found(resolver):
    assert resolver.resolve("P60174-9").status == "not_found"


def test_a3_demerged_accession_is_ambiguous_without_organism(resolver):
    res = resolver.resolve("P00938")
    assert res.status == "ambiguous"
    assert res.entity_ref is None
    assert [c["entity_ref"] for c in res.candidates] == [HUMAN_TIM, CHIMP_TIM]
    assert [c["basis"]["organism"] for c in res.candidates] == [9606, 9598]


def test_a3_demerged_accession_resolves_with_organism_and_keeps_the_alternative(
    resolver,
):
    res = resolver.resolve(EntityQuery(identifier="P00938", organism=9606))
    assert (res.status, res.entity_ref) == ("resolved", HUMAN_TIM)
    assert [a["entity_ref"] for a in res.alternatives] == [CHIMP_TIM]
    assert res.decision["rules"] == ["inactive_demerged_filtered_by_organism"]
    (link,) = res.identity_links
    assert (link["predicate"], link["qualifiers"]) == (
        "superseded_by",
        {"inactive_reason": "DEMERGED"},
    )
    assert res.source_assertions[0]["source"]["record_id"] == "P00938"


def test_merged_secondary_accession_resolves_with_same_as(resolver):
    res = resolver.resolve("Q6FHP9")
    assert (res.status, res.entity_ref) == ("resolved", HUMAN_TIM)
    (link,) = res.identity_links
    assert (link["subject_ref"], link["predicate"], link["object_ref"]) == (
        "uniprot:Q6FHP9",
        "same_as",
        "uniprot:P60174",
    )


def test_a4_identical_sequence_across_organisms_is_not_identity():
    human, chimp = _entry("P60174"), _entry("P60175")
    assert human["sequence"]["md5"] == chimp["sequence"]["md5"]
    assert sequence_identity_link(human, chimp) is None


def test_a5_identical_sequence_in_one_organism_is_only_possibly_same_as():
    link = sequence_identity_link(_entry("P60174"), _entry("V9HWK1"))
    assert (link["predicate"], link["object_ref"]) == (
        "possibly_same_as",
        "uniprot:V9HWK1",
    )
    assert "source_assertion_ids" not in link  # derived, not asserted
    assert link["derivation"]["rule"] == "identical_sequence_same_organism"
    RelationshipStore([link])  # a valid, storable relationship


def test_a12_not_found_error_and_unsupported_stay_distinct(resolver):
    assert resolver.resolve("A0A000Z9Z9").status == "not_found"
    assert resolver.resolve("P12345").status == "error"
    assert resolver.resolve("XYZ").status == "unsupported"
    assert resolver.resolve("pdb:1TCD").status == "unsupported"
    assert resolver.resolve(EntityQuery(name="triosephosphate isomerase")).status == (
        "unsupported"
    )


def test_identifier_contradicting_the_organism_does_not_resolve(resolver):
    res = resolver.resolve(EntityQuery(identifier="P60174", organism=10090))
    assert res.status == "not_found"
    assert res.decision["rules"] == ["organism_mismatch"]
