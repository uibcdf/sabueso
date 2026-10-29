"""Frozen original selection protocol; all short records here are synthetic."""

from copy import deepcopy

import pytest

from sabueso.core._source_active_site_selection_v1 import FIELD, _v1_positions
from sabueso.core.card import Card
from sabueso.core.errors import SchemaError
from sabueso.core.source_assertion_store import make_source_assertion


@pytest.fixture
def card():
    site = {
        "location": {
            "kind": "sequence",
            "sequence": {
                "sequence_id": "UniProt:SYNTHETIC",
                "indexing": "1-based",
                "start": 2,
                "end": 3,
            },
        },
        "description": "Synthetic protocol annotation, not molecular knowledge",
    }
    sequence = make_source_assertion(
        "sequence.primary", "MSTAA", "UniProt", "SYNTHETIC", "fixture"
    )
    active = make_source_assertion(
        FIELD, deepcopy(site), "UniProt", "SYNTHETIC", "fixture"
    )
    return Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:SYNTHETIC"},
        sections={
            "identifiers": {
                "uniprot": {"value": "SYNTHETIC", "source_assertion_ids": []}
            },
            "sequence": {
                "primary": {"value": "MSTAA", "source_assertion_ids": [sequence["id"]]}
            },
            "features_positional": {
                "active_site": {"value": [site], "source_assertion_ids": [active["id"]]}
            },
        },
        source_assertion_store=[sequence, active],
    )


def source(card, field=FIELD):
    return card.source_assertion_store.get(card.get(field)["source_assertion_ids"][0])


def current_positions(card):
    return [
        row["position"]
        for row in card.get_residues()
        if any(
            annotation["field_path"] == FIELD
            and annotation["support_status"] == "complete"
            for annotation in row["annotations"]
        )
    ]


@pytest.mark.parametrize(
    "change,expected",
    [
        ({}, [2, 3]),
        ({"start_modifier": "EXACT", "end_modifier": "EXACT"}, [2, 3]),
        ({"sequence_id": "uniprot:synthetic"}, [2, 3]),
        ({"sequence_id": "UniProt:OTHER"}, []),
        ({"sequence_id": "UniProt:SYNTHETIC-2"}, []),
        ({"sequence_id": None}, []),
        ({"sequence_id": []}, []),
        ({"indexing": "0-based"}, []),
        ({"start": 0}, []),
        ({"end": 6}, []),
        ({"start": 4}, []),
        ({"start": True}, []),
        ({"start": 2.0}, []),
        ({"start_modifier": "LESS_THAN"}, []),
        ({"end_modifier": "UNCERTAIN"}, []),
    ],
)
def test_original_axis_exactness_bounds_and_unknown_modifiers(card, change, expected):
    site = card.get(FIELD)["value"][0]
    site["location"]["sequence"].update(change)
    source(card)["asserted_value"] = deepcopy(site)
    before = card.to_dict()
    assert _v1_positions(card) == current_positions(card) == expected
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "damage",
    [
        "none",
        "missing",
        "mixed_missing",
        "foreign",
        "mixed_foreign",
        "wrong_field",
        "wrong_item",
    ],
)
def test_only_original_complete_item_subject_support_selects_positions(card, damage):
    node = card.get(FIELD)
    if damage == "none":
        node["source_assertion_ids"] = []
    elif damage == "missing":
        node["source_assertion_ids"] = ["SYNTHETIC_MISSING"]
    elif damage == "mixed_missing":
        node["source_assertion_ids"].append("SYNTHETIC_MISSING")
    else:
        other = deepcopy(source(card))
        other["id"] = "SYNTHETIC_OTHER"
        if damage in ("foreign", "mixed_foreign"):
            other["subject_ref"] = "uniprot:OTHER"
        elif damage == "wrong_field":
            other["field_path"] = "features_positional.binding_site"
        else:
            other["asserted_value"]["description"] = "A different original item"
        card.source_assertion_store.add(other)
        node["source_assertion_ids"] = (
            node["source_assertion_ids"] if damage == "mixed_foreign" else []
        ) + [other["id"]]
    assert _v1_positions(card) == current_positions(card) == []


@pytest.mark.parametrize(
    "sequence_version,feature_version,expected",
    [
        (2, 2, [2, 3]),
        (2, 3, []),
        (None, 3, [2, 3]),
        (2, None, [2, 3]),
        (None, None, [2, 3]),
    ],
)
def test_original_revision_policy_preserves_unstated_versions(
    card, sequence_version, feature_version, expected
):
    for field, version in [
        ("sequence.primary", sequence_version),
        (FIELD, feature_version),
    ]:
        source(card, field)["source_metadata"] = (
            {} if version is None else {"sequence_version": version}
        )
    assert _v1_positions(card) == current_positions(card) == expected


def test_normalized_assertion_values_have_original_precedence(card):
    record = source(card)
    record["normalized_value"] = deepcopy(record["asserted_value"])
    record["asserted_value"] = {"synthetic_original_wire": "not the normalized item"}
    assert _v1_positions(card) == current_positions(card) == [2, 3]
    record["normalized_value"] = None
    assert _v1_positions(card) == current_positions(card) == []


def test_overlapping_duplicate_annotations_form_ascending_unique_union(card):
    site = deepcopy(card.get(FIELD)["value"][0])
    site["location"]["sequence"].update(start=1, end=2)
    card.get(FIELD)["value"].extend([site, deepcopy(site)])
    extra = make_source_assertion(
        FIELD, [deepcopy(site)], "UniProt", "SYNTHETIC", "fixture"
    )
    card.source_assertion_store.add(extra)
    card.get(FIELD)["source_assertion_ids"].append(extra["id"])
    assert _v1_positions(card) == current_positions(card) == [1, 2, 3]


@pytest.mark.parametrize("kind", ["compound", "structure", "unknown"])
def test_original_unsupported_location_kinds_are_not_backfilled(card, kind):
    card.get(FIELD)["value"][0]["location"]["kind"] = kind
    source(card)["asserted_value"] = deepcopy(card.get(FIELD)["value"][0])
    assert _v1_positions(card) == current_positions(card) == []


def test_literal_dotted_nodes_retain_original_field_traversal(card):
    node = card.sections["features_positional"].pop("active_site")
    card.sections[FIELD] = node
    assert _v1_positions(card) == current_positions(card) == [2, 3]


@pytest.mark.parametrize("state", ["absent", "empty", "unasserted"])
def test_no_selected_positions_does_not_claim_no_sites_or_coordinate_coverage(
    card, state
):
    if state == "absent":
        del card.sections["features_positional"]["active_site"]
    elif state == "empty":
        card.get(FIELD)["value"] = []
    else:
        card.get(FIELD)["source_assertion_ids"] = []
    before = card.to_dict()
    assert _v1_positions(card) == current_positions(card) == []
    assert card.to_dict() == before


@pytest.mark.parametrize("missing", ["sequence", "identity", "nature"])
def test_invalid_original_canonical_prerequisite_is_not_an_empty_selection(
    card, missing
):
    if missing == "nature":
        card.meta["entity_type"] = "small_molecule"
    else:
        card.get(
            "sequence.primary" if missing == "sequence" else "identifiers.uniprot"
        )["value"] = None
    with pytest.raises(SchemaError):
        _v1_positions(card)


def test_frozen_selection_does_not_use_current_readers_or_value_helpers(
    card, monkeypatch
):
    import sabueso.core.residues as current
    import sabueso.core.source_assertion_store as assertions

    def forbidden(*a, **k):
        raise AssertionError("No current residue/support/value interpretation")

    for name in (
        "residues_view",
        "residue_view",
        "_prepare",
        "field_nodes",
        "item_support",
        "canonical_sequence",
    ):
        monkeypatch.setattr(current, name, forbidden)
    monkeypatch.setattr(assertions, "assertion_value", forbidden)
    monkeypatch.setattr(Card, "get_residues", forbidden)
    assert _v1_positions(card) == [2, 3]
