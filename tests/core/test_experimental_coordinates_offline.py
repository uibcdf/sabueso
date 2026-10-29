"""Original coordinate/reference admission; inconsistent edits are synthetic (#170)."""

import gzip
import hashlib
import importlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import pyunitwizard as puw

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_exploration_science import _result_ref, _verify_objects
from sabueso.core.card_exploration_storage import _seal
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.experimental_coordinates_v1 import scope
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient


def forbidden(*a, **k):
    raise AssertionError("No current science, Card reconstruction or network")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def original():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    card, _ = sabueso.resolve("P52270", resolver=resolver, structures="all")
    card.relationship_store.store = {
        key: r
        for key, r in card.relationship_store.store.items()
        if r["predicate"] == "has_structure" and r["object_ref"] == "pdb:1SUX"
    }
    return card.to_dict()


@pytest.fixture
def card(original):
    return Card.from_dict(deepcopy(original))


def relationship(card):
    return card.relationships("has_structure")[0]


def rcsb(card):
    return next(
        card.source_assertion_store.get(key)
        for key in relationship(card)["source_assertion_ids"]
        if card.source_assertion_store.get(key)["source"]["name"] == "RCSB PDB"
    )


def test_public_positive_matches_original_coordinates_and_has_named_support(card):
    before = card.to_dict()
    rel = relationship(card)
    (row,) = card.structures(region=[96])["items"]
    assert row["complete_chains"] == ["A", "B"]
    assert row["observed"] == rel["qualifiers"]["observed"]
    assert row["state"]["sequence"] == "reference"
    assert row["coordinate_scope"]["status"] == "comparable"
    assert row["coordinate_scope"]["projection_source_assertion_ids"] == [
        rcsb(card)["id"]
    ]
    assert row["coordinate_scope"]["structure_reference_revision"] == "not_stated"
    inventory = Deck([card]).structure_inventory(regions=[96])
    assert inventory["rule"]["rule"] == "structure_inventory@3"
    assert inventory["rule"]["parameters"]["state_rule"] == "structure_state@3"
    assert len(inventory["states"]) == 1
    assert card.to_dict() == before


@pytest.mark.parametrize("skip", [False, True])
def test_native_regions_outside_original_reference_never_become_missing_residues(
    card, skip
):
    beyond = card.get("sequence.length")["value"] + 1
    with pytest.raises(ArgumentError, match="outside.*reference"):
        card.structures(region=[beyond], skip_digestion=skip)
    with pytest.raises(ArgumentError, match="outside.*reference"):
        Deck([card]).structure_inventory(
            regions={card.id: [beyond]}, skip_digestion=skip
        )
    with pytest.raises(ArgumentError, match="present in the deck"):
        Deck([card]).structure_inventory(
            regions={"SYNTHETIC_ABSENT_CARD": [96]}, skip_digestion=skip
        )
    # Supported positions still normalize identically, including the bypass route.
    assert card.structures(region=[[95, 96]], skip_digestion=skip) == card.structures(
        region=[95, 96]
    )


@pytest.mark.parametrize(
    "change",
    [
        "target_support",
        "source_bounds",
        "target_bounds",
        "many_to_one",
        "self_map",
        "unnamed_target",
        "unknown_source",
    ],
)
def test_supplied_maps_require_original_target_scope_and_valid_correspondence(
    card, change
):
    other, _ = sabueso.resolve(
        "P60174",
        structures=["1HTI"],
        resolver=EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=FixtureRCSBClient("temp_data"),
        ),
    )
    deck = Deck([card, other])
    options = {"reference": other.id, "residue_maps": {card.id: {96: 95}}}
    valid = deck.structure_inventory(**options)
    params = valid["rule"]["parameters"]
    assert params["residue_maps"] == options["residue_maps"]
    assert params["reference_card_ref"] == other.pinned_ref()
    if change == "target_support":
        other.get("sequence.primary")["source_assertion_ids"] = ["SA_SYNTHETIC_MISSING"]
    elif change == "source_bounds":
        options["residue_maps"] = {card.id: {252: 95}}
    elif change == "target_bounds":
        options["residue_maps"] = {card.id: {96: 250}}
    elif change == "many_to_one":
        options["residue_maps"] = {card.id: {95: 95, 96: 95}}
    elif change == "self_map":
        options["residue_maps"] = {other.id: {96: 95}}
    elif change == "unnamed_target":
        options["reference"] = None
    else:
        options["residue_maps"] = {"SYNTHETIC_ABSENT_CARD": {96: 95}}
    for skip in (False, True):
        with pytest.raises(ArgumentError):
            deck.structure_inventory(**options, skip_digestion=skip)


@pytest.mark.parametrize(
    "change",
    [
        "selected_sequence",
        "missing_assertion",
        "foreign_assertion",
        "normalized_override",
        "identity_conflict",
        "revision_conflict",
    ],
)
def test_unsupported_reference_never_becomes_complete_chains_or_reference_state(
    card, change
):
    node = card.get("sequence.primary")
    source = card.source_assertion_store.get(node["source_assertion_ids"][0])
    if change == "selected_sequence":
        node["value"] = "A" * len(node["value"])
    elif change == "missing_assertion":
        node["source_assertion_ids"] = ["SA_SYNTHETIC_MISSING"]
    elif change == "foreign_assertion":
        source["subject_ref"] = "uniprot:P60174"
    elif change == "normalized_override":
        source["normalized_value"] = "A" * len(node["value"])
    elif change == "identity_conflict":
        card.quality.setdefault("conflicts", []).append(
            {"field": "sequence.primary.value"}
        )
    else:
        source.setdefault("source_metadata", {})["sequence_version"] = 0
    before = card.to_dict()
    (row,) = card.structures(region=[3])["items"]
    assert row["admission"]["status"] == "admitted"
    assert row["coordinate_scope"]["status"] == "not_computed"
    assert row["complete_chains"] is row["missing_in_region"] is row["observed"] is None
    assert row["state"]["sequence"] is row["substitutions"] is None
    native = Deck([card]).structure_inventory(regions=[3])
    assert not native["states"]
    assert native["items"][0]["substitutions_in_reference"] is None
    assert (
        native["not_inventoried"][card.id][0]["relationship_id"]
        == relationship(card)["id"]
    )
    explorer = card.explore()
    human = explorer.answer(
        "region_coverage", options={"sequence_ref": "uniprot:P52270", "region": [3]}
    )
    assert human.outcome["status"] == (
        "missing_prerequisite" if change == "identity_conflict" else "not_computed"
    )
    agent = explorer.access.select("structures", options={"region": [3]}, fields=[])
    page = agent.page(max_bytes=8192)
    if change != "identity_conflict":
        assert page["outcome"] == human.outcome
    assert (
        page["items"][0]["interpretation"]["coordinate_scope"]["status"]
        == "not_computed"
    )
    assert relationship(card)["qualifiers"]["observed"]
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "change",
    [
        "outer_subject",
        "inner_subject",
        "object",
        "record",
        "missing_original",
        "missing_features",
        "zero",
        "boolean",
        "out_of_bounds",
        "ambiguous_alignment",
        "duplicate_chain",
        "foreign_instance",
        "author_mapping_shape",
        "author_mapping_short",
        "author_mapping_boolean",
        "incomplete_instances",
        "malformed_feature",
        "chains",
        "qualifier",
        "qualifier_conflict",
    ],
)
def test_original_source_axes_and_normalized_projection_are_checked(card, change):
    source, rel = rcsb(card), relationship(card)
    value = source["asserted_value"]
    entity = value["ligand_contact_inputs"]["polymer_entities"][0]
    if change == "outer_subject":
        source["subject_ref"] = "pdb:4UNK"
    elif change == "inner_subject":
        value["subject_ref"] = "uniprot:P60174"
    elif change == "object":
        value["object_ref"] = "pdb:4UNK"
    elif change == "record":
        source["source"]["record_id"] = "4UNK"
    elif change == "missing_original":
        del value["ligand_contact_inputs"]
    elif change == "missing_features":
        del entity["polymer_entity_instances"][0]["rcsb_polymer_instance_feature"]
    elif change in ("zero", "boolean", "out_of_bounds", "ambiguous_alignment"):
        span = entity["rcsb_polymer_entity_align"][0]["aligned_regions"][0]
        if change == "ambiguous_alignment":
            entity["rcsb_polymer_entity_align"][0]["aligned_regions"].append(
                {
                    **span,
                    "ref_beg_seq_id": span["ref_beg_seq_id"] + 1,
                    "length": span["length"] - 1,
                }
            )
        else:
            span["ref_beg_seq_id"] = {
                "zero": 0,
                "boolean": True,
                "out_of_bounds": 10000,
            }[change]
    elif change == "duplicate_chain":
        entity["polymer_entity_instances"].append(
            deepcopy(entity["polymer_entity_instances"][0])
        )
    elif change == "foreign_instance":
        entity["polymer_entity_instances"][0][
            "rcsb_polymer_entity_instance_container_identifiers"
        ]["entity_id"] = "FOREIGN"
    elif change.startswith("author_mapping"):
        ids = entity["polymer_entity_instances"][0][
            "rcsb_polymer_entity_instance_container_identifiers"
        ]
        ids["auth_to_entity_poly_seq_mapping"] = {
            "author_mapping_shape": {"1": "1"},
            "author_mapping_short": ["1"],
            "author_mapping_boolean": [True]
            * entity["entity_poly"]["rcsb_sample_sequence_length"],
        }[change]
    elif change == "incomplete_instances":
        entity["polymer_entity_instances"].pop()
    elif change == "malformed_feature":
        entity["rcsb_polymer_entity_feature"].append({"type": []})
    elif change == "chains":
        rel["qualifiers"]["chains"] = ["SYNTHETIC_OTHER_CHAIN"]
    elif change == "qualifier":
        rel["qualifiers"]["observed"] = {"A": [[1, 251]]}
    else:
        rel.setdefault("qualifier_conflicts", {})["observed"] = [
            rel["qualifiers"]["observed"],
            {},
        ]
    bound = scope(card, rel)
    assert bound["status"] == "not_computed" and bound["reason"]
    (row,) = card.structures(region=[3])["items"]
    assert row["complete_chains"] is row["secondary_structure_in_region"] is None
    assert row["state"]["sequence"] is None


def test_partial_card_and_same_pdb_sibling_keep_separate_coordinate_decisions(card):
    rel = relationship(card)
    second = deepcopy(rel)
    second["id"] = "REL_SYNTHETIC_UNSUPPORTED"
    second["source_assertion_ids"] = ["SA_SYNTHETIC_MISSING"]
    card.relationship_store.add(second)
    inventory = Deck([card]).structure_inventory(regions=[96])
    assert len(inventory["items"]) == 2 and len(inventory["states"]) == 1
    good = Deck([card]).explain(
        card.id, structure_ref="pdb:1SUX", relationship_id=rel["id"], regions=[96]
    )
    bad = Deck([card]).explain(
        card.id, structure_ref="pdb:1SUX", relationship_id=second["id"], regions=[96]
    )
    assert good["status"] == "grouped"
    assert [r["relationship"]["id"] for r in good["members"]] == [rel["id"]]
    assert bad["status"] == "not_inventoried"
    assert bad["coordinate_scope"]["reason"] == "structure_source_support_unavailable"


def test_new_saved_reader_checks_original_inputs_without_current_science(
    card, tmp_path
):
    e = card.explore()
    e.answer(
        "region_coverage", options={"sequence_ref": "uniprot:P52270", "region": [96]}
    )
    selected = e.access.select(
        "structures", fields=["structure_ref"], options={"region": [96]}
    )
    path = tmp_path / "coordinates.json"
    selected.save(path)
    code = r"""
import importlib,socket,sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a,**k): raise AssertionError('No current science/Card/network/fixtures')
Card.__init__=Card.from_dict=forbidden
socket.socket.connect=socket.create_connection=forbidden
for module,names in {'structures':['structures_view','structure_inventory'],'structure_explanation':['explain_structure_inventory'],'card_scientific_access':['materialize'],'knowledge_state':['knowledge_state']}.items():
 for name in names:setattr(importlib.import_module('sabueso.core.'+module),name,forbidden)
import sabueso.mappings.rcsb_structures as mapper
mapper.map_structure_entities=forbidden
def audit(event,args):
 if event=='open' and 'temp_data' in str(args[0]): forbidden()
sys.addaudithook(audit)
v=sabueso.read_exploration(sys.argv[1])
assert 'experimental_structure_coordinates@1' in v.validation['verified_scientific_rules']
assert v.items()[0].open().native_payload['complete_chains']==['A','B']
assert v.items()[0].explain().native_payload['rule']['rule']=='structure_inventory_explanation@4'
"""
    subprocess.run(
        [sys.executable, "-c", code, str(path.resolve())], cwd=tmp_path, check=True
    )


def test_resealed_coordinate_scope_change_is_refused(card, tmp_path):
    path = tmp_path / "changed.json"
    card.explore().view("structures").save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    wire = next(
        v
        for v in bundle["objects"].values()
        if isinstance(v, dict)
        and v.get("context", {}).get("explanation_rule")
        == "structure_inventory_explanation@4"
        and "explanations" in v
    )
    wire["native_payload"]["items"][0]["coordinate_scope"][
        "projection_source_assertion_ids"
    ] = []
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


@pytest.mark.parametrize("change", ["scope", "chains", "state", "rule"])
def test_reidentified_coordinate_claim_still_requires_original_binding(card, change):
    access = card.access()
    wire = deepcopy(
        access.select("structures", options={"region": [96]})._scientific.wire
    )
    (row,) = wire["native_payload"]["items"]
    key = row["relationship_id"]
    if change == "scope":
        altered = {**row["coordinate_scope"], "projection_source_assertion_ids": []}
        row["coordinate_scope"] = wire["items"][key]["coordinate_scope"] = altered
        wire["interpretations"][key]["coordinate_scope"] = altered
    elif change == "chains":
        row["complete_chains"] = wire["items"][key]["complete_chains"] = [
            "SYNTHETIC_FOREIGN_CHAIN"
        ]
    elif change == "state":
        row["state"]["sequence"] = wire["items"][key]["state"]["sequence"] = "mutant"
    else:
        wire["native_payload"]["coordinate_rule"]["parameters"]["missing_inputs"] = (
            "assumed_comparable"
        )
    ref = _result_ref(access, wire)
    with pytest.raises(StorageError, match="historical input binding"):
        _verify_objects(
            {
                "objects": {ref: wire},
                "scientific_results": {ref: {"focal": access._focal_key}},
            },
            {access._focal_key: access},
        )


@pytest.mark.parametrize("unsupported", [False, True])
def test_packet_full_index_terms_include_exact_coordinate_dependencies(
    card, tmp_path, unsupported
):
    from sabueso.core.packets import full_rules

    if unsupported:
        card.get("sequence.primary")["value"] = (
            "A" * card.get("sequence.length")["value"]
        )
    before = card.to_dict()
    store = sabueso.KnowledgeStore(tmp_path / "packet.db")
    store.save(card)
    scopes = []
    for detail in ("full", "index"):
        packet = sabueso.compose_packet(
            sabueso.KnowledgeQuery("P52270", aspects=["structures"], detail=detail),
            card,
        )
        assert packet.to_dict()["aspect_mapping"] == "packet_aspects@14"
        rules = full_rules()["structures"]
        assert {
            "structure_state@3",
            "structure_inventory@3",
            "experimental_structure_coordinates@1",
            "ligand_site_coordinate_scope@1",
        } <= set(rules)
        if detail == "full":
            (row,) = packet.facts["structures"]["subject"]["experimental"]["items"]
            assert row["coordinate_scope"]["status"] == (
                "not_computed" if unsupported else "comparable"
            )
            assert row["state"]["sequence"] == (None if unsupported else "reference")
        else:
            assert packet.facts["structures"]["subject"]["full_rules"] == rules
        scopes.append(packet.terms("redistribution", store)["scope"])
    assert scopes[0] == scopes[1]
    included = {item["id"] for item in scopes[0]["subject"]["items"]}
    for path in ("identifiers.uniprot", "sequence.primary", "sequence.length"):
        assert set(card.get(path)["source_assertion_ids"]) <= included
    assert set(relationship(card)["source_assertion_ids"]) <= included
    assert card.to_dict() == before


@pytest.mark.parametrize("detail", ["full", "index"])
def test_explicit_packet_thirteen_keeps_original_coordinate_semantics(
    card, tmp_path, monkeypatch, detail
):
    from sabueso.core.packets import (
        KnowledgePacket,
        _facts,
        _index,
        as_stated,
        full_rules,
    )

    card.get("sequence.primary")["value"] = "A" * card.get("sequence.length")["value"]
    assert card.structures()["items"][0]["state"]["sequence"] is None
    payload = sabueso.compose_packet(
        sabueso.KnowledgeQuery("P52270", aspects=["structures"], detail=detail), card
    ).to_dict()
    # Explicit policy replay, not a purported genuine historical producer fixture.
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.experimental_coordinates_v1"),
        "scope",
        forbidden,
    )
    payload["aspect_mapping"] = "packet_aspects@13"
    value = (_facts if detail == "full" else _index)(
        "structures", card, mapping="packet_aspects@13"
    )
    if detail == "full":
        assert value["experimental"]["items"][0]["state"]["sequence"] == "reference"
        assert "coordinate_scope" not in value["experimental"]["items"][0]
    rules = full_rules("packet_aspects@13")["structures"]
    assert "structure_state@2" in rules and "structure_inventory@2" in rules
    assert "experimental_structure_coordinates@1" not in rules
    payload["facts"]["structures"]["subject"] = as_stated(value)
    original = KnowledgePacket(payload)
    store = sabueso.KnowledgeStore(tmp_path / "old-packet.db")
    store.save(card)
    pin = store.save_packet(original, "explicit_original_13")
    monkeypatch.setattr(Card, "structures", forbidden)
    assert store.load_packet(pin).to_dict() == payload
    assert (
        store.load_packet(pin).terms("redistribution", store)["aspect_mapping"]
        == "packet_aspects@13"
    )


def test_genuine_original_explanation_three_survives_without_new_scope(
    tmp_path, monkeypatch
):
    packed = Path("tests/core/data/card_structure_explanation_v3.json.gz").read_bytes()
    assert (
        hashlib.sha256(packed).hexdigest()
        == "644bf5ca5d48740e647b2b0230e7e3353c540fd906e2e806293b9f7babacac44"
    )
    raw = gzip.decompress(packed)
    assert (
        hashlib.sha256(raw).hexdigest()
        == "5a041a09d62d8ad0700db537dc5da07a29eb9dbff27f574efa5ff74912ec1802"
    )
    path = tmp_path / "original-three.json"
    path.write_bytes(raw)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    for module, names in {
        "experimental_coordinates_v1": ("scope", "view", "inventory"),
        "card_structure_history_v4": ("expected_structures", "explain_original"),
    }.items():
        for name in names:
            monkeypatch.setattr(
                importlib.import_module("sabueso.core." + module), name, forbidden
            )
    v = sabueso.read_exploration(path)
    assert len(v.items()) == 2 and len(v.exclusions) == 2
    assert v.native_payload["rule"]["rule"] == "structure_inventory@2"
    assert (
        puw.get_value(
            v.items()[0].open().native_payload["resolution"], to_unit="angstrom"
        )
        == 2
    )
    assert (
        v.items()[0].explain().native_payload["rule"]["rule"]
        == "structure_inventory_explanation@3"
    )
    assert path.read_bytes() == raw
