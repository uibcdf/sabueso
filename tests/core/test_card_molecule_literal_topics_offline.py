"""Named molecule routes retain original data, states and saved observations."""

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.core.snapshot import canonical_json
from sabueso.tools.card.small_molecule import single_molecule_card
from sabueso.tools.db import pdb_ccd
from sabueso.tools.db.chembl import FixtureChEMBLClient


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("Literal discovery must not acquire sources")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def value(access, location):
    cursor = None
    items = []
    while True:
        page = access.read(location).page(limit=8, max_bytes=8192, cursor=cursor)
        assert len(canonical_json(page).encode("utf-8")) <= 8192
        assert page["page"]["blocked"] is None
        items.extend(page["items"])
        cursor = page["page"]["next_cursor"]
        if cursor is None:
            break
    kind = page["node"]["node_type"]
    if kind == "object":
        return {r["key"]: value(access, r["location"]) for r in items}
    if kind == "array":
        return [
            value(access, r["location"])
            for r in sorted(items, key=lambda row: row["ordinal"])
        ]
    assert len(items) == 1 and items[0]["value_included"]
    return items[0]["value"]


def topics(access):
    return value(access, access.catalog().page()["node"]["location"])


def molecule(kind="chembl"):
    if kind == "chembl":
        return single_molecule_card(
            chembl=FixtureChEMBLClient("temp_data").molecules(["CHEMBL110"])
        )
    if kind == "ccd":
        return single_molecule_card(
            ccd=pdb_ccd.FixtureCCDClient("temp_data/pdb_ccd_charge").components(["SO4"])
        )
    return single_molecule_card(
        pubchem={
            "retrieved_at": "fixture",
            "compounds": {
                "3717450": json.loads(
                    Path("temp_data/pubchem/3717450.json").read_text()
                )
            },
        }
    )


@pytest.mark.parametrize("kind", ["chembl", "ccd", "pubchem"])
def test_public_catalog_routes_preserve_complete_fields_and_original_support(kind):
    card = molecule(kind)
    original = card.to_dict()
    access = card.access()
    catalog = topics(access)
    for key in ("chemical_identity", "property_context"):
        descriptor = catalog[key]
        assert descriptor["adapter"] == "molecule_literal_topics@1"
        assert descriptor["scientific_adapter"] is False
        assert descriptor["operations"] == ["read"]
        assert (
            value(access, descriptor["source_assertions"]["location"])
            == original["source_assertion_store"]
        )
        assert value(access, descriptor["quality"]["location"]) == original["quality"]
        assert (
            value(access, descriptor["selection_rules"]["location"])
            == original["selection_rules"]
        )
    identity = catalog["chemical_identity"]["routes"]
    assert (
        value(access, identity["identifiers"]["location"])
        == original["sections"]["identifiers"]
    )
    assert (
        value(access, identity["relationships"]["location"])
        == original["relationship_store"]
    )
    props = catalog["property_context"]["routes"]["properties"]
    assert (
        value(access, props["location"])
        == original["sections"]["properties"]["physchem"]
    )
    assert card.to_dict() == original
    if kind == "chembl":
        retained = value(access, props["location"])
        assert retained["molecular_weight"]["value"] == 260.25
        assert retained["molecular_weight"]["unit"] == "dalton"
        assert retained["logp"]["value"] == 1.11


@pytest.mark.parametrize(
    "properties,state,raw",
    [
        ({}, "not_retained", None),
        (None, "unrecognized_container", None),
        (False, "unrecognized_container", False),
        ({"physchem": None}, "retained_null", None),
        ({"physchem": {}}, "retained_empty", {}),
        ({"physchem": False}, "unrecognized_shape", False),
        ({"physchem": 0}, "unrecognized_shape", 0),
    ],
)
def test_missing_null_empty_and_malformed_routes_keep_distinct_originals(
    properties, state, raw
):
    card = Card(meta={"entity_type": "small_molecule"})
    card.sections["properties"] = properties
    access = card.access()
    route = topics(access)["property_context"]["routes"]["properties"]
    assert route["state"] == state
    location = route["location"] or route["container_location"]
    if location is not None:
        retained = value(access, location)
        assert retained == raw and type(retained) is type(raw)
    else:
        assert state == "not_retained"


@pytest.mark.parametrize("nature", [None, "protein", "disease", "unrecognized"])
def test_other_profiles_do_not_advertise_molecule_routes(nature):
    card = Card(meta={"entity_type": nature} if nature else {})
    catalog = topics(card.access())
    assert not {"chemical_identity", "property_context"}.intersection(catalog)


def test_discovery_uses_one_capture_without_scientific_calls_and_isolated_locations(
    monkeypatch,
):
    card = molecule()
    access = card.access()
    foreign = molecule("ccd").access()

    def forbidden(*a, **k):
        raise AssertionError("Discovery must not rebuild or calculate")

    monkeypatch.setattr(Card, "to_dict", forbidden)
    monkeypatch.setattr(Card, "explore", forbidden)
    monkeypatch.setattr(Card, "knowledge_state", forbidden)
    catalog = topics(access)
    route = catalog["property_context"]["routes"]["properties"]
    before = value(access, route["location"])
    card.sections["properties"]["physchem"]["molecular_weight"]["value"] = 999
    assert value(access, route["location"]) == before
    catalog["property_context"]["routes"].clear()
    assert topics(access)["property_context"]["routes"]
    with pytest.raises(ArgumentError):
        foreign.read(route["location"])


def test_catalog_routes_do_not_invent_scientific_selectors():
    access = molecule().access()
    for key in ("chemical_identity", "property_context"):
        with pytest.raises(ArgumentError):
            access.select(key)


def test_fresh_saved_reading_preserves_the_exact_observed_catalog(tmp_path):
    access = molecule().access()
    catalog = access.catalog()
    expected = value(access, catalog.page()["node"]["location"])
    path = tmp_path / "molecule-catalog.json.gz"
    receipt = catalog.save(path, compression="gzip")
    code = """
import json, socket, sys
import sabueso
from sabueso.core.card import Card
from sabueso.core import card_literal_topics_v1
def forbidden(*a, **k):
    raise AssertionError('Original catalog reading cannot reconstruct its descriptors or Card')
socket.socket.connect = socket.create_connection = forbidden
Card.__init__ = Card.from_dict = Card.from_json = forbidden
card_literal_topics_v1.descriptors = forbidden
saved = sabueso.read_exploration(sys.argv[1], expected_digest=sys.argv[2])
assert saved.explorer.mode == 'saved'
print(json.dumps(saved.native_payload, sort_keys=True))
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(path), receipt["bundle_digest"]],
        cwd=tmp_path,
        env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    assert json.loads(result.stdout) == expected
    saved = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    current = topics(saved.explorer.access)
    assert current["property_context"] == expected["property_context"]
    assert saved.native_payload == expected
