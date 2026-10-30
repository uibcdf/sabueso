"""Native symbolic source plans; modified source cases are explicitly synthetic."""

import importlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.assembly_operations_v1 import parse
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No source acquisition")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


@pytest.fixture(scope="module")
def originals():
    result = {}
    for pdb, accession in [("1SUX", "P52270"), ("2V5B", "P52270"), ("1HTI", "P60174")]:
        card, _ = sabueso.resolve(
            accession,
            resolver=EntityResolver(
                FixtureUniProtClient("temp_data"),
                rcsb_client=FixtureRCSBClient("temp_data/rcsb_assembly_generation"),
            ),
            structures=[pdb],
        )
        result[pdb] = card.to_dict()
    return result


@pytest.fixture
def card(originals):
    return Card.from_dict(deepcopy(originals["2V5B"]))


def native(card):
    return next(
        row
        for row in card.source_assertion_store.store.values()
        if row.get("source", {}).get("name") == "RCSB PDB"
    )


def generator(card, assembly=0):
    return native(card)["asserted_value"]["assembly_generation_inputs"]["assemblies"][
        assembly
    ]["pdbx_struct_assembly_gen"][0]


@pytest.mark.parametrize("pdb", ["1SUX", "2V5B", "1HTI"])
def test_native_public_sources_and_original_context_are_separate(originals, pdb):
    card = Card.from_dict(deepcopy(originals[pdb]))
    before = card.to_dict()
    result = card.assembly_generation(structure_ref=f"pdb:{pdb}")
    assert result["rule"] == "rcsb_assembly_generation@1"
    assert result["sabueso_version"] == sabueso.__version__
    assert result["card_ref"] == card.pinned_ref()
    assert result["physical_membership"] == "not_computed"
    source = result["sources"][0]
    assert source["source_assertion_id"] == native(card)["id"]
    assert source["entry_revision"] == native(card)["asserted_value"]["accession_info"]
    assert source["retrieved_at"] == "fixture"
    for parent in source["assemblies"]:
        for item in parent["generators"]:
            assert item["status"] == "parsed"
            assert item["operator_scope"] == "not_reconciled"
            assert "operation_tuples" not in item
            assert item["input_path"][-1] == item["generator_index"]
    assert card.to_dict() == before
    result["sources"].clear()
    assert card.to_dict() == before


def test_products_preserve_duplicate_occurrences_and_right_to_left_convention(card):
    generator(card)["oper_expression"] = "(X0,1,1)(2-3)"
    result = card.assembly_generation(expand_operations=True)
    row = result["sources"][0]["assemblies"][0]["generators"][0]
    assert row["plan"]["application_order"] == "right_to_left"
    assert row["plan"]["operation_count"] == 6
    assert row["operation_tuples"] == [
        ["X0", "2"],
        ["X0", "3"],
        ["1", "2"],
        ["1", "3"],
        ["1", "2"],
        ["1", "3"],
    ]
    assert result["sources"][0]["assemblies"][1]["generators"][0]["ordinal"] == 2


def test_exact_source_links_use_bounded_public_agent_access(card):
    result = card.assembly_generation()
    source = result["sources"][0]
    gen = source["assemblies"][0]["generators"][0]
    access = card.access()
    page = access.read(gen["input_location"]).page(max_bytes=8192)
    assert any(row["key"] == "oper_expression" for row in page["items"])
    page = access.read(source["source_location"]).page(max_bytes=8192)
    assert any(row["key"] == "asserted_value" for row in page["items"])
    assert access.read(result["quality_location"]).page(max_bytes=8192)["page"]


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "(1)(",
        "(1(2))",
        "1,,2",
        "2-1",
        "01-03",
        "1 + 2",
        "1\n2",
        "-1",
        "(1)junk",
        "(1),2",
    ],
)
def test_unsupported_syntax_stays_explicit_with_original_text(expression):
    result = parse(expression)
    assert result["status"] == "unsupported"
    assert result["expression"] == expression
    assert result["groups"] == []


def test_malformed_source_expression_never_aliases_mutable_card_content(card):
    generator(card)["oper_expression"] = {"synthetic": ["unrecognized"]}
    before = card.to_dict()
    row = card.assembly_generation(expand_operations=True)["sources"][0]["assemblies"][
        0
    ]["generators"][0]
    assert row["status"] == "unsupported" and row["plan"]["expression"] is None
    row["plan"]["groups"].append({"test": "local change"})
    assert card.to_dict() == before


def test_leading_zero_singletons_are_not_numeric_identity_coercion():
    plan = parse("01,1,_X")
    assert [r["id"] for r in plan["groups"][0]["terms"]] == ["01", "1", "_X"]


def test_large_decimal_range_counts_do_not_depend_on_python_int_text_limit(card):
    generator(card)["oper_expression"] = "1-" + "9" * 4500
    row = card.assembly_generation()["sources"][0]["assemblies"][0]["generators"][0]
    assert row["plan"]["count_state"] == "factored"
    assert row["plan"]["groups"][0]["count_decimal"] == "9" * 4500
    json.dumps(row)


def test_duplicate_parents_and_ordinals_are_reported_without_merging(card):
    assemblies = native(card)["asserted_value"]["assembly_generation_inputs"][
        "assemblies"
    ]
    assemblies.append(deepcopy(assemblies[0]))
    rows = assemblies[0]["pdbx_struct_assembly_gen"]
    rows.append(deepcopy(rows[0]))
    result = card.assembly_generation(expand_operations=True)
    parents = result["sources"][0]["assemblies"]
    assert len(parents) == 3
    assert parents[0]["parent_identity"] == parents[2]["parent_identity"] == "ambiguous"
    assert [r["ordinal_repeated"] for r in parents[0]["generators"]] == [True, True]
    assert [r["generator_index"] for r in parents[0]["generators"]] == [0, 1]
    assert result["expanded_tuple_count"] == 7
    assert result["physical_membership"] == "not_computed"


@pytest.mark.parametrize("skip", [False, True])
def test_expansion_and_exact_selector_guards_cannot_be_skipped(card, skip):
    with pytest.raises(ArgumentError):
        card.assembly_generation(expand_operations="yes", skip_digestion=skip)
    with pytest.raises(ArgumentError):
        card.assembly_generation(relationship_id="retained", skip_digestion=skip)
    with pytest.raises(ArgumentError):
        card.assembly_generation(structure_ref=3, skip_digestion=skip)
    absent = card.assembly_generation(
        structure_ref="pdb:2V5B", relationship_id="missing", skip_digestion=skip
    )
    assert absent["sources"] == [] and absent["status"] == "not_retained"


def test_source_assertions_with_different_revisions_are_not_pooled(card):
    original = native(card)
    other = deepcopy(original)
    other["id"] = "SYNTHETIC-SECOND-REVISION"
    other["asserted_value"]["accession_info"]["minor_revision"] = 999
    other["asserted_value"]["assembly_generation_inputs"]["assemblies"][0][
        "pdbx_struct_assembly_gen"
    ][0]["oper_expression"] = "1"
    card.source_assertion_store.store[other["id"]] = other
    rel = next(
        row
        for row in card.relationship_store.store.values()
        if original["id"] in row["source_assertion_ids"]
    )
    rel["source_assertion_ids"].append(other["id"])
    before = card.to_dict()
    sources = card.assembly_generation()["sources"]
    assert len(sources) == 2
    assert {r["entry_revision"]["minor_revision"] for r in sources} == {5, 999}
    assert {
        r["assemblies"][0]["generators"][0]["plan"]["operation_count"] for r in sources
    } == {1, 2}
    assert card.to_dict() == before


def test_compact_giant_product_is_factored_without_materialization(card, monkeypatch):
    generator(card)["oper_expression"] = "(1-10000000000)(1-10000000000)"
    backend = importlib.import_module("sabueso.core.assembly_generation_v1")
    monkeypatch.setattr(backend, "expand", lambda *args: pytest.fail("No expansion"))
    row = card.assembly_generation()["sources"][0]["assemblies"][0]["generators"][0]
    assert row["plan"]["count_state"] == "factored"
    assert row["plan"]["operation_count"] is None
    assert [g["count_decimal"] for g in row["plan"]["groups"]] == [
        "10000000000",
        "10000000000",
    ]


def test_all_expansion_is_preflighted_before_the_first_tuple(card, monkeypatch):
    generator(card, 1)["oper_expression"] = "(1-1000)(1-1000)"
    backend = importlib.import_module("sabueso.core.assembly_generation_v1")
    monkeypatch.setattr(
        backend, "expand", lambda *args: pytest.fail("No partial expansion")
    )
    before = card.to_dict()
    with pytest.raises(ArgumentError, match="operation_budget=None") as exc:
        card.assembly_generation(expand_operations=True)
    assert exc.value.extra["reason"] == "assembly_operation_budget_exceeded"
    assert exc.value.extra["assembly_workload"]["expanded"] is False
    assert card.to_dict() == before


def test_long_identifiers_are_bounded_even_when_tuple_count_fits(card, monkeypatch):
    begin = 10**499
    generator(card)["oper_expression"] = f"{begin}-{begin + 999}"
    backend = importlib.import_module("sabueso.core.assembly_generation_v1")
    monkeypatch.setattr(backend, "expand", lambda *args: pytest.fail("No tuple pools"))
    with pytest.raises(ArgumentError) as exc:
        card.assembly_generation(expand_operations=True)
    workload = exc.value.extra["assembly_workload"]
    assert workload["basis"] == "conservative_upper_bound"
    assert workload["upper_bound"] == 500_000
    assert "at_least" not in workload


@pytest.mark.parametrize("permission", ["arguments", "exception_text"])
def test_budget_diagnostics_respect_caller_capture_restrictions(card, permission):
    import smonitor

    with smonitor.diagnostic_scope(smonitor.CapturePolicy(**{permission: False})):
        with pytest.raises(ArgumentError) as exc:
            card.assembly_generation(operation_budget=1)
        assert "assembly_workload" not in exc.value.extra
        assert exc.value.extra["reason"] == "assembly_operation_budget_exceeded"


@pytest.mark.parametrize(
    "value,state", [(None, "retained_null"), ({}, "unrecognized_shape")]
)
def test_expression_shape_is_explicit_without_discarding_original(card, value, state):
    generator(card)["oper_expression"] = value
    row = card.assembly_generation()["sources"][0]["assemblies"][0]["generators"][0]
    assert row["expression_state"] == state and row["status"] == "unsupported"
    del generator(card)["oper_expression"]
    row = card.assembly_generation()["sources"][0]["assemblies"][0]["generators"][0]
    assert row["expression_state"] == "not_retained"


@pytest.mark.parametrize("limit", [1000, None])
def test_deliberate_raised_or_unlimited_budget_preserves_validation(card, limit):
    generator(card)["oper_expression"] = "(1-10)(1-10)"
    rows = card.assembly_generation(expand_operations=True, operation_budget=limit)[
        "sources"
    ][0]["assemblies"][0]["generators"]
    assert len(rows[0]["operation_tuples"]) == 100
    generator(card)["assembly_id"] = "foreign"
    row = card.assembly_generation(expand_operations=True, operation_budget=limit)[
        "sources"
    ][0]["assemblies"][0]["generators"][0]
    assert row["status"] == "parent_scope_unbound" and "operation_tuples" not in row


@pytest.mark.parametrize("limit", [True, False, 0, -1, 2.5, "100"])
@pytest.mark.parametrize("skip", [False, True])
def test_invalid_budget_refused_including_skipped_digestion(card, limit, skip):
    with pytest.raises(ArgumentError):
        card.assembly_generation(operation_budget=limit, skip_digestion=skip)


def test_raw_work_refuses_before_numeric_parsing_or_pin_capture(card, monkeypatch):
    generator(card)["oper_expression"] = "9" * 1000 + "-" + "9" * 1001
    backend = importlib.import_module("sabueso.core.assembly_generation_v1")
    monkeypatch.setattr(backend, "parse", lambda *args: pytest.fail("Preflight first"))
    monkeypatch.setattr(
        card, "pinned_ref", lambda: pytest.fail("Preflight before snapshot")
    )
    with pytest.raises(ArgumentError, match="operation_budget"):
        card.assembly_generation(operation_budget=100)


def test_source_identity_and_focal_subject_are_never_repaired(card):
    native(card)["source"]["record_id"] = "OTHER"
    assert card.assembly_generation()["sources"][0]["status"] == "source_scope_unbound"
    card.meta["card_id"] = "sabueso:protein:uniprot:P60174"
    result = card.assembly_generation()
    assert result["status"] == "missing_prerequisite"
    assert result["sources"] == [] and result["unplaced"]


def test_old_cards_report_unretained_inputs_without_inventing_history():
    card = Card.from_dict(
        json.loads(Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text())
    )
    before = card.to_dict()
    result = card.assembly_generation()
    assert result["sources"] and all(
        row["status"] == "not_retained" for row in result["sources"]
    )
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "value,expected",
    [(None, "retained_null"), ({}, "unrecognized_shape"), ([], "retained_empty")],
)
def test_null_malformed_and_empty_original_arrays_are_distinct(card, value, expected):
    native(card)["asserted_value"]["assembly_generation_inputs"]["assemblies"] = value
    assert card.assembly_generation()["sources"][0]["status"] == expected
