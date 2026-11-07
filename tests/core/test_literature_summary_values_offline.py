"""Synthetic projection controls on a public accession, not provider claims."""

from copy import deepcopy

import pytest

from sabueso.core.card import Card
from sabueso.core.snapshot import canonical_json
from sabueso.core.source_assertion_store import make_source_assertion

PUBLICATION = "pubmed:8061610"


def source_card(value):
    assertion = make_source_assertion(
        "annotations.function",
        deepcopy(value),
        "UniProt",
        "P60174",
        "2026-11-07",
        subject_ref="uniprot:P60174",
    )
    assertion["source_metadata"] = {
        "eco": [{"source": "PubMed", "id": "8061610", "code": "ECO:0000269"}]
    }
    card = Card(
        meta={
            "entity_type": "protein",
            "card_id": "sabueso:protein:uniprot:P60174",
        },
        source_assertion_store=[assertion],
    )
    return card, assertion


def assert_original_projection(value, expected):
    card, assertion = source_card(value)
    before = canonical_json(card.to_dict())
    (publication,) = card.literature()["publications"]
    assert publication["publication_ref"] == PUBLICATION
    (supported,) = publication["supports"]
    assert supported["source_assertion_id"] == assertion["id"]
    assert type(supported["value"]) is type(expected)
    assert supported["value"] == expected
    explanation = card.explain_literature(PUBLICATION)
    assert explanation["status"] == "on_card"
    (original,) = explanation["source_assertions"]
    assert original["found"]
    assert canonical_json(original["asserted_value"]) == canonical_json(value)
    assert canonical_json(card.to_dict()) == before


@pytest.mark.parametrize("value", [False, 0, 0.0])
def test_eco_summary_keeps_false_and_numeric_zero_with_their_original_types(value):
    assert_original_projection({"value": value}, value)


@pytest.mark.parametrize(
    "value, expected",
    [
        (
            {"description": "First original description", "name": "Later name"},
            "First original description",
        ),
        (
            {"description": None, "name": "", "value": "Original value"},
            "Original value",
        ),
        ({"description": False, "name": "Later name"}, False),
        ({"description": 0, "name": "Later name"}, 0),
        ({"description": 0.0, "name": "Later name"}, 0.0),
        (
            {
                "description": None,
                "name": "",
                "reaction": [],
                "location": {},
                "value": None,
            },
            None,
        ),
        (
            {"description": "", "value": [], "object_ref": "Original fallback"},
            "Original fallback",
        ),
    ],
)
def test_summary_preserves_priority_and_existing_empty_fallback(value, expected):
    assert_original_projection(value, expected)
