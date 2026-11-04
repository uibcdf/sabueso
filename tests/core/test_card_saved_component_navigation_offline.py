"""Original exact component destinations survive inert reading and tampering."""

import gzip
import hashlib
import importlib
import json
import os
import socket
import subprocess
import sys
import tempfile
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_exploration_storage import _seal
from sabueso.core.errors import StorageError


def forbidden(*a, **k):
    raise AssertionError(
        "No current Card, science, navigation producer or source acquisition"
    )


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def original():
    return json.loads(
        gzip.decompress(
            (
                Path(__file__).parent / "data/assembly_nonpolymer_live_v2.json.gz"
            ).read_bytes()
        )
    )["cases"]["1HTI"]["card"]


def role(view, key):
    return view.filter("role", equals=key).items()[0]


def journey(original):
    explorer = Card.from_dict(deepcopy(original)).explore()
    relationship = next(
        r
        for r in original["relationship_store"]
        if r.get("predicate") == "has_structure" and r.get("object_ref") == "pdb:1HTI"
    )
    location = {
        **explorer._location("relationship_store"),
        "segments": [
            {"type": "Key", "value": "relationship_store"},
            {"type": "Record", "value": relationship["id"]},
        ],
    }
    parent = explorer.inspect(locator=location)
    qualifier = next(i for i in parent.items() if i.label == "qualifiers")
    context = qualifier.related()
    question = role(context, "question")
    return explorer, question


def inert(monkeypatch):
    importlib.import_module("sabueso.core.card_assembly_access_v2")
    monkeypatch.setattr(Card, "__init__", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    for name, methods in {
        "card_context_navigation": ["related"],
        "card_structure_context_v3": ["related"],
        "card_assembly_exploration_v2": ["_materialize", "options_for_assembly"],
        "card_assembly_component_context_v1": ["assembly_related", "_emit"],
        **{f"assembly_generation_v{i}": ["generation"] for i in range(1, 6)},
    }.items():
        module = importlib.import_module("sabueso.core." + name)
        for method in methods:
            monkeypatch.setattr(module, method, forbidden)


@pytest.mark.parametrize(
    "which",
    ["question", "components", "position", "registry", "record", "source", "filter"],
)
def test_original_component_destination_reopens_without_current_producers(
    original, which, tmp_path, monkeypatch
):
    explorer, question = journey(original)
    answer = question.open()
    components = role(answer.items()[0].related(), "components").open()
    positions = components.filter("role", equals="component")
    detail = positions.items()[2].open()
    root = {"question": answer, "components": components, "position": detail}.get(which)
    if which == "registry":
        root = role(detail, "native_key").open()
    if which == "record":
        root = role(detail, "component_record").open()
    if which == "source":
        root = role(detail, "source").open()
    if which == "filter":
        root = positions
    expected = root.native_payload
    path = tmp_path / "original.json"
    receipt = root.save(path)
    assert json.loads(path.read_text())["format"] == "sabueso.card_exploration@8"
    inert(monkeypatch)
    restored = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert restored.native_payload == expected
    assert restored.validation["verifier"] == "assembly_component_navigation_binding@1"
    text, html = str(restored), restored._repr_html_()
    assert text and html
    if which == "components":
        assert "Open a position to inspect" in text
        assert "an unvisited link reports not_saved" in html
    if which == "position":
        assert "Inspect declared position" in text
        assert (
            "Read supporting source record"
            in restored.filter("role", equals="source")._repr_html_()
        )
    # Following the same retained component link reuses its saved destination.
    if which in ("components", "position"):
        reopened = (
            restored.back().items()[0].open()
            if which == "components"
            else restored.back().items()[2].open()
        )
        assert reopened.native_payload == restored.native_payload


def test_unvisited_component_destination_is_not_synthesized(
    original, tmp_path, monkeypatch
):
    explorer, question = journey(original)
    answer = question.open()
    links = answer.items()[0].related()
    path = tmp_path / "unvisited.json"
    links.save(path)
    inert(monkeypatch)
    restored = sabueso.read_exploration(path)
    assert role(restored, "components").open().outcome["status"] == "not_saved"


@pytest.mark.parametrize(
    "change",
    ["position", "boolean_index", "origin_request", "source", "scope", "null_request"],
)
def test_resealed_component_request_and_context_substitutions_are_refused(
    original, change, tmp_path
):
    explorer, question = journey(original)
    answer = question.open()
    components = role(answer.items()[0].related(), "components").open()
    detail = components.filter("role", equals="component").items()[2].open()
    path = tmp_path / "changed.json"
    detail.save(path)
    bundle = json.loads(path.read_text())
    node = bundle["views"][bundle["root_navigation_ref"]]
    if change == "position":
        node["flags"]["_component_navigation"]["request"]["component_index"] = 0
    elif change == "boolean_index":
        node["flags"]["_component_navigation"]["request"]["component_index"] = False
    elif change == "origin_request":
        node["flags"]["_component_navigation"]["link_location"]["segments"][-1][
            "value"
        ] = 0
    elif change == "source":
        node["native_payload"]["links"][-2]["support"] = []
    elif change == "null_request":
        node["flags"]["_component_navigation"] = None
    else:
        node["flags"]["_reason"] = "Distinct physical molecular copies established"
    _seal(bundle)
    path.write_text(json.dumps(bundle))
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_repeated_component_saving_preserves_original_request_and_support(
    original, tmp_path, monkeypatch
):
    explorer, question = journey(original)
    answer = question.open()
    components = role(answer.items()[0].related(), "components").open()
    detail = components.filter("role", equals="component").items()[2].open()
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    detail.save(first)
    inert(monkeypatch)
    restored = sabueso.read_exploration(first)
    restored.save(second)
    one, two = json.loads(first.read_text()), json.loads(second.read_text())
    assert one["format"] == two["format"] == "sabueso.card_exploration@8"
    assert one["objects"] == two["objects"]

    def original_views(bundle):
        # Navigation IDs are file-local; the context mode describes the active
        # reader. Neither is an original scientific or navigation assertion.
        ids = {key: value["view_ref"] for key, value in bundle["views"].items()}
        records = []
        for value in bundle["views"].values():
            record = deepcopy(value)
            for name in ("origin", "explorer_origin"):
                record[name] = ids.get(record[name], record[name])
            assert record["state"]["context"].pop("mode") in ("live", "saved")
            records.append(json.dumps(record, sort_keys=True))
        return Counter(records)

    assert original_views(one) == original_views(two)
    assert one["root_view_ref"] == two["root_view_ref"]
    assert sabueso.read_exploration(second).native_payload == detail.native_payload


def test_component_destination_reads_in_a_fresh_process_outside_checkout(
    original, tmp_path
):
    explorer, question = journey(original)
    answer = question.open()
    components = role(answer.items()[0].related(), "components").open()
    detail = components.filter("role", equals="component").items()[2].open()
    path = tmp_path / "component.json"
    receipt = detail.save(path)
    code = """
import importlib, socket, sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a, **k): raise AssertionError("No current producer or source")
socket.create_connection = forbidden
socket.socket.connect = forbidden
importlib.import_module("sabueso.core.card_assembly_access_v2")
Card.__init__ = Card.from_dict = forbidden
for name, methods in {
    "card_context_navigation": ["related"],
    "card_structure_context_v3": ["related"],
    "card_assembly_exploration_v2": ["_materialize", "options_for_assembly"],
    "card_assembly_component_context_v1": ["assembly_related", "_emit"],
    **{f"assembly_generation_v{i}": ["generation"] for i in range(1, 6)},
}.items():
    module = importlib.import_module("sabueso.core." + name)
    for method in methods: setattr(module, method, forbidden)
view = sabueso.read_exploration(sys.argv[1], expected_digest=sys.argv[2])
assert view._component_navigation["request"]["component_index"] == 2
assert view.back().items()[2].open().native_payload == view.native_payload
assert str(view) and view._repr_html_()
print("PASS fresh exact original component destination")
"""
    with tempfile.TemporaryDirectory(prefix="sabueso-component-reader-") as directory:
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        result = subprocess.run(
            [sys.executable, "-c", code, str(path.resolve()), receipt["bundle_digest"]],
            cwd=directory,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASS fresh exact original component destination" in result.stdout
        assert not (Path(directory) / "temp_data").exists()


def test_other_valid_component_cannot_replace_the_original_clicked_position(original):
    from dataclasses import replace

    from sabueso.core.card_assembly_component_context_v1 import (
        _emit,
        detail_payload,
        verify_links,
    )

    explorer, question = journey(original)
    answer = question.open()
    components = role(answer.items()[0].related(), "components").open()
    detail = components.filter("role", equals="component").items()[2].open()
    actual = detail._component_navigation
    result = answer._selection._scientific
    # A fully valid alternative native position, with its coherent payload and
    # freshly generated identity, still cannot replace the recorded click on C.
    payload = detail_payload(explorer.access, result, actual["request"]["row_key"], 0)
    forged = replace(
        _emit(explorer, payload, detail._origin, "Other valid position"),
        _component_navigation=deepcopy(actual),
    )
    with pytest.raises(StorageError, match="original requested position"):
        verify_links(forged)


def test_genuine_live_navigation_predates_and_matches_original_predicates():
    from sabueso.core.card_assembly_component_context_v1 import (
        assembly_payload,
        detail_payload,
        list_payload,
    )
    from sabueso.core.card_assembly_history_v2 import restore_result
    from sabueso.core.card_capture import _Capture
    from sabueso.core.card_exploration_assembly_v2 import verify_objects
    from sabueso.core.card_exploration_storage import _access
    from sabueso.core.snapshot import snapshot_id

    path = Path(__file__).parent / "data/assembly_component_navigation_live_v1.json.gz"
    assert (
        hashlib.sha256(path.read_bytes()).hexdigest()
        == "aae0293af668af4a2f0f71773d5e68567394fcfff81b354717e70a77f2b04b42"
    )
    capsule = json.loads(gzip.decompress(path.read_bytes()))
    assert capsule["producer"]["source"] == "63f3200f9e58fe1d4a190326b6e23fd10efa584c"
    for case in capsule["cases"].values():
        data = case["card"]
        snapshot = snapshot_id(data)
        pin = data["meta"]["card_id"] + "@" + snapshot
        capture = _Capture(data, snapshot, pin)
        ref = case["result_ref"]
        access = _access({pin: capture}, (pin,), {ref: case["wire"]}, {}, pin)
        verify_objects(
            {
                "scientific_results": {ref: {"focal": pin}},
                "objects": {ref: case["wire"]},
            },
            {pin: access},
        )
        result = restore_result(ref, case["wire"])
        key = next(
            k
            for k, row in result.wire["rows"].items()
            if row["kind"] == "assembly_generator"
        )
        assert assembly_payload(access, result, key) == case["assembly_links"]
        assert list_payload(access, result, key) == case["components"]
        assert [
            detail_payload(access, result, key, i) for i in range(len(case["details"]))
        ] == case["details"]
