"""Native domains retain source bounds, sequence scope and independent support."""

import copy
import json
from pathlib import Path

import pytest

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.errors import ConnectorError
from sabueso.mappings.uniprot import map_protein

FIELD = "features_positional.domains"


def original(accession="P52789"):
    return json.loads(Path(f"temp_data/{accession}.json").read_text())


def build(record):
    return build_card_from_mapping(
        map_protein(record, "2026-10-08"), meta={"entity_type": "protein"}
    )


def one_domain():
    record = original()
    record["features"] = [next(f for f in record["features"] if f["type"] == "Domain")]
    return record, record["features"][0]


@pytest.mark.parametrize("accession", ["P52789", "A0A140VJM9"])
def test_original_domains_preserve_bounds_support_and_native_revisions(accession):
    record = original(accession)
    before = copy.deepcopy(record)
    native = [f for f in record["features"] if f["type"] == "Domain"]
    card = build(record)
    node = card.get(FIELD)
    assert len(native) == len(node["value"]) == 2
    for item, source in zip(node["value"], native):
        coordinates = item["location"]["sequence"]
        assert coordinates == {
            "sequence_id": "UniProt:" + accession,
            "start": source["location"]["start"]["value"],
            "end": source["location"]["end"]["value"],
            "indexing": "1-based",
            "start_modifier": "EXACT",
            "end_modifier": "EXACT",
        }
        assert item["description"] == source["description"]
        (assertion,) = [
            card.source_assertion_store.get(support)
            for support in node["source_assertion_ids"]
            if card.source_assertion_store.get(support)["asserted_value"] == item
        ]
        assert assertion["subject_ref"] == "uniprot:" + accession
        assert assertion["source"]["version"] == str(
            record["entryAudit"]["entryVersion"]
        )
        assert assertion["retrieved_at"] == "2026-10-08"
        metadata = assertion["source_metadata"]
        assert metadata["uniprot_feature"] == source
        assert metadata["sequence_version"] == record["entryAudit"]["sequenceVersion"]
        assert metadata["eco"][0]["code"] == source["evidences"][0]["evidenceCode"]
        assert "knowledge_class" not in assertion and "evidence_class" not in assertion
    assert record == before


def test_native_domain_membership_has_exact_item_support_and_inclusive_boundaries():
    card = build(original())
    for position, name in [
        (16, "Hexokinase 1"),
        (458, "Hexokinase 1"),
        (464, "Hexokinase 2"),
        (906, "Hexokinase 2"),
    ]:
        (domain,) = [
            a
            for a in card.get_residue(position)["annotations"]
            if a["field_path"] == FIELD
        ]
        assert domain["annotation"]["description"] == name
        assert domain["support_status"] == "complete"
        (support,) = domain["source_assertion_ids"]
        assert (
            card.source_assertion_store.get(support)["asserted_value"]
            == domain["annotation"]
        )
    for position in [15, 459, 463, 907]:
        assert not any(
            a["field_path"] == FIELD for a in card.get_residue(position)["annotations"]
        )


@pytest.mark.parametrize("endpoint", ["start", "end"])
@pytest.mark.parametrize(
    "modifier", ["LESS_THAN", "GREATER_THAN", "UNKNOWN", "UNSURE", "FUTURE"]
)
def test_uncertain_bounds_remain_literal_and_never_become_exact_membership(
    endpoint, modifier
):
    record, feature = one_domain()
    feature["location"][endpoint]["modifier"] = modifier
    card = build(record)
    (item,) = card.get(FIELD)["value"]
    assert item["location"]["sequence"][endpoint + "_modifier"] == modifier
    view = card.get_residue(100)
    assert not any(a["field_path"] == FIELD for a in view["annotations"])
    assert {r["reason"] for r in view["unmapped"] if r["field_path"] == FIELD} == {
        "location not an exact valid range"
    }


@pytest.mark.parametrize("missing", ["start", "end", "both"])
def test_unstated_bounds_are_preserved_without_inventing_a_single_residue(missing):
    record, feature = one_domain()
    for endpoint in ("start", "end") if missing == "both" else (missing,):
        feature["location"][endpoint] = {"modifier": "UNKNOWN"}
    card = build(record)
    (item,) = card.get(FIELD)["value"]
    for endpoint in ("start", "end") if missing == "both" else (missing,):
        assert item["location"]["sequence"][endpoint] is None
    assert not any(
        a["field_path"] == FIELD for a in card.get_residue(100)["annotations"]
    )


@pytest.mark.parametrize("endpoint", ["start", "end"])
@pytest.mark.parametrize("invalid", [False, 1.5, "16", []])
def test_malformed_domain_endpoints_fail_instead_of_becoming_absent(endpoint, invalid):
    record, feature = one_domain()
    feature["location"][endpoint]["value"] = invalid
    with pytest.raises(ConnectorError, match="domain endpoints"):
        build(record)


@pytest.mark.parametrize("molecule", ["Isoform 2", "P52789-2"])
def test_other_molecule_scope_is_retained_without_canonical_placement(molecule):
    record, feature = one_domain()
    feature["molecule"] = molecule
    card = build(record)
    (item,) = card.get(FIELD)["value"]
    assert item["location"]["sequence"]["sequence_id"] is None
    (support,) = card.get(FIELD)["source_assertion_ids"]
    assert (
        card.source_assertion_store.get(support)["source_metadata"]["uniprot_feature"][
            "molecule"
        ]
        == molecule
    )
    view = card.get_residue(100)
    assert not any(a["field_path"] == FIELD for a in view["annotations"])
    assert any(
        r["field_path"] == FIELD and r["reason"] == "sequence identity not stated"
        for r in view["unmapped"]
    )


def test_unknown_revisions_stay_unknown_and_mapping_metadata_is_detached():
    record, feature = one_domain()
    record.pop("entryAudit")
    mapping = map_protein(record, "fixture")
    (assertion,) = [a for a in mapping["source_assertions"] if a["field_path"] == FIELD]
    assert assertion["source"].get("version") is None
    assert "sequence_version" not in assertion["source_metadata"]
    assertion["source_metadata"]["uniprot_feature"]["description"] = "Changed output"
    assert feature["description"] == "Hexokinase 1"


def test_domain_of_another_known_sequence_revision_is_not_placed():
    record, _ = one_domain()
    card = build(record)
    (support,) = card.get("sequence.primary")["source_assertion_ids"]
    card.source_assertion_store.get(support)["source_metadata"]["sequence_version"] = 3
    view = card.get_residue(100)
    assert not any(a["field_path"] == FIELD for a in view["annotations"])
    assert any(
        r["field_path"] == FIELD and r["reason"] == "source sequence version differs"
        for r in view["unmapped"]
    )


@pytest.mark.parametrize("invalid", [False, [], "invalid"])
def test_malformed_native_location_objects_fail(invalid):
    record, feature = one_domain()
    feature["location"] = invalid
    with pytest.raises(ConnectorError, match="location.*native object"):
        build(record)


@pytest.mark.parametrize("invalid", [False, [], "invalid"])
def test_malformed_native_endpoint_objects_fail(invalid):
    record, feature = one_domain()
    feature["location"]["start"] = invalid
    with pytest.raises(ConnectorError, match="endpoint.*native object"):
        build(record)


def test_domain_card_round_trip_preserves_exact_scientific_state(tmp_path):
    card = build(original())
    before = card.to_dict()
    card.to_json(tmp_path / "domains.json")
    card.to_sqlite(tmp_path / "domains.db")
    for restored in [
        Card.from_json(tmp_path / "domains.json"),
        Card.from_sqlite(tmp_path / "domains.db", card_id=card.id),
    ]:
        assert restored.to_dict() == before
        assert restored.snapshot_id() == card.snapshot_id()
        assert restored.get_residue(16) == card.get_residue(16)
