"""Exact structure-to-component journeys over unchanged public originals."""

import gzip
import importlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
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
    original_links = components.native_payload
    text, html = str(components), components._repr_html_()
    assert text.count("Open a position to inspect") == 1
    assert html.count("Open a position to inspect") == 1
    assert text.count("Open exact position") == min(len(expected), 10)
    assert html.count("Open exact position") == min(len(expected), 10)
    for link in original_links["links"]:
        if "component_request" in link:
            assert link["component_request"]["reason"] not in text
    assert components.native_payload == original_links
    detail = positions.items()[0].open()
    assert detail.back() is positions
    original_detail = detail.native_payload
    detail_text, detail_html = str(detail), detail._repr_html_()
    assert "Inspect declared position" in detail_text
    assert "Inspect declared position" in detail_html
    source_links = detail.filter("role", equals="source")
    assert "Read supporting source record" in str(source_links)
    assert "Read supporting source record" in source_links._repr_html_()
    assert detail.native_payload == original_detail
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


def test_repeated_declared_labels_keep_distinct_positions(originals):
    card = Card.from_dict(deepcopy(originals["1HTI"]["card"]))
    source = next(
        s
        for s in card.source_assertion_store.store.values()
        if s["source"]["name"] == "RCSB PDB"
    )
    source["asserted_value"]["assembly_generation_inputs"]["assemblies"][0][
        "pdbx_struct_assembly_gen"
    ][0]["asym_id_list"] = ["C", "C"]
    answer = by_role(
        structure_item(card.explore(), "native").related(), "question"
    ).open()
    positions = (
        by_role(answer.items()[0].related(), "components")
        .open()
        .filter("role", equals="component")
    )
    assert len(positions.items()) == 2
    assert [
        i._entry.value["component_request"]["component_index"]
        for i in positions.items()
    ] == [0, 1]
    assert all("repeated declaration label" in i.label for i in positions.items())
    assert (
        positions.items()[0].open().native_payload["source_location"]
        != positions.items()[1].open().native_payload["source_location"]
    )


def test_conflicting_native_records_are_never_selected_silently(originals):
    card = Card.from_dict(deepcopy(originals["1HTI"]["card"]))
    source = next(
        s
        for s in card.source_assertion_store.store.values()
        if s["source"]["name"] == "RCSB PDB"
    )
    records = source["asserted_value"]["assembly_component_inputs"][
        "nonpolymer_entities"
    ][0]["nonpolymer_entity_instances"]
    records.append(deepcopy(records[0]))
    answer = by_role(
        structure_item(card.explore(), "native").related(), "question"
    ).open()
    positions = (
        by_role(answer.items()[0].related(), "components")
        .open()
        .filter("role", equals="component")
    )
    component = next(i for i in positions.items() if " · C · " in i.label)
    assert "Ambiguous native key" in component.label
    registry = by_role(component.open(), "native_key").open().native_payload
    assert (
        len([r for r in registry["references"] if r["role"] == "nonpolymer_instance"])
        == 2
    )


def test_other_unrequested_structure_keeps_missing_inputs_explicit(originals):
    explorer = Card.from_dict(deepcopy(originals["1HTI"]["card"])).explore()
    other = next(
        i for i in explorer.view("structures").items() if i.label == "pdb:1WYI"
    )
    answer = by_role(other.related(), "question").open()
    assert answer.request["options"]["structure_ref"] == "pdb:1WYI"
    assert all(i.kind != "assembly_generator" for i in answer.items())
    assert not any(
        i._entry.value["role"] == "components"
        for i in answer.items()[0].related().items()
    )


@pytest.mark.parametrize("saved", [False, True])
def test_long_descriptors_keep_ambiguous_native_state_visible(
    originals, saved, tmp_path, monkeypatch
):
    card = Card.from_dict(deepcopy(originals["1HTI"]["card"]))
    source = next(
        s
        for s in card.source_assertion_store.store.values()
        if s["source"]["name"] == "RCSB PDB"
    )
    instances = source["asserted_value"]["assembly_component_inputs"][
        "nonpolymer_entities"
    ][0]["nonpolymer_entity_instances"]
    source["asserted_value"]["assembly_generation_inputs"]["assemblies"][0][
        "pdbx_struct_assembly_gen"
    ][0]["asym_id_list"] = ["C", "C"]
    long_code = "<script>" + "X" * 200
    instances[0]["rcsb_nonpolymer_entity_instance_container_identifiers"]["comp_id"] = (
        long_code
    )
    answer = by_role(
        structure_item(card.explore(), "native").related(), "question"
    ).open()
    positions = by_role(answer.items()[0].related(), "components").open()
    original_native, original_rows = positions.native_payload, positions.rows()
    if saved:
        path = tmp_path / "long-original.json"
        positions.save(path)
        monkeypatch.setattr(Card, "__init__", forbidden)
        monkeypatch.setattr(Card, "from_dict", forbidden)
        monkeypatch.setattr(
            importlib.import_module("sabueso.core.assembly_generation_v5"),
            "generation",
            forbidden,
        )
        positions = sabueso.read_exploration(path)
    component = next(i for i in positions.items() if " · C · " in i.label)
    assert long_code in component.label
    assert "Ambiguous native key" in component.label
    text, html = str(positions), positions._repr_html_()
    assert text.count("Ambiguous native key") == 2
    assert html.count("Ambiguous native key") == 2
    assert text.count("Repeated declaration label") == 2
    assert html.count("Repeated declaration label") == 2
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert positions.native_payload == original_native
    assert positions.rows() == original_rows
    assert [
        i._entry.value["component_request"]["component_index"]
        for i in positions.filter("role", equals="component").items()
    ] == [0, 1]
    assert ("an unvisited link reports not_saved" in text) is saved
