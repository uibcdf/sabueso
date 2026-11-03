"""Current native input refusal; original valid science and saved reading stay stable."""

import gzip
import hashlib
import importlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest
import smonitor

import sabueso
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import SchemaError
from sabueso.core.structure_ligand_inputs import validate
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient


def forbidden(*args, **kwargs):
    raise AssertionError("No source acquisition or scientific computation")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def original():
    card, _ = sabueso.resolve(
        "P52270",
        resolver=EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=FixtureRCSBClient("temp_data"),
        ),
        structures=["1SUX"],
    )
    card.relationship_store.store = {
        key: row
        for key, row in card.relationship_store.store.items()
        if row["predicate"] == "has_structure" and row["object_ref"] == "pdb:1SUX"
    }
    return card.to_dict()


@pytest.fixture
def card(original):
    return Card.from_dict(deepcopy(original))


def relationship(card):
    return next(iter(card.relationship_store.store.values()))


@pytest.mark.parametrize("value", [False, True, 0, 1, "", "BTS", {}])
def test_malformed_list_has_catalog_error_original_location_and_untouched_sources(
    card, value
):
    relationship(card)["qualifiers"]["ligands"] = value
    before = card.to_dict()
    with pytest.raises(SchemaError) as caught:
        card.structures(region=[96])
    error = caught.value
    assert error.code == "SABUESO-E-SCHEMA-001"
    assert error.extra["reason"] == "malformed_structure_ligand_inputs"
    assert error.extra["problem"] == "ligands_not_list"
    assert "No partial scientific result" in str(error)
    explorer = card.explore()
    assert explorer.inspect(locator=error.extra["location"]).native_payload == value
    parent = explorer.inspect(locator=error.extra["relationship_location"])
    assert parent.native_payload == relationship(card)
    assert parent.items()[0].explain().items()
    assert card.to_dict() == before


@pytest.mark.parametrize("value", [None, False, 1, "BTS", []])
def test_malformed_individual_entries_keep_exact_original_index(card, value):
    values = relationship(card)["qualifiers"]["ligands"]
    values.append(value)
    with pytest.raises(SchemaError) as caught:
        card.structures()
    assert caught.value.extra["problem"] == "ligand_not_mapping"
    location = caught.value.extra["location"]
    assert location["segments"][-1] == {"type": "Index", "value": 2}
    assert card.explore().inspect(locator=location).native_payload == value


@pytest.mark.parametrize(
    "field,value,problem",
    [
        ("comp_id", 1, "component_id_not_string"),
        ("comp_id", False, "component_id_not_string"),
        ("comp_id", [], "component_id_not_string"),
        ("comp_id", {}, "component_id_not_string"),
        ("subject_of_investigation", 1, "investigation_flag_not_boolean"),
        ("subject_of_investigation", 0, "investigation_flag_not_boolean"),
        ("subject_of_investigation", "false", "investigation_flag_not_boolean"),
        ("subject_of_investigation", [], "investigation_flag_not_boolean"),
    ],
)
def test_interpreted_component_and_flag_values_are_typed_without_coercion(
    card, field, value, problem
):
    relationship(card)["qualifiers"]["ligands"][0][field] = value
    with pytest.raises(SchemaError) as caught:
        card.structures()
    assert caught.value.extra["problem"] == problem
    location = caught.value.extra["location"]
    assert location["segments"][-1] == {"type": "Key", "value": field}
    assert card.explore().inspect(locator=location).native_payload == value


@pytest.mark.parametrize("route", ["card", "deck", "explanation", "human", "agent"])
def test_native_human_and_agent_routes_refuse_before_any_scientific_result(
    card, route, monkeypatch
):
    relationship(card)["qualifiers"]["ligands"] = False
    coordinates = importlib.import_module("sabueso.core.experimental_coordinates_v1")
    monkeypatch.setattr(coordinates, "view", forbidden)
    monkeypatch.setattr(coordinates, "inventory", forbidden)
    deck = Deck(cards=[card])
    with pytest.raises(SchemaError) as caught:
        if route == "card":
            card.structures()
        elif route == "deck":
            deck.structure_inventory()
        elif route == "explanation":
            deck.explain(card.id, structure_ref="pdb:1SUX")
        elif route == "human":
            card.explore().answer(
                "region_coverage",
                options={"sequence_ref": "uniprot:P52270", "region": [96]},
            )
        else:
            card.access().select("structures", options={"region": [96]})
    assert caught.value.extra["problem"] == "ligands_not_list"


def test_entire_multicard_request_is_checked_before_computation(card, monkeypatch):
    other = Card.from_dict(
        json.loads(Path("temp_data/frozen_cards/schema_0.3.8__P60174.json").read_text())
    )
    relationship(card)["qualifiers"]["ligands"] = False
    coordinates = importlib.import_module("sabueso.core.experimental_coordinates_v1")
    monkeypatch.setattr(coordinates, "inventory", forbidden)
    with pytest.raises(SchemaError):
        Deck(cards=[other, card]).structure_inventory()


@pytest.mark.parametrize(
    "value,state,interested",
    [
        (None, None, None),
        ([], "no_ligands", []),
        ([{}], "unstated", []),
        (
            [{"comp_id": "BTS", "subject_of_investigation": False}],
            "no_ligand_of_interest",
            [],
        ),
        (
            [{"comp_id": "BTS", "subject_of_investigation": True}],
            "ligand_of_interest",
            ["BTS"],
        ),
        ([{"subject_of_investigation": True}], "ligand_of_interest", []),
    ],
)
def test_valid_null_empty_partial_and_true_false_keep_original_interpretation(
    card, value, state, interested
):
    relationship(card)["qualifiers"]["ligands"] = value
    before = card.to_dict()
    result = card.structures()
    item = result["items"][0]
    assert item["state"]["ligands"] == state
    assert item["ligands_of_interest"] == interested
    assert item["ligands"] == value
    assert result["state_rule"]["rule"] == "structure_state@3"
    assert (
        Deck(cards=[card]).structure_inventory()["rule"]["rule"]
        == "structure_inventory@3"
    )
    assert before == card.to_dict()


def test_missing_list_and_uninterpreted_partial_instance_data_remain_valid(card):
    row = relationship(card)
    del row["qualifiers"]["ligands"]
    assert card.structures()["items"][0]["state"]["ligands"] is None
    row["qualifiers"]["ligands"] = [
        {"comp_id": "BTS", "subject_of_investigation": True, "instances": False}
    ]
    assert card.structures()["items"][0]["state"]["ligands"] == "ligand_of_interest"


def test_foreign_unplaced_declaration_does_not_enter_current_input_validation(card):
    row = deepcopy(relationship(card))
    row.update(id="REL_SYNTHETIC_FOREIGN", subject_ref="uniprot:P60174")
    row["qualifiers"]["ligands"] = False
    card.relationship_store.add(row)
    result = card.structures()
    assert len(result["items"]) == 1
    assert result["unplaced"][0]["relationship"]["qualifiers"]["ligands"] is False


def test_restricted_diagnostics_do_not_add_captured_identity_or_value(card):
    relationship(card)["qualifiers"]["ligands"] = "SYNTHETIC_PRIVATE_VALUE"
    with smonitor.diagnostic_scope():
        with pytest.raises(SchemaError) as caught:
            validate([card])
    assert caught.value.extra["reason"] == "malformed_structure_ligand_inputs"
    assert not {"location", "relationship_location"}.intersection(caught.value.extra)
    assert "SYNTHETIC_PRIVATE_VALUE" not in str(caught.value)
    assert card.id not in str(caught.value.extra)


def test_failed_capture_stays_inspectable_and_cannot_be_silently_repaired_by_caller_mutation(
    card,
):
    row = relationship(card)
    retained = deepcopy(row["qualifiers"]["ligands"])
    row["qualifiers"]["ligands"] = False
    explorer = card.explore()
    with pytest.raises(SchemaError) as caught:
        explorer.answer(
            "region_coverage",
            options={"sequence_ref": "uniprot:P52270", "region": [96]},
        )
    location = caught.value.extra["location"]
    row["qualifiers"]["ligands"] = retained
    assert explorer.inspect(locator=location).native_payload is False
    with pytest.raises(SchemaError):
        explorer.access.select("structures", options={"region": [96]})
    fresh = card.explore().answer(
        "region_coverage", options={"sequence_ref": "uniprot:P52270", "region": [96]}
    )
    assert (
        fresh.items()[0].open().native_payload["state"]["ligands"]
        == "ligand_of_interest"
    )


@pytest.mark.parametrize(
    "name",
    ["card_structure_context_legacy_v1.json.gz", "card_navigation_prefix_v6.json.gz"],
)
def test_original_saved_readers_never_use_current_input_validation(
    name, tmp_path, monkeypatch
):
    source = Path("tests/core/data") / name
    original = source.read_bytes()
    path = tmp_path / "original.json"
    path.write_bytes(gzip.decompress(original))
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.structure_ligand_inputs"),
        "validate",
        forbidden,
    )
    saved = sabueso.read_exploration(path)
    assert saved.validation["integrity"] == "verified"
    assert (
        hashlib.sha256(source.read_bytes()).digest()
        == hashlib.sha256(original).digest()
    )
