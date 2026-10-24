"""Distinct executions and original output context survive relationship merging."""

import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import StorageError
from sabueso.core.relationship_store import (
    RelationshipStore,
    make_derivation,
    make_relationship,
)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No source acquisition")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


def occurrence(inputs, *, value="A", rule="synthetic@1", parameters=None):
    return make_relationship(
        "uniprot:SYNTHETIC",
        "has_structure",
        "pdb:SYNTHETIC",
        qualifiers={
            "chains": [value],
            "resolution": {"value": 2.0, "unit": "angstrom"},
        },
        source_assertion_ids=inputs,
        derivation=make_derivation(rule, inputs, parameters or {"scope": ["chains"]}),
    )


@pytest.mark.parametrize(
    "change", ["inputs", "overlap", "parameters", "rule", "version", "output"]
)
def test_distinct_applications_keep_their_exact_inputs_and_outputs(change):
    first = occurrence(["SA_A", "SA_SHARED"])
    incoming = occurrence(["SA_A", "SA_SHARED"])
    if change == "inputs":
        incoming = occurrence(["SA_B"])
    elif change == "overlap":
        incoming = occurrence(["SA_SHARED", "SA_B"])
    elif change == "parameters":
        incoming = occurrence(
            ["SA_A", "SA_SHARED"], parameters={"scope": ["resolution"]}
        )
    elif change == "rule":
        incoming = occurrence(["SA_A", "SA_SHARED"], rule="synthetic@2")
    elif change == "version":
        incoming["derivation"]["sabueso_version"] = "synthetic-other-sdk"
        incoming["derivation_applications"][0]["derivation"] = deepcopy(
            incoming["derivation"]
        )
    else:
        incoming = occurrence(["SA_A", "SA_SHARED"], value="B")
    original = deepcopy([first, incoming])
    store = RelationshipStore([first, incoming, incoming, first])
    merged = store.get(first["id"])
    assert merged["derivation"] == first["derivation"]
    applications = merged["derivation_applications"]
    assert len(applications) == 2
    for row in original:
        assert row["derivation_applications"][0] in applications
    assert [first, incoming] == original
    assert set(merged["source_assertion_ids"]) == set(
        first["source_assertion_ids"] + incoming["source_assertion_ids"]
    )
    # Serializing/loading a merged relationship does not add an application.
    assert (
        RelationshipStore(json.loads(json.dumps(store.to_list()))).to_list()
        == store.to_list()
    )
    reverse = RelationshipStore([incoming, first]).get(first["id"])
    assert reverse["derivation_applications"] == applications


def test_new_application_is_detached_and_exact_duplicate_is_idempotent():
    parameters = {"scope": ["chains"]}
    derivation = make_derivation("synthetic@1", ["SA_A"], parameters)
    qualifiers = {"chains": ["A"]}
    row = make_relationship(
        "uniprot:S",
        "has_structure",
        "pdb:S",
        qualifiers=qualifiers,
        derivation=derivation,
    )
    original = deepcopy(row)
    parameters["scope"].append("changed")
    derivation["inputs"].append("SA_CHANGED")
    qualifiers["chains"].append("changed")
    assert row == original
    store = RelationshipStore([row, row])
    assert store.get(row["id"]) == original
    row["derivation_applications"][0]["qualifiers"]["chains"].append("changed")
    assert store.get(row["id"]) == original


def test_legacy_loading_preserves_bytes_and_merge_does_not_invent_old_output():
    old = occurrence(["SA_OLD"])
    del old["derivation_applications"]
    old["qualifier_conflicts"] = {"chains": [["A"], ["B"]]}
    original = deepcopy(old)
    store = RelationshipStore([old])
    assert store.to_list() == [original]
    incoming = occurrence(["SA_NEW"], value="C")
    store.add(incoming)
    merged = store.get(old["id"])
    (legacy,) = [
        a
        for a in merged["derivation_applications"]
        if a["binding"] == "recorded_context"
    ]
    assert legacy["derivation"] == original["derivation"]
    assert legacy["qualifier_conflicts"] == original["qualifier_conflicts"]
    assert legacy["qualifiers"] == original["qualifiers"]
    assert incoming["derivation_applications"][0] in merged["derivation_applications"]
    assert merged["qualifier_conflicts"]["chains"] == [["A"], ["B"], ["C"]]
    assert old == original


def test_premerged_conflicts_and_inputs_survive_further_merges_without_aliases():
    first, second, third = [occurrence([f"SA_{c}"], value=c) for c in "ABC"]
    incoming = RelationshipStore([second, third]).to_list()[0]
    expected = deepcopy(incoming)
    store = RelationshipStore([first, incoming, incoming])
    row = store.get(first["id"])
    assert row["qualifier_conflicts"]["chains"] == [["A"], ["B"], ["C"]]
    assert len(row["derivation_applications"]) == 3
    incoming["qualifier_conflicts"]["chains"][1].append("changed")
    assert row["qualifier_conflicts"]["chains"] == [["A"], ["B"], ["C"]]
    assert expected["qualifier_conflicts"]["chains"] == [["B"], ["C"]]


@pytest.mark.parametrize("derived_first", [True, False])
def test_asserted_support_does_not_become_a_derivation_application(derived_first):
    derived = occurrence(["SA_DERIVED"])
    asserted = occurrence(["SA_ASSERTED"], value="B")
    del asserted["derivation"]
    del asserted["derivation_applications"]
    records = [derived, asserted] if derived_first else [asserted, derived]
    row = RelationshipStore(records).to_list()[0]
    assert row["derivation_applications"] == derived["derivation_applications"]
    assert set(row["source_assertion_ids"]) == {"SA_ASSERTED", "SA_DERIVED"}


def test_legacy_equal_parameters_do_not_union_independent_input_sets():
    first, second = occurrence(["SA_A"]), occurrence(["SA_B"])
    del first["derivation_applications"], second["derivation_applications"]
    merged = RelationshipStore([first, second]).to_list()[0]
    assert merged["derivation"]["inputs"] == ["SA_A"]
    assert {
        tuple(a["derivation"]["inputs"]) for a in merged["derivation_applications"]
    } == {("SA_A",), ("SA_B",)}
    assert all(
        a["binding"] == "recorded_context" for a in merged["derivation_applications"]
    )


def test_application_deduplication_preserves_json_types_and_input_order():
    rows = [
        occurrence(inputs, parameters={"flag": flag})
        for inputs, flag in [
            (["SA_A", "SA_B"], 1),
            (["SA_A", "SA_B"], True),
            (["SA_B", "SA_A"], 1),
        ]
    ]
    merged = RelationshipStore(rows + rows).to_list()[0]
    assert len(merged["derivation_applications"]) == 3


def test_legacy_card_loading_and_migration_do_not_reconstruct_applications():
    card, _, _ = public_card()
    for relationship in card.relationships():
        relationship.pop("derivation_applications", None)
    card.meta["schema_version"] = "0.3.13"
    original = card.to_dict()
    assert Card.from_dict(original).to_dict() == original
    migrated = sabueso.migrate_card(original).to_dict()
    assert migrated["relationship_store"] == original["relationship_store"]
    assert all(
        "derivation_applications" not in r for r in migrated["relationship_store"]
    )
    assert card.to_dict() == original


def test_expansion_basis_retains_detached_application_context():
    from sabueso.tools.navigate import _statement

    card, rel, _ = public_card()
    expected = deepcopy(rel["derivation_applications"])
    statement = _statement(card, rel)
    assert statement["derivation_applications"] == expected
    statement["derivation_applications"][0]["derivation"]["inputs"].append("SA_CHANGED")
    assert rel["derivation_applications"] == expected


def public_card():
    """Public frozen input; the two derived occurrences below are synthetic."""
    card = Card.from_dict(
        json.loads(Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text())
    )
    rel = next(
        r for r in card.relationships("has_structure") if r["object_ref"] == "pdb:1SUX"
    )
    first, second = list(card.source_assertion_store.store)[:2]
    original = deepcopy(rel)
    del card.relationship_store.store[rel["id"]]
    for source, distance in [(first, 1.0), (second, 3.0)]:
        qualifiers = deepcopy(original["qualifiers"])
        qualifiers["resolution"] = {"value": distance, "unit": "angstrom"}
        card.relationship_store.add(
            make_relationship(
                rel["subject_ref"],
                rel["predicate"],
                rel["object_ref"],
                qualifiers=qualifiers,
                derivation=make_derivation(
                    "synthetic_contact_context@1",
                    [source],
                    {"qualifier_paths": ["resolution"]},
                ),
            )
        )
    return card, card.relationship_store.get(rel["id"]), [first, second]


@pytest.mark.parametrize("which", [0, 1, "merged_alternative"])
def test_each_application_quantity_is_sealed_and_roundtrips(which):
    card, rel, _ = public_card()
    data = card.to_dict()
    assert Card.from_dict(data).to_dict() == data
    stored = next(r for r in data["relationship_store"] if r["id"] == rel["id"])
    if which == "merged_alternative":
        stored["qualifier_conflicts"]["resolution"][1]["value"] += 0.1
    else:
        stored["derivation_applications"][which]["qualifiers"]["resolution"][
            "value"
        ] += 0.1
    with pytest.raises(StorageError, match="quantit"):
        Card.from_dict(data)


@pytest.mark.parametrize("detail", ["full", "index"])
def test_packets_keep_all_application_inputs_in_terms_requirements(tmp_path, detail):
    card, rel, sources = public_card()
    store = sabueso.KnowledgeStore(tmp_path / "cards.db")
    store.save(card)
    packet = sabueso.compose_packet(
        sabueso.KnowledgeQuery("P52270", aspects=["structures"], detail=detail), card
    )
    terms = packet.terms("commercial_product", store=store)
    items = terms["scope"]["subject"]["items"]
    assert all(any(item["id"] == source for item in items) for source in sources)
    item = next(item for item in items if item["id"] == rel["id"])
    assert len(item["requirements"]) == 2


def test_original_saved_inspection_keeps_applications_without_live_reconstruction(
    tmp_path,
):
    card, rel, _ = public_card()
    view = (
        card.explore()
        .view("ligand_instances")
        .filter("structure_ref", equals="pdb:1SUX")
    )
    support = view.items()[0].support[0]
    assert support["derivation_applications"] == rel["derivation_applications"]
    saved = tmp_path / "applications.json"
    view.save(saved)
    script = """
import socket, sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a, **k): raise AssertionError('No live reconstruction')
socket.socket.connect = forbidden
Card.from_dict = forbidden
Card.explore = forbidden
view = sabueso.read_exploration(sys.argv[1])
apps = view.items()[0].support[0]['derivation_applications']
assert len(apps) == 2
assert {a['qualifiers']['resolution']['value'] for a in apps} == {1.0, 3.0}
assert all(a['binding'] == 'original_output' for a in apps)
print('PASS original applications')
"""
    with TemporaryDirectory(prefix="sabueso-application-reader-") as cwd:
        read = subprocess.run(
            [sys.executable, "-c", script, str(saved.resolve())],
            cwd=cwd,
            text=True,
            capture_output=True,
        )
    assert read.returncode == 0, read.stdout + read.stderr
    assert "PASS original applications" in read.stdout
