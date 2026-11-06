"""Original public classifications; deliberately altered cases are synthetic."""

import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.chebi import map_chebi_identity

ROLE_PATH = "annotations.chemical_roles"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*a, **k):
        pytest.fail("Classification reads must not query sources")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def card():
    records = json.loads(Path("temp_data/chebi/compounds.json").read_text())
    mapping, key = map_chebi_identity(records["compounds"]["CHEBI:28445"], "2026-09-30")
    return build_card_from_mapping(
        mapping,
        meta={"entity_type": "small_molecule"},
        card_id="sabueso:small_molecule:inchikey:" + key,
    )


def original_role(card):
    return card.source_assertion_store.get(
        card.get(ROLE_PATH)["source_assertion_ids"][0]
    )


def row(result, name):
    return next(
        r
        for r in result["rows"]
        if isinstance(r["value"], dict) and r["value"].get("name") == name
    )


def replace_roles(card, values):
    source = deepcopy(original_role(card))
    made = make_source_assertion(
        ROLE_PATH,
        values,
        "ChEBI",
        "CHEBI:28445",
        source["retrieved_at"],
        subject_ref=source["subject_ref"],
    )
    made["source_metadata"] = source["source_metadata"]
    card.source_assertion_store.add(made)
    card.get(ROLE_PATH).update(
        value=deepcopy(values), source_assertion_ids=[made["id"]]
    )


def test_public_direct_inherited_roles_and_complete_support_stay_distinct(card):
    before = card.to_dict()
    result = card.chemical_classification()
    assert result["status"] == "ok"
    assert result["rule"] == "chemical_classification_context@1"
    assert row(result, "vinca alkaloid")["assignment"] == "class_membership"
    direct = row(result, "antineoplastic agent")
    inherited = row(result, "Bronsted base")
    assert (
        direct["assignment"] == "direct" and direct["categories"]["application"] is True
    )
    assert (
        inherited["assignment"] == "inherited"
        and inherited["categories"]["chemical_role"] is True
    )
    assert "not target-specific activity" in result["scope"]
    for item in result["rows"]:
        assert item["state"] == "source_supported"
        for membership in item["source_memberships"]:
            source = result["input_source_assertions"][
                membership["source_assertion_id"]
            ]
            assert source["asserted_value"][membership["index"]] == item["value"]
            assert result["identity_bindings"][source["id"]]["state"] == "bound"
            assert source["source_metadata"]["stars"] == 3
    assert card.to_dict() == before
    result["rows"][0]["value"].clear()
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "change",
    [
        "no_link",
        "foreign_subject",
        "wrong_field",
        "wrong_value",
        "observation",
        "missing_support",
        "unselected_support",
        "contradictory_anchor",
    ],
)
def test_unknown_support_and_identity_never_become_focal_role_claims(card, change):
    source = original_role(card)
    if change == "no_link":
        card.relationship_store.store.clear()
    elif change == "foreign_subject":
        source["subject_ref"] = "chebi:17150"
    elif change == "wrong_field":
        source["field_path"] = "annotations.definition"
    elif change == "wrong_value":
        card.get(ROLE_PATH)["value"] = deepcopy(card.get(ROLE_PATH)["value"])
        card.get(ROLE_PATH)["value"][0]["name"] = "synthetic unrelated role"
    elif change == "observation":
        source["retrieved_at"] = "another observation"
    elif change == "missing_support":
        card.get(ROLE_PATH)["source_assertion_ids"] = ["SA_missing"]
    elif change == "unselected_support":
        card.get(ROLE_PATH)["source_assertion_ids"] = []
    else:
        card.set("identifiers.inchikey", "ASCFNMCAHFUBCO-UHFFFAOYSA-N", [])
    result = card.chemical_classification()
    roles = [r for r in result["rows"] if r["kind"] == "role"]
    assert roles and result["status"] in ("partial", "missing_prerequisite")
    unknown = roles[:1] if change == "wrong_value" else roles
    assert all(r["assignment"] == "unknown" for r in unknown)
    assert all(not r["source_memberships"] for r in unknown)
    checks = result["fields"][ROLE_PATH]["support_checks"]
    if change == "missing_support":
        assert checks == {"SA_missing": "source_not_retained"}
    elif change == "wrong_field":
        assert "field_path_mismatch" in checks.values()
    elif change == "observation":
        assert "identity_unknown" in checks.values()
    assert result["fields"][ROLE_PATH]["original_node"] == card.get(ROLE_PATH)


def test_duplicate_selected_members_remain_distinct_positions(card):
    value = deepcopy(card.get(ROLE_PATH)["value"][0])
    replace_roles(card, [value, deepcopy(value)])
    card.get(ROLE_PATH)["source_assertion_ids"] *= 2
    result = card.chemical_classification()
    roles = [r for r in result["rows"] if r["kind"] == "role"]
    assert len(roles) == 2 and roles[0]["row_ref"] != roles[1]["row_ref"]
    assert roles[0]["index"] == 0 and roles[1]["index"] == 1
    assert [m["index"] for m in roles[0]["source_memberships"]] == [0, 1]
    roles[0]["source_memberships"].clear()
    assert len(roles[1]["source_memberships"]) == 2


@pytest.mark.parametrize(
    "value,assignment",
    [
        (False, "inherited"),
        (True, "direct"),
        (0, "unrecognized"),
        ("false", "unrecognized"),
        (None, "not_stated"),
    ],
)
def test_literal_false_and_unknown_role_flags_are_never_coerced(
    card, value, assignment
):
    role = deepcopy(card.get(ROLE_PATH)["value"][0])
    role.update(direct=value, application=value)
    replace_roles(card, [role])
    reading = next(
        r for r in card.chemical_classification()["rows"] if r["kind"] == "role"
    )
    assert reading["assignment"] == assignment
    assert reading["categories"]["application"] is (
        value if type(value) is bool else None
    )
    assert type(reading["value"]["direct"]) is type(value)


def test_unselected_source_values_and_stored_conflicts_are_inspectable(card):
    original = deepcopy(original_role(card))
    new = make_source_assertion(
        ROLE_PATH,
        [{"name": "another retained role", "chebi_id": "CHEBI:1"}],
        "ChEBI",
        "CHEBI:28445",
        "another date",
        subject_ref="chebi:28445",
    )
    card.source_assertion_store.add(new)
    card.quality["conflicts"] = [
        {"field": ROLE_PATH, "value": "synthetic unresolved conflict"}
    ]
    result = card.chemical_classification()
    assert new["id"] in result["fields"][ROLE_PATH]["alternative_source_assertion_ids"]
    assert result["input_source_assertions"][new["id"]] == new
    assert result["input_source_assertions"][original["id"]] == original
    assert result["stored_conflicts"] == card.quality["conflicts"]
    assert all(
        m["source_assertion_id"] != new["id"]
        for r in result["rows"]
        for m in r["source_memberships"]
    )


def test_coherent_competing_identity_targets_remain_ambiguous(card):
    source = original_role(card)
    other = "ASCFNMCAHFUBCO-UHFFFAOYSA-N"
    assertion = make_source_assertion(
        "relationships.same_as",
        {"object_ref": "inchikey:" + other, "inchikey": other},
        "ChEBI",
        "CHEBI:28445",
        source["retrieved_at"],
        subject_ref="chebi:28445",
    )
    assertion["source_metadata"] = deepcopy(source["source_metadata"])
    card.source_assertion_store.add(assertion)
    card.relationship_store.add(
        make_relationship(
            "chebi:28445",
            "same_as",
            "inchikey:" + other,
            source_assertion_ids=[assertion["id"]],
        )
    )
    result = card.chemical_classification()
    assert result["status"] == "partial"
    assert all(b["state"] == "ambiguous" for b in result["identity_bindings"].values())
    assert all(r["assignment"] == "unknown" for r in result["rows"])
    assert assertion["id"] in result["input_source_assertions"]


@pytest.mark.parametrize(
    "change",
    ["missing_date", "invalid_source", "invalid_anchor", "annotation_container"],
)
def test_unrecognized_original_context_stays_inspectable(card, change):
    if change == "missing_date":
        original_role(card).pop("retrieved_at")
    elif change == "invalid_source":
        original_role(card)["source"] = "ChEBI"
    elif change == "invalid_anchor":
        card.meta["card_id"] = "sabueso:small_molecule:inchikey:invalid"
    else:
        card.sections["annotations"] = "synthetic malformed container"
    result = card.chemical_classification()
    assert result["status"] in ("partial", "missing_prerequisite", "unknown")
    if change == "annotation_container":
        assert result["annotation_container_state"] == "unrecognized_shape"
        assert (
            result["unrecognized_annotation_container"]
            == "synthetic malformed container"
        )
    else:
        assert all(
            r["assignment"] == "unknown" for r in result["rows"] if r["kind"] == "role"
        )


@pytest.mark.parametrize(
    "state,value",
    [
        ("retained_empty", []),
        ("retained_null", None),
        ("unrecognized_shape", {"unknown": "shape"}),
    ],
)
def test_empty_null_and_malformed_fields_keep_original_meaning(card, state, value):
    card.get(ROLE_PATH)["value"] = deepcopy(value)
    result = card.chemical_classification()
    assert result["fields"][ROLE_PATH]["state"] == state
    assert result["fields"][ROLE_PATH]["original_node"]["value"] == value
    assert "source/global absence" in result["scope"]


def test_unknown_and_inapplicable_natures_do_not_claim_empty_chemistry():
    molecule = Card(
        meta={
            "entity_type": "small_molecule",
            "card_id": "sabueso:small_molecule:inchikey:ASCFNMCAHFUBCO-UHFFFAOYSA-N",
        }
    )
    assert molecule.chemical_classification()["status"] == "unknown"
    assert (
        Card(meta={"entity_type": "protein"}).chemical_classification()["status"]
        == "not_applicable"
    )


def test_public_biochemical_compound_has_its_own_source_roles():
    records = json.loads(Path("temp_data/chebi/compounds.json").read_text())
    mapping, key = map_chebi_identity(records["compounds"]["CHEBI:17150"], "2026-09-30")
    card = build_card_from_mapping(
        mapping,
        meta={"entity_type": "small_molecule"},
        card_id="sabueso:small_molecule:inchikey:" + key,
    )
    result = card.chemical_classification()
    assert result["status"] == "ok"
    assert all(r["state"] == "source_supported" for r in result["rows"])
    assert result["focal_ref"] == "inchikey:ASCFNMCAHFUBCO-UHFFFAOYSA-N"
    assert all(
        s["source"]["record_id"] == "CHEBI:17150"
        for s in result["input_source_assertions"].values()
    )


def test_normalized_role_values_do_not_replace_the_original_source_statement(card):
    original = original_role(card)
    value = deepcopy(card.get(ROLE_PATH)["value"])
    value[0]["direct"] = not value[0]["direct"]
    original["normalized_value"] = deepcopy(value)
    card.get(ROLE_PATH)["value"] = value
    result = card.chemical_classification()
    first = next(r for r in result["rows"] if r["kind"] == "role")
    assert first["assignment"] == "unknown" and not first["source_memberships"]
    assert result["input_source_assertions"][original["id"]] == original


@pytest.mark.parametrize("edited", ["selected_value", "source_assertion"])
def test_field_edits_and_source_edits_do_not_rewrite_each_other(card, edited):
    selected = deepcopy(card.get(ROLE_PATH)["value"])
    source = deepcopy(original_role(card))
    if edited == "selected_value":
        card.get(ROLE_PATH)["value"][0]["name"] = "synthetic selected edit"
        assert original_role(card) == source
    else:
        original_role(card)["asserted_value"][0]["name"] = "synthetic source edit"
        assert card.get(ROLE_PATH)["value"] == selected
    result = card.chemical_classification()
    first = next(r for r in result["rows"] if r["kind"] == "role")
    assert first["assignment"] == "unknown"
    assert not first["source_memberships"]
