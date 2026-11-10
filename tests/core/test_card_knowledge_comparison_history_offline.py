"""Independent SDK243 comparison predicates with every current science route forbidden."""

import importlib
import json
import socket
from copy import deepcopy
from types import SimpleNamespace

import pytest
from test_card_knowledge_comparison_original_offline import CASES
from test_card_knowledge_comparison_original_offline import original as original

from sabueso.core.card_access import _handle
from sabueso.core.card_knowledge_comparison_history_v1 import (
    ADAPTER,
    restore_result,
    verify_result,
)
from sabueso.core.errors import StorageError
from sabueso.core.snapshot import canonical_json


def block_current(guard):
    """Preload current consumers before temporary guards, preserving later LIVE imports."""
    from sabueso.core.card import Card

    def forbidden(*args, **kwargs):
        raise AssertionError("Original comparison used current science or acquisition")

    targets = {
        "card_knowledge_comparison_access": ("materialize",),
        "card_knowledge_diff_v2": ("compare",),
        "knowledge_state": ("knowledge_state",),
        "source_assertion_store": ("assertion_value", "make_source_assertion"),
        "relationship_store": ("make_derivation",),
        "card_knowledge_comparison_exploration": (
            "view",
            "open_item",
            "explain",
            "links",
            "display_filter",
            "display_sort",
        ),
        "card_protein_context_access": ("materialize",),
        "card_protein_context_exploration": ("view",),
        "card_protein_context_selection_v1": ("evaluate", "normalize", "projection"),
        "card_sequence_change_access": ("materialize",),
        "card_sequence_change_exploration": ("view",),
        "card_variant_access": ("materialize",),
        "card_variant_exploration": ("view",),
        "card_disease_association_access": ("materialize",),
        "card_disease_association_exploration": ("view",),
        "card_molecule_activity_access": ("materialize",),
        "card_molecule_activity_exploration": ("view",),
    }
    modules = {
        name: importlib.import_module("sabueso.core." + name) for name in targets
    }
    from sabueso import enrichers
    from sabueso.core import curation
    from sabueso.mappings import uniprot

    for name, attributes in targets.items():
        for attribute in attributes:
            guard.setattr(modules[name], attribute, forbidden)
    for name in ("knowledge_areas", "count_by_area", "not_queried_details_by_area"):
        guard.setattr(enrichers, name, forbidden)
    guard.setattr(curation, "ITEM_IDENTITY", None)
    guard.setattr(uniprot, "STATED_FIELDS", frozenset({"current.unavailable"}))
    guard.setattr(uniprot, "STATED_PREDICATES", frozenset({"current_unavailable"}))
    for name in ("__init__", "from_dict", "compare_knowledge", "knowledge_state"):
        guard.setattr(Card, name, forbidden)
    guard.setattr(socket, "create_connection", forbidden)
    guard.setattr(socket.socket, "connect", forbidden)


def root_result(original, name):
    original.cache.clear()
    case = original.case(name)
    row = case["accesses"][case["root_access_node"]]
    captures = original.ref(row["fields"]["captures"])
    access = SimpleNamespace(
        _focal_key=row["focal"],
        _inputs=original.ref(row["fields"]["inputs"]),
        _captures={
            key: SimpleNamespace(
                pin=value["pin"],
                snapshot=value["snapshot"],
                data=deepcopy(original.ref(value["data_ref"])),
            )
            for key, value in captures.items()
        },
    )
    objects = original.ref(row["fields"]["objects"])
    ref = case["projection_result_ref"]
    return case, access, ref, original.ref(objects[ref])


@pytest.mark.parametrize("name", CASES)
def test_all_original_native_results_and_row_order_without_current_science(
    original, monkeypatch, name
):
    case, access, ref, wire = root_result(original, name)
    block_current(monkeypatch)
    verify_result(access, ref, wire)
    restored = restore_result(ref, wire)
    assert canonical_json(restored.wire) == canonical_json(wire)
    if case["named_views"]:
        node = original.nodes(case)[case["named_views"]["root"]]
        entries = node["observation"]["selection"]["entries"]
    else:
        root = case["accesses"][case["root_access_node"]]
        selections = original.ref(root["fields"]["selections"])
        entries = selections[case["queries"][0]["selection_ref"]]["entries"]
    assert [entry.key for entry in restored.entries] == [
        entry["key"] for entry in entries
    ]
    assert [canonical_json(entry.value) for entry in restored.entries] == [
        canonical_json(original.ref(entry["value_ref"])) for entry in entries
    ]


@pytest.mark.parametrize(
    "alteration",
    [
        "typed-value",
        "quantity-unit",
        "candidate",
        "map-pair",
        "support",
        "row-label",
        "state",
        "relationship",
    ],
)
def test_coherently_rehashed_native_or_projection_changes_are_refused(
    original, monkeypatch, alteration
):
    name = {
        "typed-value": "zero-false",
        "quantity-unit": "quantity-units",
        "candidate": "ambiguous-forward",
        "map-pair": "complete-map",
        "support": "missing-source",
        "row-label": "same-rendered-state-labels",
        "state": "same-rendered-state-labels",
        "relationship": "relationship-direction-channels",
    }[alteration]
    _, access, old_ref, wire = root_result(original, name)
    wire = deepcopy(wire)
    native = wire["native_payload"]
    if alteration == "typed-value":
        native["fields"]["annotations.taxon_id"]["self"] = False
    elif alteration == "quantity-unit":
        native["fields"]["sequence.molecular_weight"]["self"]["unit"] = "gram"
    elif alteration == "candidate":
        native["fields"]["features_positional.active_site"]["ambiguous"][0][
            "other"
        ].pop()
    elif alteration == "map-pair":
        native["residue_map"]["pairs"][0][1] = 1
    elif alteration == "support":
        field = native["fields"]["annotations.taxon_id"]
        field["support"]["self"]["missing_source_assertion_ids"] = []
    elif alteration == "row-label":
        next(iter(wire["rows"].values()))["label"] = "synthetic altered display"
    elif alteration == "state":
        native["knowledge_states"][0]["self"] = []
    else:
        native["relationships"]["interacts_with"]["self_records"][0]["qualifiers"][
            "original"
        ] = 0
    new_ref = _handle(
        "XR_",
        {"adapter": ADAPTER, "options": wire["context"]["options"], "native": native},
    )

    def rebind(value):
        if isinstance(value, list):
            return [rebind(item) for item in value]
        if isinstance(value, dict):
            return {
                key: new_ref
                if key == "result_ref" and item == old_ref
                else rebind(item)
                for key, item in value.items()
            }
        return value

    wire = rebind(wire)
    block_current(monkeypatch)
    with pytest.raises(StorageError):
        verify_result(access, new_ref, wire)


def test_frozen_source_manifest_names_actual_clean_producer():
    from importlib.resources import files

    source = json.loads(
        files("sabueso.core._knowledge_comparison_history_v1")
        .joinpath("SOURCE.json")
        .read_text()
    )
    assert source["producer_head"] == "f6d8e4a3e57944ebe1ab4ab838600870ed720e2b"
    assert source["producer_version"] == "0.14.0+243.gf6d8e4a"
    assert (
        source["capsule_sha256"]
        == "3a656731e69d1f1a5f04bf4b836467ffffd4f0a49d94f69e7e7ade2683335d3e"
    )
    assert "core/knowledge_state.py" in source["producer_sources"]
    assert "core/curation.py" in source["producer_sources"]
    assert "enrichers/__init__.py" in source["producer_sources"]


def original_accesses(original, name):
    case = original.case(name)
    states = original.accesses(case)
    inputs = {}
    first_key = case["root_access_node"]
    captures = {
        ref: SimpleNamespace(
            pin=capture["pin"],
            snapshot=capture["snapshot"],
            data=deepcopy(original.ref(capture["data_ref"])),
        )
        for ref, capture in states[first_key]["captures"].items()
    }
    for key, state in states.items():
        assert (
            case["accesses"][key]["fields"]["captures"]
            == case["accesses"][first_key]["fields"]["captures"]
        )
        inputs[key] = SimpleNamespace(
            _captures=captures, _inputs=state["inputs"], _focal_key=state["focal"]
        )
    return case, states, inputs


def hydrate_original(original, name, *, include_accesses=False):
    """Restore actual observed objects and origins; execute no archived code."""
    from sabueso.core.card_access import AccessSelection, _Entry, _handle
    from sabueso.core.card_exploration import CardView
    from sabueso.core.card_exploration_storage import _access, _explorer
    from sabueso.core.card_navigation_preview_v1 import metadata

    case, states, inputs = original_accesses(original, name)
    accesses, results = {}, {}
    common_state = states[case["root_access_node"]]
    objects = {
        ref: deepcopy(original.ref(value))
        for ref, value in common_state["objects"].items()
    }
    locations = deepcopy(common_state["locations"])
    for key, state in states.items():
        access = _access(
            inputs[key]._captures,
            inputs[key]._inputs,
            objects,
            locations,
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
                    == "protein_knowledge_comparison_exploration@1"
                ):
                    results[ref] = restore_result(ref, objects[ref])
                elif objects[ref]["context"]["adapter"] == "bioactivity_exploration@1":
                    from sabueso.core.card_bioactivity_history_v1 import (
                        restore_result as restore_activity,
                    )

                    results[ref] = restore_activity(ref, objects[ref])
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
        "format": "sabueso.card_exploration@35",
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
        buckets = {}
        for entry in selected._entries:
            ref = _handle(
                "XI_", {"result_ref": selected.result_ref, "location": entry.location}
            )
            buckets.setdefault(ref, []).append(entry)
        consumed = {}
        entries = []
        for row in observed["items"]:
            ref = row["item_ref"]
            index = consumed.get(ref, 0)
            entries.append(buckets[ref][index])
            consumed[ref] = index + 1
        view = CardView(
            explorer,
            selected,
            tuple(entries),
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
    from sabueso.core.card_exploration_knowledge_comparison import _state

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


@pytest.mark.parametrize("name", CASES)
def test_original_human_source_and_display_binding(original, monkeypatch, name):
    from sabueso.core.card_exploration_knowledge_comparison import (
        is_context,
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
        if is_view(view) or is_context(view):
            verify_view(view, binding_record(original, view, observed))
            checked += 1
    assert checked > 0 or name == "machine-only"


@pytest.mark.parametrize("name", CASES)
def test_original_finite_machine_requests_and_pages(original, monkeypatch, name):
    from sabueso.core._knowledge_comparison_history_v1.machine import _machine

    original.cache.clear()
    case = original.case(name)
    nodes, records, accesses = hydrate_original(original, name, include_accesses=True)
    access = accesses[case["root_access_node"]]
    block_current(monkeypatch)
    for query in case["queries"]:
        selected = access._selections[query["selection_ref"]]
        entries = _machine(selected, access, selected._scientific)
        assert canonical_json([vars(e) for e in entries]) == canonical_json(
            [vars(e) for e in selected._entries]
        )
        cursor = None
        for ref in query["pages"]:
            recorded = original.ref(ref)
            page = selected.page(
                limit=recorded["page"]["limit"],
                max_bytes=recorded["page"]["max_bytes"],
                cursor=cursor,
                skip_digestion=True,
            )
            assert canonical_json(page) == canonical_json(recorded)
            cursor = page["page"]["next_cursor"]
        assert cursor is None


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
            query["topic"],
            options=query["options"],
            **query["request"],
            skip_digestion=True,
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
