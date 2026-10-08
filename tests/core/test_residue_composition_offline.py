"""Composition counts a supported sequence set, not repeated or unnamed rows."""

import copy
import hashlib
import json
from pathlib import Path

import ackredit
import pytest

from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, SchemaError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.mobidb import map_disorder_regions
from sabueso.tools.db.mobidb import FixtureMobiDBClient, get_annotations


def protein(sequence="GGK"):
    assertion = make_source_assertion(
        "sequence.primary", sequence, "UniProt", "P60174", "2026-01-01"
    )
    return Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:P60174"},
        sections={
            "identifiers": {"uniprot": {"value": "P60174", "source_assertion_ids": []}},
            "sequence": {
                "primary": {
                    "value": sequence,
                    "source_assertion_ids": [assertion["id"]],
                }
            },
        },
        source_assertion_store=[assertion],
    )


def declaration(
    sequence="GXXK", sequence_ref="Source:P60174", subject="uniprot:P60174"
):
    assertion = make_source_assertion(
        "sequence.residue_tracks.test",
        {"native": True},
        "Source",
        "original-record",
        "2020-01-01",
        subject_ref=subject,
    )
    assertion["source"]["version"] = "revision-1"
    assertion["source_metadata"] = {
        "sequence": {
            "id": sequence_ref,
            "value": sequence,
            "uniprot_ref": subject,
            "sha256": hashlib.sha256(sequence.encode()).hexdigest(),
        },
        "native_method": "source-defined",
    }
    return assertion


def test_unique_set_retains_original_selection_support_and_detached_counts():
    card = protein()
    positions = [3, 1, 1, 2, 3]
    before = card.to_dict()
    report = card.residue_composition(positions)
    assert report["rule"] == "residue_set_composition@1"
    assert report["status"] == "complete" and report["total"] == 3
    assert report["counts"] == {"G": 2, "K": 1}
    assert report["fractions"] == {"G": 2 / 3, "K": 1 / 3}
    assert report["denominator"]["count"] == 3
    assert report["selection"]["requested_positions"] == positions
    assert report["selection"]["unique_positions"] == [1, 2, 3]
    assert report["selection"]["duplicate_occurrences"] == [
        {"input_index": 2, "position": 1},
        {"input_index": 4, "position": 3},
    ]
    assert "cavity_membership_not_established" in report["selection"]["basis"]
    assert report["card_ref"] == card.pinned_ref()
    assert report["sequence_ref"] == "UniProt:P60174"
    (support,) = report["sequence_support"]["support"]
    assert support["assertion"]["asserted_value"] == "GGK"
    assert support["snapshot_id"] == digest(canonical_json(support["assertion"]))
    assert report["sequence_support"]["support_status"] == "complete"
    report["members"][0].clear()
    report["selection"]["requested_positions"].clear()
    support["assertion"].clear()
    assert card.to_dict() == before and positions == [3, 1, 1, 2, 3]


def test_ambiguous_types_remain_in_denominator_and_concrete_u_o_remain_literal():
    card = protein("GXBUOZJ")
    report = card.residue_composition([1, 2, 3, 4, 5, 6, 7])
    assert report["status"] == "partial" and report["total"] == 7
    assert report["counts"] == {"G": 1, "O": 1, "U": 1}
    assert report["unresolved_counts"] == {"B": 1, "J": 1, "X": 1, "Z": 1}
    assert report["concrete_count"] == 3 and report["unresolved_count"] == 4
    assert report["fractions"] == {"G": 1 / 7, "O": 1 / 7, "U": 1 / 7}
    assert report["unresolved_fraction"] == 4 / 7
    assert sum(report["fractions"].values()) + report["unresolved_fraction"] == 1
    unknown = card.residue_composition([2, 3])
    assert unknown["counts"] == {} and unknown["fractions"] == {}
    assert unknown["total"] == 2 and unknown["unresolved_fraction"] == 1


def test_explicit_empty_selection_has_zero_count_and_no_fabricated_fraction():
    report = protein().residue_composition([])
    assert report["status"] == "empty" and report["total"] == 0
    assert report["counts"] == report["fractions"] == report["unresolved_counts"] == {}
    assert report["members"] == [] and report["unresolved_fraction"] is None
    assert report["sequence_support"]["support_status"] == "complete"


@pytest.mark.parametrize(
    "positions",
    [
        None,
        "1,2",
        (1, 2),
        [0],
        [-1],
        [True],
        [1.0],
        ["1"],
        [{"one_letter_code": "GLY"}],
        [{"chain": "A", "position": 1}],
    ],
)
def test_unsafe_or_structural_positions_are_refused_without_coercion(positions):
    card = protein()
    for skip in (False, True):
        with pytest.raises(ArgumentError):
            card.residue_composition(positions, skip_digestion=skip)


@pytest.mark.parametrize("positions", [[4], [1, 4]])
def test_out_of_bounds_selection_is_not_a_silently_truncated_set(positions):
    with pytest.raises(IndexError):
        protein().residue_composition(positions)


@pytest.mark.parametrize("sequence", ["", "G K", "G*K", "ggk", "GλK"])
def test_missing_or_malformed_sequence_cannot_produce_an_empty_answer(sequence):
    with pytest.raises(SchemaError):
        protein(sequence).residue_composition([])


def test_missing_and_incompatible_sequence_support_is_explicit():
    card = protein()
    node = card.get("sequence.primary")
    original = node["source_assertion_ids"][0]
    foreign = make_source_assertion(
        "sequence.primary", "GGK", "UniProt", "P37840", "2020-01-01"
    )
    card.source_assertion_store.add(foreign)
    node["source_assertion_ids"] = [original, foreign["id"], "missing"]
    report = card.residue_composition([1, 2, 3])
    support = report["sequence_support"]
    assert report["status"] == "partial" and report["counts"] == {"G": 2, "K": 1}
    assert support["source_assertion_ids"] == [original]
    assert support["incompatible_source_assertion_ids"] == [foreign["id"]]
    assert support["missing_source_assertion_ids"] == ["missing"]
    assert len(support["support"]) == 1 and support["support_status"] == "incomplete"
    node["source_assertion_ids"] = []
    unsupported = card.residue_composition([1])
    assert (
        unsupported["status"] == "partial"
        and unsupported["sequence_support"]["support"] == []
    )


def test_explicit_source_sequence_retains_full_revisions_and_does_not_project():
    card = protein("KKKK")
    assertion = declaration()
    before = copy.deepcopy(assertion)
    report = card.residue_composition(
        [1, 4], sequence_ref="Source:P60174", source_assertions=[assertion]
    )
    assert report["counts"] == {"G": 1, "K": 1}
    assert report["sequence_ref"] == "Source:P60174"
    assert report["sequence_sha256"] == hashlib.sha256(b"GXXK").hexdigest()
    support = report["sequence_support"]["support"][0]
    assert support["assertion"] == assertion and support["origin"] == "supplied"
    assert support["assertion"]["source"]["version"] == "revision-1"
    assert support["assertion"]["retrieved_at"] == "2020-01-01"
    assert "canonical_positions" not in report and "source_assertion" not in report
    canonical = card.residue_composition([1, 4], source_assertions=[assertion])
    assert canonical["counts"] == {"K": 2}
    assert canonical["selection"]["supplied_assertions_not_used"] == 1
    support["assertion"]["source_metadata"].clear()
    assert assertion == before


def test_multiple_equal_sequence_declarations_preserve_independent_source_snapshots():
    first = declaration()
    second = copy.deepcopy(first)
    second["source"]["version"] = "revision-2"
    report = protein().residue_composition(
        [1], sequence_ref="Source:P60174", source_assertions=[first, second]
    )
    supports = report["sequence_support"]["support"]
    assert len(supports) == 2
    assert supports[0]["source_assertion_id"] == supports[1]["source_assertion_id"]
    assert supports[0]["snapshot_id"] != supports[1]["snapshot_id"]
    assert report["counts"] == {"G": 1}
    changed = copy.deepcopy(first)
    changed["source"]["version"] = "revision-3"
    other = protein().residue_composition(
        [1], sequence_ref="Source:P60174", source_assertions=[changed]
    )
    assert other["counts"] == report["counts"]
    assert (
        other["sequence_support"]["support"][0]["snapshot_id"]
        != supports[0]["snapshot_id"]
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda a: a.update(subject_ref="uniprot:P37840"),
        lambda a: a["source_metadata"]["sequence"].update(uniprot_ref="uniprot:P37840"),
        lambda a: a["source_metadata"]["sequence"].update(sha256="incorrect"),
        lambda a: a["source_metadata"]["sequence"].update(value="G K"),
    ],
)
def test_wrong_source_subject_or_sequence_digest_cannot_support_the_selected_axis(
    change,
):
    assertion = declaration()
    change(assertion)
    card = protein()
    with pytest.raises(SchemaError):
        card.residue_composition(
            [1], sequence_ref="Source:P60174", source_assertions=[assertion]
        )
    valid = declaration()
    report = card.residue_composition(
        [1], sequence_ref="Source:P60174", source_assertions=[assertion, valid]
    )
    assert report["status"] == "partial" and report["counts"] == {"G": 1}
    assert len(report["sequence_support"]["support"]) == 1
    (excluded,) = report["sequence_support"]["excluded_declarations"]
    assert excluded["support"]["assertion"] == assertion


def test_contradictory_sequence_declarations_are_refused_instead_of_selected():
    with pytest.raises(SchemaError, match="contradictory"):
        protein().residue_composition(
            [1],
            sequence_ref="Source:P60174",
            source_assertions=[declaration("GXXK"), declaration("KXXG")],
        )
    with pytest.raises(SchemaError):
        protein().residue_composition([], sequence_ref="Unqueried:P60174")


@pytest.mark.parametrize(
    "sequence_ref", [None, "", "P60174", "Source: P60174", ":P60174"]
)
def test_invalid_axis_fails_even_when_argument_digestion_is_skipped(sequence_ref):
    for skip in (False, True):
        with pytest.raises(ArgumentError):
            protein().residue_composition(
                [1], sequence_ref=sequence_ref, skip_digestion=skip
            )


def test_source_declarations_already_in_card_and_bad_input_records_keep_their_scope():
    card = protein()
    assertion = declaration()
    card.source_assertion_store.add(assertion)
    report = card.residue_composition([1], sequence_ref="Source:P60174")
    assert report["sequence_support"]["support"][0]["origin"] == "card_store"
    for invalid in ({}, [None]):
        with pytest.raises(ArgumentError):
            card.residue_composition(
                [1], source_assertions=invalid, skip_digestion=True
            )
    nonfinite = declaration()
    nonfinite["source_metadata"]["extra"] = float("nan")
    with pytest.raises(SchemaError):
        card.residue_composition(
            [1], sequence_ref="Source:P60174", source_assertions=[nonfinite]
        )


def test_public_mobidb_axis_matches_source_sequence_with_no_new_acquisition(
    monkeypatch,
):
    assertions = map_disorder_regions(
        get_annotations("P60174", client=FixtureMobiDBClient())
    )
    sequence = assertions[0]["source_metadata"]["sequence"]["value"]
    card = Card.from_json("temp_data/frozen_cards/schema_0.3.12__P60174.json")
    before = card.to_dict()

    def forbidden(*args, **kwargs):
        pytest.fail("A composition reader must not reach the network or create credit.")

    monkeypatch.setattr("sabueso.tools.db._http._urlopen", forbidden)
    with ackredit.session("composition reader"):
        with ackredit.capture("reader") as workflow:
            report = card.residue_composition(
                [1, 2, 249], sequence_ref="MobiDB:P60174", source_assertions=assertions
            )
    assert workflow.attribution.to_dict()["uses"] == []
    assert [member["amino_acid"] for member in report["members"]] == [
        sequence[n - 1] for n in [1, 2, 249]
    ]
    assert report["sequence_ref"] == "MobiDB:P60174" and report["total"] == 3
    assert all(
        s["assertion"]["source"]["version"] == "7.0"
        for s in report["sequence_support"]["support"]
    )
    assert "acquisition_trace" not in report
    json.dumps(report, allow_nan=False)
    assert card.to_dict() == before


def test_frozen_public_card_roundtrip_pin_schema_and_canonical_counts_are_unchanged():
    path = Path("temp_data/frozen_cards/schema_0.3.12__P60174.json")
    original_bytes = path.read_bytes()
    card = Card.from_json(path)
    before = card.to_dict()
    original_pin = card.pinned_ref()
    report = card.residue_composition([164, 1, 164, 2])
    assert (
        report["total"] == 3 and len(report["selection"]["duplicate_occurrences"]) == 1
    )
    assert report["card_ref"] == original_pin
    assert card.to_dict() == before and path.read_bytes() == original_bytes
    reloaded = Card.from_dict(card.to_dict())
    assert reloaded.residue_composition([164, 1, 164, 2]) == report
