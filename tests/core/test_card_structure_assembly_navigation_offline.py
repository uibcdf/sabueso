"""Exact original structure-to-assembly questions, including inert saved reading."""

import gzip
import hashlib
import importlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import StorageError


def forbidden(*args, **kwargs):
    raise AssertionError("No acquisition or implicit scientific evaluation")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def card():
    capsule = Path(__file__).parent / "data/assembly_live_v1.json.gz"
    data = json.loads(gzip.decompress(capsule.read_bytes()))
    card = Card.from_dict(deepcopy(data["cases"]["2V5B"]["card"]))
    card.relationship_store.store = {
        key: row
        for key, row in card.relationship_store.store.items()
        if row["predicate"] != "has_structure" or row["object_ref"] == "pdb:2V5B"
    }
    return card


def link(view, role="question"):
    return view.filter("role", equals=role).items()[0]


def entry(explorer, route):
    if route == "native":
        return explorer.view("structures").items()[0]
    parent = explorer.inspect(locator=explorer._location("relationship_store"))
    item = next(
        i for i in parent.items() if i._entry.value["predicate"] == "has_structure"
    )
    if route == "qualifiers":
        return next(i for i in item.open().items() if i.label == "qualifiers")
    return item


@pytest.mark.parametrize("route", ["native", "literal", "qualifiers"])
def test_question_is_lazy_exact_and_uses_one_shared_result(card, monkeypatch, route):
    explorer = card.explore()
    item = entry(explorer, route)
    backend = importlib.import_module("sabueso.core.assembly_generation_v4")
    native = backend.generation
    monkeypatch.setattr(backend, "generation", forbidden)
    related = item.related()
    question = link(related)
    assert "Assembly components and operations for this declaration" in str(
        related.table()
    )
    assert related._repr_html_()
    basis = question._entry.value["assembly_request"]
    options = basis["request"]["options"]
    parent = link(related, "structure_context").open().native_payload
    assert options["relationship_id"] == parent["id"]
    assert options["structure_ref"] == parent["object_ref"]
    assert options["expand_operations"] is options["expand_occurrences"] is False
    assert options["operation_budget"] > 0
    assert question._entry.value["support"] == item.support
    calls = []

    def counted(*a, **k):
        calls.append(1)
        return native(*a, **k)

    monkeypatch.setattr(backend, "generation", counted)
    card.relationship_store.store.clear()
    answer = question.open()
    assert answer.back() is question._view
    assert answer.back().back() is related
    assert related.back().back() is item._view
    assert answer.request == {**basis["request"], "topic": "assembly_generation"}
    agent = explorer.access.select("assembly_generation", options=options)
    assert agent.result_ref == answer.result_ref
    assert calls == [1]
    assert all(
        row["relationship_id"] == parent["id"]
        for row in agent._scientific.wire["rows"].values()
    )


def test_duplicate_pdb_labels_do_not_pool_relationships(card):
    row = next(
        r
        for r in card.relationship_store.store.values()
        if r["predicate"] == "has_structure"
    )
    other = deepcopy(row)
    other["id"] += "_SYNTHETIC_DUPLICATE"
    card.relationship_store.add(other)
    explorer = card.explore()
    items = explorer.view("structures").items()
    assert len(items) == 2
    answers = [link(item.related()).open() for item in items]
    assert len({answer.result_ref for answer in answers}) == 2
    assert {answer.context["options"]["relationship_id"] for answer in answers} == {
        row["id"],
        other["id"],
    }
    for answer in answers:
        assert {
            r["relationship_id"]
            for r in answer._selection._scientific.wire["rows"].values()
        } == {answer.context["options"]["relationship_id"]}


def test_literal_rule_lookalike_does_not_choose_new_codec(card, tmp_path):
    literal = card.explore()._metadata(
        {"rule": "structure_declaration_context_links@2", "synthetic": True},
        "Synthetic literal metadata",
    )
    path = tmp_path / "lookalike.json"
    literal.save(path)
    assert json.loads(path.read_text())["format"] == "sabueso.card_exploration@1"
    assert sabueso.read_exploration(path).native_payload == literal.native_payload


@pytest.mark.parametrize("role", ["subject", "source"])
def test_followed_card_endpoint_keeps_its_own_explicit_scientific_questions(
    card, tmp_path, role
):
    related = entry(card.explore(), "native").related()
    overview = link(related, role).open()
    independent = overview.explorer.answer("assembly_generation")
    assert independent.context["options"]["relationship_id"] is None
    path = tmp_path / "independent-card.json"
    independent.save(path)
    original = sabueso.read_exploration(path)
    assert original.native_payload == independent.native_payload
    assert original.back().native_payload == independent.back().native_payload


@pytest.mark.parametrize("followed", [False, True])
def test_saved_question_is_original_or_explicitly_not_saved(
    card, tmp_path, monkeypatch, followed
):
    explorer = card.explore()
    root = explorer.view("structures")
    question = link(root.items()[0].related())
    original = question.open() if followed else None
    path = tmp_path / "structure.json"
    root.save(path)
    assert json.loads(path.read_text())["format"] == "sabueso.card_exploration@6"
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(Card, "__init__", forbidden)
    monkeypatch.setattr(Card, "assembly_generation", forbidden)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_context_navigation"),
        "related",
        forbidden,
    )
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_assembly_exploration"),
        "_materialize",
        forbidden,
    )
    loaded = sabueso.read_exploration(path)
    saved_question = link(loaded.items()[0].related())
    answer = saved_question.open()
    if followed:
        assert answer.native_payload == original.native_payload
        assert answer.request == original.request
        assert answer.back().native_payload == question._view.native_payload
    else:
        assert answer.outcome["status"] == "not_saved"
    assert loaded.validation["verifier"] == "structure_assembly_navigation_binding@1"


@pytest.mark.parametrize(
    "field",
    ["structure_ref", "relationship_id", "expand_operations", "operation_budget"],
)
def test_fresh_coherent_question_substitution_is_refused(card, tmp_path, field):
    from sabueso.core.card_context_navigation import _link_view

    original = entry(card.explore(), "literal").related()
    links = deepcopy(original.native_payload["links"])
    options = links[-1]["assembly_request"]["request"]["options"]
    options[field] = {
        "structure_ref": "pdb:1SUX",
        "relationship_id": "SYNTHETIC_OTHER",
        "expand_operations": True,
        "operation_budget": None,
    }[field]
    forged = _link_view(
        original.explorer,
        links,
        original._origin,
        "Synthetic substitution",
        source_location=original.native_payload["source_location"],
        rule="structure_declaration_context_links@2",
    )
    with pytest.raises(StorageError, match="Original structure field/source/endpoint"):
        forged.save(tmp_path / "forged.json")


@pytest.mark.parametrize(
    "replacement", ["unscoped_assembly", "quaternary", "structures"]
)
def test_followed_other_valid_request_cannot_replace_exact_destination(
    card, tmp_path, replacement
):
    explorer = card.explore()
    related = entry(explorer, "native").related()
    answer = link(related).open()
    options = {**answer.request["options"], "relationship_id": None}
    other = (
        explorer.answer("assembly_generation", options=options)
        if replacement == "unscoped_assembly"
        else explorer.answer("quaternary_interpretation")
        if replacement == "quaternary"
        else explorer.view("structures")
    )
    forged = replace(other, _origin=related)
    with pytest.raises(StorageError, match="exact originating declaration"):
        forged.save(tmp_path / "other.json")


def test_legacy_missing_inputs_are_not_source_absence(tmp_path):
    data = json.loads(
        Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text()
    )
    explorer = Card.from_dict(data).explore()
    answer = link(entry(explorer, "native").related()).open()
    assert answer.items()
    assert any(
        row["status"] == "not_retained"
        for row in answer._selection._scientific.wire["rows"].values()
    )
    path = tmp_path / "legacy-input.json"
    answer.save(path)
    assert sabueso.read_exploration(path).native_payload == answer.native_payload


def test_fresh_reader_without_checkout_cards_live_navigation_or_sources(card, tmp_path):
    answer = link(entry(card.explore(), "native").related()).open()
    path = tmp_path / "original.json"
    receipt = answer.save(path)
    raw = path.read_bytes()
    code = r"""
import importlib,socket,sys
from pathlib import Path
import sabueso
from sabueso.core.card import Card
def forbidden(*a,**k):raise AssertionError('No current Card, scientific engine, live links or source inputs')
Card.__init__=Card.from_dict=Card.assembly_generation=forbidden
socket.socket.connect=socket.create_connection=forbidden
assert not Path.cwd().is_relative_to(Path(sabueso.__file__).resolve().parents[1])
for name,methods in {
 'card_context_navigation':['related'],
 'card_structure_context_v2':['related'],
 'card_assembly_exploration':['_materialize','links','_rows'],
 'assembly_generation_v4':['generation'],
 'card_assembly_access':['materialize','descriptor'],
}.items():
 module=importlib.import_module('sabueso.core.'+name)
 for method in methods:setattr(module,method,forbidden)
def audit(event,args):
 if event=='open' and isinstance(args[0],str) and 'temp_data' in args[0].replace(chr(92),'/').split('/'):forbidden()
sys.addaudithook(audit)
saved=sabueso.read_exploration(sys.argv[1],expected_digest=sys.argv[2])
assert saved.validation['verifier']=='structure_assembly_navigation_binding@1'
links=saved.back().back()
question=links.filter('role',equals='question').items()[0]
assert question.open().native_payload==saved.native_payload
assert question.open().request==saved.request
for source in links.filter('role',equals='source').items():assert source.open().native_payload['source']
parent=links.filter('role',equals='structure_context').items()[0].open()
assert parent.native_payload['id']==saved.request['options']['relationship_id']
assert str(saved) and saved._repr_html_() and str(links.table())
"""
    with TemporaryDirectory(
        prefix="sabueso-structure-assembly-reader-",
        dir=None if sys.platform == "win32" else "/tmp",
    ) as outside:
        result = subprocess.run(
            [sys.executable, "-c", code, str(path.resolve()), receipt["bundle_digest"]],
            cwd=outside,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    assert path.read_bytes() == raw


def test_genuine_original_v5_retains_its_original_codec(tmp_path, monkeypatch):
    path = Path(__file__).parent / "data/card_assembly_saved_v5.json.gz"
    packed = path.read_bytes()
    assert (
        hashlib.sha256(packed).hexdigest()
        == "7141cdff76c6dc7afbc60d093b5d7ec56fff06a5ba5b07bbcb7164d446a34923"
    )
    raw = gzip.decompress(packed)
    assert (
        hashlib.sha256(raw).hexdigest()
        == "76530c66b9025e7ccb2a85b878c68884d5508d260fd495ed56a61cf32af7c5ff"
    )
    original = tmp_path / "v5.json"
    original.write_bytes(raw)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_structure_context_v2"),
        "links",
        forbidden,
    )
    loaded = sabueso.read_exploration(original)
    assert loaded.validation["verifier"] == "assembly_generation_exploration_binding@1"
    assert loaded.native_payload["sabueso_version"] == "0.14.0+136.g3842d1a"
    assert (
        loaded.items()[0].related().native_payload["rule"]
        == "assembly_generation_links@1"
    )
    saved = tmp_path / "again.json"
    loaded.save(saved)
    assert json.loads(saved.read_text())["format"] == "sabueso.card_exploration@5"


@pytest.mark.parametrize("object_ref", ["pdb:SYNTHETIC_BAD", "alphafold:synthetic"])
def test_unsupported_question_stays_inspectable_when_saved(card, tmp_path, object_ref):
    row = next(
        r
        for r in card.relationship_store.store.values()
        if r["predicate"] == "has_structure"
    )
    row["object_ref"] = object_ref
    question = link(entry(card.explore(), "literal").related())
    assert question._entry.value["availability"] == "unsupported"
    answer = question.open()
    assert answer.outcome["status"] == "unsupported"
    assert "no assembly request is guessed" in answer.outcome["reason"]
    path = tmp_path / "unsupported.json"
    answer.save(path)
    assert sabueso.read_exploration(path).native_payload == answer.native_payload
