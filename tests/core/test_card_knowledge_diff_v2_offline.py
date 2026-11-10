"""Explicit knowledge comparison: types, occurrences and supplied coordinates."""

import json
import socket
from pathlib import Path

import pytest

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.core.relationship_store import make_relationship
from sabueso.core.snapshot import canonical_json
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.uniprot import map_protein

RULE = "card_knowledge_diff@2"
PATH = "features_positional.active_site"
DATA = Path(__file__).resolve().parents[2] / "temp_data"
if not (DATA / "P52270.json").exists():
    DATA = Path.cwd() / "temp_data"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Knowledge comparison must not acquire source data")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    from sabueso.tools.db import _http

    monkeypatch.setattr(_http, "_urlopen", forbidden)


def card(name="LEFT", sequence="MAGR"):
    value = Card(
        meta={"card_id": "sabueso:protein:uniprot:" + name, "entity_type": "protein"}
    )
    if sequence is not None:
        stated(value, "sequence.primary", sequence)
    return value


def stated(value, path, original):
    record = make_source_assertion(
        path,
        original,
        "synthetic",
        value.id + path,
        "original time",
        subject_ref=value.id.split(":", 2)[2],
    )
    value.source_assertion_store.add(record)
    value.set(path, original, [record["id"]])
    return record


def annotation(owner="LEFT", position=1, description="stated site", **extra):
    return {
        "location": {
            "sequence": {
                "sequence_id": "UniProt:" + owner,
                "start": position,
                "end": position,
            }
        },
        "description": description,
        **extra,
    }


def ask(left, right, mapping=None, **kwargs):
    return left.compare_knowledge(
        right, residue_map=mapping, comparison_rule=RULE, **kwargs
    )


@pytest.mark.parametrize(
    "a,b",
    [
        (0, False),
        (1, True),
        (1, 1.0),
        ({"x": [0]}, {"x": [False]}),
        ([0], [False]),
        ([1], [1.0]),
        (None, False),
        ("0", 0),
    ],
)
def test_original_typed_values_are_distinct(a, b):
    left, right = card(), card("RIGHT")
    stated(left, "annotations.taxon_id", a)
    stated(right, "annotations.taxon_id", b)
    row = ask(left, right)["fields"]["annotations.taxon_id"]
    assert row["status"] == "differs"
    assert canonical_json(row["self"]) == canonical_json(a)
    assert canonical_json(row["other"]) == canonical_json(b)
    assert row["support"]["self"]["state"] == "retained_references"


@pytest.mark.parametrize("a,b", [(0, False), (1, 1.0), ({"x": [0]}, {"x": [False]})])
def test_published_default_equality_stays_explicitly_available(a, b):
    left, right = card(), card("RIGHT")
    stated(left, "annotations.taxon_id", a)
    stated(right, "annotations.taxon_id", b)
    default = left.compare_knowledge(right)
    explicit = left.compare_knowledge(right, comparison_rule="card_knowledge_diff@1")
    assert default == explicit
    assert default["fields"]["annotations.taxon_id"] == {"status": "same"}
    assert default["rule"]["rule"] == "card_knowledge_diff@1"
    assert ask(left, right)["fields"]["annotations.taxon_id"]["status"] == "differs"


@pytest.mark.parametrize("reverse", [False, True])
def test_all_identity_candidates_are_retained_without_first_choice(reverse):
    left, right = card(), card("RIGHT")
    original = annotation()
    candidates = [
        annotation("RIGHT"),
        annotation("RIGHT", description="another source statement"),
    ]
    if reverse:
        candidates.reverse()
    stated(left, PATH, [original])
    stated(right, PATH, candidates)
    row = ask(left, right, {1: 1})["fields"][PATH]
    assert row["status"] == "partial" and not row["both"] and not row["differ"]
    (group,) = row["ambiguous"]
    assert group["self"] == [{"index": 0, "item": original}]
    assert [v["item"] for v in group["other"]] == candidates
    assert [v["index"] for v in group["other"]] == [0, 1]


def test_repeated_source_occurrences_are_not_merged():
    left, right = card(), card("RIGHT")
    stated(left, PATH, [annotation(), annotation()])
    stated(right, PATH, [annotation("RIGHT")])
    row = ask(left, right, {1: 1})["fields"][PATH]
    assert row["status"] == "partial"
    assert len(row["ambiguous"][0]["self"]) == 2


def test_complete_map_binds_exact_pairs_and_keeps_original_coordinates():
    left, right = card(sequence="MA"), card("RIGHT", "AMA")
    original, counterpart = annotation(position=1), annotation("RIGHT", 2)
    stated(left, PATH, [original])
    stated(right, PATH, [counterpart])
    result = ask(left, right, {2: 3, 1: 2})
    row = result["fields"][PATH]
    assert row["status"] == "same" and len(row["both"]) == 1
    assert row["self"] == [original] and row["other"] == [counterpart]
    assert result["residue_map"]["pairs"] == [[1, 2], [2, 3]]
    assert result["rule"]["parameters"]["residue_map"] == [[1, 2], [2, 3]]
    assert result["inputs"] == {"self": left.pinned_ref(), "other": right.pinned_ref()}
    assert not result["residue_map"]["alignment_performed"]
    assert not result["residue_map"]["scientific_correspondence_validated"]


def test_equal_positions_without_map_never_establish_correspondence():
    left, right = card(), card("RIGHT")
    stated(left, PATH, [annotation()])
    stated(right, PATH, [annotation("RIGHT")])
    row = ask(left, right)["fields"][PATH]
    assert row["status"] == "not_compared" and row["reason"] == "no residue mapping"


def test_partial_map_keeps_unmapped_annotations_and_unresolved_counterparts():
    left, right = card(), card("RIGHT")
    stated(left, PATH, [annotation(position=1), annotation(position=2)])
    stated(right, PATH, [annotation("RIGHT", 1), annotation("RIGHT", 2)])
    row = ask(left, right, {1: 1})["fields"][PATH]
    assert row["status"] == "partial" and len(row["both"]) == 1
    assert row["not_comparable_self"][0]["item"]["location"]["sequence"]["start"] == 2
    assert len(row["not_comparable_other"]) == 1
    assert not row["only_self"] and not row["only_other"]


@pytest.mark.parametrize(
    "defect",
    [
        "foreign",
        "missing-axis",
        "boolean-position",
        "missing-position",
        "reversed-span",
        "huge-span",
        "uncertain-boundary",
        "wrong-indexing",
    ],
)
def test_foreign_unplaced_and_large_scopes_stay_explicit(defect):
    left, right = card(), card("RIGHT")
    item = annotation()
    location = item["location"]["sequence"]
    if defect == "foreign":
        location["sequence_id"] = "UniProt:FOREIGN"
    elif defect == "missing-axis":
        location.pop("sequence_id")
    elif defect == "boolean-position":
        location["start"] = True
    elif defect == "missing-position":
        location["start"] = None
    elif defect == "reversed-span":
        location.update(start=2, end=1)
    elif defect == "huge-span":
        location["end"] = 10**9
    elif defect == "uncertain-boundary":
        location["start_modifier"] = "LESS_THAN"
    else:
        location["indexing"] = "0-based"
    stated(left, PATH, [item])
    stated(right, PATH, [annotation("RIGHT")])
    row = ask(left, right, {1: 1})["fields"][PATH]
    assert row["status"] == "partial"
    assert row["not_comparable_self"][0]["item"] == item
    assert not row["only_other"] and len(row["unresolved_other"]) == 1


def test_nonsequence_location_metadata_is_never_overwritten_by_mapping():
    left, right = card(), card("RIGHT")
    a, b = annotation(), annotation("RIGHT")
    a["location"]["structure"] = {"id": "pdb:ONE", "chain": "A"}
    b["location"]["structure"] = {"id": "pdb:TWO", "chain": "B"}
    stated(left, PATH, [a])
    stated(right, PATH, [b])
    row = ask(left, right, {1: 1})["fields"][PATH]
    assert row["status"] == "differs" and len(row["differ"]) == 1
    assert row["self"][0]["location"]["structure"]["id"] == "pdb:ONE"


@pytest.mark.parametrize(
    "mapping",
    [
        {0: 1},
        {True: 1},
        {1: True},
        {1: 1.0},
        {1: 0},
        {1: -2},
        {1: 1, 2: 1},
        {"1": 1},
        {5: 1},
        {1: 5},
        {1: []},
        [],
        "alignment",
    ],
)
def test_rule_rejects_invalid_or_nonbijective_maps_even_without_digestion(mapping):
    left, right = card(), card("RIGHT")
    with pytest.raises(ArgumentError):
        ask(left, right, mapping, skip_digestion=True)


@pytest.mark.parametrize("invalid", [None, False, 2, "card_knowledge_diff@3", [], {}])
def test_unknown_rules_are_not_coerced(invalid):
    left, right = card(), card("RIGHT")
    with pytest.raises(ArgumentError):
        left.compare_knowledge(right, comparison_rule=invalid)
    with pytest.raises(ArgumentError):
        left.compare_knowledge(right, comparison_rule=invalid, skip_digestion=True)


def test_free_text_is_retained_and_never_classified_by_meaning():
    left, right = card(), card("RIGHT")
    stated(left, "annotations.function", ["uninterpreted source text"])
    stated(right, "annotations.function", ["a different description"])
    row = ask(left, right)["fields"]["annotations.function"]
    assert row["status"] == "not_compared" and row["reason"] == "free text"
    assert row["self"] == ["uninterpreted source text"]


def test_quantities_remain_original_stored_values_with_units():
    left, right = card(), card("RIGHT")
    for owner, mass in ((left, 3.5), (right, 4.5)):
        stated(owner, "sequence.molecular_weight", mass)
    row = ask(left, right)["fields"]["sequence.molecular_weight"]
    assert row["status"] == "differs"
    assert row["self"] == {"value": 3.5, "unit": "dalton"}
    assert row["other"] == {"value": 4.5, "unit": "dalton"}
    assert (
        row["support"]["self"]["selected_source_assertions"][0]["asserted_value"]
        == row["self"]["value"]
    )


def test_missing_and_misbound_sources_remain_explicit():
    left, right = card(), card("RIGHT")
    source = stated(left, "annotations.taxon_id", 0)
    source["asserted_value"] = False
    left.source_assertion_store.store[source["id"]] = source
    stated(right, "annotations.taxon_id", False)
    left.get("annotations.taxon_id")["source_assertion_ids"].append("SA_missing")
    row = ask(left, right)["fields"]["annotations.taxon_id"]
    support = row["support"]["self"]
    assert support["state"] == "partial" and support[
        "missing_source_assertion_ids"
    ] == ["SA_missing"]
    assert support["bindings"][0]["state"] == "binding_mismatch"


def test_every_field_alternative_and_conflict_is_retained():
    left, right = card(), card("RIGHT")
    selected = stated(left, "annotations.taxon_id", 0)
    alternative = make_source_assertion(
        "annotations.taxon_id",
        False,
        "alternative",
        "native",
        "time",
        subject_ref="uniprot:LEFT",
    )
    left.source_assertion_store.add(alternative)
    left.quality["conflicts"] = [
        {"field": "annotations.taxon_id", "reason": "literal source disagreement"}
    ]
    stated(right, "annotations.taxon_id", 0)
    support = ask(left, right)["fields"]["annotations.taxon_id"]["support"]["self"]
    assert support["selected_source_assertions"] == [selected]
    assert support["other_field_assertions"] == [alternative]
    assert support["quality_conflicts"] == left.quality["conflicts"]


def test_duplicate_knowledge_state_rows_are_not_silently_overwritten(monkeypatch):
    left, right = card(), card("RIGHT")
    known = {"area": "annotations.function", "source": "synthetic", "state": "known"}
    failed = {**known, "state": "unavailable"}
    monkeypatch.setattr(left, "knowledge_state", lambda: {"rows": [known, failed]})
    monkeypatch.setattr(right, "knowledge_state", lambda: {"rows": [failed]})
    (row,) = ask(left, right)["knowledge_states"]
    assert row["self"] == [known, failed] and row["other"] == [failed]


def test_relationships_keep_full_direction_channels_and_source_references():
    left, right = card(), card("RIGHT")
    source = stated(
        left, "annotations.relationship_context", {"literal": "source record"}
    )
    for target in ("uniprot:TARGET1", "uniprot:TARGET2"):
        left.relationship_store.add(
            make_relationship(
                "uniprot:LEFT",
                "interacts_with",
                target,
                {"channel": "physical", "original": False},
                [source["id"]],
            )
        )
    result = ask(left, right)
    rows = result["relationships"]["interacts_with"]["self_records"]
    assert len(rows) == 2 and all(r["qualifiers"]["original"] is False for r in rows)
    assert result["relationship_sources"]["self"]["assertions"] == {
        source["id"]: source
    }


def test_reader_is_detached_and_does_not_construct_cards_or_assertions(monkeypatch):
    left, right = card(), card("RIGHT")
    stated(left, PATH, [annotation()])
    stated(right, PATH, [annotation("RIGHT")])
    before = [c.to_dict() for c in (left, right)]

    def forbidden(*args, **kwargs):
        raise AssertionError("Comparison must read the existing captured inputs")

    monkeypatch.setattr(Card, "__init__", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(
        "sabueso.core.source_assertion_store.make_source_assertion", forbidden
    )
    result = ask(left, right, {1: 1})
    result["fields"][PATH]["self"][0]["description"] = "caller mutation"
    assert [c.to_dict() for c in (left, right)] == before


@pytest.fixture(scope="module")
def public_cards():
    return [
        build_card_from_mapping(
            map_protein(
                json.loads((DATA / (a + ".json")).read_text()), "frozen public response"
            ),
            meta={"entity_type": "protein"},
            card_id="sabueso:protein:uniprot:" + a,
        )
        for a in ("P52270", "P60174")
    ]


def test_public_tim_comparison_uses_only_the_supplied_correspondence(public_cards):
    left, right = public_cards
    before = [c.to_dict() for c in public_cards]
    unmapped = ask(left, right)["fields"][PATH]
    assert unmapped["status"] == "not_compared"
    mapped = ask(left, right, {12: 12, 14: 14, 96: 96, 168: 166})
    row = mapped["fields"][PATH]
    assert row["status"] in ("same", "differs")
    assert len(row["both"]) + len(row["differ"]) == 2
    assert mapped["fields"]["annotations.function"]["status"] == "only_other"
    assert [c.to_dict() for c in public_cards] == before
