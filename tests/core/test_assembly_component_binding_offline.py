"""Original native component keys; modified inputs are explicitly synthetic."""

import importlib
import socket
from copy import deepcopy

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

IDS = "rcsb_polymer_entity_instance_container_identifiers"
EIDS = "rcsb_polymer_entity_container_identifiers"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(
        socket.socket, "connect", lambda *a, **k: pytest.fail("No acquisition")
    )


@pytest.fixture(scope="module")
def originals():
    out = {}
    for pdb, acc in [("1SUX", "P52270"), ("2V5B", "P52270"), ("1HTI", "P60174")]:
        card, _ = sabueso.resolve(
            acc,
            resolver=EntityResolver(
                FixtureUniProtClient("temp_data"),
                rcsb_client=FixtureRCSBClient("temp_data/rcsb_assembly_generation"),
            ),
            structures=[pdb],
        )
        out[pdb] = card.to_dict()
    return out


@pytest.fixture
def card(originals):
    return Card.from_dict(deepcopy(originals["2V5B"]))


def assertion(card):
    return next(
        sa
        for sa in card.source_assertion_store.store.values()
        if sa.get("source", {}).get("name") == "RCSB PDB"
    )


def value(card):
    return assertion(card)["asserted_value"]


def entity(card):
    return value(card)["ligand_contact_inputs"]["polymer_entities"][0]


def instance(card):
    return entity(card)["polymer_entity_instances"][0]


def generator(card):
    return value(card)["assembly_generation_inputs"]["assemblies"][0][
        "pdbx_struct_assembly_gen"
    ][0]


def source(card, **kwargs):
    return card.assembly_generation(**kwargs)["sources"][0]


@pytest.mark.parametrize(
    "pdb,expected",
    [
        (
            "1SUX",
            {
                **{k: "resolved" for k in "AB"},
                **{k: "referenced" for k in "CDEFGHIJ"},
                **{k: "unresolved" for k in "KL"},
            },
        ),
        ("2V5B", {"A": "resolved", "B": "unresolved"}),
        ("1HTI", {"A": "resolved", "B": "resolved", "C": "referenced"}),
    ],
)
def test_original_controls_keep_polymer_neighbor_and_unknown_bases(
    originals, pdb, expected
):
    card = Card.from_dict(deepcopy(originals[pdb]))
    before = card.to_dict()
    result = card.assembly_generation(structure_ref=f"pdb:{pdb}")
    assert result["rule"] == "rcsb_assembly_generation@3"
    assert result["component_binding_rule"] == "native_entry_component_key@1"
    assert result["physical_membership"] == "not_computed"
    row = result["sources"][0]
    for parent in row["assemblies"]:
        item = parent["generators"][0]
        assert {
            r["asym_id"]: r["state"] for r in item["component_bindings"]
        } == expected
        assert item["component_scope"] == "partial"
        for reference in item["component_bindings"]:
            assert (
                card.access()
                .read(reference["input_location"])
                .page(max_bytes=8192)["page"]
            )
    for record in row["component_registry"]:
        for reference in record["references"]:
            assert (
                card.access()
                .read(reference["input_location"])
                .page(max_bytes=8192)["page"]
            )
            if "entity_input_location" in reference:
                assert (
                    card.access()
                    .read(reference["entity_input_location"])
                    .page(max_bytes=8192)["page"]
                )
            if "instance_input_location" in reference:
                assert (
                    card.access()
                    .read(reference["instance_input_location"])
                    .page(max_bytes=8192)["page"]
                )
    assert before == card.to_dict()


def test_author_labels_never_substitute_and_source_labels_are_exact(card):
    instance(card)[IDS]["asym_id"] = "X"
    instance(card)[IDS]["auth_asym_id"] = "A"
    generator(card)["asym_id_list"] = ["A", "X", "x", "01", "1"]
    rows = source(card)["assemblies"][0]["generators"][0]["component_bindings"]
    assert [r["state"] for r in rows] == [
        "unresolved",
        "resolved",
        "unresolved",
        "unresolved",
        "unresolved",
    ]


def test_duplicate_polymer_records_are_ambiguous_even_when_identical(card):
    entity(card)["polymer_entity_instances"].append(deepcopy(instance(card)))
    record = source(card)["component_registry"][0]
    assert record["binding_state"] == "ambiguous"
    assert record["reasons"] == ["duplicate_polymer_instance_records"]
    assert len(record["references"]) == 2


def test_repeated_neighbor_rows_keep_all_original_references(card):
    instance(card)["rcsb_ligand_neighbors"] = [
        {"ligand_asym_id": "B", "ligand_comp_id": "SYN"}
    ] * 2
    row = source(card)
    record = row["component_registry"][1]
    assert record["binding_state"] == "referenced" and not record["reasons"]
    assert record["basis"] == "native_ligand_neighbor_reference"
    assert len(record["references"]) == 2
    assert (
        record["references"][0]["input_path"] != record["references"][1]["input_path"]
    )


@pytest.mark.parametrize(
    "rows,reason",
    [
        (
            [{"ligand_asym_id": "A", "ligand_comp_id": "SYN"}],
            "conflicting_source_roles",
        ),
        (
            [
                {"ligand_asym_id": "B", "ligand_comp_id": "SYN"},
                {"ligand_asym_id": "B", "ligand_comp_id": "OTHER"},
            ],
            "conflicting_ligand_component_references",
        ),
        (
            [{"ligand_asym_id": "B", "ligand_comp_id": {}}],
            "unrecognized_descriptor_shape",
        ),
    ],
)
def test_inconsistent_role_and_component_references_never_select_a_winner(
    card, rows, reason
):
    instance(card)["rcsb_ligand_neighbors"] = rows
    record = next(
        r for r in source(card)["component_registry"] if reason in r["reasons"]
    )
    assert record["binding_state"] == "ambiguous"


def test_missing_neighbor_descriptor_is_not_completed(card):
    instance(card)["rcsb_ligand_neighbors"] = [
        {"ligand_asym_id": "B", "ligand_comp_id": "SYN"},
        {"ligand_asym_id": "B"},
    ]
    record = source(card)["component_registry"][1]
    assert record["binding_state"] == "referenced"
    assert (
        record["references"][1]["descriptor_states"]["ligand_comp_id"] == "not_retained"
    )
    assert "ligand_comp_id" not in record["references"][1]["descriptors"]


@pytest.mark.parametrize(
    "target,state",
    [
        ("entry", "foreign_entry_identity"),
        ("parent", "conflicting_parent_entity_identity"),
        ("shape", "unrecognized_descriptor_shape"),
    ],
)
def test_foreign_or_conflicting_native_context_is_not_resolved(card, target, state):
    if target == "entry":
        instance(card)[IDS]["entry_id"] = "1HTI"
    elif target == "parent":
        instance(card)[IDS]["entity_id"] = "999"
    else:
        instance(card)[IDS]["auth_asym_id"] = []
    record = source(card)["component_registry"][0]
    assert record["binding_state"] == "ambiguous" and state in record["reasons"]


@pytest.mark.parametrize(
    "raw,state",
    [(None, "retained_null"), ({}, "unrecognized_shape"), ([], "retained_empty")],
)
def test_component_input_null_empty_and_malformed_are_distinct(card, raw, state):
    value(card)["ligand_contact_inputs"]["polymer_entities"] = raw
    row = source(card)
    assert row["component_registry"] == []
    if state == "retained_empty":
        assert not row["component_input_issues"]
    else:
        assert row["component_input_issues"][0]["state"] == state


def test_missing_input_stays_unknown_and_qualifiers_never_backfill(card):
    del value(card)["ligand_contact_inputs"]
    row = source(card)
    assert row["component_registry"] == []
    issue = row["component_input_issues"][0]
    assert (
        issue["state"] == "not_retained"
        and issue["missing_field"] == "ligand_contact_inputs"
    )
    assert card.access().read(issue["input_location"]).page(max_bytes=8192)["page"]


@pytest.mark.parametrize(
    "raw,state",
    [
        (None, "retained_null"),
        ({}, "unrecognized_shape"),
        ([], "retained_empty"),
        ([None, " A", ""], "retained"),
    ],
)
def test_generator_label_input_states_do_not_fabricate_members(card, raw, state):
    generator(card)["asym_id_list"] = raw
    item = source(card)["assemblies"][0]["generators"][0]
    assert item["component_input_state"] == state
    if state == "retained":
        assert all(
            r["state"] == "unrecognized_label" for r in item["component_bindings"]
        )
    else:
        assert not item["component_bindings"]


def test_missing_identifier_container_has_an_existing_location(card):
    del instance(card)[IDS]
    row = source(card)
    issue = next(
        i for i in row["component_input_issues"] if i.get("missing_field") == IDS
    )
    assert card.access().read(issue["input_location"]).page(max_bytes=8192)["page"]


def test_duplicate_generator_labels_remain_occurrences_not_distinct_molecules(card):
    generator(card)["asym_id_list"] = ["A", "A"]
    row = source(card)["assemblies"][0]["generators"][0]
    assert row["component_scope"] == "resolved"
    assert [r["label_index"] for r in row["component_bindings"]] == [0, 1]
    assert all(r["repeated"] for r in row["component_bindings"])


def test_source_revisions_never_supply_each_others_component_records(card):
    sa = assertion(card)
    other = deepcopy(sa)
    other["id"] = "SYNTHETIC-REVISION"
    other["asserted_value"]["accession_info"]["minor_revision"] = 999
    other["asserted_value"]["ligand_contact_inputs"]["polymer_entities"] = []
    card.source_assertion_store.store[other["id"]] = other
    rel = next(
        r
        for r in card.relationship_store.store.values()
        if sa["id"] in r["source_assertion_ids"]
    )
    rel["source_assertion_ids"].append(other["id"])
    rows = card.assembly_generation()["sources"]
    assert rows[0]["component_registry"] and rows[1]["component_registry"] == []
    assert rows[1]["assemblies"][0]["generators"][0]["component_scope"] == "unresolved"


@pytest.mark.parametrize("phase", ["rows", "text"])
def test_component_budget_refuses_before_pin_or_tuple_expansion(
    card, monkeypatch, phase
):
    backend = importlib.import_module("sabueso.core.assembly_generation_v3")
    monkeypatch.setattr(card, "pinned_ref", lambda: pytest.fail("No pin before guard"))
    monkeypatch.setattr(
        backend, "expand", lambda *a: pytest.fail("No expansion before guard")
    )
    limit = 200
    if phase == "rows":
        instance(card)["rcsb_ligand_neighbors"] = [{}] * 1000
    else:
        instance(card)[IDS]["auth_asym_id"] = "X" * 1000
    before = card.to_dict()
    with pytest.raises(ArgumentError, match="operation_budget=None"):
        card.assembly_generation(expand_operations=True, operation_budget=limit)
    assert before == card.to_dict()


@pytest.mark.parametrize("limit", [1000, None])
def test_deliberate_budget_override_preserves_unresolved_declarations(card, limit):
    generator(card)["asym_id_list"] = ["A", "UNKNOWN"]
    result = card.assembly_generation(
        structure_ref="pdb:2V5B", expand_operations=True, operation_budget=limit
    )
    item = result["sources"][0]["assemblies"][0]["generators"][0]
    assert item["component_scope"] == "partial" and item["operation_tuples"] == [
        ["1"],
        ["2"],
    ]
    assert result["tuple_expansion_state"] == "expanded"


def test_prior_rules_stay_exact_and_returned_references_are_detached(card):
    before = card.to_dict()
    result = source(card)
    result["component_registry"][0]["references"][0]["descriptors"][
        "author_asym_id"
    ] = "local edit"
    assert before == card.to_dict()
    for version in [1, 2]:
        module = importlib.import_module(f"sabueso.core.assembly_generation_v{version}")
        assert card.assembly_generation(
            generation_rule=f"rcsb_assembly_generation@{version}"
        ) == module.generation(card, None, None, False, 100000)


def test_component_keys_do_not_require_supported_operation_syntax(card):
    generator(card)["oper_expression"] = "(1,(2))"
    generator(card)["asym_id_list"] = ["A"]
    item = source(card)["assemblies"][0]["generators"][0]
    assert item["status"] == "unsupported" and item["component_scope"] == "resolved"
    assert "operation_tuples" not in item


def test_foreign_generator_parent_does_not_admit_component_references(card):
    generator(card)["assembly_id"] = "SYNTHETIC-FOREIGN"
    item = source(card)["assemblies"][0]["generators"][0]
    assert item["component_scope"] == "parent_scope_unbound"
    assert not item["component_bindings"]


@pytest.mark.parametrize(
    "raw,state", [(None, "retained_null"), ([], "unrecognized_shape")]
)
def test_identifier_container_states_remain_explicit(card, raw, state):
    instance(card)[IDS] = raw
    issue = next(
        i for i in source(card)["component_input_issues"] if i.get("role") == IDS
    )
    assert issue["state"] == state
    assert card.access().read(issue["input_location"]).page(max_bytes=8192)["page"]


@pytest.mark.parametrize("record_id", ["1HTI_1", "2V5B_999", []])
def test_native_entity_record_identity_cannot_contradict_its_container(card, record_id):
    entity(card)["rcsb_id"] = record_id
    instance(card)["rcsb_ligand_neighbors"] = [
        {"ligand_asym_id": "B", "ligand_comp_id": "SYN"}
    ]
    records = source(card)["component_registry"]
    assert all(r["binding_state"] == "ambiguous" for r in records)
    assert all(
        r["references"][0]["descriptor_states"]["entity_record_id"] != "not_retained"
        for r in records
    )
