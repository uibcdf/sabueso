"""Native operator keys; changed inputs are synthetic, not source observations."""

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


def assemblies(card):
    return assertion(card)["asserted_value"]["assembly_generation_inputs"]["assemblies"]


def gen(card, index=0):
    return assemblies(card)[index]["pdbx_struct_assembly_gen"][0]


def source(card, **kwargs):
    return card.assembly_generation(**kwargs)["sources"][0]


@pytest.mark.parametrize("pdb", ["1SUX", "2V5B", "1HTI"])
def test_public_native_ids_bind_with_original_locations(originals, pdb):
    card = Card.from_dict(deepcopy(originals[pdb]))
    before = card.to_dict()
    result = card.assembly_generation(
        structure_ref=f"pdb:{pdb}", generation_rule="rcsb_assembly_generation@2"
    )
    assert result["rule"] == "rcsb_assembly_generation@2"
    assert result["operator_binding_rule"] == "native_entry_operator_key@1"
    assert result["physical_membership"] == "not_computed"
    row = result["sources"][0]
    for parent in row["assemblies"]:
        for generator in parent["generators"]:
            assert generator["operator_scope"] == "resolved"
            assert "operation_tuples" not in generator
    access = card.access()
    for node in row["operator_registry"]:
        assert node["binding_state"] == "resolved"
        for projection in node["projections"]:
            page = access.read(projection["input_location"]).page(max_bytes=8192)
            assert any(item["key"] == "id" for item in page["items"])
    assert before == card.to_dict()


def test_entry_key_repeated_across_parent_projections_keeps_both(card):
    row = source(card)
    assert [n["operator_id"] for n in row["operator_registry"]] == ["1", "2"]
    assert all(len(n["projections"]) == 2 for n in row["operator_registry"])
    assert all(n["reasons"] == [] for n in row["operator_registry"])
    assert (
        row["assemblies"][1]["generators"][0]["operator_bindings"][0]["terms"][0][
            "matches"
        ][0]["operator_id"]
        == "1"
    )


def test_duplicate_within_one_parent_is_not_silently_deduplicated(card):
    ops = assemblies(card)[0]["pdbx_struct_oper_list"]
    ops.append(deepcopy(ops[0]))
    row = source(card)
    node = row["operator_registry"][0]
    assert node["operator_id"] == "1" and node["binding_state"] == "ambiguous"
    assert node["reasons"] == ["duplicate_records_within_parent"]
    assert len(node["projections"]) == 3
    assert row["assemblies"][0]["generators"][0]["operator_scope"] == "partial"


def test_conflicting_descriptors_across_parents_never_select_a_winner(card):
    assemblies(card)[1]["pdbx_struct_oper_list"][0]["name"] = "synthetic different name"
    row = source(card)
    node = row["operator_registry"][0]
    assert node["binding_state"] == "ambiguous"
    assert node["conflicting_fields"] == ["name"]
    assert {p["descriptors"]["name"] for p in node["projections"]} == {
        "1_555",
        "synthetic different name",
    }
    assert row["assemblies"][1]["generators"][0]["operator_scope"] == "unresolved"


def test_unknown_descriptor_fields_are_not_filled_from_another_projection(card):
    del assemblies(card)[1]["pdbx_struct_oper_list"][0]["name"]
    node = source(card)["operator_registry"][0]
    assert node["binding_state"] == "resolved"
    assert node["projections"][1]["descriptor_states"]["name"] == "not_retained"
    assert "name" not in node["projections"][1]["descriptors"]
    assemblies(card)[1]["pdbx_struct_oper_list"][0]["type"] = {}
    node = source(card)["operator_registry"][0]
    assert "unrecognized_descriptor_shape" in node["reasons"]


def test_names_equal_transforms_and_zero_padding_do_not_merge_native_ids(card):
    ops = assemblies(card)[0]["pdbx_struct_oper_list"]
    other = deepcopy(ops[0])
    other["id"] = "01"
    ops.append(other)
    gen(card)["oper_expression"] = "01,1,1_555"
    generator = source(card)["assemblies"][0]["generators"][0]
    terms = generator["operator_bindings"][0]["terms"]
    assert [t["matches"][0]["operator_id"] for t in terms[:2]] == ["01", "1"]
    assert terms[2]["matches"] == [] and terms[2]["unrepresented_count_decimal"] == "1"
    gen(card)["oper_expression"] = "1-2"
    terms = source(card)["assemblies"][0]["generators"][0]["operator_bindings"][0][
        "terms"
    ]
    assert [m["operator_id"] for m in terms[0]["matches"]] == ["1", "2"]


def test_giant_range_binds_only_retained_records_without_expansion(card, monkeypatch):
    gen(card)["oper_expression"] = "1-100000000000000000000"
    backend = importlib.import_module("sabueso.core.assembly_generation_v2")
    monkeypatch.setattr(backend, "expand", lambda *a: pytest.fail("No expansion"))
    result = card.assembly_generation()
    term = result["sources"][0]["assemblies"][0]["generators"][0]["operator_bindings"][
        0
    ]["terms"][0]
    assert term["resolved_count"] == 2
    assert term["unrepresented_count_decimal"] == "99999999999999999998"
    assert term["unrepresented_scope"] == "retained_operator_records_only"
    assert result["operator_candidate_checks"] == 3


@pytest.mark.parametrize(
    "value,state", [(None, "retained_null"), ({}, "unrecognized_shape"), ([], None)]
)
def test_unavailable_and_empty_input_remain_distinct(card, value, state):
    for parent in assemblies(card):
        parent["pdbx_struct_oper_list"] = deepcopy(value)
    row = source(card)
    assert row["operator_registry"] == []
    if state:
        assert all(i["state"] == state for i in row["operator_input_issues"])
    else:
        assert (
            row["operator_input_issues"] == []
            and row["operator_input_state"] == "retained_empty"
        )
    assert row["assemblies"][0]["generators"][0]["operator_scope"] == "unresolved"


def test_missing_fields_point_to_original_parent_not_an_invented_node(card):
    for parent in assemblies(card):
        del parent["pdbx_struct_oper_list"]
    row = source(card)
    assert all(i["state"] == "not_retained" for i in row["operator_input_issues"])
    for issue in row["operator_input_issues"]:
        assert card.access().read(issue["input_location"]).page(max_bytes=8192)["page"]


def test_unidentified_operator_rows_stay_inspectable(card):
    assemblies(card)[0]["pdbx_struct_oper_list"].extend(
        [None, {}, {"id": None}, {"id": " 1"}]
    )
    row = source(card)
    assert len(row["operator_input_issues"]) == 4
    assert row["operator_input_state"] == "partial"
    assert row["assemblies"][0]["generators"][0]["operator_scope"] == "resolved"


def test_different_source_revisions_never_supply_missing_operators(card):
    original = assertion(card)
    other = deepcopy(original)
    other["id"] = "SYNTHETIC-REVISION"
    other["asserted_value"]["accession_info"]["minor_revision"] = 999
    for parent in other["asserted_value"]["assembly_generation_inputs"]["assemblies"]:
        parent["pdbx_struct_oper_list"] = []
    card.source_assertion_store.store[other["id"]] = other
    rel = next(
        r
        for r in card.relationship_store.store.values()
        if original["id"] in r["source_assertion_ids"]
    )
    rel["source_assertion_ids"].append(other["id"])
    rows = card.assembly_generation()["sources"]
    assert rows[0]["assemblies"][0]["generators"][0]["operator_scope"] == "resolved"
    assert rows[1]["assemblies"][0]["generators"][0]["operator_scope"] == "unresolved"


@pytest.mark.parametrize("phase", ["rows", "text", "comparisons", "references"])
def test_all_operator_work_is_checked_before_pin_or_expansion(card, monkeypatch, phase):
    backend = importlib.import_module("sabueso.core.assembly_generation_v2")
    monkeypatch.setattr(card, "pinned_ref", lambda: pytest.fail("Guard before pin"))
    monkeypatch.setattr(
        backend, "expand", lambda *a: pytest.fail("Guard before expansion")
    )
    limit = 200
    if phase == "rows":
        assemblies(card)[1]["pdbx_struct_oper_list"] = [
            {"id": str(i)} for i in range(1000)
        ]
    elif phase == "text":
        assemblies(card)[1]["pdbx_struct_oper_list"][0]["name"] = "X" * 1000
    elif phase == "comparisons":
        for parent in assemblies(card):
            parent["pdbx_struct_oper_list"] = [{"id": str(i)} for i in range(1, 21)]
        template = deepcopy(gen(card))
        template["oper_expression"] = "1-20"
        template["asym_id_list"] = []
        assemblies(card)[0]["pdbx_struct_assembly_gen"] = [
            deepcopy(template) for _ in range(20)
        ]
    else:
        limit = 15000
        begin = 10**499
        for parent in assemblies(card):
            parent["pdbx_struct_oper_list"] = [
                {"id": str(begin + i)} for i in range(10)
            ]
        gen(card)["oper_expression"] = ",".join([f"{begin}-{begin + 9}"] * 5)
    before = card.to_dict()
    with pytest.raises(ArgumentError, match="operation_budget=None"):
        card.assembly_generation(expand_operations=True, operation_budget=limit)
    assert before == card.to_dict()


@pytest.mark.parametrize("limit", [1000, None])
def test_raised_and_unlimited_budgets_keep_unknown_tuples_explicit(card, limit):
    gen(card)["oper_expression"] = "1,3"
    result = card.assembly_generation(
        structure_ref="pdb:2V5B", expand_operations=True, operation_budget=limit
    )
    item = result["sources"][0]["assemblies"][0]["generators"][0]
    assert item["operator_scope"] == "partial"
    assert item["operation_tuples"] == [["1"], ["3"]]
    assert result["tuple_expansion_state"] == "expanded"


def test_output_metadata_never_aliases_card_and_original_rule_is_unchanged(card):
    before = card.to_dict()
    row = source(card)
    row["operator_registry"][0]["projections"][0]["descriptors"]["name"] = "local edit"
    assert before == card.to_dict()
    original = importlib.import_module("sabueso.core.assembly_generation_v1")
    assert card.assembly_generation(
        generation_rule="rcsb_assembly_generation@1"
    ) == original.generation(card, None, None, False, 100000)


@pytest.mark.parametrize("rule", [None, True, [], "rcsb_assembly_generation@99"])
@pytest.mark.parametrize("skip", [True, False])
def test_rule_selection_is_validated_even_with_digestion_skipped(card, rule, skip):
    with pytest.raises(ArgumentError):
        card.assembly_generation(generation_rule=rule, skip_digestion=skip)
