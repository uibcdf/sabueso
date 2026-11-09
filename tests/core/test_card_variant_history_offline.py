"""Independent SDK230 expectations over immutable observed variant tissue data."""

import hashlib
import importlib
import importlib.resources
import json
import os
import socket
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_card_variant_original_offline import CASES
from test_card_variant_original_offline import original as original

from sabueso.core.card_variant_history_v1 import restore_result, verify_result
from sabueso.core.snapshot import canonical_json


def hydrate_original(original, name):
    """Restore actual observed objects and origins; execute no archived code."""
    from sabueso.core.card_access import AccessSelection, _Entry, _handle
    from sabueso.core.card_exploration import CardView
    from sabueso.core.card_exploration_storage import _access, _explorer
    from sabueso.core.card_navigation_preview_v1 import metadata

    case, states, inputs = original_accesses(original, name)
    accesses, results = {}, {}
    for key, state in states.items():
        objects = {
            ref: deepcopy(original.ref(value))
            for ref, value in state["objects"].items()
        }
        access = _access(
            inputs[key]._captures,
            inputs[key]._inputs,
            objects,
            deepcopy(state["locations"]),
            state["focal"],
        )
        access._mode, access._nonce = "live", state["nonce"]
        access._metadata_refs = set(state["metadata_refs"])
        access._cursors = deepcopy(state["cursors"])
        access._tokens = {
            (row["selection_ref"], row["offset"]): row["token"]
            for row in state["tokens"]
        }
        for row in state["scientific_cache"]:
            ref = row["result_ref"]
            result = results.setdefault(ref, restore_result(ref, objects[ref]))
            access._scientific_cache[tuple(row["key"])] = result
        for ref, row in state["scientific_items"].items():
            access._scientific_items[ref] = results[row["result_ref"]], row["entry_key"]
        accesses[key] = access

    def selection(access, spec):
        return AccessSelection(
            access,
            spec["result_ref"],
            spec["selection_ref"],
            tuple(
                _Entry(
                    deepcopy(row["location"]),
                    row["key"],
                    original.ref(row["value_ref"]),
                    row["ordinal"],
                )
                for row in spec["entries"]
            ),
            spec["context_location"],
            spec["request"]["target"],
            spec["request"]["operation"],
            spec["slice"],
            results.get(spec["scientific_result_ref"]),
            tuple(spec["request"]["fields"]),
            spec["outcome_override"],
        )

    for key, state in states.items():
        accesses[key]._selections = {
            ref: selection(accesses[key], spec)
            for ref, spec in state["selections"].items()
        }
    session = {
        "views": {},
        "links": {},
        "explanations": {},
        "presentation_metadata": metadata(),
        "format": "sabueso.card_exploration@29",
        "original_nodes": {},
    }
    records, nodes = original.nodes(case), {}

    def node(key):
        if key is None:
            return None
        if key in nodes:
            return nodes[key]
        record = records[key]
        observed = record["observation"]
        explorer = _explorer(accesses[record["access_node"]], session)
        explorer._origin = node(record["explorer_origin_node"])
        selected = selection(
            accesses[record["selection_access_node"]], observed["selection"]
        )
        by_ref = {
            _handle(
                "XI_", {"result_ref": selected.result_ref, "location": entry.location}
            ): entry
            for entry in selected._entries
        }
        view = CardView(
            explorer,
            selected,
            tuple(by_ref[row["item_ref"]] for row in observed["items"]),
            _origin=node(record["origin_node"]),
            _native_override=original.ref(observed["native_payload_ref"]),
            **deepcopy(record["flags"]),
        )
        nodes[key] = view
        return view

    for key in records:
        node(key)
    for kind, mappings in case["session_operations"].items():
        session[kind] = {key: node(value) for key, value in mappings.items()}
    return nodes, records


def binding_record(original, view, observed):
    from sabueso.core.card_exploration_variant import _state

    state = {
        "context": observed["context"],
        "schema": observed["schema"],
        "coverage": view.coverage,
        "items": {},
    }
    actual = _state(view)["items"]
    # Original observations list displayed rows; saved state deliberately keeps
    # the full underlying selection, including display-filtered occurrences.
    state["items"] = actual
    for item in observed["items"]:
        expected = {
            "label": item["label"],
            "kind": item["kind"],
            "support": original.ref(item["support_ref"]),
            "cells": {
                key: {
                    **{
                        field: value
                        for field, value in cell.items()
                        if field != "support_ref"
                    },
                    "support": original.ref(cell["support_ref"]),
                }
                for key, cell in item["cells"].items()
            },
        }
        assert canonical_json(actual[item["item_ref"]]) == canonical_json(expected)
        state["items"][item["item_ref"]] = expected
    return {
        "native_payload": original.ref(observed["native_payload_ref"]),
        "state": state,
    }


def block_current(guard):
    """No current Card, science, source client, mapping or scientific digester."""
    from sabueso.core.card import Card
    from sabueso.core.card_exploration import CardExplorer

    names = {
        "card_variant_access": ("materialize", "_support"),
        "card_variant_selection_v1": ("evaluate", "normalize", "projection"),
        "card_variant_exploration": (
            "view",
            "open_item",
            "explain",
            "links",
            "follow",
            "display_filter",
            "display_sort",
        ),
        "comparative_explanation": (
            "explain_variant_tissue_usage",
            "explain_isoform_tissue_usage",
            "_scoped_explanation",
        ),
        "scoped_tissue_usage": ("variant_view", "isoform_view", "check_arguments"),
        "tissue_usage": (
            "variant_tissue_usage_view",
            "isoform_tissue_usage_view",
            "tissue_terms",
        ),
    }
    modules = {key: importlib.import_module("sabueso.core." + key) for key in names}

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Independent variant reading used current science or acquisition"
        )

    guard.setattr(CardExplorer, "_live_topic", forbidden)

    for name in (
        "__init__",
        "from_dict",
        "variant_tissue_usage",
        "isoform_tissue_usage",
        "explain_variant_tissue_usage",
        "explain_isoform_tissue_usage",
        "knowledge_state",
    ):
        guard.setattr(Card, name, forbidden)
    for name in ("create_connection", "getaddrinfo"):
        guard.setattr(socket, name, forbidden)
    guard.setattr(socket.socket, "connect", forbidden)
    for key, functions in names.items():
        for name in functions:
            guard.setattr(modules[key], name, forbidden)
    for key in ("threshold", "usage_rule", "item_ref"):
        module = importlib.import_module("sabueso._private.argdigest.argument." + key)
        guard.setattr(module, "digest_" + key, forbidden)
    module = importlib.import_module("sabueso.mappings.gtex")
    guard.setattr(module, "tissue_key", forbidden)
    for name in ("uniprot", "gnomad", "gtex"):
        module = importlib.import_module("sabueso.tools.db." + name)
        for key, value in vars(module).items():
            if (
                key.startswith(("Online", "Fixture"))
                and key.endswith("Client")
                and isinstance(value, type)
            ):
                guard.setattr(value, "__init__", forbidden)


def original_accesses(original, name):
    case = original.case(name)
    states = original.accesses(case)
    accesses = {}
    for key, state in states.items():
        captures = {
            ref: SimpleNamespace(
                pin=capture["pin"],
                snapshot=capture["snapshot"],
                data=deepcopy(original.ref(capture["data_ref"])),
            )
            for ref, capture in state["captures"].items()
        }
        accesses[key] = SimpleNamespace(
            _captures=captures, _inputs=state["inputs"], _focal_key=state["focal"]
        )
    return case, states, accesses


def test_frozen_variant_lineage_matches_original_source(original):
    package = importlib.resources.files("sabueso.core._variant_history_v1")
    source = json.loads(package.joinpath("SOURCE.json").read_text(encoding="utf-8"))
    assert source["producer_head"] == "c5b573b15f61619ff0a3f52ba3c3275807fcd8ba"
    assert set(source["frozen_files"]) == {
        p.name for p in package.iterdir() if p.name.endswith(".py")
    }
    for name, digest in source["frozen_files"].items():
        assert hashlib.sha256(package.joinpath(name).read_bytes()).hexdigest() == digest
    before = json.loads(
        (original.directory / "source-before.json").read_text(encoding="utf-8")
    )
    for name, digest in {
        **source["original_files"],
        **source["reused_frozen_files"],
    }.items():
        assert before[name] == digest


@pytest.mark.parametrize("name", CASES)
def test_all_original_native_results_have_independent_input_scope_binding(
    original, monkeypatch, name
):
    original.cache.clear()
    case, states, accesses = original_accesses(original, name)
    block_current(monkeypatch)
    seen = set()
    for key, state in states.items():
        for row in state["scientific_cache"]:
            ref = row["result_ref"]
            if ref in seen:
                continue
            seen.add(ref)
            wire = deepcopy(original.ref(state["objects"][ref]))
            assert canonical_json(wire["context"]["options"]) == row["key"][2]
            verify_result(accesses[key], ref, wire)
            restored = restore_result(ref, wire)
            assert restored.wire is wire
            assert [entry.key for entry in restored.entries] == [
                f"{restored.options['mode']}:{i}" for i in range(len(wire["rows"]))
            ]
    assert len(seen) == len(original.ref(case["native_oracles"]))


@pytest.mark.parametrize("name", CASES)
def test_every_actual_original_human_source_and_machine_view_is_independent(
    original, monkeypatch, name
):
    from sabueso.core.card_exploration_variant import (
        is_context,
        is_links,
        is_view,
        verify_literal_view,
        verify_view,
    )

    original.cache.clear()
    nodes, records = hydrate_original(original, name)
    block_current(monkeypatch)
    checked = 0
    for key, view in nodes.items():
        observed = records[key]["observation"]
        assert view.view_ref == observed["view_ref"]
        assert str(view) == observed["text"]
        assert view._repr_html_() == observed["html"]
        if is_view(view) or is_context(view) or is_links(view):
            verify_view(view, binding_record(original, view, observed))
        else:
            verify_literal_view(view, binding_record(original, view, observed))
        checked += 1
    assert checked == len(records)


def original_navigation_ids(nodes):
    session = next(iter(nodes.values()))._explorer._session
    ids = {key: "N" + str(index) for index, key in enumerate(session["views"])}
    return {key: ids[id(view)] for key, view in nodes.items()}


def assert_saved_original(saved, original, name, ids):
    """Every actual origin, complete cells and finite original agent pages."""
    from sabueso.core.card_exploration_storage import _cell_record

    case = original.case(name)
    records = original.nodes(case)
    retained = saved._explorer._session["original_nodes"]
    assert set(ids) == set(records)
    for key, row in records.items():
        view = retained[ids[key]]
        observed = row["observation"]
        assert view.view_ref == observed["view_ref"]
        assert view._explorer.access._focal_key == observed["focal"]
        assert view._origin is (
            None if row["origin_node"] is None else retained[ids[row["origin_node"]]]
        )
        assert view._explorer._origin is (
            None
            if row["explorer_origin_node"] is None
            else retained[ids[row["explorer_origin_node"]]]
        )
        assert canonical_json(view.native_payload) == canonical_json(
            original.ref(observed["native_payload_ref"])
        )
        assert canonical_json(view.request) == canonical_json(observed["request"])
        assert view.schema == observed["schema"]
        assert (view.explorer is not None) == observed["explorer_available"]
        items = list(view.items())
        assert [item.item_ref for item in items] == [
            item["item_ref"] for item in observed["items"]
        ]
        for item, recorded in zip(items, observed["items"], strict=True):
            assert item.label == recorded["label"] and item.kind == recorded["kind"]
            assert canonical_json(item.support) == canonical_json(
                original.ref(recorded["support_ref"])
            )
            for column, cell in item.cells.items():
                expected = {
                    field: value
                    for field, value in recorded["cells"][column].items()
                    if field != "support_ref"
                }
                expected["support"] = original.ref(
                    recorded["cells"][column]["support_ref"]
                )
                assert canonical_json(
                    _cell_record(item, column, cell)
                ) == canonical_json(expected)

    states = original.accesses(case)
    original_locations = states[case["root_access_node"]]["locations"]

    def locations(items, lookup):
        rows = deepcopy(items)
        for row in rows:
            for node in (row, *row.get("cells", {}).values()):
                for field in (
                    "location",
                    "payload_location",
                    "value_location",
                    "interpretation_location",
                    "support_location",
                    "context_location",
                ):
                    location = node.get(field)
                    if isinstance(location, dict) and location.get("kind") == "lookup":
                        node[field] = lookup(location)
        return rows

    for query in case["queries"]:
        selection = saved.explorer.access.select(
            "variants", **query["request"], skip_digestion=True
        )
        assert (
            selection.selection_ref == query["selection_ref"]
            and selection.count == query["count"]
        )
        cursor = None
        for ref in query["pages"]:
            recorded = original.ref(ref)
            page = selection.page(
                limit=recorded["page"]["limit"],
                max_bytes=recorded["page"]["max_bytes"],
                cursor=cursor,
                skip_digestion=True,
            )
            assert canonical_json(
                locations(
                    page["items"], lambda loc: saved.explorer.access._resolve(loc)[1]
                )
            ) == canonical_json(
                locations(
                    recorded["items"],
                    lambda loc: original_locations[loc["location_ref"]],
                )
            )
            assert page["page"]["offset"] == recorded["page"]["offset"]
            assert page["page"]["total"] == recorded["page"]["total"]
            cursor = page["page"]["next_cursor"]
        assert cursor is None


def independent_receive(path, directory, name, ids_path):
    from test_card_variant_original_offline import MANIFEST_SHA256, Original

    import sabueso

    assert (
        not Path.cwd()
        .resolve()
        .is_relative_to(Path(sabueso.__file__).resolve().parents[1])
    )
    directory = Path(directory)
    assert (
        hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest()
        == MANIFEST_SHA256
    )
    original = Original(directory)
    for relative, record in original.manifest["files"].items():
        member = directory / relative
        assert (
            member.resolve().is_relative_to(directory.resolve())
            and not member.is_symlink()
        )
        assert member.stat().st_size == record["bytes"]
        with member.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == record["sha256"]
    with pytest.MonkeyPatch.context() as guard:
        block_current(guard)
        saved = sabueso.read_exploration(
            path, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
        )
        assert (
            saved.validation["verifier"]
            == "variant_tissue_context_exploration_binding@1"
        )
        assert_saved_original(
            saved,
            original,
            name,
            json.loads(Path(ids_path).read_text(encoding="utf-8")),
        )


@pytest.mark.parametrize("name", CASES)
def test_all_actual_original_variant_files_receive_independently(
    original, monkeypatch, tmp_path, name
):
    import sabueso

    original.cache.clear()
    nodes, _ = hydrate_original(original, name)
    root = nodes[original.case(name)["named_views"]["root"]]
    ids = original_navigation_ids(nodes)
    path = tmp_path / "original.json.gz"
    with monkeypatch.context() as guard:
        block_current(guard)
        root.save(
            path,
            compression="gzip",
            max_encoded_bytes=None,
            max_decoded_bytes=None,
            max_logical_bytes=None,
        )
        saved = sabueso.read_exploration(
            path, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
        )
        assert (
            saved.validation["verifier"]
            == "variant_tissue_context_exploration_binding@1"
        )
        assert_saved_original(saved, original, name, ids)
    if name in (
        "public-variants",
        "public-isoforms",
        "threshold-integer-first",
        "variants-support-missing",
    ):
        ids_path = tmp_path / "ids.json"
        ids_path.write_text(json.dumps(ids), encoding="utf-8")
        code = "import sys; sys.path.insert(0,sys.argv[5]); from test_card_variant_history_offline import independent_receive; independent_receive(*sys.argv[1:5])"
        with tempfile.TemporaryDirectory(
            prefix="sabueso-variant-independent-", dir="/tmp"
        ) as cwd:
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            received = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    code,
                    str(path.resolve()),
                    str(original.directory.resolve()),
                    name,
                    str(ids_path.resolve()),
                    str(Path(__file__).resolve().parent),
                ],
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=600,
            )
        assert received.returncode == 0, received.stdout + received.stderr
        assert not received.stderr
