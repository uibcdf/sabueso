"""Independent SDK234 sequence-change consistency and original actual-origin replay."""

import hashlib
import importlib
import importlib.resources
import json
import socket
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_card_sequence_change_original_offline import CASES
from test_card_sequence_change_original_offline import original as original

from sabueso.core.card_sequence_change_history_v1 import restore_result, verify_result
from sabueso.core.snapshot import canonical_json


def block_current(guard):
    from sabueso.core.card import Card

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Independent sequence-change reader used current science or acquisition"
        )

    for module, names in {
        "card_sequence_change_access": ("materialize", "_AnnotationInputs"),
        "card_sequence_change_selection_v1": ("evaluate", "normalize", "projection"),
        "card_sequence_change_exploration": (
            "view",
            "open_item",
            "explain",
            "display_filter",
            "display_sort",
        ),
        "card_annotation_regions_v1": ("entries", "support", "context", "link"),
        "relationship_store": ("make_derivation",),
    }.items():
        imported = importlib.import_module("sabueso.core." + module)
        for name in names:
            guard.setattr(imported, name, forbidden)
    for name in (
        "__init__",
        "from_dict",
        "knowledge_state",
        "structure_inventory",
        "explain_structure_inventory",
    ):
        if hasattr(Card, name):
            guard.setattr(Card, name, forbidden)
    for name in ("create_connection", "getaddrinfo"):
        guard.setattr(socket, name, forbidden)
    guard.setattr(socket.socket, "connect", forbidden)
    from sabueso.core.card_exploration import CardExplorer

    guard.setattr(CardExplorer, "_live_topic", forbidden)
    module = importlib.import_module("sabueso._private.argdigest.argument.item_ref")
    guard.setattr(module, "digest_item_ref", forbidden)
    for name in ("uniprot", "rcsb"):
        module = importlib.import_module("sabueso.tools.db." + name)
        for key, value in vars(module).items():
            if (
                key.startswith(("Online", "Fixture"))
                and key.endswith("Client")
                and isinstance(value, type)
            ):
                guard.setattr(value, "__init__", forbidden)


def observation_value(value):
    """The original observation codec; declared runtime quantities retain units."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, dict):
        return {key: observation_value(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [observation_value(child) for child in value]
    import pyunitwizard as puw

    assert puw.is_quantity(value)
    unit = puw.convert(str(puw.get_unit(value)), to_form="record", to_type="unit")
    number = puw.get_value(value, to_unit=unit)
    return {
        "value": number.tolist() if hasattr(number, "tolist") else number,
        "unit": unit,
    }


def hydrate_original(original, name, *, include_accesses=False):
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
            if ref not in results:
                if (
                    objects[ref]["context"]["adapter"]
                    == "sequence_change_exploration@1"
                ):
                    results[ref] = restore_result(ref, objects[ref])
                else:
                    from sabueso.core.card_exploration_science import _restore_result

                    results[ref] = _restore_result(ref, objects[ref])
            result = results[ref]
            access._scientific_cache[
                row["key"] if isinstance(row["key"], str) else tuple(row["key"])
            ] = result
        for ref, row in state["scientific_items"].items():
            access._scientific_items[ref] = results[row["result_ref"]], row["entry_key"]
        accesses[key] = access

    # capture-script.py asserts identity of these exact shared containers before
    # storing their common references. Equal bytes alone do not establish this.
    common = {
        "_captures": "captures",
        "_inputs": "inputs",
        "_objects": "objects",
        "_locations": "locations",
        "_metadata_refs": "metadata_refs",
        "_scientific_cache": "scientific_cache",
    }
    first_key = case["root_access_node"]
    first = accesses[first_key]
    for key, access in accesses.items():
        for attribute, field in common.items():
            assert (
                case["accesses"][key]["fields"][field]
                == case["accesses"][first_key]["fields"][field]
            )
            setattr(access, attribute, getattr(first, attribute))

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
        "format": "sabueso.card_exploration@31",
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
            _native_override=original.ref(
                record["runtime_state_refs"]["_native_override"]
            ),
            **deepcopy(record["flags"]),
        )
        nodes[key] = view
        return view

    for key in records:
        node(key)
    for kind, mappings in case["session_operations"].items():
        session[kind] = {key: node(value) for key, value in mappings.items()}
    return (nodes, records, accesses) if include_accesses else (nodes, records)


def binding_record(original, view, observed):
    from sabueso.core.card_exploration_sequence_change import _state

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


@pytest.mark.parametrize("name", CASES)
def test_all_original_sequence_results_are_bound_to_exact_captured_inputs(
    original, monkeypatch, name
):
    original.cache.clear()
    case, states, accesses = original_accesses(original, name)
    block_current(monkeypatch)
    ref = case["projection_result_ref"]
    root = case["root_access_node"]
    wire = deepcopy(original.ref(states[root]["objects"][ref]))
    verify_result(accesses[root], ref, wire)
    restored = restore_result(ref, wire)
    assert restored.wire is wire
    assert [entry.value["item"] for entry in restored.entries] == original.ref(
        case["source_oracle"]
    )["items"]
    assert canonical_json(restored.wire) == canonical_json(wire)


@pytest.mark.parametrize(
    "target",
    [
        "item",
        "axis",
        "support",
        "interpretation",
        "outcome",
        "producer",
        "literal-source",
    ],
)
def test_changed_sequence_scientific_bindings_are_refused(
    original, monkeypatch, target
):
    from sabueso.core.errors import StorageError

    case, states, accesses = original_accesses(original, "opaque-source")
    root = case["root_access_node"]
    ref = case["projection_result_ref"]
    wire = deepcopy(original.ref(states[root]["objects"][ref]))
    key = next(iter(wire["rows"]))
    if target == "item":
        wire["rows"][key]["item"]["description"] = "foreign"
    elif target == "axis":
        wire["rows"][key]["start"] = 3
    elif target == "support":
        wire["support"][key]["source_assertions"] = []
    elif target == "interpretation":
        wire["rows"][key]["interpretation"]["source_conflicts"] = []
        wire["rows"][key]["interpretation"]["mapping_lineage"] = (
            "invented unique feature correspondence"
        )
    elif target == "outcome":
        wire["outcome"]["status"] = "empty"
    elif target == "producer":
        wire["native_payload"]["rule"]["rule"] = "sequence_change_projection@999"
    else:
        for source in (
            accesses[root]
            ._captures[accesses[root]._focal_key]
            .data["source_assertion_store"]
        ):
            metadata = (
                source.get("source_metadata", {})
                .get("uniprot_feature", {})
                .get("source_owned")
            )
            if metadata is not None:
                metadata["values"][2] = 0
    block_current(monkeypatch)
    with pytest.raises(StorageError):
        verify_result(accesses[root], ref, wire)


@pytest.mark.parametrize("name", CASES)
def test_original_sequence_human_source_and_display_binding(
    original, monkeypatch, name
):
    from sabueso.core.card_exploration_sequence_change import (
        is_context,
        is_links,
        is_view,
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
            checked += 1
    assert checked > 0 or name == "machine-only"


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
        assert canonical_json(observation_value(view.native_payload)) == canonical_json(
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

    actual_accesses = {}
    for key, row in records.items():
        view = retained[ids[key]]
        for name, access in (
            ("access_node", view._explorer.access),
            ("selection_access_node", view._selection._access),
        ):
            original_id = row[name]
            assert actual_accesses.setdefault(original_id, access) is access
    assert len({id(access) for access in actual_accesses.values()}) == len(
        actual_accesses
    )

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
            "sequence_changes", **query["request"], skip_digestion=True
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


def test_frozen_sequence_lineage_is_bound_to_clean_sdk234(original):
    package = importlib.resources.files("sabueso.core._sequence_change_history_v1")
    source = json.loads(package.joinpath("SOURCE.json").read_text(encoding="utf-8"))
    assert source["producer_head"] == "87537f5c70f51f540bb82044fdc080bd5c78b547"
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


def independent_receive(path, directory, name, ids_path):
    from test_card_sequence_change_original_offline import MANIFEST_SHA256, Original

    import sabueso

    directory = Path(directory)
    assert (
        hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest()
        == MANIFEST_SHA256
    )
    checkout = Path(sabueso.__file__).resolve().parents[1]
    assert not Path.cwd().resolve().is_relative_to(checkout)
    data = Original(directory)
    ids = json.loads(Path(ids_path).read_text(encoding="utf-8"))
    with pytest.MonkeyPatch.context() as guard:
        block_current(guard)
        saved = sabueso.read_exploration(
            path, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
        )
        assert_saved_original(saved, data, name, ids)
    print(
        json.dumps(
            {
                "state": "PASS",
                "case": name,
                "original_views": len(data.case(name)["views"]),
                "current_science_and_acquisition": "forbidden",
                "scope": "Fresh inert receiving outside checkout; no scientific or human acceptance.",
            }
        )
    )
