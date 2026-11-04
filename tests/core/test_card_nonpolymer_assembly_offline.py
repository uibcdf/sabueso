"""Explicit nonpolymer assembly exploration over unchanged public originals."""

import importlib
import socket
from copy import deepcopy

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

TOPIC = "assembly_generation"
RULE = "rcsb_assembly_generation@5"
ADAPTER = "assembly_generation_exploration@2"


def forbidden(*a, **k):
    raise AssertionError("No acquisition, recapture or current scientific evaluation")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def originals():
    return {
        pdb: sabueso.resolve(
            acc,
            resolver=EntityResolver(
                FixtureUniProtClient("temp_data"),
                rcsb_client=FixtureRCSBClient("temp_data/rcsb_nonpolymer_instances"),
            ),
            structures=[pdb],
        )[0].to_dict()
        for pdb, acc in [("1SUX", "P52270"), ("2V5B", "P52270"), ("1HTI", "P60174")]
    }


@pytest.mark.parametrize("pdb", ["1SUX", "2V5B", "1HTI"])
@pytest.mark.parametrize("first", ["human", "agent"])
def test_explicit_original_keys_share_capture_and_result(
    originals, pdb, first, monkeypatch
):
    card = Card.from_dict(deepcopy(originals[pdb]))
    before = card.to_dict()
    original_export = card.to_dict
    options = {"structure_ref": f"pdb:{pdb}", "generation_rule": RULE}
    expected = card.assembly_generation(**options)
    explorer = card.explore()
    backend = importlib.import_module("sabueso.core.assembly_generation_v5")
    original, calls = backend.generation, []

    def spy(*a, **k):
        calls.append(1)
        return original(*a, **k)

    monkeypatch.setattr(backend, "generation", spy)
    monkeypatch.setattr(card, "to_dict", forbidden)
    if first == "human":
        view = explorer.answer(TOPIC, options=options)
        selection = explorer.access.select(TOPIC, options=options)
    else:
        selection = explorer.access.select(TOPIC, options=options)
        view = explorer.answer(TOPIC, options=options)
    assert calls == [1]
    assert view.result_ref == selection.result_ref
    assert view.native_payload == expected
    assert view.context["adapter"] == ADAPTER
    assert view.request["options"] == selection._scientific.options
    assert view.request["options"]["generation_rule"] == RULE
    assert "nonpolymer instance keys" in str(view)
    assert "distinct physical molecules" in str(view)
    assert "assembly contacts remain uncomputed" in str(view)
    assert "Assembly components and operations" in view._repr_html_()
    frames = selection.page(max_bytes=65536)["items"]
    assert all(frame["adapter"] == ADAPTER for frame in frames)
    assert all(RULE in frame["interpretation"]["rule_names"] for frame in frames)
    assert original_export() == before


def test_default_and_explicit_original_rule_have_identical_requests(originals):
    explorer = Card.from_dict(deepcopy(originals["1HTI"])).explore()
    old = explorer.answer(TOPIC)
    explicit = explorer.answer(
        TOPIC, options={"generation_rule": "rcsb_assembly_generation@4"}
    )
    new = explorer.answer(TOPIC, options={"generation_rule": RULE})
    assert old.native_payload["rule"] == "rcsb_assembly_generation@4"
    assert old.result_ref == explicit.result_ref != new.result_ref
    assert old.request == explicit.request
    assert "generation_rule" not in old.request["options"]
    assert old.context["adapter"] == "assembly_generation_exploration@1"


@pytest.mark.parametrize(
    "rule",
    [
        None,
        True,
        5,
        [],
        {},
        "@5",
        "rcsb_assembly_generation@1",
        "rcsb_assembly_generation@99",
    ],
)
def test_invalid_exploration_rule_is_refused_before_scientific_work(
    originals, rule, monkeypatch
):
    explorer = Card.from_dict(deepcopy(originals["1HTI"])).explore()
    for version in (4, 5):
        monkeypatch.setattr(
            importlib.import_module(f"sabueso.core.assembly_generation_v{version}"),
            "generation",
            forbidden,
        )
    with pytest.raises(ArgumentError):
        explorer.answer(TOPIC, options={"generation_rule": rule})
    assert not explorer.access._scientific_cache


def test_exact_detail_support_and_new_navigation_rule(originals):
    explorer = Card.from_dict(deepcopy(originals["1HTI"])).explore()
    view = explorer.answer(TOPIC, options={"generation_rule": RULE})
    item = view.items()[0]
    detail, explanation, links = item.open(), item.explain(), item.related()
    assert detail.back() is view
    assert detail.native_payload == item._entry.value["item"]
    assert explanation.native_payload["request"]["generation_rule"] == RULE
    assert item.support[0]["rule_names"][0] == RULE
    assert links.native_payload["rule"] == "assembly_generation_links@3"
    assert {r["role"] for r in links.native_payload["links"]} >= {
        "source",
        "original_input",
        "structure_context",
    }
    assert all(
        r["rule"] == "assembly_generation_links@3"
        for r in links.native_payload["links"]
    )
    assert "Native keys are matched" in str(detail)
