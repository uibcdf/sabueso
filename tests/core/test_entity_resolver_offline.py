"""EntityResolver (uibcdf/sabueso#6, steps 2 and 3).

Acceptance cases A1-A7b and A12 of devguide/pending_proposals/entity_resolver.md, on
frozen public UniProt REST responses (retrieved 2026-09-23, UniProt release 2026_03).
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


# Step 3: protein name + organism, resolved by an explicit preference policy (A6, A7, A7b)

TIM_NAME = "triosephosphate isomerase"


def test_a6_name_and_organism_resolved_by_preference_with_trace(resolver):
    res = resolver.resolve(EntityQuery(name=TIM_NAME, organism=9606))
    assert (res.status, res.entity_ref) == ("resolved", HUMAN_TIM)
    assert res.policy == "prefer_reviewed@1"
    assert res.decision["rules"] == ["preference:prefer_reviewed@1"]
    assert len(res.alternatives) == 18
    assert not any(a["basis"]["reviewed"] for a in res.alternatives)
    (search,) = res.decision["sources"]
    assert (search["total"], search["release"]) == (19, "2026_03")
    # The identical-sequence human entry is surfaced as a derived possibly_same_as.
    assert [(lk["predicate"], lk["object_ref"]) for lk in res.identity_links] == [
        ("possibly_same_as", "uniprot:V9HWK1")
    ]


def test_a7_single_match_at_species_level_needs_no_policy(resolver):
    res = resolver.resolve(EntityQuery(name=TIM_NAME, organism=5693))
    assert (res.status, res.entity_ref) == (
        "resolved",
        "sabueso:protein:uniprot:P52270",
    )
    assert res.policy is None
    assert res.decision["rules"] == ["name_organism_single_match"]


def test_a7b_strain_variant_is_kept_as_alternative(resolver):
    res = resolver.resolve(
        EntityQuery(name=TIM_NAME, organism=5693, include_subtaxa=True)
    )
    assert (res.status, res.entity_ref) == (
        "resolved",
        "sabueso:protein:uniprot:P52270",
    )
    (alternative,) = res.alternatives
    assert alternative["basis"]["accession"] == "Q4DV43"
    assert alternative["basis"]["organism"] == 353153  # strain CL Brener
    assert res.identity_links == []  # different sequence: no identity link


def test_without_policy_several_matches_stay_ambiguous():
    resolver = EntityResolver(FixtureUniProtClient("temp_data"), policy=None)
    res = resolver.resolve(EntityQuery(name=TIM_NAME, organism=9606))
    assert res.status == "ambiguous"
    assert len(res.candidates) == 19
    assert res.decision["rules"] == ["no_preference_policy"]


def test_name_search_failure_is_an_error():
    client = FixtureUniProtClient(
        "temp_data", failing={"triosephosphate_isomerase__9606"}
    )
    res = EntityResolver(client).resolve(EntityQuery(name=TIM_NAME, organism=9606))
    assert res.status == "error"


class _StubSearch:
    def __init__(self, results, total=None):
        self.results, self.total = results, total

    def search(self, name, organism, include_subtaxa=False):
        return {
            "query": "stub",
            "total": self.total if self.total is not None else len(self.results),
            "release": None,
            "retrieved_at": "stub",
            "results": self.results,
        }


def _hit(accession, reviewed):
    return {
        "primaryAccession": accession,
        "entryType": "UniProtKB reviewed (Swiss-Prot)"
        if reviewed
        else "UniProtKB unreviewed (TrEMBL)",
        "organism": {"taxonId": 9606, "scientificName": "Homo sapiens"},
        "sequence": {"length": 10, "md5": accession},
    }


def test_truncated_search_never_resolves():
    stub = _StubSearch([_hit("P11111", True), _hit("Q22222", False)], total=900)
    res = EntityResolver(stub).resolve(EntityQuery(name="x", organism=9606))
    assert res.status == "ambiguous"
    assert res.decision["rules"] == ["search_truncated"]


def test_preference_is_inconclusive_with_several_reviewed_matches():
    stub = _StubSearch([_hit("P11111", True), _hit("P33333", True)])
    res = EntityResolver(stub).resolve(EntityQuery(name="x", organism=9606))
    assert res.status == "ambiguous"
    assert res.decision["rules"] == ["preference_inconclusive:prefer_reviewed@1"]


def test_unknown_policy_is_rejected():
    with pytest.raises(ValueError):
        EntityResolver(FixtureUniProtClient("temp_data"), policy="prefer_longest@1")
