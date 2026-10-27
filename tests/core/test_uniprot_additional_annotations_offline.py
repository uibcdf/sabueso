"""Additional native UniProt statements preserve their types and source scope."""

import json
from pathlib import Path

import pytest

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.source_assertion_store import assertion_value
from sabueso.mappings.uniprot import map_protein

COMMENTS = {
    "ACTIVITY REGULATION": "annotations.activity_regulation",
    "DOMAIN": "annotations.domain_notes",
    "SIMILARITY": "annotations.similarity",
    "CAUTION": "annotations.source_cautions",
    "MISCELLANEOUS": "annotations.miscellaneous",
}
FEATURES = {
    "Domain": "features_positional.domains",
    "Chain": "features_positional.chain",
    "Lipidation": "features_positional.lipidation",
    "Motif": "features_positional.motif",
    "Region": "features_positional.region",
    "Sequence conflict": "features_positional.sequence_conflict",
    "Topological domain": "features_positional.topological_domain",
    "Transmembrane": "features_positional.transmembrane",
}
ORIGINALS = {
    accession: json.loads(
        Path(f"temp_data/{accession}.json").read_text(encoding="utf-8")
    )
    for accession in ["P52789", "P35372", "A0A140VJM9", "P60174", "P52270"]
}


@pytest.mark.parametrize("kind,path", COMMENTS.items())
def test_all_native_extra_text_occurrences_keep_original_support(kind, path):
    count = 0
    for accession, record in ORIGINALS.items():
        mapping = map_protein(record, "fixture")
        native = [
            (text, comment, index)
            for comment in record.get("comments", [])
            if comment["commentType"] == kind
            for index, text in enumerate(comment.get("texts", []))
            if text.get("value")
        ]
        assert mapping["fields"].get(path, []) == [t["value"] for t, _, _ in native]
        assertions = [
            a for a in mapping["source_assertions"] if a["field_path"] == path
        ]
        assert len(assertions) == len(native)
        for assertion, (text, comment, index) in zip(assertions, native):
            assert assertion["subject_ref"] == "uniprot:" + accession
            assert assertion_value(assertion) == text["value"]
            assert assertion["source"]["version"] == str(
                record["entryAudit"]["entryVersion"]
            )
            if comment.get("molecule"):
                assert assertion["source_metadata"]["molecule"] == comment["molecule"]
                assert assertion["asserted_value"] == {
                    "comment": comment,
                    "text_index": index,
                }
            else:
                assert assertion["asserted_value"] == text["value"]
            assert (
                "knowledge_class" not in assertion and "evidence_class" not in assertion
            )
        count += len(native)
    assert count > 0


@pytest.mark.parametrize("kind,path", FEATURES.items())
def test_all_native_extra_feature_occurrences_keep_locations_and_sequence_revision(
    kind, path
):
    count = 0
    for accession, record in ORIGINALS.items():
        mapping = map_protein(record, "fixture")
        native = [f for f in record.get("features", []) if f["type"] == kind]
        items = mapping["features"].get(path, [])
        assert len(items) == len(native)
        assertions = [
            a for a in mapping["source_assertions"] if a["field_path"] == path
        ]
        assert len(assertions) == len(native)
        for item, source, assertion in zip(items, native, assertions):
            assert assertion["asserted_value"] == source
            assert assertion["normalized_value"] == item
            assert assertion["source_metadata"]["uniprot_feature"] == source
            assert (
                assertion["source_metadata"]["sequence_version"]
                == record["entryAudit"]["sequenceVersion"]
            )
            for endpoint in ("start", "end"):
                coordinates = item["location"]["sequence"]
                assert coordinates[endpoint] == source["location"][endpoint].get(
                    "value"
                )
                assert coordinates.get(endpoint + "_modifier") == source["location"][
                    endpoint
                ].get("modifier")
            assert (
                "knowledge_class" not in assertion and "evidence_class" not in assertion
            )
        count += len(native)
    assert count > 0


@pytest.mark.parametrize("kind,path", COMMENTS.items())
def test_missing_comment_kind_is_not_stated_without_inventing_an_empty_value(
    kind, path
):
    record = json.loads(json.dumps(ORIGINALS["P52789"]))
    record["comments"] = [c for c in record["comments"] if c["commentType"] != kind]
    card = build_card_from_mapping(
        map_protein(record, "fixture"), meta={"entity_type": "protein"}
    )
    assert card.get(path) is None
    (state,) = [r for r in card.knowledge_state()["rows"] if r["area"] == path]
    assert state["state"] == "not_stated"


def test_source_caution_and_similarity_do_not_become_quality_or_identity_findings():
    card = build_card_from_mapping(
        map_protein(ORIGINALS["P52789"], "fixture"), meta={"entity_type": "protein"}
    )
    assert card.get("annotations.source_cautions") is not None
    assert card.get("annotations.similarity") is not None
    assert card.get("quality.cautions") is None
    assert card.relationships("same_as") == []
