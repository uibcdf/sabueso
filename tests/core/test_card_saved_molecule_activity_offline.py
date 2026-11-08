"""Actual files from the complete SDK211 original, without new source science."""

import importlib
import inspect
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

from sabueso.core import card_exploration_molecule_activity as binding
from sabueso.core.snapshot import canonical_json


@pytest.fixture(scope="module")
def retained_writer(tmp_path_factory):
    from test_card_molecule_activity_binding_offline import original_graph

    generator = original_graph.__wrapped__(tmp_path_factory)
    original = next(generator)
    # Import provider aliases before scientific guards; never leave a temporary
    # forbidden alias captured by a subsequently imported LIVE UI module.
    for name in (
        "card_molecule_activity_exploration",
        "card_literature_exploration",
        "card_bioactivity_exploration",
    ):
        importlib.import_module("sabueso.core." + name)
    for view in original.nodes.values():
        object.__setattr__(view, "_saved_state", None)
    original.session.pop("format")
    for access_id, access in original.accesses.items():
        access._mode = "live"
        for (owner, ref), result in original.results.items():
            if owner != access_id:
                continue
            adapter = result.wire["context"]["adapter"]
            key = (adapter, access._focal_key, canonical_json(result.options))
            if adapter == binding.ADAPTER:
                key = (
                    adapter,
                    access._focal_key,
                    tuple(access._inputs),
                    canonical_json(result.options),
                )
            access._scientific_cache[key] = result
        for record in original.graph["access_states"][access_id]["native_cache"]:
            access._scientific_cache[tuple(record["key"])] = original.value(
                record["payload_ref"]
            )
    # The observed LIVE _for_capture() instances share these stores. Hydrate
    # that ownership before writing, so newly issued target-location aliases
    # are retained by the same writer closure as the molecule's aliases.
    objects, locations, metadata_refs, cache = {}, {}, set(), {}
    for access in original.accesses.values():
        for target, values in (
            (objects, access._objects),
            (locations, access._locations),
        ):
            for key, value in values.items():
                if key in target:
                    assert canonical_json(target[key]) == canonical_json(value)
                target[key] = value
        metadata_refs.update(access._metadata_refs)
        cache.update(access._scientific_cache)
    for access in original.accesses.values():
        access._objects, access._locations = objects, locations
        access._metadata_refs, access._scientific_cache = metadata_refs, cache
    for request in original.graph["machine"]:
        access_id = next(
            key
            for key, access in original.accesses.items()
            if access._focal_key == request["focal"]
        )
        selection = original.selection(access_id, request["selection"])
        selection._access._selections[selection.selection_ref] = selection
    # Keep original observed instances, in their recorded producer order.
    original.session["views"] = {
        id(view): view
        for key, view in sorted(
            original.nodes.items(), key=lambda pair: int(pair[0][1:])
        )
    }
    yield original
    try:
        next(generator)
    except StopIteration:
        pass


@pytest.fixture(scope="module")
def saved_original(retained_writer, tmp_path_factory):
    import hashlib

    from test_card_molecule_activity_history_offline import (
        block_current as block_science,
    )

    root, _ = retained_writer.named("root")

    def source_hashes():
        return {
            capture.pin: hashlib.sha256(
                canonical_json(capture.data).encode()
            ).hexdigest()
            for capture in root._explorer.access._captures.values()
        }

    before = source_hashes()
    directory = tmp_path_factory.mktemp("molecule-file")
    path = directory / "original-molecule.json"
    with pytest.MonkeyPatch.context() as guard:
        block_science(guard)
        root.save(
            path,
            max_encoded_bytes=None,
            max_decoded_bytes=None,
            max_logical_bytes=None,
            skip_digestion=True,
        )
    assert path.is_file() and source_hashes() == before
    return {
        "path": path,
        "directory": directory,
        "root": root,
        "original": retained_writer,
        "tar": Path(retained_writer.archive.name),
    }


def test_complete_original_quantity_graph_writes_and_opens_actual_file(
    saved_original, monkeypatch
):
    from test_card_molecule_activity_binding_offline import block_current

    from sabueso.core.card_exploration_storage import read_exploration

    path, root = saved_original["path"], saved_original["root"]
    retained_writer, artifact_directory = (
        saved_original["original"],
        saved_original["directory"],
    )
    block_current(monkeypatch)
    received = read_exploration(
        path, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
    )
    assert received.view_ref == root.view_ref
    assert canonical_json(received.native_payload) == canonical_json(
        root.native_payload
    )
    assert (
        received.validation["activity_context"]
        == "original_frozen_v1_consistency_verified"
    )
    for form in ("node", "pyunitwizard"):
        import pyunitwizard as puw

        operand = (
            {"value": 33, "unit": "micromolar"}
            if form == "node"
            else puw.quantity(33, "micromolar", form="pint")
        )
        selected = received.filter("measurement", equals=operand, skip_digestion=True)
        links = selected.items()[0].related()
        assert canonical_json(links.native_payload) == canonical_json(
            retained_writer.named("target/" + form + "/links")[0].native_payload
        )
        for role in (
            "source",
            "native_ligand_crossing",
            "publication_context",
            "molecule_root",
        ):
            item = next(
                item for item in links.items() if item._entry.value["role"] == role
            )
            endpoint = item.open()
            assert endpoint.outcome["status"] != "not_saved"
            assert endpoint.back() is links
    script = (
        "import sys\nsys.path.insert(0, sys.argv[4])\n"
        + inspect.getsource(_independent_receive)
        + "\n_independent_receive(*sys.argv[1:4])\n"
    )
    with tempfile.TemporaryDirectory(
        prefix="sabueso-molecule-reader-",
        dir=None if sys.platform == "win32" else "/tmp",
    ) as reader_directory:
        child = subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                script,
                str(path),
                str(retained_writer.archive.name),
                str(artifact_directory / "reader-report.json"),
                str(Path(__file__).resolve().parent),
            ],
            cwd=reader_directory,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=600,
        )
    assert child.returncode == 0, child.stdout + child.stderr
    assert not child.stderr, child.stderr


def test_explicit_foreign_source_child_preserves_scope_without_broadening_inspection(
    retained_writer, monkeypatch
):
    from test_card_molecule_activity_history_offline import block_current

    from sabueso.core.errors import ArgumentError

    block_current(monkeypatch)
    parent = next(
        view
        for view in retained_writer.nodes.values()
        if binding.is_context(view)
        and view._context_override.get("activity_context") == "source"
        and any(
            entry.location["kind"] == "card"
            and entry.location["card_ref"] != view._explorer.access._focal.pin
            for entry in view._selected
        )
    )
    item = next(
        item
        for item in parent.items()
        if item.payload_location["card_ref"] != parent._explorer.access._focal.pin
    )
    child = item.open()
    assert (
        child.native_payload
        == parent._explorer.access._resolve(item.payload_location)[0]
    )
    assert child.back() is parent
    assert child._context_override == parent._context_override
    assert child._explorer.access._focal_key == parent._explorer.access._focal_key
    with pytest.raises(
        ArgumentError, match="Inspection is limited to the focal capture"
    ):
        parent.explorer.inspect(locator=item.payload_location, skip_digestion=True)


def test_original_machine_selection_saves_with_its_molecule_panel(
    retained_writer, tmp_path, monkeypatch
):
    from test_card_molecule_activity_history_offline import block_current

    import sabueso

    observed = retained_writer.graph["machine"][0]
    access_id = next(
        key
        for key, access in retained_writer.accesses.items()
        if access._focal_key == observed["focal"]
    )
    # A fresh facade of the exact recorded request exercises machine-first
    # saving instead of reusing an existing human/machine view instance.
    selection = retained_writer.selection(access_id, observed["selection"])
    assert not any(
        view._selection is selection
        for view in retained_writer.session["views"].values()
    )
    block_current(monkeypatch)
    path = tmp_path / "molecule-machine.json"
    selection.save(
        path,
        max_encoded_bytes=None,
        max_decoded_bytes=None,
        max_logical_bytes=None,
        skip_digestion=True,
    )
    from test_card_molecule_activity_binding_offline import block_current as block_ui

    block_ui(monkeypatch)
    saved = sabueso.read_exploration(
        path, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
    )
    assert saved._record_panel == "activity_context"
    assert saved._machine_ref == selection.selection_ref
    assert saved._selection.selection_ref == selection.selection_ref
    assert saved.native_payload == selection._scientific.wire["native_payload"]
    received = saved.explorer.access.select(
        "activity_context", **observed["query"], skip_digestion=True
    )
    assert received.selection_ref == selection.selection_ref
    assert received.capabilities["save"]
    assert saved.capabilities["save"]
    rebound_access = saved.explorer.access._for_capture(
        saved.explorer.access._focal_key
    )
    rebound = rebound_access.select(
        "activity_context", **observed["query"], skip_digestion=True
    )
    assert rebound._access is not saved.explorer.access
    assert rebound.capabilities["save"]
    repeated_path = tmp_path / "rebound-molecule-machine.json"
    rebound.save(
        repeated_path,
        max_encoded_bytes=None,
        max_decoded_bytes=None,
        max_logical_bytes=None,
        skip_digestion=True,
    )
    repeated = sabueso.read_exploration(
        repeated_path,
        max_encoded_bytes=None,
        max_decoded_bytes=None,
        max_logical_bytes=None,
    )
    assert repeated._machine_ref == selection.selection_ref
    assert repeated.native_payload == saved.native_payload


def _independent_receive(path, original_tar, report_path):
    """Read one real file outside the checkout with every mutable reader blocked."""
    import hashlib
    import json
    import re
    import tarfile
    from pathlib import Path

    import pytest
    import pyunitwizard as puw
    from test_card_molecule_activity_binding_offline import block_current

    import sabueso
    from sabueso.core.card_exploration_storage import _cell_record
    from sabueso.core.snapshot import canonical_json

    with Path(original_tar).open("rb") as stream:
        assert (
            hashlib.file_digest(stream, "sha256").hexdigest()
            == "bc102cfe44cdefaee99b26b4a361f14e27543ec62a5165e26659ffb59e4e6b60"
        )
    archive = tarfile.open(original_tar, "r:")

    def member(ref):
        with archive.extractfile(
            ref if isinstance(ref, str) else ref["path"]
        ) as stream:
            return json.load(stream)

    graph = member("graph.json")

    def observed(name):
        return member(graph["nodes"][graph["named"][name]])

    with pytest.MonkeyPatch.context() as guard:
        block_current(guard)
        saved = sabueso.read_exploration(
            path, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
        )
        root = saved.explorer.answer("measured_targets", skip_digestion=True)
        assert "activity_context" in root.explorer.capabilities["scientific_topics"]
        assert (
            root.explorer.topics().native_payload["activity_context"]["availability"]
            == "retained"
        )
        assert "activity_context" not in root.explorer.capabilities["not_saved_topics"]
        assert root.capabilities["save"]
        descriptor = next(
            entry.value
            for entry in root.explorer.access.catalog()._entries
            if entry.key == "activity_context"
        )
        assert descriptor["save"] and descriptor["availability"] == "retained"
        assert descriptor["selection_availability"] == "retained_requests_only"
        groups = root.items()[0].open()
        records = groups.items()[0].open()
        actual = {"root": root, "groups": groups, "records": records}
        for grain, scope in (("target", root), ("group", groups), ("record", records)):
            for form in ("node", "pyunitwizard"):
                prefix = grain + "/" + form
                operand = (
                    {"value": 33, "unit": "micromolar"}
                    if form == "node"
                    else puw.quantity(33, "micromolar", form="pint")
                )
                selected = scope.filter(
                    "measurement", equals=operand, skip_digestion=True
                )
                assert all(
                    selected.capabilities[key] for key in ("related", "explain", "save")
                )
                links = selected.items()[0].related()
                actual[prefix + "/filtered"] = selected
                actual[prefix + "/links"] = links
                actual[prefix + "/back"] = links.back()
                for name in graph["named"]:
                    if name.startswith(prefix + "/link/"):
                        index = int(re.search(r"/link/(\d+)/", name).group(1))
                        actual[name] = links.items()[index].open()
        destination = actual["target/node/link/5/target_card"]
        publications = destination.explorer.answer("publications", skip_digestion=True)
        actual["target/publications"] = publications
        for reference in ("pubmed:35189560", "pubmed:20889239"):
            item = next(
                item
                for item in publications.items()
                if item.cells["publication_ref"].value == reference
            )
            actual["target/publication/" + reference] = item.open()
        assert set(actual) == set(graph["named"])
        for name, view in actual.items():
            expected = observed(name)
            assert view.view_ref == expected["view_ref"], name
            assert view.result_ref == expected["result_ref"], name
            assert canonical_json(view.native_payload) == canonical_json(
                member(expected["native_payload_ref"])
            ), name
            assert canonical_json(view.request) == canonical_json(
                expected["request"]
            ), name
            assert canonical_json(view._display_request) == canonical_json(
                expected["display_request"]
            ), name
            assert canonical_json(view.context) == canonical_json(
                {**expected["context"], "mode": "saved"}
            ), name
            assert (
                view.schema == expected["schema"]
                and view.outcome == expected["outcome"]
            ), name
            assert (view.back().view_ref if not view.at_root else None) == expected[
                "back_view_ref"
            ], name
            items = view.items()
            assert [item.item_ref for item in items] == [
                item["item_ref"] for item in expected["items"]
            ], name
            for item, raw in zip(items, expected["items"], strict=True):
                assert item.label == raw["label"] and item.kind == raw["kind"], name
                assert canonical_json(item.support) == canonical_json(
                    member(raw["support_ref"])
                ), name
                for column, cell in item.cells.items():
                    old = raw["cells"][column]
                    wanted = {
                        **{
                            key: value
                            for key, value in old.items()
                            if key != "support_ref"
                        },
                        "support": member(old["support_ref"]),
                    }
                    assert canonical_json(
                        _cell_record(item, column, cell)
                    ) == canonical_json(wanted), (name, column)

        def locations(value, resolve):
            if isinstance(value, dict):
                if (
                    set(value) == {"format", "kind", "location_ref"}
                    and value["format"] == "card_access_location@1"
                    and value["kind"] == "lookup"
                ):
                    return resolve(value)
                return {key: locations(child, resolve) for key, child in value.items()}
            if isinstance(value, list):
                return [locations(child, resolve) for child in value]
            return value

        for request in graph["machine"]:
            selection = root.explorer.access.select(
                "activity_context", **request["query"], skip_digestion=True
            )
            assert selection.selection_ref == request["selection"]["selection_ref"]
            assert selection.capabilities["save"]
            rebound = root.explorer.access._for_capture(request["focal"])
            assert rebound.select(
                "activity_context", **request["query"], skip_digestion=True
            ).capabilities["save"]
            page = selection.page(limit=1, max_bytes=65536, skip_digestion=True)
            old = member(request["pages_ref"])[0]
            old["context"]["mode"] = "saved"
            state = next(
                state
                for state in graph["access_states"].values()
                if state["focal"] == request["focal"]
            )
            assert canonical_json(
                locations(page, lambda loc: selection._access._resolve(loc)[1])
            ) == canonical_json(
                locations(old, lambda loc: state["locations"][loc["location_ref"]])
            )
        unretained = root.filter(
            "measurement",
            equals={"value": 33000, "unit": "nanomolar"},
            skip_digestion=True,
        )
        assert len(unretained.items()) == 1
        assert (
            unretained._display_request
            != observed("target/node/filtered")["display_request"]
        )
        assert not any(
            unretained.capabilities[key] for key in ("related", "explain", "save")
        )
        assert unretained.items()[0].related().outcome["status"] == "not_saved"
        assert unretained.items()[0].explain().outcome["status"] == "not_saved"
        from sabueso.core.errors import StorageError

        refused = Path.cwd() / "unretained-molecule-display.json"
        with pytest.raises(StorageError, match="closure was not retained"):
            unretained.save(refused, skip_digestion=True)
        assert not refused.exists()
        assert (
            len(actual["target/publication/pubmed:35189560"].native_payload["links"])
            == 9
        )
        assert (
            len(actual["target/publication/pubmed:20889239"].native_payload["links"])
            == 459
        )
        report = {
            "actual_file": str(path),
            "native_original_human_views": len(actual),
            "original_machine_requests_and_pages": len(graph["machine"]),
            "current_cards_science_sources_digesters_and_molecule_ui_forbidden": True,
            "runtime": sabueso.__version__,
            "import_path": sabueso.__file__,
            "cwd": str(Path.cwd()),
            "publication_links": [9, 459],
            "saved_activity_menu_retained": True,
            "capabilities_bound_to_actual_operation_history": True,
        }
        Path(report_path).write_text(json.dumps(report, indent=2) + "\n")
    archive.close()
    print(json.dumps(report))


def _transport_receive(codec, original, original_tar, output_directory):
    import importlib
    import json
    from pathlib import Path

    import pytest
    from test_card_molecule_activity_binding_offline import block_current

    import sabueso

    directory = Path(output_directory)
    directory.mkdir()
    for name in (
        "card_molecule_activity_exploration",
        "card_literature_exploration",
        "card_bioactivity_exploration",
    ):
        importlib.import_module("sabueso.core." + name)
    with pytest.MonkeyPatch.context() as guard:
        block_current(guard)
        saved = sabueso.read_exploration(
            original,
            max_encoded_bytes=None,
            max_decoded_bytes=None,
            max_logical_bytes=None,
        )
        path = directory / ("again.json" if codec == "none" else "again.json." + codec)
        saved.save(
            path,
            compression=codec,
            max_encoded_bytes=None,
            max_decoded_bytes=None,
            max_logical_bytes=None,
        )
    _independent_receive(
        str(path), str(original_tar), str(directory / "reader-report.json")
    )
    print(
        json.dumps(
            {"codec": codec, "resaved_file": str(path), "bytes": path.stat().st_size}
        )
    )


def test_all_transports_resave_original_graph_in_independent_receivers(
    saved_original, tmp_path
):
    from concurrent.futures import ThreadPoolExecutor

    source = (
        "import sys\nsys.path.insert(0, sys.argv[5])\n"
        + inspect.getsource(_independent_receive)
        + "\n"
        + inspect.getsource(_transport_receive)
        + "\n_transport_receive(*sys.argv[1:5])\n"
    )

    def receive(codec):
        with tempfile.TemporaryDirectory(
            prefix="sabueso-molecule-transport-",
            dir=None if sys.platform == "win32" else "/tmp",
        ) as cwd:
            process = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    source,
                    codec,
                    str(saved_original["path"]),
                    str(saved_original["tar"]),
                    str(tmp_path / codec),
                    str(Path(__file__).resolve().parent),
                ],
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=900,
            )
        assert process.returncode == 0, process.stdout + process.stderr
        assert not process.stderr, process.stderr

    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(receive, ("none", "gzip", "zstd")))


@pytest.fixture(scope="module")
def logical_original(saved_original):
    import json

    from sabueso.core.card_exploration_shared_values_v5 import unpack

    packed = json.loads(saved_original["path"].read_text())
    logical, _ = unpack(packed, None, limit=None, component_limit=None)
    return logical


@pytest.mark.parametrize(
    "change",
    (
        "source_history",
        "missing_operation",
        "quantity_unit",
        "missing_crossing",
        "publication_scope",
        "selection_membership",
    ),
)
def test_resealed_original_bundle_refuses_semantic_changes(
    logical_original, change, monkeypatch
):
    from test_card_molecule_activity_binding_offline import block_current

    from sabueso.core.card_exploration_shared_values_v5 import pack
    from sabueso.core.card_exploration_storage import _restore, _seal
    from sabueso.core.errors import StorageError

    block_current(monkeypatch)
    base = logical_original
    altered = {**base}
    if change in ("source_history", "missing_operation"):
        altered["molecule_activity_operations"] = deepcopy(
            base["molecule_activity_operations"]
        )
        records = altered["molecule_activity_operations"]
        key, operation = next(
            (key, value)
            for key, value in records.items()
            if value["operation"] == "links"
            and isinstance(
                base["views"][value["source"]]["flags"]["_display_request"], dict
            )
            and type(
                base["views"][value["source"]]["flags"]["_display_request"]
                .get("equals", {})
                .get("value")
            )
            is int
        )
        if change == "missing_operation":
            del records[key]
        else:
            altered["views"] = {**base["views"]}
            original = base["views"][operation["source"]]
            other = next(
                node
                for node, view in base["views"].items()
                if view["view_ref"] == original["view_ref"]
                and view["flags"]["_display_request"]
                != original["flags"]["_display_request"]
            )
            destination = operation["destinations"][0]
            altered["views"][destination] = {
                **base["views"][destination],
                "origin": other,
            }
            operation["source"] = other
            del records[key]
            from sabueso.core.card_molecule_activity_operations_v1 import _key

            records[_key(other, "links", operation["row_key"])] = operation
    elif change == "missing_crossing":
        altered["molecule_activity_crossings"] = {}
    elif change in ("quantity_unit", "publication_scope"):
        altered["objects"] = {**base["objects"]}
        adapter = (
            binding.ADAPTER if change == "quantity_unit" else "literature_exploration@1"
        )
        reference = next(
            ref
            for ref in base["scientific_results"]
            if base["objects"][ref]["context"]["adapter"] == adapter
            and (
                change == "quantity_unit"
                or "pubmed:20889239" in base["objects"][ref]["explanations"]
            )
        )
        wire = deepcopy(base["objects"][reference])
        altered["objects"][reference] = wire
        if change == "quantity_unit":
            row = next(
                row for row in wire["rows"].values() if row["measurement"] is not None
            )
            row["measurement"]["unit"] = "micromolar"
        else:
            wire["explanations"]["pubmed:20889239"]["links"].pop()
    else:
        altered["views"] = {**base["views"]}
        key = base["root_navigation_ref"]
        altered["views"][key] = {**base["views"][key], "selected": []}
    # Rebuild every physical Merkle identifier and both digest layers. Failure
    # must come from retained semantic binding, not stale integrity hashes.
    packed = _seal(pack(altered, None, threshold=0, min_saving=0))
    with pytest.raises(StorageError):
        _restore(packed, None, owned=True, max_logical_bytes=None, component_limit=None)
