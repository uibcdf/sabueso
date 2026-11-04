"""Exact structure-to-component journeys over unchanged public originals."""

import gzip
import importlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest

from sabueso.core.card import Card


def forbidden(*a, **k):
    raise AssertionError("No source acquisition or caller recapture")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def originals():
    return json.loads(
        gzip.decompress(
            (
                Path(__file__).parent / "data/assembly_nonpolymer_live_v2.json.gz"
            ).read_bytes()
        )
    )["cases"]


def by_role(view, role):
    return view.filter("role", equals=role).items()[0]


def structure_item(explorer, route, structure="1HTI"):
    if route == "native":
        return next(
            i
            for i in explorer.view("structures").items()
            if i.label == "pdb:" + structure
        )
    relationships = explorer.inspect(locator=explorer._location("relationship_store"))
    item = next(
        i
        for i in relationships.items()
        if i._entry.value["predicate"] == "has_structure"
        and i._entry.value["object_ref"] == "pdb:" + structure
    )
    return (
        next(i for i in item.open().items() if i.label == "qualifiers")
        if route == "qualifiers"
        else item
    )


@pytest.mark.parametrize("case", ["1SUX", "2V5B", "1HTI"])
@pytest.mark.parametrize("route", ["native", "literal", "qualifiers"])
def test_live_structure_component_and_source_journey_is_lazy_and_exact(
    originals, case, route, monkeypatch
):
    card = Card.from_dict(deepcopy(originals[case]["card"]))
    before = card.to_dict()
    export = card.to_dict
    explorer = card.explore()
    item = structure_item(explorer, route, case)
    backend = importlib.import_module("sabueso.core.assembly_generation_v5")
    original, calls = backend.generation, []

    def spy(*a, **k):
        calls.append(1)
        return original(*a, **k)

    monkeypatch.setattr(backend, "generation", spy)
    monkeypatch.setattr(card, "to_dict", forbidden)
    context = item.related()
    assert calls == []
    assert context.native_payload["rule"] == "structure_declaration_context_links@3"
    question = by_role(context, "question")
    assert "@5" not in question.label
    answer = question.open()
    assert answer.native_payload["rule"] == "rcsb_assembly_generation@5"
    selected = explorer.access.select(
        "assembly_generation", options=answer.request["options"]
    )
    assert selected.result_ref == answer.result_ref and calls == [1]
    links = answer.items()[0].related()
    components = by_role(links, "components").open()
    assert components.back().native_payload == links.native_payload
    positions = components.filter("role", equals="component")
    expected = answer.items()[0]._entry.value["item"]["component_bindings"]
    assert len(positions.items()) == len(expected)
    assert [
        i._entry.value["component_request"]["component_index"]
        for i in positions.items()
    ] == list(range(len(expected)))
    detail = positions.items()[0].open()
    assert detail.back() is positions
    binding = by_role(detail, "component_binding").open()
    assert binding.native_payload == expected[0]
    source = by_role(detail, "source").open()
    assert source.native_payload["id"] in {
        r["id"] for r in answer.items()[0].support[0]["source_assertions"]
    }
    assert "physical copies" in str(components)
    assert "No sources are queried" in detail._repr_html_()
    assert calls == [1] and export() == before


def test_native_nonpolymer_record_is_separate_from_author_label_and_neighbors(
    originals,
):
    explorer = Card.from_dict(deepcopy(originals["1HTI"]["card"])).explore()
    answer = by_role(
        explorer.view("structures").items()[0].related(), "question"
    ).open()
    components = by_role(answer.items()[0].related(), "components").open()
    component = next(
        i
        for i in components.filter("role", equals="component").items()
        if " · C · " in i.label
    )
    assert "PGA" in component.label and "Native key matched" in component.label
    detail = component.open()
    registry = by_role(detail, "native_key").open().native_payload
    assert (
        registry["asym_id"] == "C"
        and registry["basis"] == "native_nonpolymer_instance_identifier"
    )
    assert {r["role"] for r in registry["references"]} >= {
        "nonpolymer_instance",
        "ligand_neighbor_reference",
    }
    assert any(
        i._entry.value["role"] == "component_record" and "Nonpolymer record" in i.label
        for i in detail.items()
    )


def test_direct_public_defaults_keep_original_interpretation(originals):
    explorer = Card.from_dict(deepcopy(originals["1HTI"]["card"])).explore()
    assert (
        explorer.answer("assembly_generation").native_payload["rule"]
        == "rcsb_assembly_generation@4"
    )
    answer = by_role(
        explorer.view("structures").items()[0].related(), "question"
    ).open()
    assert answer.request["options"]["generation_rule"] == "rcsb_assembly_generation@5"
