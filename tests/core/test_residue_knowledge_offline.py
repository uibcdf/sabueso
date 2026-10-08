"""Recovered residue views retain exact sequence scope and actual item support."""

import copy

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, SchemaError
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.resolver import EntityResolver, FixtureUniProtClient


def protein():
    site = {
        "location": {
            "kind": "sequence",
            "sequence": {
                "sequence_id": "UniProt:P60174",
                "start": 2,
                "end": 2,
                "indexing": "1-based",
            },
        },
        "description": "Source-stated active residue",
    }
    other = copy.deepcopy(site)
    other["description"] = "Another item"
    assertions = [
        make_source_assertion(path, value, "UniProt", "P60174", "2026-01-01")
        for path, value in [
            ("sequence.primary", "MST"),
            ("features_positional.active_site", site),
            ("features_positional.active_site", other),
        ]
    ]
    return Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:P60174"},
        sections={
            "identifiers": {"uniprot": {"value": "P60174", "source_assertion_ids": []}},
            "sequence": {
                "primary": {
                    "value": "MST",
                    "source_assertion_ids": [assertions[0]["id"]],
                }
            },
            "features_positional": {
                "active_site": {
                    "value": [site],
                    "source_assertion_ids": [a["id"] for a in assertions[1:]],
                }
            },
        },
        source_assertion_store=assertions,
    )


def test_exact_item_support_and_detached_output():
    card = protein()
    before = card.to_dict()
    view = card.get_residue(2)
    assert view["rule"] == "residue_annotations@1" and view["amino_acid"] == "S"
    (item,) = view["annotations"]
    (identifier,) = item["source_assertion_ids"]
    assert (
        card.source_assertion_store.get(identifier)["asserted_value"]
        == item["annotation"]
    )
    assert item["support_status"] == "complete"
    item["annotation"]["description"] = "changed output"
    assert card.to_dict() == before


def test_equal_item_from_another_subject_is_not_support():
    card = protein()
    node = card.get("features_positional.active_site")
    wrong = make_source_assertion(
        "features_positional.active_site",
        node["value"][0],
        "UniProt",
        "P99999",
        "fixture",
    )
    card.source_assertion_store.add(wrong)
    node["source_assertion_ids"] = [wrong["id"]]
    item = card.get_residue(2)["annotations"][0]
    assert item["source_assertion_ids"] == []
    assert item["incompatible_source_assertion_ids"] == [wrong["id"]]
    assert item["support_status"] == "incomplete"


def test_unknown_sequence_and_numbering_are_not_placed():
    card = protein()
    original = card.get("features_positional.active_site")["value"][0]
    alternatives = []
    for changes in (
        {"sequence_id": "UniProt:another"},
        {"sequence_id": None},
        {"indexing": "0-based"},
    ):
        item = copy.deepcopy(original)
        item["location"]["sequence"].update(changes)
        alternatives.append(item)
    card.get("features_positional.active_site")["value"] = alternatives
    view = card.get_residue(2)
    assert view["annotations"] == [] and len(view["unmapped"]) == 2


def test_disulfide_bond_has_endpoints_rather_than_an_interval():
    card = protein()
    site = copy.deepcopy(card.get("features_positional.active_site")["value"][0])
    site["location"]["sequence"].update(start=1, end=3)
    card.set("features_positional.disulfide_bond", [site], [])
    assert any(
        r["field_path"].endswith("disulfide_bond")
        for r in card.get_residue(1)["annotations"]
    )
    assert not any(
        r["field_path"].endswith("disulfide_bond")
        for r in card.get_residue(2)["annotations"]
    )


def test_missing_support_is_explicit_and_mutation_is_read():
    card = protein()
    card.get("features_positional.active_site")["source_assertion_ids"] = ["missing"]
    item = card.get_residue(2)["annotations"][0]
    assert item["support_status"] == "incomplete" and item[
        "missing_source_assertion_ids"
    ] == ["missing"]
    card.get("features_positional.active_site")["value"] = []
    assert card.get_residue(2)["annotations"] == []


@pytest.mark.parametrize("position", [0, -1, True, 1.5, "2"])
def test_positions_are_positive_integers(position):
    with pytest.raises(ArgumentError):
        protein().get_residue(position)


def test_missing_sequence_isoform_and_out_of_range_are_refused():
    card = protein()
    with pytest.raises(ArgumentError):
        card.get_residue(1, sequence="P60174-2")
    with pytest.raises(IndexError):
        card.get_residue(4)
    card.sections["sequence"] = {}
    with pytest.raises(SchemaError):
        card.get_residue(1)


def test_fixture_and_saved_reader_have_identical_views(monkeypatch):
    card, _ = sabueso.resolve(
        "P60174", resolver=EntityResolver(FixtureUniProtClient("temp_data"))
    )
    saved = Card.from_dict(card.to_dict())
    monkeypatch.setattr(
        sabueso, "resolve", lambda *a, **k: pytest.fail("Reader acquired knowledge")
    )
    views = saved.get_residues()
    assert len(views) == card.get("sequence.length")["value"]
    assert all(view["card_ref"] == card.pinned_ref() for view in views)
    assert views[163] == card.get_residue(164)
