"""Independent human bindings over the immutable, complete SDK211 view graph.

These tests hydrate retained observations. They never run the producer recipe,
construct Cards or replace original results with the verifier's calculations.
"""

import gzip
import hashlib
import json
import tarfile
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from sabueso.core import card_exploration_molecule_activity as binding
from sabueso.core.card_access import AccessSelection, _Entry
from sabueso.core.card_exploration import CardView
from sabueso.core.card_exploration_storage import _access, _explorer
from sabueso.core.errors import StorageError
from sabueso.core.snapshot import canonical_json

DATA = (
    Path(__file__).with_name("data") / "molecule_activity_quantity_live_sdk211.tar.gz"
)
ENCODED_SHA = "b7aef835ed698e613e1dd74fc9e3e8085f00e221ff7fe4f17e106eb4641ee012"
DECODED_SHA = "bc102cfe44cdefaee99b26b4a361f14e27543ec62a5165e26659ffb59e4e6b60"
MANIFEST_SHA = "59d35b9a32726ec432c8e2f570977711188894fc385233bc4a48834facba6f30"


class OriginalGraph:
    SAVED_FORMAT = binding.FORMAT

    def __init__(self, path):
        self.archive = tarfile.open(path, "r:")
        self.cache = {}
        self.manifest = self.member("manifest.json")
        assert (
            self.manifest["producer_head"] == "af5180b1fd146e83e1a25eb88a5703e68c072229"
        )
        assert self.manifest["producer_version"] == "0.14.0+211.gaf5180b"
        assert (
            self.manifest["capture_complete"]
            and not self.manifest["admitted_saved_format"]
        )
        members = self.archive.getmembers()
        assert len(members) == 516
        assert {item.name for item in members} == {
            *self.manifest["files"],
            "manifest.json",
        }
        for member in members:
            assert member.isfile() and not Path(member.name).is_absolute()
            assert ".." not in Path(member.name).parts
            with self.archive.extractfile(member) as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if member.name == "manifest.json":
                assert actual == MANIFEST_SHA
            else:
                assert actual == self.manifest["files"][member.name]["sha256"]
                assert member.size == self.manifest["files"][member.name]["bytes"]
        self.graph = self.value(self.manifest["graph"])
        self.observed = {
            key: self.value(ref) for key, ref in self.graph["nodes"].items()
        }
        self._hydrate_graph()

    def _hydrate_graph(self):
        self.accesses, self.results, self.nodes, self.records = {}, {}, {}, {}
        self.session = {
            "format": self.SAVED_FORMAT,
            "views": {},
            "explanations": {},
            "links": {},
            "presentation_metadata": {
                "navigation_preview": "question_destination_preview@1"
            },
        }
        for key, state in self.graph["access_states"].items():
            captures = {
                pin: SimpleNamespace(
                    pin=record["pin"],
                    snapshot=record["snapshot"],
                    data=self.value(record["data_ref"]),
                )
                for pin, record in state["captures"].items()
            }
            access = _access(
                captures,
                state["inputs"],
                {ref: self.value(record) for ref, record in state["objects"].items()},
                deepcopy(state["locations"]),
                state["focal"],
            )
            access._metadata_refs = set(state["metadata_refs"]) | (
                set(access._objects) - set(state["objects"])
            )
            self.accesses[key] = access
            for ref, wire in list(access._objects.items()):
                if ref in access._metadata_refs:
                    continue
                adapter = wire.get("context", {}).get("adapter")
                if wire.get("context", {}).get("card_ref") != access._focal.pin:
                    continue
                if adapter == binding.ADAPTER:
                    witnesses = [
                        view["selection"]
                        for view in self.observed.values()
                        if view["selection"].get("scientific_result_ref") == ref
                        and view["display_request"] is None
                    ]
                    keys = [row["key"] for row in witnesses[0]["entries"]]
                    crossings = {}
                    for view in self.observed.values():
                        context = view["context_override"] or {}
                        navigation = context.get("molecule_activity_navigation", {})
                        if (
                            context.get("activity_context") != "native_ligand_crossing"
                            or navigation.get("source_result_ref") != ref
                        ):
                            continue
                        full = self.accesses.get(view["access_id"], access)._resolve(
                            view["selection"]["request"]["target"]["location"]
                        )[1]
                        crossings[context["target_card_ref"]] = {
                            "wrapper": access._objects[full["result_ref"]],
                            "location": full,
                            "inputs": list(access._inputs),
                            "policies": binding._policies(wire["context"]["options"]),
                        }
                    result = binding.restore_result(
                        access, ref, wire, entry_keys=keys, native_crossings=crossings
                    )
                elif adapter == "literature_exploration@1":
                    from sabueso.core.card_literature_history_v1 import restore_result

                    result = restore_result(ref, wire)
                elif adapter == "bioactivity_exploration@1":
                    from sabueso.core.card_bioactivity_history_v2 import restore_result

                    result = restore_result(ref, wire)
                else:
                    raise AssertionError(adapter)
                self.results[key, ref] = result
                access._scientific_cache[ref] = result
        for key in self.observed:
            self.node(key)
        assert len(self.nodes) == 104

    def member(self, path):
        if path not in self.cache:
            with self.archive.extractfile(path) as stream:
                self.cache[path] = json.load(stream)
        return self.cache[path]

    def value(self, ref):
        return self.member(ref["path"])

    def selection(self, access_id, observed):
        access, request = self.accesses[access_id], observed["request"]
        return AccessSelection(
            access,
            observed["result_ref"],
            observed["selection_ref"],
            tuple(
                _Entry(
                    row["location"],
                    row["key"],
                    self.value(row["value_ref"]),
                    row["ordinal"],
                )
                for row in observed["entries"]
            ),
            observed["context_location"],
            request["target"],
            request["operation"],
            observed["slice"],
            self.results.get((access_id, observed.get("scientific_result_ref"))),
            tuple(request["fields"]),
            observed["outcome_override"],
        )

    def node(self, key):
        if key in self.nodes:
            return self.nodes[key]
        observed = self.observed[key]
        access = self.accesses[observed["access_id"]]
        origin = (
            self.node(observed["origin_node_id"])
            if observed["origin_node_id"] is not None
            else None
        )
        explorer_origin = (
            self.node(observed["explorer_origin_node_id"])
            if observed["explorer_origin_node_id"] is not None
            else None
        )
        explorer = _explorer(access, self.session)
        explorer._origin = explorer_origin
        selection = self.selection(observed["access_id"], observed["selection"])
        from sabueso.core.card_access import _handle

        available = {
            _handle(
                "XI_", {"result_ref": selection.result_ref, "location": row.location}
            ): row
            for row in selection._entries
        }
        entries = tuple(available[row["item_ref"]] for row in observed["items"])
        view = CardView(
            explorer,
            selection,
            entries,
            _origin=origin,
            _native_override=self.value(observed["native_override_ref"]),
            _component_navigation=observed["component_navigation"],
            **observed["flags"],
        )
        assert view.view_ref == observed["view_ref"]
        state = {
            "items": {
                row["item_ref"]: {
                    "label": row["label"],
                    "kind": row["kind"],
                    "support": self.value(row["support_ref"]),
                    "cells": {
                        column: {
                            **{k: v for k, v in cell.items() if k != "support_ref"},
                            "support": self.value(cell["support_ref"]),
                        }
                        for column, cell in row["cells"].items()
                    },
                }
                for row in observed["items"]
            },
            "context": observed["context"],
            "schema": observed["schema"],
            "coverage": selection._scientific.wire["coverage"]
            if selection._scientific is not None
            else view.coverage,
        }
        object.__setattr__(view, "_saved_state", state)
        self.nodes[key] = view
        self.records[key] = {
            "state": state,
            "native_payload": self.value(observed["native_payload_ref"]),
            "native_encoding": "json",
            "selected": [row["item_ref"] for row in observed["items"]],
            "flags": observed["flags"],
        }
        return view

    def named(self, name):
        key = self.graph["named"][name]
        return self.nodes[key], self.records[key]


@pytest.fixture(scope="module")
def original_graph(tmp_path_factory):
    with DATA.open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == ENCODED_SHA
    target = tmp_path_factory.mktemp("molecule-quantity-binding") / "original.tar"
    total, decoded = 0, hashlib.sha256()
    with gzip.open(DATA, "rb") as source, target.open("xb") as output:
        while block := source.read(1024**2):
            total += len(block)
            decoded.update(block)
            output.write(block)
    assert total == 123873280 and decoded.hexdigest() == DECODED_SHA
    original = OriginalGraph(target)
    yield original
    original.archive.close()
    original.cache.clear()


def block_current(monkeypatch):
    from test_card_molecule_activity_history_offline import (
        block_current as block_science,
    )

    import sabueso.core.card_molecule_activity_exploration as current

    # Import aliases before their providers are patched. Importing the LIVE UI
    # under the science guard would capture its temporary forbidden materialize
    # alias and contaminate later LIVE tests in the same process.
    block_science(monkeypatch)

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Independent original binding cannot use current LIVE molecule UI"
        )

    for name in (
        "view",
        "open_item",
        "support",
        "_navigation",
        "_selection_binding",
        "explain",
        "links",
        "follow",
        "display_filter",
        "display_sort",
    ):
        monkeypatch.setattr(current, name, forbidden)


@pytest.mark.parametrize("node", [f"N{i}" for i in range(104)])
def test_original_quantity_graph_human_binding(original_graph, node, monkeypatch):
    block_current(monkeypatch)
    view, record = original_graph.nodes[node], original_graph.records[node]
    if binding.is_view(view):
        binding.verify_view(view, record)
    elif binding.is_context(view):
        binding.verify_context(view, record)
    elif view._record_panel == "literature":
        # Native literature keeps its separately frozen @19 predicates. The
        # new activity binding must never claim these as molecule science.
        binding.verify_literature_view(view, record)
    else:
        from sabueso.core.card_exploration_verification_v19 import (
            _verify_display,
            _verify_profile,
            _verify_request,
            _verify_state,
        )

        access = view._explorer.access
        native = _verify_request(view, access)
        _verify_state(view, record, native, access)
        _verify_display(view, record)
        _verify_profile(view, native, access)


@pytest.mark.parametrize("index", range(6))
def test_original_quantity_machine_binding(original_graph, index, monkeypatch):
    block_current(monkeypatch)
    request = original_graph.graph["machine"][index]
    access_id = next(
        key
        for key, access in original_graph.accesses.items()
        if access._focal_key == request["focal"]
    )
    selection = original_graph.selection(access_id, request["selection"])
    result = selection._scientific
    entries = binding._machine(selection, selection._access, result)
    assert canonical_json([vars(entry) for entry in entries]) == canonical_json(
        [vars(entry) for entry in selection._entries]
    )


@pytest.mark.parametrize(
    "change", ("support", "unit", "membership", "native", "question")
)
def test_original_quantity_human_semantic_changes_are_rejected(original_graph, change):
    view, record = original_graph.named("target/node/filtered")
    record = deepcopy(record)
    item = next(iter(record["state"]["items"].values()))
    if change == "support":
        item["support"] = []
    elif change == "unit":
        item["cells"]["measurement"]["unit"] = "micromolar"
    elif change == "membership":
        view = replace(view, _selected=())
    elif change == "native":
        record["native_payload"]["targets"] = {}
    else:
        view = replace(view, _request={**view.request, "question": "publications"})
    with pytest.raises(StorageError):
        binding.verify_view(view, record)


@pytest.mark.parametrize(
    "change", ("root_display", "source_row", "target_pin", "source_membership")
)
def test_original_quantity_navigation_scope_changes_are_rejected(
    original_graph, change
):
    view, _ = original_graph.named("group/node/links")
    context = deepcopy(view._context_override)
    if change == "root_display":
        context["molecule_activity_navigation"]["molecule_root_selection"][
            "display_request"
        ] = {"operation": "foreign"}
    elif change == "source_row":
        context["molecule_activity_navigation"]["source_row_key"] = "foreign"
    elif change == "target_pin":
        context["molecule_activity_navigation"]["target_card_ref"] = "foreign"
    else:
        native = deepcopy(view.native_payload)
        native["links"] = native["links"][1:]
        view = replace(view, _native_override=native)
    view = replace(view, _context_override=context)
    with pytest.raises(StorageError):
        binding.verify_links(view)


def test_original_root_return_preserves_observed_python_numeric_equality(
    original_graph,
):
    view, record = original_graph.named("target/pyunitwizard/link/17/molecule_root")
    expected = view._origin._context_override["molecule_activity_navigation"][
        "molecule_root_selection"
    ]
    actual = binding._selection_binding(view)
    assert actual == expected
    assert canonical_json(actual) != canonical_json(expected)
    assert type(actual["display_request"]["equals"]["value"]) is int
    assert type(expected["display_request"]["equals"]["value"]) is float
    binding.verify_view(view, record)


@pytest.mark.parametrize("change", ("foreign_question", "foreign_target", "no_parent"))
def test_intermediate_publication_crossing_requires_exact_incoming_scope(
    original_graph, change
):
    view = next(
        view
        for view in original_graph.nodes.values()
        if view._record_panel == "literature"
        and view.request is not None
        and view.request["question"] == "measured_targets"
    )
    record = original_graph.records[
        next(key for key, value in original_graph.nodes.items() if value is view)
    ]
    if change == "foreign_question":
        view = replace(view, _request={**view.request, "options": {}})
    elif change == "no_parent":
        view = replace(view, _origin=None)
    else:
        parent = view._origin
        context = deepcopy(parent._context_override)
        context["molecule_activity_navigation"]["target_card_ref"] = "foreign"
        view = replace(view, _origin=replace(parent, _context_override=context))
    with pytest.raises(StorageError):
        binding.verify_literature_view(view, record)


@pytest.mark.parametrize(
    "change",
    (
        "links_state",
        "links_route",
        "endpoint_state",
        "endpoint_route",
        "source_payload",
        "source_back",
    ),
)
def test_original_context_semantic_and_presentation_scope_changes_are_rejected(
    original_graph, change
):
    links = change.startswith("links_")
    name = "target/node/links" if links else "target/node/link/0/source"
    view, record = original_graph.named(name)
    record = deepcopy(record)
    if change.endswith("state"):
        view = replace(view, _status="empty")
    elif change.endswith("route"):
        view = replace(view, _route_catalog=True)
    elif change == "source_payload":
        record["native_payload"]["field_path"] = "foreign"
    else:
        view = replace(view, _origin=None)
    with pytest.raises(StorageError):
        binding.verify_context(view, record)
