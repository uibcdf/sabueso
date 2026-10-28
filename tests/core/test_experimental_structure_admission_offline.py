"""Declaration scope over public data; all inconsistent variants are synthetic."""

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

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_exploration_storage import _seal
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.experimental_structure_admission_v1 import decision

PUBLIC = Path("temp_data/frozen_cards/schema_0.3.9__P52270.json")


def forbidden(*args, **kwargs):
    raise AssertionError("No network, Card reconstruction or current science")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def card():
    result = Card.from_dict(json.loads(PUBLIC.read_text(encoding="utf-8")))
    result.relationship_store.store = {
        key: row
        for key, row in result.relationship_store.store.items()
        if row["predicate"] == "has_structure" and row["object_ref"] == "pdb:1SUX"
    }
    return result


def foreign(card, subject="uniprot:P60174"):
    row = deepcopy(next(iter(card.relationship_store.store.values())))
    row.update(id="REL_SYNTHETIC_FOREIGN", subject_ref=subject)
    card.relationship_store.add(row)
    return card.relationship_store.get(row["id"])


def test_exact_subject_is_declaration_scope_without_creating_source_support(card):
    row = next(iter(card.relationship_store.store.values()))
    row["source_assertion_ids"] = ["SA_SYNTHETIC_NOT_RETAINED"]
    card.sections["sequence"] = {}
    before = card.to_dict()
    result = card.structures()
    assert len(result["items"]) == 1 and result["unplaced"] == []
    admitted = result["items"][0]["admission"]
    assert admitted["status"] == "admitted"
    assert admitted["card_subject"]["basis"] == "exact_declared_card_subject"
    assert admitted["card_subject"]["scope"] == "relationship_declaration_only"
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "nature, status",
    [
        (None, "not_applicable"),
        ("small_molecule", "not_applicable"),
        ("disease", "not_applicable"),
        ("protein", "missing_prerequisite"),
    ],
)
def test_uncomputed_admission_has_unknown_counts_live_and_saved(
    nature, status, tmp_path, monkeypatch
):
    card = Card(meta={"entity_type": nature} if nature else {})
    selection = card.access().select("structures", fields=[])
    page = selection.page(max_bytes=8192)
    assert page["outcome"]["status"] == status
    admission = page["declaration_admission"]
    assert admission["status"] == "not_evaluated"
    assert admission["reason"] == page["outcome"]["reason"]
    for key in (
        "rule",
        "inventory_rows",
        "unplaced_declarations",
        "excluded_fragments",
        "exclusions_location",
    ):
        assert admission[key] is None
    path = tmp_path / "uncomputed.json"
    selection.save(path)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_scientific_access"),
        "materialize",
        forbidden,
    )
    saved = sabueso.read_exploration(path)
    restored = saved.explorer.access.select("structures", fields=[]).page(
        max_bytes=8192
    )
    assert restored["outcome"] == page["outcome"]
    assert restored["declaration_admission"] == admission


@pytest.mark.parametrize(
    "subject", [None, "", "uniprot:P60174", "P52270", "alias:TcTIM"]
)
def test_missing_foreign_or_alias_subject_never_enters_focal_state(card, subject):
    row = foreign(card, subject)
    # Unplaced qualifier content must never reach the ordinary classifier.
    row["qualifiers"] = {"mutations": 7, "coverage": "malformed"}
    before = card.to_dict()
    view = card.structures(include_fragments=True, region=[96])
    assert [r["relationship_id"] for r in view["items"]] != [row["id"]]
    assert len(view["items"]) == len(view["unplaced"]) == 1
    unplaced = view["unplaced"][0]
    assert unplaced["relationship"] == row
    assert unplaced["admission"]["status"] == "unplaced"
    expected = (
        "relationship_subject_unavailable"
        if not subject
        else "relationship_subject_mismatch"
    )
    assert unplaced["reason"] == expected
    assert unplaced["relationship_location"]["card_ref"] == card.pinned_ref()
    assert unplaced["relationship_location"]["snapshot_id"] == card.snapshot_id()
    assert all(s["state"] == "present" for s in unplaced["source_assertions"])
    inventory = Deck([card]).structure_inventory(regions=[96])
    assert inventory["rule"]["rule"] == "structure_inventory@2"
    assert len(inventory["items"]) == 1
    assert inventory["unplaced"][card.id] == view["unplaced"]
    assert sum(len(g["structures"][card.id]) for g in inventory["states"]) == 1
    why = Deck([card]).explain(
        card.id, structure_ref="pdb:1SUX", relationship_id=row["id"]
    )
    assert why["status"] == "unplaced" and why["reason"] == expected
    assert why["item"] is why["group"] is None
    assert why["members"][0]["relationship"] == row
    assert why["admission"] == unplaced["admission"]
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "change, reason",
    [
        ("id", "canonical_card_subject_unavailable"),
        ("identifier", "canonical_card_subject_mismatch"),
        ("null", "canonical_card_identifier_unavailable"),
        ("conflict", "canonical_card_subject_conflicting"),
        ("value_conflict", "canonical_card_subject_conflicting"),
        ("nature", "not_protein"),
    ],
)
def test_uncertain_card_anchor_is_unplaced_even_with_an_equal_sequence(
    card, change, reason
):
    row = next(iter(card.relationship_store.store.values()))
    if change == "id":
        card.meta["card_id"] = "sabueso:protein:synthetic:opaque"
    elif change == "identifier":
        card.get("identifiers.uniprot")["value"] = "P60174"
    elif change == "null":
        card.get("identifiers.uniprot")["value"] = None
    elif change in ("conflict", "value_conflict"):
        card.quality.setdefault("conflicts", []).append(
            {
                "field": "identifiers.uniprot"
                + (".value" if change == "value_conflict" else "")
            }
        )
    else:
        card.meta["entity_type"] = "small_molecule"
    assert decision(card, row)["reason"] == reason
    assert card.structures()["items"] == []
    assert card.structures()["unplaced"][0]["reason"] == reason


def test_missing_identifier_stays_unplaced_and_does_not_disagree_with_navigation(card):
    from sabueso.core.card_protein_source_v1 import focal_subject

    del card.sections["identifiers"]["uniprot"]
    result = card.structures()
    assert result["items"] == []
    assert result["unplaced"][0]["reason"] == "canonical_card_identifier_unavailable"
    assert (
        result["unplaced"][0]["admission"]["card_subject"]["identifier_state"]
        == "not_retained"
    )
    assert focal_subject(card.explore()) is None


def test_equal_card_ids_cannot_overwrite_another_snapshots_admission(card):
    other = Card.from_dict(card.to_dict())
    next(iter(other.relationship_store.store.values()))["subject_ref"] = (
        "uniprot:P60174"
    )
    with pytest.raises(ArgumentError, match="distinct protein card ids"):
        Deck([card, other]).structure_inventory()


def test_foreign_fragment_is_not_conflated_with_admitted_fragment_exclusion(card):
    first = next(iter(card.relationship_store.store.values()))
    first["qualifiers"]["coverage"] = 0.1
    row = foreign(card)
    view = card.structures()
    assert not view["items"]
    assert view["excluded"] == ["pdb:1SUX"]
    assert [r["relationship_id"] for r in view["unplaced"]] == [row["id"]]
    assert len(card.structures(include_fragments=True)["items"]) == 1
    human = card.explore().view("structures")
    assert {r["relationship_id"] for r in human.exclusions} == {first["id"], row["id"]}
    assert {r["reason"] for r in human.exclusions} == {
        "fragment_or_peptide",
        "relationship_subject_mismatch",
    }


def test_human_agent_region_and_packet_share_admission_and_originals(card, tmp_path):
    row = foreign(card)
    before = card.to_dict()
    explorer = card.explore()
    view = explorer.view("structures")
    agent = explorer.access.select("structures", fields=[])
    page = agent.page(max_bytes=8192)
    assert agent.result_ref == view.result_ref
    assert page["page"]["total"] == len(view.items()) == 1
    assert page["items"][0]["interpretation"]["admission"]["status"] == "admitted"
    admission = page["declaration_admission"]
    assert admission["inventory_rows"] == admission["unplaced_declarations"] == 1
    assert admission["excluded_fragments"] == 0
    originals = explorer.access.read(admission["exclusions_location"]).page(
        max_bytes=8192
    )
    assert originals["page"]["total"] == 1
    fields = explorer.access.read(originals["items"][0]["location"]).page(
        max_bytes=8192
    )
    assert (
        next(r["value"] for r in fields["items"] if r["key"] == "status") == "unplaced"
    )
    assert view.exclusions[0]["explanation"]["members"][0]["relationship"] == row
    assert "cannot be assigned to this protein" in repr(view)
    region = explorer.answer(
        "region_coverage", options={"sequence_ref": "uniprot:P52270", "region": [96]}
    )
    assert len(region.items()) == 1
    assert region.exclusions[0]["relationship_id"] == row["id"]
    reports = []
    store = sabueso.KnowledgeStore(tmp_path / "packets.db")
    store.save(card)
    for detail in ("full", "index"):
        packet = sabueso.compose_packet(
            sabueso.KnowledgeQuery("P52270", aspects=["structures"], detail=detail),
            card,
        )
        assert packet.to_dict()["aspect_mapping"] == "packet_aspects@13"
        if detail == "full":
            native = packet.facts["structures"]["subject"]["experimental"]
            assert len(native["items"]) == 1
            assert native["unplaced"][0]["relationship"] == row
        reports.append(packet.terms("redistribution", store)["scope"])
    assert reports[0] == reports[1]
    reported = {item["id"] for item in reports[0]["subject"]["items"]}
    assert set(card.get("identifiers.uniprot")["source_assertion_ids"]) <= reported
    assert card.to_dict() == before


@pytest.mark.parametrize("detail", ["full", "index"])
def test_original_packet_12_keeps_its_declarations_and_support(
    card, tmp_path, monkeypatch, detail
):
    from sabueso.core.packets import (
        KnowledgePacket,
        _facts,
        _index,
        as_stated,
        full_rules,
    )

    foreign(card)
    packet = sabueso.compose_packet(
        sabueso.KnowledgeQuery("P52270", aspects=["structures"], detail=detail), card
    )
    payload = packet.to_dict()
    payload["aspect_mapping"] = "packet_aspects@12"
    represented = (
        _facts("structures", card, mapping="packet_aspects@12")
        if detail == "full"
        else _index("structures", card, mapping="packet_aspects@12")
    )
    if detail == "full":
        assert len(represented["experimental"]["items"]) == 2
        assert "unplaced" not in represented["experimental"]
    else:
        assert (
            represented["full_rules"] == full_rules("packet_aspects@12")["structures"]
        )
        assert "structure_inventory@1" in represented["full_rules"]
        assert "experimental_structure_admission@1" not in represented["full_rules"]
    payload["facts"]["structures"]["subject"] = as_stated(represented)
    original = KnowledgePacket(payload)
    store = sabueso.KnowledgeStore(tmp_path / "original.db")
    store.save(card)
    pin = store.save_packet(original, "synthetic_original_12")
    monkeypatch.setattr(Card, "structures", forbidden)
    loaded = store.load_packet(pin)
    assert loaded.to_dict() == payload
    assert (
        loaded.terms("redistribution", store)["aspect_mapping"] == "packet_aspects@12"
    )


def test_new_saved_reader_is_independent_and_keeps_unplaced_support(card, tmp_path):
    row = foreign(card)
    explorer = card.explore()
    view = explorer.view("structures")
    assert len(view.items()) == 1
    machine = explorer.access.select("structures", fields=[])
    machine.page(max_bytes=8192)
    path = tmp_path / "admission.json"
    machine.save(path)
    code = r"""
import importlib, socket, sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a, **k): raise AssertionError('No current science or acquisition')
Card.__init__ = Card.from_dict = forbidden
socket.socket.connect = socket.create_connection = forbidden
for module, names in {
 'structures': ['structures_view', 'structure_inventory', '_declared_structures_view'],
 'structure_explanation': ['explain_structure_inventory'],
 'card_scientific_access': ['materialize'],
 'knowledge_state': ['knowledge_state'],
}.items():
 for name in names: setattr(importlib.import_module('sabueso.core.'+module), name, forbidden)
def audit(event, args):
 if event == 'open' and 'temp_data' in str(args[0]): forbidden()
sys.addaudithook(audit)
view = sabueso.read_exploration(sys.argv[1])
assert len(view.items()) == 1
assert view.exclusions[0]['status'] == 'unplaced'
assert view.exclusions[0]['explanation']['members'][0]['relationship']['id'] == sys.argv[2]
assert view.items()[0].explain().native_payload['rule']['rule'] == 'structure_inventory_explanation@3'
assert 'experimental_structure_admission@1' in view.validation['verified_scientific_rules']
s = view.explorer.access.select('structures', fields=[])
page = s.page(max_bytes=8192)
assert page['declaration_admission']['unplaced_declarations'] == 1
assert view.explorer.access.read(page['declaration_admission']['exclusions_location']).page(max_bytes=8192)['page']['total'] == 1
"""
    subprocess.run(
        [sys.executable, "-c", code, str(path.resolve()), row["id"]],
        cwd=tmp_path,
        check=True,
    )


@pytest.mark.parametrize(
    "part", ["reason", "subject", "location", "membership", "source"]
)
def test_resealed_unplaced_scope_and_support_changes_are_refused(card, tmp_path, part):
    foreign(card)
    path = tmp_path / "changed.json"
    card.explore().view("structures").save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    wire = next(
        v
        for v in bundle["objects"].values()
        if isinstance(v, dict)
        and v.get("context", {}).get("explanation_rule")
        == "structure_inventory_explanation@3"
        and "explanations" in v
    )
    record = wire["native_payload"]["unplaced"][card.id][0]
    if part == "reason":
        record["reason"] = "not_requested"
    elif part == "subject":
        record["relationship"]["subject_ref"] = "uniprot:P52270"
    elif part == "location":
        record["relationship_location"]["segments"][-1]["value"] = "REL_SYNTHETIC_OTHER"
    elif part == "membership":
        wire["exclusions"] = []
    else:
        record["source_assertions"] = []
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError, match="identity differs|historical input binding"):
        sabueso.read_exploration(path)


def test_genuine_original_explanation_v2_survives_without_admission_policy(
    tmp_path, monkeypatch
):
    packed = Path("tests/core/data/card_structure_explanation_v2.json.gz").read_bytes()
    assert (
        hashlib.sha256(packed).hexdigest()
        == "570642999ab8dead73983418fe2545fae5b941e2049012b48227fdca219e3591"
    )
    raw = gzip.decompress(packed)
    assert (
        hashlib.sha256(raw).hexdigest()
        == "ca9ca15bca50daff28ae479175a33adf3997c777cfb28adc27d55a5564c529d3"
    )
    path = tmp_path / "original-v2.json"
    path.write_bytes(raw)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    for module, names in {
        "experimental_structure_admission_v1": ("decision", "view", "inventory"),
        "card_structure_history_v3": ("expected_structures", "explain_original"),
        "structure_explanation_scope_v3": ("evaluate",),
        "card_scientific_access": ("materialize",),
    }.items():
        for name in names:
            monkeypatch.setattr(
                importlib.import_module("sabueso.core." + module), name, forbidden
            )
    saved = sabueso.read_exploration(path)
    assert len(saved.items()) == 2
    assert saved.native_payload["rule"]["rule"] == "structure_inventory@1"
    assert "unplaced" not in saved.native_payload
    assert (
        "structure_inventory_explanation@2"
        in saved.validation["verified_scientific_rules"]
    )
    assert (
        saved.items()[0].explain().native_payload["rule"]["rule"]
        == "structure_inventory_explanation@2"
    )
    assert path.read_bytes() == raw
