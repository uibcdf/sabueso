"""Declared component/operation combinations; altered inputs are synthetic."""

import importlib
import socket
from copy import deepcopy

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient


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


def generators(card, parent=0):
    return assertion(card)["asserted_value"]["assembly_generation_inputs"][
        "assemblies"
    ][parent]["pdbx_struct_assembly_gen"]


def first(card, **kwargs):
    return card.assembly_generation(**kwargs)["sources"][0]["assemblies"][0][
        "generators"
    ][0]


@pytest.mark.parametrize(
    "pdb,counts", [("1SUX", [12]), ("2V5B", [4, 2]), ("1HTI", [3])]
)
def test_public_compact_plans_count_declarations_not_physical_molecules(
    originals, pdb, counts
):
    card = Card.from_dict(deepcopy(originals[pdb]))
    before = card.to_dict()
    result = card.assembly_generation(structure_ref=f"pdb:{pdb}")
    assert result["rule"] == "rcsb_assembly_generation@4"
    assert result["occurrence_rule"] == "source_assembly_occurrence@1"
    assert result["physical_membership"] == "not_computed"
    assert result["occurrence_expansion_state"] == "not_requested"
    items = [g for a in result["sources"][0]["assemblies"] for g in a["generators"]]
    assert [i["occurrence_plan"]["declared_occurrence_count"] for i in items] == counts
    assert all(i["occurrence_plan"]["count_state"] == "exact" for i in items)
    assert all(
        "declared_occurrences" not in i and "operation_tuples" not in i for i in items
    )
    assert card.to_dict() == before


def test_expansion_has_exact_component_then_operation_order_and_key_bases(card):
    result = card.assembly_generation(structure_ref="pdb:2V5B", expand_occurrences=True)
    item = result["sources"][0]["assemblies"][0]["generators"][0]
    rows = item["declared_occurrences"]
    assert [(r["asym_id"], r["operator_ids"], r["binding_state"]) for r in rows] == [
        ("A", ["1"], "resolved"),
        ("A", ["2"], "resolved"),
        ("B", ["1"], "unresolved"),
        ("B", ["2"], "unresolved"),
    ]
    assert [
        (r["component_binding_index"], r["operation_tuple_index"]) for r in rows
    ] == [(0, 0), (0, 1), (1, 0), (1, 1)]
    assert [r["declaration_index"] for r in rows] == [0, 1, 2, 3]
    assert result["expanded_occurrence_count"] == 6
    assert result["occurrence_expansion_state"] == "expanded"
    assert (
        result["tuple_expansion_state"] == "not_requested"
        and "operation_tuples" not in item
    )
    assert (
        item["occurrence_plan"]["context"]["source_assertion_id"]
        == assertion(card)["id"]
    )


def test_original_component_and_operator_locations_remain_navigable(card):
    result = card.assembly_generation(expand_occurrences=True)
    source = result["sources"][0]
    item = source["assemblies"][0]["generators"][0]
    for row in item["declared_occurrences"]:
        component = item["component_bindings"][row["component_binding_index"]]
        assert (
            card.access().read(component["input_location"]).page(max_bytes=8192)["page"]
        )
        for index in row["operator_registry_indices"]:
            for projection in source["operator_registry"][index]["projections"]:
                assert (
                    card.access()
                    .read(projection["input_location"])
                    .page(max_bytes=8192)["page"]
                )


def test_ligand_neighbor_reference_never_becomes_a_complete_instance(originals):
    card = Card.from_dict(deepcopy(originals["1HTI"]))
    row = next(
        r
        for r in first(card, expand_occurrences=True)["declared_occurrences"]
        if r["asym_id"] == "C"
    )
    assert row["binding_state"] == row["component_state"] == "referenced"
    assert row["operator_states"] == ["resolved"]


def test_binding_is_evaluated_per_tuple_not_copied_from_generator_summary(card):
    generators(card)[0]["oper_expression"] = "1,9"
    item = first(card, expand_occurrences=True)
    assert item["operator_scope"] == "partial"
    assert [r["binding_state"] for r in item["declared_occurrences"][:2]] == [
        "resolved",
        "unresolved",
    ]
    assert item["declared_occurrences"][1]["operator_registry_indices"] == [None]
    ops = assertion(card)["asserted_value"]["assembly_generation_inputs"]["assemblies"][
        0
    ]["pdbx_struct_oper_list"]
    ops.append(deepcopy(ops[0]))
    generators(card)[0]["oper_expression"] = "1,2"
    assert [
        r["binding_state"]
        for r in first(card, expand_occurrences=True)["declared_occurrences"][:2]
    ] == ["ambiguous", "resolved"]


def test_products_retain_source_tuple_order_and_right_to_left_application(card):
    generators(card)[0].update(asym_id_list=["A"], oper_expression="(1,2)(X0,3)")
    item = first(card, expand_occurrences=True)
    assert [r["operator_ids"] for r in item["declared_occurrences"]] == [
        ["1", "X0"],
        ["1", "3"],
        ["2", "X0"],
        ["2", "3"],
    ]
    assert item["occurrence_plan"]["application_order"] == "right_to_left"


def test_repeated_labels_operators_and_generators_are_not_deduplicated(card):
    raw = generators(card)[0]
    raw.update(asym_id_list=["A", "A"], oper_expression="1,1")
    generators(card).append(deepcopy(raw))
    result = card.assembly_generation(expand_occurrences=True)
    items = result["sources"][0]["assemblies"][0]["generators"]
    assert [i["occurrence_plan"]["declared_occurrence_count"] for i in items] == [4, 4]
    assert items[0]["ordinal_repeated"] and items[1]["ordinal_repeated"]
    assert [i["occurrence_plan"]["context"]["generator_index"] for i in items] == [0, 1]
    assert all(
        [r["declaration_index"] for r in i["declared_occurrences"]] == [0, 1, 2, 3]
        for i in items
    )


def test_duplicate_native_parent_ids_keep_original_occurrence_contexts(card):
    parents = assertion(card)["asserted_value"]["assembly_generation_inputs"][
        "assemblies"
    ]
    parents.append(deepcopy(parents[0]))
    result = card.assembly_generation(expand_occurrences=True)
    first_item = result["sources"][0]["assemblies"][0]["generators"][0]
    last_item = result["sources"][0]["assemblies"][2]["generators"][0]
    assert first_item["occurrence_plan"]["context"]["parent_identity"] == "ambiguous"
    assert last_item["occurrence_plan"]["context"]["assembly_index"] == 2
    assert first_item["declared_occurrences"] == last_item["declared_occurrences"]


@pytest.mark.parametrize(
    "expression",
    ["1-100000000000000000000", "(1-100000000000000000000)(1-100000000000000000000)"],
)
def test_giant_compact_plans_retain_factors_without_materialization(
    card, monkeypatch, expression
):
    backend = importlib.import_module("sabueso.core.assembly_occurrences_v1")
    monkeypatch.setattr(
        backend, "expand", lambda *a: pytest.fail("No compact expansion")
    )
    generators(card)[0]["oper_expression"] = expression
    item = first(card)
    assert item["occurrence_plan"]["count_state"] == "factored"
    assert item["occurrence_plan"]["declared_occurrence_count"] is None
    assert item["occurrence_plan"]["factors"]["component_positions_decimal"] == "2"
    assert item["occurrence_plan"]["factors"]["operation_groups_decimal"] == [
        "100000000000000000000"
    ] * len(item["plan"]["groups"])


def test_component_multiplier_can_overflow_scalar_count_with_exact_factors(card):
    generators(card)[0]["oper_expression"] = "1-4611686018427387904"
    plan = first(card)["occurrence_plan"]
    assert plan["operation_count"] == 4611686018427387904
    assert (
        plan["declared_occurrence_count"] is None and plan["count_state"] == "factored"
    )


def test_empty_component_list_avoids_even_giant_operation_pool(card, monkeypatch):
    backend = importlib.import_module("sabueso.core.assembly_occurrences_v1")
    monkeypatch.setattr(
        backend,
        "expand",
        lambda *a: pytest.fail("Empty declarations do not need tuples"),
    )
    for pi in [0, 1]:
        generators(card, pi)[0].update(
            asym_id_list=[], oper_expression="1-100000000000000000000"
        )
    result = card.assembly_generation(structure_ref="pdb:2V5B", expand_occurrences=True)
    assert (
        result["expanded_occurrence_count"] == 0
        and result["occurrence_expansion_state"] == "expanded"
    )
    item = result["sources"][0]["assemblies"][0]["generators"][0]
    assert item["declared_occurrences"] == []
    assert item["occurrence_plan"]["declared_occurrence_count"] == 0


@pytest.mark.parametrize(
    "value,reason",
    [
        (None, "retained_null"),
        ({}, "unrecognized_shape"),
        (["A", None], "unrecognized_component_labels"),
    ],
)
def test_unavailable_labels_do_not_deliver_a_partial_generator_prefix(
    card, value, reason
):
    generators(card)[0]["asym_id_list"] = value
    result = card.assembly_generation(
        structure_ref="pdb:2V5B", expand_operations=True, expand_occurrences=True
    )
    item = result["sources"][0]["assemblies"][0]["generators"][0]
    assert item["occurrence_plan"]["reason"] == reason
    assert "declared_occurrences" not in item
    assert item["operation_tuples"] == [["1"], ["2"]]
    assert (
        result["occurrence_expansion_state"] == "incomplete"
        and result["tuple_expansion_state"] == "expanded"
    )


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("assembly_id", "FOREIGN", "parent_scope_unbound"),
        ("oper_expression", "(1,(2))", "unsupported"),
    ],
)
def test_unbound_parent_and_unsupported_operations_stay_unavailable(
    card, field, value, reason
):
    generators(card)[0][field] = value
    item = first(card, expand_occurrences=True)
    assert item["occurrence_plan"]["reason"] == reason
    assert "declared_occurrences" not in item


@pytest.mark.parametrize("mode", ["cardinality", "identifier_text"])
def test_all_request_preflight_runs_before_pin_or_any_tuple_pool(
    card, monkeypatch, mode
):
    backend = importlib.import_module("sabueso.core.assembly_occurrences_v1")
    receiving = importlib.import_module("sabueso.core.assembly_requests")
    monkeypatch.setattr(
        card, "pinned_ref", lambda: pytest.fail("No pin before complete preflight")
    )
    monkeypatch.setattr(
        backend, "expand", lambda *a: pytest.fail("No pool before complete preflight")
    )
    monkeypatch.setattr(receiving, "_diagnostic_details_allowed", lambda: True)
    if mode == "cardinality":
        for pi in [0, 1]:
            generators(card, pi)[0].update(
                asym_id_list=["A"] * 30, oper_expression="1-10"
            )
        limit = 500
        phase = "requested declared occurrences"
    else:
        label = "A" * 40
        raw_instance = assertion(card)["asserted_value"]["ligand_contact_inputs"][
            "polymer_entities"
        ][0]["polymer_entity_instances"][0]
        raw_instance["rcsb_polymer_entity_instance_container_identifiers"][
            "asym_id"
        ] = label
        generators(card)[0].update(asym_id_list=[label] * 3, oper_expression="1-3")
        limit = 300
        phase = "conservative occurrence text bound"
    before = card.to_dict()
    with pytest.raises(ArgumentError, match="operation_budget=None") as caught:
        card.assembly_generation(expand_occurrences=True, operation_budget=limit)
    assert caught.value.extra["assembly_workload"]["phase"] == phase
    if mode == "identifier_text":
        assert (
            caught.value.extra["assembly_workload"]["basis"]
            == "conservative_upper_bound"
        )
    assert card.to_dict() == before


@pytest.mark.parametrize("limit", [1000, None])
def test_deliberate_budget_override_delivers_all_declarations(card, limit):
    result = card.assembly_generation(
        structure_ref="pdb:2V5B",
        expand_operations=True,
        expand_occurrences=True,
        operation_budget=limit,
    )
    assert (
        result["expanded_tuple_count"] == 3 and result["expanded_occurrence_count"] == 6
    )
    assert (
        result["occurrence_expansion_state"]
        == result["tuple_expansion_state"]
        == "expanded"
    )


def test_outputs_and_original_rules_are_independent(card):
    before = card.to_dict()
    item = first(card, expand_operations=True, expand_occurrences=True)
    item["declared_occurrences"][0]["operator_ids"].append("LOCAL")
    assert item["declared_occurrences"][2]["operator_ids"] == ["1"]
    assert item["operation_tuples"] == [["1"], ["2"]]
    assert card.to_dict() == before
    for version in [1, 2, 3]:
        module = importlib.import_module(f"sabueso.core.assembly_generation_v{version}")
        assert card.assembly_generation(
            generation_rule=f"rcsb_assembly_generation@{version}"
        ) == module.generation(card, None, None, False, 100000)


@pytest.mark.parametrize("value", [None, 1, "yes", []])
@pytest.mark.parametrize("skip", [False, True])
def test_occurrence_expansion_is_a_strict_public_boolean(card, value, skip):
    with pytest.raises(ArgumentError):
        card.assembly_generation(expand_occurrences=value, skip_digestion=skip)


@pytest.mark.parametrize("version", [1, 2, 3])
def test_new_expansion_cannot_be_silently_ignored_by_a_prior_rule(card, version):
    with pytest.raises(ArgumentError, match="rcsb_assembly_generation@4"):
        card.assembly_generation(
            expand_occurrences=True,
            generation_rule=f"rcsb_assembly_generation@{version}",
        )


def test_original_source_revision_contexts_never_share_occurrence_bindings(card):
    original = assertion(card)
    other = deepcopy(original)
    other["id"] = "SYNTHETIC-REVISION"
    other["asserted_value"]["accession_info"]["minor_revision"] = 999
    other["asserted_value"]["ligand_contact_inputs"]["polymer_entities"] = []
    card.source_assertion_store.store[other["id"]] = other
    rel = next(
        r
        for r in card.relationship_store.store.values()
        if original["id"] in r["source_assertion_ids"]
    )
    rel["source_assertion_ids"].append(other["id"])
    sources = card.assembly_generation(expand_occurrences=True)["sources"]
    first_item = sources[0]["assemblies"][0]["generators"][0]
    second_item = sources[1]["assemblies"][0]["generators"][0]
    assert first_item["declared_occurrences"][0]["binding_state"] == "resolved"
    assert second_item["declared_occurrences"][0]["binding_state"] == "unresolved"
    assert (
        first_item["occurrence_plan"]["context"]["source_assertion_id"]
        == original["id"]
    )
    assert (
        second_item["occurrence_plan"]["context"]["source_assertion_id"] == other["id"]
    )
