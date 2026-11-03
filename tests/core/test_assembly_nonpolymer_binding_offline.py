"""Native nonpolymer keys from public originals; altered inputs are synthetic."""

import importlib
import socket
from copy import deepcopy

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

RULE = "rcsb_assembly_generation@5"
EIDS = "rcsb_nonpolymer_entity_container_identifiers"
IIDS = "rcsb_nonpolymer_entity_instance_container_identifiers"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No acquisition")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def build(acc, pdbs):
    return sabueso.resolve(
        acc,
        resolver=EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=FixtureRCSBClient("temp_data/rcsb_nonpolymer_instances"),
        ),
        structures=pdbs,
    )[0]


@pytest.fixture(scope="module")
def originals():
    return {
        pdb: build(acc, [pdb]).to_dict()
        for pdb, acc in [("1SUX", "P52270"), ("2V5B", "P52270"), ("1HTI", "P60174")]
    }


@pytest.fixture
def card(originals):
    return Card.from_dict(deepcopy(originals["1HTI"]))


def assertion(card):
    return next(
        s
        for s in card.source_assertion_store.store.values()
        if s["source"]["name"] == "RCSB PDB"
    )


def value(card):
    return assertion(card)["asserted_value"]


def entity(card):
    return value(card)["assembly_component_inputs"]["nonpolymer_entities"][0]


def instance(card):
    return entity(card)["nonpolymer_entity_instances"][0]


def generator(card):
    return value(card)["assembly_generation_inputs"]["assemblies"][0][
        "pdbx_struct_assembly_gen"
    ][0]


def result(card, **options):
    return card.assembly_generation(generation_rule=RULE, **options)


def node(card, identifier="C"):
    return next(
        n
        for n in result(card)["sources"][0]["component_registry"]
        if n["asym_id"] == identifier
    )


def native_reference(card):
    return next(
        r for r in node(card)["references"] if r["role"] == "nonpolymer_instance"
    )


@pytest.mark.parametrize(
    "pdb,nonpolymers,unresolved",
    [("1SUX", "CDEFGHIJ", "KL"), ("2V5B", "", "B"), ("1HTI", "C", "")],
)
def test_public_original_keys_keep_native_author_and_unknown_bases(
    originals, pdb, nonpolymers, unresolved
):
    card = Card.from_dict(deepcopy(originals[pdb]))
    before = card.to_dict()
    output = result(card, expand_occurrences=True)
    assert (
        output["rule"] == RULE
        and output["component_binding_rule"] == "native_entry_component_key@2"
    )
    assert output["physical_membership"] == "not_computed"
    source = output["sources"][0]
    nodes = {r["asym_id"]: r for r in source["component_registry"]}
    for identifier in nonpolymers:
        record = nodes[identifier]
        assert record["binding_state"] == "resolved"
        assert record["basis"] == "native_nonpolymer_instance_identifier"
        assert any(
            r["role"] == "nonpolymer_instance" and r["identity_state"] == "resolved"
            for r in record["references"]
        )
    for parent in source["assemblies"]:
        for item in parent["generators"]:
            for row in item["declared_occurrences"]:
                if row["asym_id"] in nonpolymers:
                    assert row["component_state"] == "resolved"
                elif row["asym_id"] in unresolved:
                    assert row["component_state"] == "unresolved"
    if pdb == "1HTI":
        ref = next(
            r for r in nodes["C"]["references"] if r["role"] == "nonpolymer_instance"
        )
        assert ref["descriptors"]["author_asym_id"] == "B"
        assert ref["descriptors"]["author_seq_id"] == "549"
        assert nodes["B"]["basis"] == "native_polymer_instance_identifier"
    if pdb == "2V5B":
        assert source["nonpolymer_input_state"] == "retained_null"
    assert before == card.to_dict()


@pytest.mark.parametrize(
    "owner,field",
    [
        ("entity", "rcsb_id"),
        ("entity_ids", "entry_id"),
        ("entity_ids", "entity_id"),
        ("instance", "rcsb_id"),
        ("instance_ids", "entry_id"),
        ("instance_ids", "entity_id"),
    ],
)
@pytest.mark.parametrize("mode", ["missing", "null"])
def test_missing_native_context_is_not_completed_from_record_ids_or_neighbors(
    card, owner, field, mode
):
    containers = {
        "entity": entity(card),
        "entity_ids": entity(card)[EIDS],
        "instance": instance(card),
        "instance_ids": instance(card)[IIDS],
    }
    target = containers[owner]
    if mode == "missing":
        del target[field]
    else:
        target[field] = None
    record = node(card)
    assert record["binding_state"] == "referenced"
    assert record["basis"] == "native_ligand_neighbor_reference"
    ref = native_reference(card)
    assert ref["identity_state"] == "incomplete" and ref["identity_gaps"]
    assert record["references"] and not record["reasons"]


def test_an_incomplete_record_without_neighbor_support_remains_unresolved(card):
    value(card)["ligand_contact_inputs"]["polymer_entities"] = []
    del instance(card)[IIDS]["entry_id"]
    assert node(card)["binding_state"] == "unresolved"
    assert native_reference(card)["identity_state"] == "incomplete"


def test_complete_native_instance_does_not_require_a_neighbor_reference(card):
    value(card)["ligand_contact_inputs"]["polymer_entities"] = []
    record = node(card)
    assert record["binding_state"] == "resolved"
    assert record["basis"] == "native_nonpolymer_instance_identifier"
    assert {r["role"] for r in record["references"]} == {"nonpolymer_instance"}


@pytest.mark.parametrize("field", ["auth_asym_id", "auth_seq_id", "comp_id"])
def test_optional_descriptors_are_not_filled_from_other_records(card, field):
    del instance(card)[IIDS][field]
    record = node(card)
    assert record["binding_state"] == "resolved"
    names = {
        "auth_asym_id": "author_asym_id",
        "auth_seq_id": "author_seq_id",
        "comp_id": "comp_id",
    }
    ref = native_reference(card)
    assert names[field] not in ref["descriptors"]
    assert ref["descriptor_states"][names[field]] == "not_retained"


@pytest.mark.parametrize(
    "owner,field,raw,reason",
    [
        ("entity_ids", "entry_id", "OTHER", "foreign_entry_identity"),
        ("instance_ids", "entry_id", "OTHER", "foreign_entry_identity"),
        ("instance_ids", "entity_id", "999", "conflicting_parent_entity_identity"),
        ("entity", "rcsb_id", "1HTI_999", "conflicting_entity_record_identity"),
        ("instance", "rcsb_id", "1HTI.B", "conflicting_instance_record_identity"),
        ("entity_ids", "rcsb_id", "1HTI_999", "conflicting_entity_record_identity"),
        ("instance_ids", "rcsb_id", "1HTI.B", "conflicting_instance_record_identity"),
        (
            "instance_ids",
            "comp_id",
            "OTHER",
            "conflicting_nonpolymer_component_identity",
        ),
        ("instance_ids", "entry_id", 17, "unrecognized_descriptor_shape"),
        ("instance_ids", "entity_id", [], "unrecognized_descriptor_shape"),
        ("instance_ids", "entity_id", "", "invalid_native_identifier"),
        ("instance_ids", "comp_id", "bad code", "invalid_component_identifier"),
    ],
)
def test_explicit_contradictions_are_not_overridden_by_a_positive_neighbor(
    card, owner, field, raw, reason
):
    targets = {
        "entity": entity(card),
        "entity_ids": entity(card)[EIDS],
        "instance": instance(card),
        "instance_ids": instance(card)[IIDS],
    }
    targets[owner][field] = raw
    before = card.to_dict()
    record = node(card)
    assert record["binding_state"] == "ambiguous" and reason in record["reasons"]
    assert any(r["role"] == "ligand_neighbor_reference" for r in record["references"])
    assert card.to_dict() == before


@pytest.mark.parametrize("label", [None, False, 0, "", "bad label", []])
def test_record_id_or_author_label_never_supplies_an_unusable_native_label(card, label):
    instance(card)[IIDS]["asym_id"] = label
    record = node(card)
    assert record["binding_state"] == "referenced"
    assert not any(r["role"] == "nonpolymer_instance" for r in record["references"])
    assert any(
        i["state"] == "unidentified_record"
        for i in result(card)["sources"][0]["component_input_issues"]
    )


@pytest.mark.parametrize(
    "kind,reason",
    [
        ("instance", "duplicate_nonpolymer_instance_records"),
        ("entity", "duplicate_nonpolymer_entity_records"),
    ],
)
def test_duplicate_original_records_are_not_deduplicated_or_selected(
    card, kind, reason
):
    if kind == "instance":
        entity(card)["nonpolymer_entity_instances"].append(deepcopy(instance(card)))
    else:
        value(card)["assembly_component_inputs"]["nonpolymer_entities"].append(
            deepcopy(entity(card))
        )
    record = node(card)
    assert record["binding_state"] == "ambiguous" and reason in record["reasons"]
    assert (
        len([r for r in record["references"] if r["role"] == "nonpolymer_instance"])
        == 2
    )


def test_duplicate_entity_keys_do_not_select_the_coherent_parent(card):
    duplicate = deepcopy(entity(card))
    duplicate["rcsb_id"] = "1HTI_999"
    duplicate["nonpolymer_entity_instances"][0]["rcsb_id"] = "1HTI.D"
    duplicate["nonpolymer_entity_instances"][0][IIDS]["asym_id"] = "D"
    value(card)["assembly_component_inputs"]["nonpolymer_entities"].append(duplicate)
    assert "duplicate_nonpolymer_entity_records" in node(card)["reasons"]
    assert node(card, "D")["binding_state"] == "ambiguous"


def test_native_and_neighbor_component_disagreement_retains_both_bases(card):
    entity(card)[EIDS]["nonpolymer_comp_id"] = instance(card)[IIDS]["comp_id"] = (
        "SYNTHETIC"
    )
    record = node(card)
    assert "conflicting_ligand_component_references" in record["reasons"]
    assert record["binding_state"] == "ambiguous"
    assert {r["role"] for r in record["references"]} == {
        "nonpolymer_instance",
        "ligand_neighbor_reference",
    }


@pytest.mark.parametrize("label", ["D", None])
def test_duplicate_instance_record_ids_do_not_select_the_coherent_label(card, label):
    duplicate = deepcopy(instance(card))
    duplicate[IIDS]["asym_id"] = label
    entity(card)["nonpolymer_entity_instances"].append(duplicate)
    record = node(card)
    assert record["binding_state"] == "ambiguous"
    assert "duplicate_nonpolymer_instance_record_ids" in record["reasons"]
    assert (
        len([r for r in record["references"] if r["role"] == "nonpolymer_instance"])
        == 1
    )


def test_native_polymer_and_nonpolymer_role_conflict_is_explicit(card):
    polymer = value(card)["ligand_contact_inputs"]["polymer_entities"][0]
    polymer["polymer_entity_instances"][0][
        "rcsb_polymer_entity_instance_container_identifiers"
    ]["asym_id"] = "C"
    assert "conflicting_source_roles" in node(card)["reasons"]
    assert node(card)["binding_state"] == "ambiguous"


@pytest.mark.parametrize(
    "raw,state",
    [
        (None, "retained_null"),
        ([], "unrecognized_shape"),
        ({}, "not_retained"),
        ({"nonpolymer_entities": None}, "retained_null"),
        ({"nonpolymer_entities": []}, "retained_empty"),
        ({"nonpolymer_entities": "synthetic"}, "unrecognized_shape"),
    ],
)
def test_source_input_states_stay_distinct_without_inventing_absence(card, raw, state):
    value(card)["assembly_component_inputs"] = raw
    output = result(card)
    assert output["sources"][0]["nonpolymer_input_state"] == state
    assert node(card)["binding_state"] == "referenced"
    assert output["physical_membership"] == "not_computed"


def test_source_revisions_never_complete_each_others_identity(card):
    sa = assertion(card)
    other = deepcopy(sa)
    other["id"] = "SYNTHETIC_OTHER_REVISION"
    del other["asserted_value"]["assembly_component_inputs"]
    other["asserted_value"]["accession_info"]["minor_revision"] = 999
    card.source_assertion_store.store[other["id"]] = other
    rel = next(
        r
        for r in card.relationship_store.store.values()
        if sa["id"] in r.get("source_assertion_ids", [])
    )
    rel["source_assertion_ids"].append(other["id"])
    sources = {s["source_assertion_id"]: s for s in result(card)["sources"]}
    for identifier, expected in [(sa["id"], "resolved"), (other["id"], "referenced")]:
        record = next(
            n for n in sources[identifier]["component_registry"] if n["asym_id"] == "C"
        )
        assert record["binding_state"] == expected


def test_only_selected_originals_enter_the_new_input_preflight():
    card = build("P52270", ["1SUX", "2V5B"])
    other = next(
        s
        for s in card.source_assertion_store.store.values()
        if s["source"]["name"] == "RCSB PDB"
        and s["asserted_value"].get("object_ref") == "pdb:2V5B"
    )
    other["asserted_value"]["assembly_component_inputs"] = {
        "nonpolymer_entities": [{"rcsb_id": "SYNTHETIC" * 20000}]
    }
    selected = result(card, structure_ref="pdb:1SUX")
    assert (
        len(selected["sources"]) == 1
        and selected["sources"][0]["structure_ref"] == "pdb:1SUX"
    )
    with pytest.raises(ArgumentError, match="operation_budget=None"):
        result(card)


@pytest.mark.parametrize("phase", ["rows", "text", "expansion"])
def test_new_input_and_expansion_budgets_refuse_before_pin_or_materialization(
    card, monkeypatch, phase
):
    value(card)["ligand_contact_inputs"]["polymer_entities"] = []
    if phase == "rows":
        value(card)["assembly_component_inputs"]["nonpolymer_entities"] = [{}] * 2000
    elif phase == "text":
        instance(card)[IIDS]["auth_seq_id"] = "X" * 2000
    else:
        generator(card)["oper_expression"] = "(1-1000000000)(1-1000000000)"
    monkeypatch.setattr(card, "pinned_ref", lambda: pytest.fail("Pin before admission"))
    backend = importlib.import_module("sabueso.core.assembly_occurrences_v1")
    monkeypatch.setattr(
        backend,
        "expand",
        lambda *a, **k: pytest.fail("Expansion before admission"),
    )
    # The frozen compact prefix does not materialize tuples either.
    with pytest.raises(ArgumentError, match="operation_budget=None"):
        result(card, expand_occurrences=True, operation_budget=1000)


@pytest.mark.parametrize("limit", [100000, None])
def test_explicit_budget_override_keeps_complete_declared_occurrences(card, limit):
    output = result(
        card, expand_operations=True, expand_occurrences=True, operation_budget=limit
    )
    assert output["expanded_occurrence_count"] == 3
    assert (
        output["sources"][0]["assemblies"][0]["generators"][0]["declared_occurrences"][
            2
        ]["component_state"]
        == "resolved"
    )


def test_independent_native_binding_survives_unsupported_expression_but_not_a_foreign_parent(
    card,
):
    generator(card)["oper_expression"] = "(1,(2))"
    item = result(card)["sources"][0]["assemblies"][0]["generators"][0]
    assert (
        item["component_scope"] == "resolved"
        and item["occurrence_plan"]["status"] == "unavailable"
    )
    generator(card)["assembly_id"] = "SYNTHETIC_FOREIGN"
    item = result(card)["sources"][0]["assemblies"][0]["generators"][0]
    assert (
        item["component_scope"] == "parent_scope_unbound"
        and not item["component_bindings"]
    )


def test_exact_original_locations_and_detached_output(card):
    before = card.to_dict()
    output = result(card)
    reference = next(
        r
        for r in output["sources"][0]["component_registry"][2]["references"]
        if r["role"] == "nonpolymer_instance"
    )
    explorer = card.explore()
    assert explorer.inspect(
        locator=reference["input_location"]
    ).native_payload == instance(card)
    assert explorer.access.read(reference["entity_input_location"]).page(
        max_bytes=16384
    )["items"]
    reference["descriptors"]["comp_id"] = "caller mutation"
    assert (
        card.to_dict() == before
        and native_reference(card)["descriptors"]["comp_id"] == "PGA"
    )


def test_original_rules_default_and_live_adapter_remain_original(card):
    assert card.assembly_generation() == card.assembly_generation(
        generation_rule="rcsb_assembly_generation@4"
    )
    for version in (1, 2, 3, 4):
        module = importlib.import_module(f"sabueso.core.assembly_generation_v{version}")
        assert card.assembly_generation(
            generation_rule=f"rcsb_assembly_generation@{version}"
        ) == module.generation(card, None, None, False, 100000)
    # The existing human/agent adapter is still explicitly @4 until a new saved
    # scientific interpretation qualifies @5; it cannot silently adopt it.
    explorer = card.explore()
    selection = explorer.access.select(
        "assembly_generation", options={"structure_ref": "pdb:1HTI"}
    )
    view = explorer.answer("assembly_generation", options={"structure_ref": "pdb:1HTI"})
    assert view.native_payload["rule"] == "rcsb_assembly_generation@4"
    assert view.result_ref == selection.result_ref


@pytest.mark.parametrize("skip", [False, True])
def test_native_v5_boolean_validation_survives_skipped_digestion(card, skip):
    with pytest.raises(ArgumentError):
        card.assembly_generation(
            generation_rule=RULE, expand_occurrences=1, skip_digestion=skip
        )
