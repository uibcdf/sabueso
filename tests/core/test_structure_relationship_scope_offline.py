"""Exact synthetic relationship scope within a real public structure context (#168)."""

import gzip
import importlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_exploration_storage import _seal
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError, StorageError


def forbidden(*a, **k):
    raise AssertionError("No network, Card reconstruction or live scientific readers")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def card():
    c = Card.from_dict(
        json.loads(
            Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text(
                encoding="utf-8"
            )
        )
    )
    c.relationship_store.store = {
        k: r
        for k, r in c.relationship_store.store.items()
        if r["predicate"] == "has_structure" and r["object_ref"] == "pdb:1SUX"
    }
    return c


def duplicate(card, **qualifiers):
    row = deepcopy(next(iter(card.relationship_store.store.values())))
    row["id"] += "_SYNTHETIC_" + str(len(card.relationship_store.store))
    row["qualifiers"].update(qualifiers)
    card.relationship_store.add(row)
    return card.relationship_store.get(row["id"])


def explanation(card, **options):
    return Deck([card]).explain(card.id, structure_ref="pdb:1SUX", **options)


def test_default_ambiguity_and_exact_public_deck_selection_keep_original_candidates(
    card,
):
    second = duplicate(card, chains=["SYNTHETIC_SECOND"])
    original = card.to_dict()
    ambiguous = explanation(card)
    assert ambiguous["status"] == "ambiguous"
    assert ambiguous["reason"] == "multiple_has_structure_relationships"
    assert ambiguous["item"] is ambiguous["group"] is None
    assert {c["relationship_id"] for c in ambiguous["candidates"]} == set(
        card.relationship_store.store
    )
    assert {m["relationship"]["id"] for m in ambiguous["members"]} == set(
        card.relationship_store.store
    )
    selected = explanation(card, relationship_id=second["id"])
    assert selected["status"] == "grouped"
    assert (
        selected["item"]["relationship_id"]
        == selected["relationship_id"]
        == second["id"]
    )
    assert selected["item"]["chains"] == ["SYNTHETIC_SECOND"]
    assert selected["rule"]["rule"] == "structure_inventory_explanation@3"
    assert selected["rule"]["parameters"]["relationship_id"] == second["id"]
    assert (
        len(selected["members"]) == 2
    )  # Never four from a reference-only cross product.
    assert card.to_dict() == original
    selected["members"][0]["relationship"]["qualifiers"].clear()
    assert card.to_dict() == original


@pytest.mark.parametrize(
    "keys", [None, ["in_complex"], ["ligands:interest"], ["substitutions"]]
)
def test_different_states_never_import_same_label_sibling_support(card, keys):
    second = duplicate(card, other_entities=[{"synthetic": "partner"}], ligands=[])
    second["qualifiers"]["mutations"] = [
        {"reference": "A", "residue": "G", "position": 1, "name": "engineered mutation"}
    ]
    second["qualifiers"]["sequence_differences"] = [
        {"reference": "A", "residue": "G", "position": 1}
    ]
    for row in card.relationship_store.store.values():
        selected = explanation(card, relationship_id=row["id"], group_by=keys)
        assert selected["status"] == "grouped"
        assert {m["relationship"]["id"] for m in selected["members"]} == {row["id"]}
        assert selected["item"]["state"]["in_complex"] == bool(
            row["qualifiers"]["other_entities"]
        )


def test_same_pdb_admitted_excluded_and_unknown_rows_keep_separate_outcomes(card):
    first = next(iter(card.relationship_store.store.values()))
    fragment = duplicate(card, coverage=0.1)
    unknown = duplicate(card)
    unknown["qualifiers"].pop("mutations", None)
    view = card.explore().view("structures")
    states = {
        item.open().native_payload["relationship_id"]: item.explain().native_payload
        for item in view.items()
    }
    assert states[first["id"]]["status"] == "grouped"
    assert states[unknown["id"]]["status"] == "not_inventoried"
    assert {m["relationship"]["id"] for m in states[first["id"]]["members"]} == {
        first["id"]
    }
    wire = view._selection._scientific.wire
    assert len(wire["exclusions"]) == 1
    assert wire["exclusions"][0]["relationship_id"] == fragment["id"]
    assert (
        wire["exclusions"][0]["explanation"]["item"]["relationship_id"]
        == fragment["id"]
    )
    assert explanation(card, relationship_id=fragment["id"])["status"] == "excluded"
    included = card.explore().view("structures", options={"include_fragments": True})
    assert len(included.items()) == 3
    assert all(
        i.explain().native_payload["relationship_id"]
        == i.open().native_payload["relationship_id"]
        for i in included.items()
    )


def test_multiple_excluded_declarations_are_not_coalesced_by_pdb(card):
    first = next(iter(card.relationship_store.store.values()))
    first["qualifiers"]["coverage"] = 0.1
    duplicate(card, coverage=0.2)
    view = card.explore().view("structures")
    assert not view.items()
    excluded = view._selection._scientific.wire["exclusions"]
    assert len(excluded) == 2
    assert {e["relationship_id"] for e in excluded} == set(
        card.relationship_store.store
    )


@pytest.mark.parametrize("bad", [False, True, 0, 1, [], {}, "", "  "])
@pytest.mark.parametrize("skip", [False, True])
def test_public_selector_validation_and_backend_refusal(card, bad, skip, monkeypatch):
    monkeypatch.setattr(Deck, "structure_inventory", forbidden)
    with pytest.raises(ArgumentError):
        explanation(card, relationship_id=bad, skip_digestion=skip)


def test_selector_requires_structure_context_and_never_falls_back_to_another_id(card):
    with pytest.raises(ArgumentError):
        Deck([card]).explain(card.id, relationship_id="REL_SYNTHETIC_UNKNOWN")
    result = explanation(card, relationship_id="REL_SYNTHETIC_UNKNOWN")
    assert result["status"] == "not_on_card"
    assert result["reason"] == "relationship_not_on_card_for_structure"
    assert result["item"] is None and result["members"] == []


def test_human_agent_and_original_source_navigation_share_exact_duplicate_rows(card):
    duplicate(card, chains=["SYNTHETIC_SECOND"])
    explorer = card.explore()
    view = explorer.view("structures")
    selection = explorer.access.select("structures", fields=[])
    page = selection.page(max_bytes=8192)
    assert page["page"]["total"] == 2
    assert {i["item_ref"] for i in page["items"]} == {i.item_ref for i in view.items()}
    assert selection.result_ref == view.result_ref
    for item in view.items():
        row = item.open().native_payload
        why = item.explain().native_payload
        assert why["item"] == row
        assert why["relationship_id"] == row["relationship_id"]
        parent = (
            item.related().filter("role", equals="structure_context").items()[0].open()
        )
        assert parent.native_payload["id"] == row["relationship_id"]
        assert why["members"] and item.support


def test_saved_duplicate_reader_is_inert_and_exact_in_independent_process(
    card, tmp_path
):
    duplicate(card, other_entities=[{"synthetic": "partner"}])
    explorer = card.explore()
    explorer.view("structures")
    selection = explorer.access.select("structures", fields=["structure_ref"])
    selection.page(max_bytes=8192)
    path = tmp_path / "duplicates.json"
    receipt = selection.save(path)
    original = path.read_bytes()
    code = r"""
import importlib,json,socket,sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a,**k):raise AssertionError('No current readers, Card construction, fixtures or network')
Card.__init__=Card.from_dict=forbidden
socket.socket.connect=socket.create_connection=forbidden
for module,names in {
 'structure_explanation':['explain_structure_inventory'],
 'structures':['structure_inventory','structures_view'],
 'card_scientific_access':['materialize'],
 'knowledge_state':['knowledge_state'],
}.items():
 m=importlib.import_module('sabueso.core.'+module)
 for n in names:setattr(m,n,forbidden)
def audit(event,args):
 if event=='open' and 'temp_data' in str(args[0]):forbidden()
sys.addaudithook(audit)
v=sabueso.read_exploration(sys.argv[1],expected_digest=sys.argv[2])
assert 'structure_inventory_explanation@3' in v.validation['verified_scientific_rules']
assert len(v.items())==2
for i in v.items():
 p=i.explain().native_payload
 assert p['relationship_id']==i.open().native_payload['relationship_id']
 assert len(p['members'])==1
 assert i.related().filter('role',equals='structure_context').items()[0].open().native_payload['id']==p['relationship_id']
s=v.explorer.access.select('structures',fields=['structure_ref'])
assert s.page(max_bytes=8192)['page']['total']==2
assert v.explorer.access.select('structures',fields=[]).page()['outcome']['status']=='not_saved'
"""
    with TemporaryDirectory(prefix="sabueso-168-reader-") as working:
        subprocess.run(
            [sys.executable, "-c", code, str(path.resolve()), receipt["bundle_digest"]],
            cwd=working,
            check=True,
        )
    again = tmp_path / "again.json"
    selection.save(again)
    assert again.read_bytes() == original == path.read_bytes()


@pytest.mark.parametrize("part", ["selected", "support", "exclusion", "rule"])
def test_resealed_duplicate_semantic_substitution_is_refused(card, tmp_path, part):
    duplicate(card, other_entities=[{"synthetic": "partner"}])
    if part == "exclusion":
        duplicate(card, coverage=0.1)
    view = card.explore().view("structures")
    path = tmp_path / "altered.json"
    view.save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    wire = next(
        v
        for v in bundle["objects"].values()
        if isinstance(v, dict)
        and v.get("context", {}).get("explanation_rule")
        == "structure_inventory_explanation@3"
        and "explanations" in v
    )
    keys = list(wire["explanations"])
    if part == "selected":
        wire["explanations"][keys[0]] = deepcopy(wire["explanations"][keys[1]])
    elif part == "support":
        wire["explanations"][keys[0]]["members"].append(
            deepcopy(wire["explanations"][keys[1]]["members"][0])
        )
    elif part == "exclusion":
        wire["exclusions"][0]["relationship_id"] = keys[0]
    else:
        wire["context"]["explanation_rule"] = "structure_inventory_explanation@999"
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(
        StorageError,
        match="historical input binding|Unsupported structural explanation rule",
    ):
        sabueso.read_exploration(path)


def test_original_scientific_capsule_keeps_v1_without_new_policy(tmp_path, monkeypatch):
    packed = Path("tests/core/data/card_exploration_science_v2.json.gz").read_bytes()
    path = tmp_path / "original.json"
    path.write_bytes(gzip.decompress(packed))
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_structure_history_v2"),
        "expected_structures",
        forbidden,
    )
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.structure_explanation_scope_v2"),
        "evaluate",
        forbidden,
    )
    saved = sabueso.read_exploration(path).explorer.view("structures")
    assert all(
        i.explain().native_payload["rule"]["rule"]
        == "structure_inventory_explanation@1"
        for i in saved.items()
    )


def test_cross_card_same_ids_and_explicit_maps_keep_exact_original_group_members(card):
    first = next(iter(card.relationship_store.store.values()))
    first["qualifiers"].update(
        mutations=[
            {
                "reference": "A",
                "residue": "G",
                "position": 1,
                "name": "engineered mutation",
            }
        ],
        sequence_differences=[{"reference": "A", "residue": "G", "position": 1}],
    )
    duplicate(card)
    # Explicitly synthetic clone, not a source claim about the other accession.
    other = Card.from_dict(card.to_dict())
    other.meta["card_id"] = "sabueso:protein:uniprot:P60174"
    other.sections["identifiers"]["uniprot"]["value"] = "P60174"
    for row in other.relationship_store.store.values():
        row["subject_ref"] = "uniprot:P60174"
        row["qualifiers"]["mutations"][0]["position"] = 2
        row["qualifiers"]["sequence_differences"][0]["position"] = 2
    deck = Deck([card, other])
    options = {
        "structure_ref": "pdb:1SUX",
        "relationship_id": first["id"],
        "group_by": ["substitutions"],
    }
    unaligned = deck.explain(card.id, **options)
    assert len(unaligned["members"]) == 2
    assert {m["card_ref"] for m in unaligned["members"]} == {card.pinned_ref()}
    aligned = deck.explain(
        card.id, **options, residue_maps={other.id: {2: 1}}, reference=card.id
    )
    assert aligned["group"]["shared"]
    assert aligned["group"]["state"]["substitutions"] == ["1G"]
    assert len(aligned["members"]) == 4
    assert len({m["relationship_ref"] for m in aligned["members"]}) == 4
    assert {m["card_ref"] for m in aligned["members"]} == {
        card.pinned_ref(),
        other.pinned_ref(),
    }


@pytest.mark.parametrize("scientific", [False, True])
def test_repeat_machine_save_preserves_root_and_complete_original_bytes(
    card, tmp_path, scientific
):
    access = card.access()
    selection = (
        access.select("structures", fields=[])
        if scientific
        else access.read(access.root_location)
    )
    first, second = tmp_path / "one.json", tmp_path / "two.json"
    a = selection.save(first)
    b = selection.save(second)
    assert a["bundle_digest"] == b["bundle_digest"]
    assert first.read_bytes() == second.read_bytes()
    saved = sabueso.read_exploration(first)
    exact = saved.explorer.access.selection(selection.selection_ref)
    third, fourth = tmp_path / "three.json", tmp_path / "four.json"
    exact.save(third)
    exact.save(fourth)
    assert third.read_bytes() == fourth.read_bytes()
    assert sabueso.read_exploration(third)._machine_ref == selection.selection_ref
