"""Independent interval cases and public original-policy compatibility (#184/#185)."""

import socket
from copy import deepcopy

import pytest
import pyunitwizard as puw

from sabueso.core.bioactivity_class_v4 import RULE, classify
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No acquisition during scientific interpretation")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.mark.parametrize(
    "value,relation,expected",
    [
        (1, "=", "active"), (10, "=", "active"),
        (11, "=", "weak"), (100, "=", "weak"), (101, "=", "inactive"),
        (10, "<", "active"), (10, "<=", "active"),
        (11, "<", "inconclusive"), (100, "<=", "inconclusive"),
        (101, "<", "inconclusive"),
        (10, ">", "inconclusive"), (99, ">", "inconclusive"),
        (100, ">", "inactive"), (100, ">=", "inconclusive"),
        (101, ">=", "inactive"), (1, "~", "inconclusive"),
        (1, "!=", "inconclusive"),
    ],
)  # fmt: skip
def test_all_permitted_values_must_fit_one_band(value, relation, expected):
    answer = classify(
        {"type": "IC50", "value": value, "units": "uM", "relation": relation}
    )
    assert answer["class"] == expected
    assert answer["interpretation"]


@pytest.mark.parametrize(
    "low,high,expected",
    [(1, 10, "active"), (11, 100, "weak"), (101, 200, "inactive"),
     (10, 11, "inconclusive"), (100, 101, "inconclusive"),
     (100, 100, "weak"), (11, 10, "inconclusive")],
)  # fmt: skip
def test_closed_ranges_keep_their_boundaries(low, high, expected):
    answer = classify(
        {
            "type": "IC50",
            "value": low,
            "upper_value": high,
            "units": "uM",
            "relation": "=",
        }
    )
    assert answer["class"] == expected


@pytest.mark.parametrize("value", [True, -1, 0, float("nan"), float("inf"), "invalid"])
def test_invalid_potency_never_becomes_a_band(value):
    assert (
        classify({"type": "IC50", "value": value, "units": "uM"})["class"]
        == "inconclusive"
    )


@pytest.mark.parametrize("relation", ["=", ">", ">=", "<", "<=", "~"])
@pytest.mark.parametrize("value", [40, 70])
def test_single_point_is_not_a_dose_response_curve(value, relation):
    answer = classify(
        {"type": "Inhibition", "value": value, "units": "%", "relation": relation},
        "Assay at 1 uM substrate; inhibition measured at 100 uM compound",
    )
    assert answer["class"] == "inconclusive"
    assert answer["test_concentration_state"] == "not_interpreted"
    assert "test_concentration" not in answer
    assert "tested-compound dose" in answer["interpretation"]


@pytest.mark.parametrize("units,value", [("nM", 100000), ("uM", 100), ("mM", 0.1)])
def test_equivalent_units_preserve_the_inclusive_lower_bound(units, value):
    assert (
        classify({"type": "Ki", "value": value, "units": units, "relation": ">="})[
            "class"
        ]
        == "inconclusive"
    )


@pytest.mark.parametrize("field", ["uncertainty", "normalized_uncertainty"])
def test_uninterpreted_uncertainty_does_not_become_an_exact_point(field):
    answer = classify(
        {"type": "Kd", "value": 5, "units": "uM", field: {"kind": "unspecified"}}
    )
    assert answer["class"] == "inconclusive"
    assert answer["basis"] == "uncertainty_not_interpreted"


def synthetic_card():
    card = Card(
        meta={"card_id": "sabueso:protein:uniprot:P52270", "entity_type": "protein"}
    )
    qualifiers = {
        "source": "Synthetic",
        "activity_id": "synthetic-inhibition",
        "measurement": {
            "type": "Inhibition",
            "value": 40,
            "units": "%",
            "relation": ">",
        },
        "assay": {
            "id": "synthetic:assay",
            "relationship_type": "D",
            "description": "Inhibition at 200 uM",
        },
        "document": {},
    }
    assertion = make_source_assertion(
        "relationships.has_bioactivity",
        deepcopy(qualifiers),
        "Synthetic",
        "synthetic-inhibition",
        "2026-11-04",
    )
    card.source_assertion_store.add(assertion)
    card.relationship_store.add(
        make_relationship(
            "uniprot:P52270",
            "has_bioactivity",
            "chembl:CHEMBL_SYNTHETIC",
            qualifiers,
            [assertion["id"]],
        )
    )
    return card


def test_public_opt_in_explains_the_change_and_preserves_original_policy_and_card():
    card = synthetic_card()
    before = card.to_dict()
    old = card.bioactivities()
    current = card.bioactivities(classification_rule=RULE)
    old_item, new_item = old["items"][0], current["items"][0]
    assert old_item["class"] == "inactive"
    assert new_item["class"] == "inconclusive"
    original, new = old_item["measurements"][0], new_item["measurements"][0]
    for field in [
        "relationship_id",
        "activity_id",
        "relation",
        "value",
        "units",
        "source",
        "group",
    ]:
        assert new[field] == original[field]
    assert puw.get_value(new["normalized"], to_unit="percent") == 40
    assert current["classification"]["rule"] == RULE
    assert "single_point_policy" in current["classification"]["parameters"]
    assert current["classification"]["parameters"]["unused_thresholds"] == [
        "single_point_min"
    ]
    explanation = card.explain_bioactivity(
        new_item["molecule_ref"], classification_rule=RULE
    )
    assert explanation["item"] == new_item
    assert explanation["classification"] == current["classification"]
    assert explanation["rule"]["rule"] == "bioactivity_explanation@2"
    assert explanation["rule"]["parameters"]["classification_rule"] == RULE
    assert explanation["records"]
    assert (
        card.explain_bioactivity(old_item["molecule_ref"])["rule"]["rule"]
        == "bioactivity_explanation@1"
    )
    assert card.bioactivities(classification_rule="bioactivity_class@3") == old
    assert card.to_dict() == before


@pytest.mark.parametrize("rule", [None, 4, True, "@4", "bioactivity_class@5"])
@pytest.mark.parametrize("skip", [False, True])
def test_unknown_rule_is_refused_even_when_digestion_is_skipped(rule, skip):
    card = Card()
    with pytest.raises(ArgumentError):
        card.bioactivities(classification_rule=rule, skip_digestion=skip)
    with pytest.raises(ArgumentError):
        card.explain_bioactivity(
            "chembl:CHEMBL_SYNTHETIC", classification_rule=rule, skip_digestion=skip
        )


@pytest.mark.parametrize(
    "thresholds",
    [
        {"active_max": "200 uM"},
        {"weak_max": "0 uM"},
        {"active_max": "nan uM"},
        {"single_point_min": "101 percent"},
    ],
)
def test_invalid_thresholds_are_refused_even_on_an_empty_card(thresholds):
    with pytest.raises(ArgumentError):
        Card().bioactivities(classification_rule=RULE, thresholds=thresholds)
