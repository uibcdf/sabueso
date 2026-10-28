"""Exact original parents, never joins by repeated structure/component labels."""

import gzip
import hashlib
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
from sabueso.core.errors import StorageError


def forbidden(*a, **k):
    raise AssertionError("No acquisition, new source interpretation or recapture")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def card():
    return Card.from_dict(
        json.loads(
            Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text(
                encoding="utf-8"
            )
        )
    )


@pytest.fixture
def synthetic(card):
    card.relationship_store.store = {
        key: row
        for key, row in card.relationship_store.store.items()
        if row["predicate"] == "has_structure" and row["object_ref"] == "pdb:1SUX"
    }
    row = next(iter(card.relationship_store.store.values()))
    row["qualifiers"]["ligands"] = row["qualifiers"]["ligands"][:1]
    row["qualifiers"]["ligands"][0]["instances"] = row["qualifiers"]["ligands"][0][
        "instances"
    ][:1]
    return card


def parent_link(item):
    return item.related().filter("role", equals="structure_context").items()[0]


def test_public_instance_opens_its_exact_parent_and_keeps_object_card_separate(card):
    original = card.to_dict()
    explorer = card.explore()
    instances = explorer.answer("structure_ligands")
    instance = instances.items()[0]
    links = instance.related()
    parent = links.filter("role", equals="structure_context").items()[0].open()
    identifier = instance.payload_location["segments"][1]["value"]
    expected = next(
        row for row in original["relationship_store"] if row["id"] == identifier
    )
    assert parent.native_payload == expected
    location = next(
        link["candidates"][0]["location"]
        for link in links.native_payload["links"]
        if link["role"] == "structure_context"
    )
    assert location["segments"] == instance.payload_location["segments"][:2]
    assert parent.back().back().back().back() is instances
    assert "Original structure declaration · pdb:1SUX" in repr(links)
    assert links.filter("role", equals="source").items()
    separate = links.filter("role", equals="object").items()[0].open()
    assert separate.outcome["status"] == "context_not_supplied"
    assert card.to_dict() == original
    # Compact literal access can retrieve the exact destination without another Card.
    page = explorer.access.read(location).page(max_bytes=8192)
    assert page["page"]["returned"] > 0
    assert any(
        row["key"] == "id" and row["value"] == identifier for row in page["items"]
    )


def test_duplicate_labels_select_the_actual_relationship_and_original_occurrence(
    synthetic,
):
    first = next(iter(synthetic.relationship_store.store.values()))
    second = deepcopy(first)
    second["id"] += "_SYNTHETIC_OTHER_DECLARATION"
    second["qualifiers"]["synthetic_marker"] = "second retained declaration"
    synthetic.relationship_store.add(second)
    first["qualifiers"]["ligands"][0]["instances"].append(
        deepcopy(first["qualifiers"]["ligands"][0]["instances"][0])
    )
    view = synthetic.explore().answer("structure_ligands")
    assert len(view.items()) == 3
    assert len({item.item_ref for item in view.items()}) == 3
    for item in view.items():
        identifier = item.payload_location["segments"][1]["value"]
        assert parent_link(
            item
        ).open().native_payload == synthetic.relationship_store.get(identifier)


def test_conflicts_unknowns_and_caller_mutation_do_not_replace_captured_parent(
    synthetic,
):
    row = next(iter(synthetic.relationship_store.store.values()))
    row["qualifier_conflicts"] = {"synthetic": [False, None, 0, []]}
    row["qualifiers"]["synthetic_marker"] = [False, None, 0, []]
    original = deepcopy(row)
    item = synthetic.explore().answer("structure_ligands").items()[0]
    row["qualifiers"].clear()
    assert parent_link(item).open().native_payload == original
    # Foreign declarations with matching display labels never become this parent.
    assert (
        parent_link(item)._entry.value["candidates"][0]["basis"]
        == "exact_retained_node"
    )


def test_saved_parent_is_inert_and_uses_the_original_navigation(
    synthetic, tmp_path, monkeypatch
):
    view = synthetic.explore().answer("structure_ligands")
    expected = parent_link(view.items()[0]).open().native_payload
    path = tmp_path / "parent.json"
    receipt = view.save(path)
    raw = path.read_bytes()
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_context_navigation"),
        "related",
        forbidden,
    )
    for method in ("structures", "ligand_sites", "predicted_structures"):
        monkeypatch.setattr(Card, method, forbidden)
    saved = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    destination = parent_link(saved.items()[0]).open()
    assert destination.native_payload == expected
    assert destination.back().back().back().back() is saved
    assert path.read_bytes() == raw


@pytest.mark.parametrize(
    "part", ["parent", "source", "capture", "support", "membership", "origin"]
)
def test_resealed_parent_substitution_is_refused(synthetic, tmp_path, part):
    view = synthetic.explore().answer("structure_ligands")
    links = view.items()[0].related()
    path = tmp_path / "changed.json"
    view.save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    payload = next(
        value
        for value in bundle["objects"].values()
        if isinstance(value, dict)
        and value.get("rule") == "ligand_instance_context_links@1"
        and "links" in value
    )
    link = next(row for row in payload["links"] if row["role"] == "structure_context")
    if part == "parent":
        link["candidates"][0]["location"]["segments"] = []
    elif part == "source":
        payload["source_location"]["segments"][-1]["value"] = True
    elif part == "capture":
        payload["focal"] = "unretained capture"
    elif part == "support":
        link["support"] = []
    elif part == "membership":
        payload["links"].remove(link)
    else:
        # The source detail is mandatory even if the original links remain valid.
        record = next(
            record
            for record in bundle["views"].values()
            if record["view_ref"] == links.view_ref and record["flags"]["_link_panel"]
        )
        record["origin"] = None
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_independent_parent_reader_does_not_construct_a_card_or_run_live_navigation(
    synthetic, tmp_path
):
    view = synthetic.explore().answer("structure_ligands")
    path = tmp_path / "parent.json"
    view.save(path)
    code = r"""
import importlib,socket,sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a,**k):raise AssertionError('No live reconstruction/navigation/science')
Card.from_dict=forbidden;socket.socket.connect=forbidden
Card.__init__=forbidden
navigation=importlib.import_module('sabueso.core.card_context_navigation')
navigation.related=navigation._resolve_target=navigation._link=forbidden
for name in ('structures','ligand_sites','predicted_structures'):setattr(Card,name,forbidden)
def audit(event,args):
 if event=='open' and 'temp_data' in str(args[0]):forbidden()
sys.addaudithook(audit)
v=sabueso.read_exploration(sys.argv[1])
p=v.items()[0].related().filter('role',equals='structure_context').items()[0].open()
assert p.native_payload['object_ref']=='pdb:1SUX'
assert p.back().back().back().back() is v
"""
    with TemporaryDirectory(prefix="sabueso-parent-reader-") as working:
        subprocess.run(
            [sys.executable, "-c", code, str(path.resolve())], cwd=working, check=True
        )


def test_freshly_identified_parent_substitution_fails_original_binding(
    synthetic, tmp_path
):
    from sabueso.core.card_context_navigation import _link_view

    first = next(iter(synthetic.relationship_store.store.values()))
    second = deepcopy(first)
    second["id"] += "_SYNTHETIC_OTHER_PARENT"
    synthetic.relationship_store.add(second)
    view = synthetic.explore().answer("structure_ligands")
    original = view.items()[0].related()
    alternative = view.items()[1].related()
    forged_links = deepcopy(original.native_payload["links"])
    forged_links[-1] = deepcopy(alternative.native_payload["links"][-1])
    forged = _link_view(
        view.explorer,
        forged_links,
        original._origin,
        "Synthetically substituted original parent",
        source_location=view.items()[0].payload_location,
        rule="ligand_instance_context_links@1",
    )
    path = tmp_path / "coherent.json"
    # The normal writer generates all metadata/item/view identities, retained
    # state and digests. Rejection must come from original semantic parent binding.
    with pytest.raises(StorageError, match="Original ligand source/endpoint/parent"):
        forged.save(path)
    assert not path.exists()


def test_foreign_same_label_declaration_never_becomes_a_parent(synthetic):
    first = next(iter(synthetic.relationship_store.store.values()))
    foreign = deepcopy(first)
    foreign.update(id=first["id"] + "_SYNTHETIC_FOREIGN", subject_ref="uniprot:P60174")
    synthetic.relationship_store.add(foreign)
    view = synthetic.explore().answer("structure_ligands")
    assert len(view.items()) == 1
    assert parent_link(view.items()[0]).open().native_payload == first


def test_empty_instance_keeps_unknown_scope_and_exact_parent(synthetic):
    first = next(iter(synthetic.relationship_store.store.values()))
    first["qualifiers"]["ligands"][0]["instances"] = [{}]
    instance = synthetic.explore().answer("structure_ligands").items()[0]
    assert "instance unknown" in instance.label
    assert instance.open().native_payload == {}
    assert parent_link(instance).open().native_payload == first


def test_supplied_object_card_and_local_parent_keep_separate_destinations(synthetic):
    supplied = Card(
        meta={"card_id": "sabueso:structure:pdb:1SUX", "entity_type": "structure"}
    )
    instance = (
        synthetic.explore(related_cards=[supplied])
        .answer("structure_ligands")
        .items()[0]
    )
    links = instance.related()
    object_card = links.filter("role", equals="object").items()[0].open()
    parent = links.filter("role", equals="structure_context").items()[0].open()
    assert object_card.context["card_ref"] == supplied.pinned_ref()
    assert parent.context["card_ref"] == synthetic.pinned_ref()
    assert parent.native_payload == next(
        iter(synthetic.relationship_store.store.values())
    )


def test_object_revision_ambiguity_does_not_make_the_retained_parent_ambiguous(
    synthetic,
):
    one = Card(
        meta={"card_id": "sabueso:structure:pdb:1SUX", "entity_type": "structure"}
    )
    two = Card(
        meta={"card_id": "sabueso:structure:pdb:1SUX", "entity_type": "structure"}
    )
    two.unknown_stored["synthetic_revision"] = 2
    instance = (
        synthetic.explore(related_cards=[one, two])
        .answer("structure_ligands")
        .items()[0]
    )
    links = instance.related()
    object_link = links.filter("role", equals="object").items()[0]
    assert object_link._entry.value["availability"] == "ambiguous"
    assert len(object_link._entry.value["candidates"]) == 2
    parent = links.filter("role", equals="structure_context").items()[0]
    assert parent._entry.value["availability"] == "available"
    assert parent.open().context["card_ref"] == synthetic.pinned_ref()


def test_related_operation_swap_between_identical_instances_is_refused(
    synthetic, tmp_path
):
    from sabueso.core.card_exploration_storage import operation_key

    row = next(iter(synthetic.relationship_store.store.values()))
    values = row["qualifiers"]["ligands"][0]["instances"]
    values.append(deepcopy(values[0]))
    view = synthetic.explore().answer("structure_ligands")
    path = tmp_path / "swapped.json"
    view.save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    navigation = bundle["navigation"]["links"]
    a, b = (operation_key(item) for item in view.items())
    navigation[a], navigation[b] = navigation[b], navigation[a]
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError, match="different originating item"):
        sabueso.read_exploration(path)


def test_repeated_saving_and_link_detail_do_not_expand_navigation(synthetic, tmp_path):
    view = synthetic.explore().answer("structure_ligands")
    link = parent_link(view.items()[0])
    assert not link.related().items()
    parent = link.open()
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    parent.save(first)
    parent.save(second)
    assert first.read_bytes() == second.read_bytes()
    assert sabueso.read_exploration(first).native_payload == parent.native_payload


def test_genuine_old_navigation_remains_original_without_backfill(
    tmp_path, monkeypatch
):
    packed = Path("tests/core/data/card_ligand_instance_legacy_v1.json.gz").read_bytes()
    assert (
        hashlib.sha256(packed).hexdigest()
        == "918c61b5ee776c111dfad8a37b2b6232336d92d5b65c90534fb93f9c446269d1"
    )
    raw = gzip.decompress(packed)
    assert (
        hashlib.sha256(raw).hexdigest()
        == "f57aced52ec5e9b0ddd38dbe70284284f569992238e74dd5812013a01ee78df4"
    )
    path = tmp_path / "original.json"
    path.write_bytes(raw)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_ligand_instance_navigation_v1"),
        "links",
        forbidden,
    )
    saved = sabueso.read_exploration(path)
    original = saved.items()[0].related()
    assert original.native_payload["rule"] == "retained_context_links@2"
    assert not original.filter("role", equals="structure_context").items()
    assert path.read_bytes() == raw
