"""Independent SDK227 disease expectations over immutable original observations."""

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
from test_card_disease_association_original_offline import CASES
from test_card_disease_association_original_offline import original as original

from sabueso.core.card_disease_association_history_v1 import (
    expected_result,
    restore_result,
    verify_result,
)
from sabueso.core.errors import StorageError
from sabueso.core.snapshot import canonical_json


def block_current(guard):
    from sabueso.core.card import Card

    # Import mutable aliases before installing guards; otherwise importing a
    # module under the guard can permanently capture a patched dependency.
    for module_name in (
        "card_disease_association_access",
        "card_disease_association_selection_v1",
        "card_disease_association_exploration",
        "diseases",
        "clinical",
    ):
        importlib.import_module("sabueso.core." + module_name)

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Independent disease reading used current science or acquisition"
        )

    for name in ("__init__", "from_dict", "clinical", "diseases", "knowledge_state"):
        guard.setattr(Card, name, forbidden)
    for name in ("create_connection", "getaddrinfo"):
        guard.setattr(socket, name, forbidden)
    guard.setattr(socket.socket, "connect", forbidden)
    for module_name, names in (
        ("card_disease_association_access", ("materialize", "_identity", "_norm")),
        (
            "card_disease_association_selection_v1",
            ("evaluate", "normalize", "projection"),
        ),
        (
            "card_disease_association_exploration",
            (
                "view",
                "open_item",
                "explain",
                "links",
                "follow",
                "display_filter",
                "display_sort",
            ),
        ),
        ("diseases", ("disease_statements", "_card_statements", "diseases_view")),
        ("clinical", ("clinical_view",)),
    ):
        module = importlib.import_module("sabueso.core." + module_name)
        for name in names:
            guard.setattr(module, name, forbidden)
    for module_name in (
        "mondo",
        "chembl",
        "clinicaltrials",
        "unichem",
        "uniprot",
        "europepmc",
        "pdb_ccd",
    ):
        module = importlib.import_module("sabueso.tools.db." + module_name)
        if module_name == "mondo":
            guard.setattr(module, "normalize", forbidden)
        for name, value in vars(module).items():
            if (
                name.startswith(("Online", "Fixture"))
                and name.endswith("Client")
                and isinstance(value, type)
            ):
                guard.setattr(value, "__init__", forbidden)
    digester = importlib.import_module("sabueso._private.argdigest.argument.item_ref")
    guard.setattr(digester, "digest_item_ref", forbidden)


def original_access(original, name):
    case = original.case(name)
    stored = original.accesses(case)[case["root_access_node"]]
    captures = {
        key: SimpleNamespace(
            pin=row["pin"],
            snapshot=row["snapshot"],
            data=deepcopy(original.ref(row["data_ref"])),
        )
        for key, row in stored["captures"].items()
    }
    access = SimpleNamespace(
        _captures=captures, _inputs=stored["inputs"], _focal_key=stored["focal"]
    )
    root = original.nodes(case)[case["named_views"]["root"]]["observation"]
    ref = root["result_ref"]
    wire = deepcopy(original.ref(stored["objects"][ref]))
    return access, ref, wire, case, stored


def test_frozen_disease_module_lineage_matches_the_clean_original(original):
    package = importlib.resources.files("sabueso.core._disease_association_history_v1")
    source = json.loads(package.joinpath("SOURCE.json").read_text(encoding="utf-8"))
    assert source["producer_head"] == "0e17f8561381c6016ca6ebe77c336b357b0d4203"
    assert set(source["frozen_files"]) == {
        path.name for path in package.iterdir() if path.name.endswith(".py")
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
        relative = os.path.normpath("sabueso/core/" + name).replace(os.sep, "/")
        assert before[relative] == digest


def hydrate_original(original, name):
    """Rebuild observed containers and actual nodes, executing no archived code."""
    from sabueso.core.card_access import AccessSelection, _Entry, _handle
    from sabueso.core.card_exploration import CardView
    from sabueso.core.card_exploration_storage import _access, _explorer
    from sabueso.core.card_navigation_preview_v1 import metadata

    inputs, ref, wire, case, stored = original_access(original, name)
    objects = {
        key: deepcopy(original.ref(value)) for key, value in stored["objects"].items()
    }
    locations = deepcopy(stored["locations"])
    result = restore_result(ref, wire)
    states = original.accesses(case)
    accesses = {}

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
            result if spec["scientific_result_ref"] else None,
            tuple(spec["request"]["fields"]),
            spec["outcome_override"],
        )

    for key, state in states.items():
        access = _access(
            inputs._captures, inputs._inputs, objects, locations, state["focal"]
        )
        access._mode, access._nonce = "live", state["nonce"]
        access._metadata_refs = set(state["metadata_refs"])
        access._cursors = deepcopy(state["cursors"])
        access._tokens = {
            (row["selection_ref"], row["offset"]): row["token"]
            for row in state["tokens"]
        }
        for item_ref, row in state["scientific_items"].items():
            assert row["result_ref"] == ref
            access._scientific_items[item_ref] = result, row["entry_key"]
        access._selections = {
            key: selection(access, spec) for key, spec in state["selections"].items()
        }
        accesses[key] = access
    session = {
        "views": {},
        "links": {},
        "explanations": {},
        "presentation_metadata": metadata(),
    }
    records = original.nodes(case)
    nodes = {}

    def node(key):
        if key is None:
            return None
        if key in nodes:
            return nodes[key]
        record = records[key]
        observed = record["observation"]
        access = accesses[record["access_node"]]
        explorer = _explorer(access, session)
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
        subset = tuple(by_ref[row["item_ref"]] for row in observed["items"])
        view = CardView(
            explorer,
            selected,
            subset,
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
    from sabueso.core.card_exploration_disease_association import _state

    record = {
        "native_payload": original.ref(observed["native_payload_ref"]),
        "state": {
            "context": observed["context"],
            "schema": observed["schema"],
            "coverage": view.coverage,
            "items": _state(view)["items"],
        },
    }
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
        assert canonical_json(
            record["state"]["items"][item["item_ref"]]
        ) == canonical_json(expected)
    return record


def original_navigation_ids(nodes):
    session = next(iter(nodes.values()))._explorer._session
    ids = {key: "N" + str(index) for index, key in enumerate(session["views"])}
    return {key: ids[id(view)] for key, view in nodes.items()}


def assert_saved_original(saved, original, name, navigation_ids):
    """Check each actual original node/parent, all cells and finite agent pages."""
    from sabueso.core.card_exploration_storage import _cell_record

    case = original.case(name)
    records = original.nodes(case)
    retained = saved.explorer._session["original_nodes"]
    assert set(navigation_ids) == set(records)
    for key, row in records.items():
        view = retained[navigation_ids[key]]
        observed = row["observation"]
        assert view.view_ref == observed["view_ref"]
        assert view._explorer.access._focal_key == observed["focal"]
        assert view._origin is (
            None
            if row["origin_node"] is None
            else retained[navigation_ids[row["origin_node"]]]
        )
        assert view._explorer._origin is (
            None
            if row["explorer_origin_node"] is None
            else retained[navigation_ids[row["explorer_origin_node"]]]
        )
        assert canonical_json(view.native_payload) == canonical_json(
            original.ref(observed["native_payload_ref"])
        )
        assert canonical_json(view.request) == canonical_json(observed["request"])
        assert view.schema == observed["schema"]
        assert [item.item_ref for item in view.items()] == [
            item["item_ref"] for item in observed["items"]
        ]
        for item, recorded in zip(view.items(), observed["items"]):
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

    original_locations = original.accesses(case)[case["root_access_node"]]["locations"]

    def normalize_locations(items, lookup):
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
            "associations", **query["request"], skip_digestion=True
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
                normalize_locations(
                    page["items"], lambda loc: saved.explorer.access._resolve(loc)[1]
                )
            ) == canonical_json(
                normalize_locations(
                    recorded["items"],
                    lambda loc: original_locations[loc["location_ref"]],
                )
            )
            assert page["page"]["offset"] == recorded["page"]["offset"]
            assert page["page"]["total"] == recorded["page"]["total"]
            cursor = page["page"]["next_cursor"]
        assert cursor is None


def independent_receive(path, directory, name, ids_path):
    """Receive in a fresh outside-checkout process with current science blocked."""
    import hashlib

    from test_card_disease_association_original_offline import Original

    import sabueso

    assert (
        not Path.cwd()
        .resolve()
        .is_relative_to(Path(sabueso.__file__).resolve().parents[1])
    )

    directory = Path(directory)
    manifest_path = directory / "manifest.json"
    assert (
        hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        == "f4d7a91be5d6abdc0a2a66086bdab1f3ec8bf7be87a91d09d2f085982c2047e1"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for relative, record in manifest["files"].items():
        member = directory / relative
        assert (
            member.resolve().is_relative_to(directory.resolve())
            and not member.is_symlink()
        )
        assert member.stat().st_size == record["bytes"]
        with member.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == record["sha256"]
    original = Original(directory, manifest["files"])
    with pytest.MonkeyPatch.context() as guard:
        block_current(guard)
        saved = sabueso.read_exploration(
            path, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
        )
        assert (
            saved.validation["verifier"] == "disease_association_exploration_binding@1"
        )
        assert_saved_original(
            saved,
            original,
            name,
            json.loads(Path(ids_path).read_text(encoding="utf-8")),
        )


@pytest.mark.parametrize("name", CASES)
def test_actual_original_disease_file_round_trip(original, monkeypatch, tmp_path, name):
    import sabueso
    from sabueso.core import card_exploration_storage as storage

    nodes, _ = hydrate_original(original, name)
    navigation_ids = original_navigation_ids(nodes)
    root = nodes[original.case(name)["named_views"]["root"]]
    block_current(monkeypatch)
    restore = storage._restore

    def retain_failed_boundary(packet, *args, **kwargs):
        try:
            return restore(packet, *args, **kwargs)
        except StorageError:
            with (tmp_path / "failed-prepared-original.json").open(
                "w", encoding="utf-8"
            ) as stream:
                json.dump(packet, stream, ensure_ascii=False, allow_nan=False)
            raise

    monkeypatch.setattr(storage, "_restore", retain_failed_boundary)
    path = tmp_path / "disease-original.json"
    root.save(
        path, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
    )
    saved = sabueso.read_exploration(
        path, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
    )
    assert saved.validation["verifier"] == "disease_association_exploration_binding@1"
    assert_saved_original(saved, original, name, navigation_ids)
    ids_path = tmp_path / "original-node-map.json"
    ids_path.write_text(json.dumps(navigation_ids), encoding="utf-8")
    code = "import sys; sys.path.insert(0, sys.argv[5]); from test_card_disease_association_history_offline import independent_receive; independent_receive(*sys.argv[1:5])"
    with tempfile.TemporaryDirectory(
        prefix="sabueso-disease-receiver-", dir="/tmp" if os.name == "posix" else None
    ) as receiving_cwd:
        received = subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                code,
                str(path),
                str(original.directory),
                name,
                str(ids_path),
                str(Path(__file__).resolve().parent),
            ],
            cwd=receiving_cwd,
            capture_output=True,
            text=True,
            timeout=300,
        )
    assert received.returncode == 0, received.stdout + received.stderr
    assert not received.stderr


@pytest.mark.parametrize("name", CASES)
def test_original_human_disease_source_and_cross_capture_graph(
    original, monkeypatch, name
):
    from sabueso.core.card_exploration_disease_association import (
        is_context,
        is_links,
        is_view,
        verify_view,
    )

    nodes, records = hydrate_original(original, name)
    block_current(monkeypatch)
    checked = 0
    for key, view in nodes.items():
        if is_view(view) or is_context(view) or is_links(view):
            record = binding_record(original, view, records[key]["observation"])
            try:
                verify_view(view, record)
            except StorageError as error:
                raise AssertionError(
                    f"Original node {name}/{key}: {view.title}; context={view._context_override}; "
                    f"origin={records[key]['origin_node']}: {error}"
                ) from error
            checked += 1
    assert checked > 0


@pytest.mark.parametrize("name", CASES)
def test_frozen_disease_original_native_identity_sources_and_order(
    original, monkeypatch, name
):
    access, ref, wire, case, _ = original_access(original, name)
    before = canonical_json({key: row.data for key, row in access._captures.items()})
    original_wire = canonical_json(wire)
    block_current(monkeypatch)
    expected = expected_result(access, original=wire)
    assert expected.result_ref == ref
    assert canonical_json(expected.wire) == original_wire
    verify_result(access, ref, wire)
    restored = restore_result(ref, wire)
    assert [entry.key for entry in restored.entries] == [
        entry.key for entry in expected.entries
    ]
    observation = original.nodes(case)[case["named_views"]["root"]]["observation"]
    assert [entry.key for entry in restored.entries] == [
        row["key"] for row in observation["selection"]["entries"]
    ]
    assert canonical_json(wire) == original_wire
    assert (
        canonical_json({key: row.data for key, row in access._captures.items()})
        == before
    )


@pytest.mark.parametrize("name", CASES)
def test_frozen_disease_all_original_typed_machine_requests_and_frames(
    original, monkeypatch, name
):
    from sabueso.core._disease_association_history_v1.machine import _machine
    from sabueso.core.card_access import AccessSelection, _Entry
    from sabueso.core.card_exploration_storage import _access

    inputs, ref, wire, case, stored = original_access(original, name)
    access = _access(
        inputs._captures,
        inputs._inputs,
        {
            key: deepcopy(original.ref(value))
            for key, value in stored["objects"].items()
        },
        deepcopy(stored["locations"]),
        inputs._focal_key,
    )
    access._mode, access._nonce = "live", stored["nonce"]
    access._metadata_refs = set(stored["metadata_refs"])
    result = restore_result(ref, wire)
    block_current(monkeypatch)
    for query in case["queries"]:
        spec = stored["selections"][query["selection_ref"]]
        selection = AccessSelection(
            access,
            spec["result_ref"],
            spec["selection_ref"],
            tuple(
                _Entry(
                    row["location"],
                    row["key"],
                    deepcopy(original.ref(row["value_ref"])),
                    row["ordinal"],
                )
                for row in spec["entries"]
            ),
            spec["context_location"],
            spec["request"]["target"],
            spec["request"]["operation"],
            spec["slice"],
            result,
            tuple(spec["request"]["fields"]),
            spec["outcome_override"],
        )
        entries = _machine(selection, access, result)
        assert len(entries) == query["count"]
        assert [entry.key for entry in entries] == [
            entry.key for entry in selection._entries
        ]
        observed = [
            row for page in query["pages"] for row in original.ref(page)["items"]
        ]
        frames = [result.frame(access, selection, entry) for entry in entries]
        assert canonical_json(frames) == canonical_json(observed)


@pytest.mark.parametrize(
    "mutation",
    (
        "row",
        "raw",
        "identity",
        "source_role",
        "direction",
        "coverage",
        "excluded",
        "options",
    ),
)
def test_altered_original_disease_wires_are_refused(original, monkeypatch, mutation):
    access, ref, wire, _, _ = original_access(original, "public-protein")
    rows = wire["rows"]
    key = next(key for key, row in rows.items() if row["kind"] != "association_context")
    if mutation == "row":
        rows[key]["source"] = "Synthetic substituted source"
    elif mutation == "raw":
        rows[key]["item"]["synthetic_substitution"] = True
    elif mutation == "identity":
        wire["native_payload"]["identity"]["focal"] = "MONDO:OTHER"
    elif mutation == "source_role":
        wire["support"][key]["source_assertions"][0]["role"] = "synthetic other role"
    elif mutation == "direction":
        rows[key]["subject_ref"], rows[key]["object_ref"] = (
            rows[key]["object_ref"],
            rows[key]["subject_ref"],
        )
    elif mutation == "coverage":
        wire["coverage"]["contexts"][0]["stored_occurrences"] += 1
    elif mutation == "excluded":
        wire["exclusions"] = []
    else:
        wire["context"]["options"] = {"fetch": True}
    block_current(monkeypatch)
    with pytest.raises((StorageError, ValueError)):
        verify_result(access, ref, wire)
