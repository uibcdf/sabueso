"""Independent SDK239 retained values and typed compact requests with LIVE forbidden."""

import importlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_card_protein_context_original_offline import CASES
from test_card_protein_context_original_offline import original as original

from sabueso.core.card_protein_context_history_v1 import restore_result, verify_result
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.snapshot import canonical_json


def block_current(guard):
    from sabueso.core.card import Card

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Independent protein-context reader used LIVE science or acquisition"
        )

    targets = {
        "card_protein_context_access": (
            "materialize",
            "source_records",
            "_SequenceInput",
        ),
        "card_protein_context_selection_v1": ("evaluate", "normalize", "projection"),
        "card_protein_context_exploration": (
            "view",
            "open_item",
            "explain",
            "links",
            "display_filter",
            "display_sort",
        ),
        "card_annotation_regions_v1": ("entries", "support"),
        "card_sequence_change_access": ("materialize", "make_derivation"),
        "card_variant_access": ("materialize", "assertion_value"),
        "card_knowledge_comparison_access": ("materialize", "make_derivation"),
        "card_knowledge_diff_v2": ("compare", "make_derivation"),
        "card_disease_association_access": (
            "materialize",
            "make_derivation",
            "assertion_value",
        ),
        "card_molecule_activity_access": ("materialize", "make_derivation"),
        "card_sequence_change_exploration": ("view", "materialize"),
        "card_variant_exploration": ("view", "materialize"),
        "card_knowledge_comparison_exploration": ("view", "materialize"),
        "card_disease_association_exploration": ("view", "materialize"),
        "card_molecule_activity_exploration": ("view", "materialize"),
        "sequences": ("sequence_differences_view",),
        "relationship_store": ("make_derivation",),
        "source_assertion_store": ("assertion_value",),
    }
    modules = {
        name: importlib.import_module("sabueso.core." + name) for name in targets
    }
    for name, attributes in targets.items():
        module = modules[name]
        for attribute in attributes:
            guard.setattr(module, attribute, forbidden)
    for attribute in ("__init__", "from_dict", "sequence_differences", "bioactivities"):
        guard.setattr(Card, attribute, forbidden)
    from sabueso.core.card_exploration import CardExplorer

    guard.setattr(CardExplorer, "_live_topic", forbidden)
    guard.setattr(socket, "create_connection", forbidden)
    guard.setattr(socket.socket, "connect", forbidden)
    for name in ("uniprot", "rcsb", "uniref", "oma"):
        module = importlib.import_module("sabueso.tools.db." + name)
        for attribute, value in vars(module).items():
            if (
                attribute.startswith(("Online", "Fixture"))
                and attribute.endswith("Client")
                and isinstance(value, type)
            ):
                guard.setattr(value, "__init__", forbidden)


def original_accesses(original, name):
    case = original.case(name)
    states = original.accesses(case)
    inputs = {}
    for key, state in states.items():
        captures = {
            ref: SimpleNamespace(
                pin=capture["pin"],
                snapshot=capture["snapshot"],
                data=deepcopy(original.ref(capture["data_ref"])),
            )
            for ref, capture in state["captures"].items()
        }
        inputs[key] = SimpleNamespace(
            _captures=captures, _inputs=state["inputs"], _focal_key=state["focal"]
        )
    return case, states, inputs


@pytest.mark.parametrize("name", CASES)
def test_all_original_results_bind_exact_inputs_without_current_science(
    original, monkeypatch, name
):
    original.cache.clear()
    case, states, inputs = original_accesses(original, name)
    root = case["root_access_node"]
    state = states[root]
    block_current(monkeypatch)
    for cached in state["scientific_cache"]:
        ref = cached["result_ref"]
        wire = original.ref(state["objects"][ref])
        if wire.get("context", {}).get("adapter") != "protein_context_exploration@1":
            continue
        access = SimpleNamespace(**vars(inputs[root]))
        access._focal_key = next(
            key
            for key, capture in access._captures.items()
            if capture.pin == wire["context"]["card_ref"]
            and capture.snapshot == wire["context"]["snapshot_id"]
        )
        verify_result(access, ref, wire)
        result = restore_result(ref, deepcopy(wire))
        assert result.result_ref == ref and canonical_json(
            result.wire
        ) == canonical_json(wire)
        assert canonical_json(
            [entry.value["item"] for entry in result.entries]
        ) == canonical_json(wire["native_payload"]["items"])


@pytest.mark.parametrize(
    "field",
    [
        "item",
        "source",
        "count",
        "equality",
        "scope",
        "options",
        "producer",
        "row-order",
    ],
)
def test_altered_original_result_bindings_are_refused(original, monkeypatch, field):
    name = (
        "sequence-different"
        if field in ("count", "equality", "options")
        else "synthetic-associations"
    )
    case, states, inputs = original_accesses(original, name)
    key = case["root_access_node"]
    ref = case["projection_result_ref"]
    wire = deepcopy(original.ref(states[key]["objects"][ref]))
    row = next(iter(wire["rows"].values()))
    if field == "item":
        row["item"]["qualifiers"]["literal"] = "synthetic changed original"
    elif field == "source":
        next(iter(wire["support"].values()))["source_assertions"][0]["id"] = (
            "SA_foreign"
        )
    elif field == "count":
        row["difference_count"] = 0
    elif field == "equality":
        row["identical"] = True
    elif field == "scope":
        row["interpretation"]["scope"] = "synthetic foreign meaning"
    elif field == "options":
        wire["context"]["options"]["other_ref"] = "missing"
    elif field == "producer":
        wire["native_payload"]["rule"]["rule"] = "unqualified@99"
    else:
        wire["native_payload"]["items"].reverse()
    block_current(monkeypatch)
    with pytest.raises((StorageError, ArgumentError)):
        verify_result(inputs[key], ref, wire)


def test_frozen_lineage_names_exact_clean_producer_and_capsule(original):
    import importlib.resources

    from test_card_protein_context_original_offline import ENCODED_SHA256, PRODUCER

    record = json.loads(
        importlib.resources.files("sabueso.core._protein_context_history_v1")
        .joinpath("SOURCE.json")
        .read_text()
    )
    assert (
        record["producer_head"] == PRODUCER
        and record["capsule_sha256"] == ENCODED_SHA256
    )
    before = json.loads((original.directory / "source-before.json").read_text())
    for name, digest in record["producer_sources"].items():
        assert before["sabueso/core/" + name] == digest


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
                    == "protein_context_exploration@1"
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
        "format": "sabueso.card_exploration@33",
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
    from sabueso.core.card_exploration_protein_context import _state

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
    from sabueso.core.card_exploration_protein_context import (
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
        assert str(view) == observed["text"] and view._repr_html_() == observed["html"]
        if is_view(view) or is_context(view):
            verify_view(view, binding_record(original, view, observed))
            checked += 1
    assert checked > 0 or name == "machine-only"


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


def test_live_context_remains_usable_after_guarded_original_reading(original):
    case, states, inputs = original_accesses(original, "bare")
    ref = case["projection_result_ref"]
    root = case["root_access_node"]
    with pytest.MonkeyPatch.context() as guard:
        block_current(guard)
        verify_result(inputs[root], ref, original.ref(states[root]["objects"][ref]))
    from test_card_protein_context_offline import protein, relationship

    card = protein()
    expected, ref = relationship(card, "associated_with")
    assert (
        card.explore().answer("protein_associations").items()[0].open().native_payload
        == expected
    )


def test_history_guards_restore_cold_live_imports(tmp_path):
    script = r"""
import importlib
import sys
from pytest import MonkeyPatch

sys.path.insert(0, sys.argv[1])
from test_card_protein_context_history_offline import block_current
from test_card_protein_context_offline import protein

assert "sabueso.core.card_sequence_change_access" not in sys.modules
assert "sabueso.core.card_knowledge_comparison_access" not in sys.modules
with MonkeyPatch.context() as guard:
    block_current(guard)
    for name in ("card_sequence_change_access", "card_variant_access",
                 "card_knowledge_comparison_access"):
        module = importlib.import_module("sabueso.core." + name)
        try:
            module.materialize(None)
        except AssertionError as error:
            assert "Independent protein-context reader" in str(error)
        else:
            raise AssertionError("LIVE adapter guard was weakened")
    for name in ("card_sequence_change_exploration", "card_variant_exploration",
                 "card_knowledge_comparison_exploration"):
        module = importlib.import_module("sabueso.core." + name)
        try:
            module.view(None, None)
        except AssertionError as error:
            assert "Independent protein-context reader" in str(error)
        else:
            raise AssertionError("LIVE presentation guard was weakened")
left, right = protein(), protein("P52270")
explorer = left.explore(related_cards=[right])
assert explorer.answer("sequence_changes").native_payload is not None
assert explorer.answer("variant_tissue_context").native_payload is not None
knowledge = explorer.answer("knowledge_differences", options={
    "other_ref": explorer.context["inputs"][1]})
assert knowledge.native_payload["rule"]["rule"] == "card_knowledge_diff@2"
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script, str(Path(__file__).parent), str(tmp_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr
