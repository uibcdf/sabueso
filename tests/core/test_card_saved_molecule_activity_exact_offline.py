"""Real @23/@24 files over both immutable clean SDK218 LIVE originals.

Writer facades retain original data; inert receivers cannot use current science,
Cards or LIVE UI. Public saving and independent receiving use the admitted new binding.
"""

import importlib
import inspect
import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest
from test_card_molecule_activity_exact_binding_offline import (
    DECODED_SHA,
    ExactGraph,
)
from test_card_molecule_activity_exact_binding_offline import (
    original_tar as original_tar,
)
from test_card_molecule_activity_history_offline import block_current as block_science
from test_card_saved_molecule_activity_offline import (
    _independent_receive,
    _prepare_retained_writer,
)

from sabueso.core import card_exploration_molecule_activity_v2 as binding
from sabueso.core import card_exploration_storage as storage
from sabueso.core.errors import StorageError


@pytest.fixture(scope="module", params=("node-first", "quantity-first"))
def exact_writer(request, original_tar):
    for name in (
        "card_molecule_activity_exploration",
        "card_bioactivity_exploration",
        "card_literature_exploration",
    ):
        importlib.import_module("sabueso.core." + name)
    with pytest.MonkeyPatch.context() as guard:
        block_science(guard)
        graph = ExactGraph(original_tar, request.param)
        _prepare_retained_writer(graph, binding.ROOT_RETURN_POLICY)
        yield graph, request.param
        graph.archive.close()
        graph.cache.clear()


@pytest.fixture(scope="module")
def saved_exact_original(exact_writer, tmp_path_factory):
    graph, order = exact_writer
    root, _ = graph.named("root")
    path = tmp_path_factory.mktemp("exact-origin-file-" + order) / "original.json"
    receipt = root.save(
        path,
        max_encoded_bytes=None,
        max_decoded_bytes=None,
        max_logical_bytes=None,
    )
    assert path.is_file()
    raw = json.loads(path.read_text())
    assert raw["format"] in (binding.FORMAT, "sabueso.card_exploration@24")
    assert receipt["bundle_digest"] == raw["bundle_digest"]
    return {"graph": graph, "order": order, "path": path, "raw": raw}


def test_complete_sdk218_original_writes_and_reads_inertly(
    saved_exact_original, tmp_path
):
    graph = saved_exact_original["graph"]
    order, path = saved_exact_original["order"], saved_exact_original["path"]
    report = tmp_path / "reader-report.json"
    _receive_exact_original(path, graph, order, report)


def _receive_exact_original(path, graph, order, report):
    script = (
        "import sys\nsys.path.insert(0, sys.argv[4])\n"
        + inspect.getsource(_independent_receive)
        + "\n_independent_receive(*sys.argv[1:4], original_sha=sys.argv[5], original_prefix=sys.argv[6])\n"
    )
    with tempfile.TemporaryDirectory(
        prefix="sabueso-exact-molecule-reader-",
        dir=None if sys.platform == "win32" else "/tmp",
    ) as directory:
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                script,
                str(path),
                graph.archive.name,
                str(report),
                str(Path(__file__).resolve().parent),
                DECODED_SHA,
                order + "/",
            ],
            cwd=directory,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=900,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not result.stderr, result.stderr
    result = json.loads(report.read_text())
    assert result["native_original_human_views"] == 96
    assert result["original_machine_requests_and_pages"] == 6
    assert result["verified_navigation_policies"] == [binding.ROOT_RETURN_POLICY]
    assert result["typed_root_return"] == {
        "requested_type": "float",
        "returned_type": "float",
    }


@pytest.fixture(scope="module")
def logical_exact_original(saved_exact_original):
    from sabueso.core.card_exploration_shared_values_v6 import unpack

    raw = saved_exact_original["raw"]
    if raw["format"] == binding.FORMAT:
        return {
            key: value
            for key, value in raw.items()
            if key not in ("digests", "bundle_digest")
        }
    logical, _ = unpack(raw, limit=None, component_limit=None)
    return logical


@pytest.mark.parametrize(
    "change",
    (
        "policy",
        "missing_origin",
        "foreign_instance",
        "numeric_type",
        "extra_origin",
        "quantity_unit",
        "publication_scope",
        "selection_membership",
    ),
)
def test_fully_resealed_root_semantic_changes_are_refused(
    logical_exact_original, change
):
    from test_card_molecule_activity_binding_offline import block_current

    from sabueso.core.card_exploration_shared_values_v6 import pack

    logical = {**logical_exact_original}
    roots = logical[binding.MEMBER] = deepcopy(logical[binding.MEMBER])
    source, target = next(iter(roots["origins"].items()))
    if change == "policy":
        roots["rule"] = binding.original.ROOT_RETURN_EQUALITY
    elif change == "missing_origin":
        roots["origins"].pop(source)
    elif change == "foreign_instance":
        roots["origins"][source] = source
    elif change == "extra_origin":
        roots["origins"][target] = target
    elif change == "numeric_type":
        source = next(
            key
            for key, record in logical["views"].items()
            if key in roots["origins"]
            and record["flags"]["_display_request"] is not None
            and type(record["flags"]["_display_request"]["equals"]["value"]) is float
        )
        logical["views"] = {**logical["views"]}
        record = logical["views"][source] = {**logical["views"][source]}
        record["flags"] = deepcopy(record["flags"])
        record["flags"]["_display_request"]["equals"]["value"] = 33
    elif change == "selection_membership":
        logical["views"] = {**logical["views"]}
        source = logical["root_navigation_ref"]
        logical["views"][source] = {**logical["views"][source], "selected": []}
    else:
        logical["objects"] = {**logical["objects"]}
        adapter = (
            binding.original.ADAPTER
            if change == "quantity_unit"
            else "literature_exploration@1"
        )
        reference = next(
            ref
            for ref in logical["scientific_results"]
            if logical["objects"][ref]["context"]["adapter"] == adapter
            and (
                change == "quantity_unit"
                or "pubmed:20889239" in logical["objects"][ref]["explanations"]
            )
        )
        wire = logical["objects"][reference] = deepcopy(logical["objects"][reference])
        if change == "quantity_unit":
            row = next(
                row for row in wire["rows"].values() if row["measurement"] is not None
            )
            row["measurement"]["unit"] = "micromolar"
        else:
            wire["explanations"]["pubmed:20889239"]["links"].pop()
    # Rebuild all physical identifiers and digests without allocating the large
    # repeated logical JSON document solely for hashing it.
    packed = storage._seal(pack(logical, None, threshold=0, min_saving=0))
    message = (
        "typed originating root|molecule original navigation history"
        if change == "numeric_type"
        else "originating-root policy"
        if change == "policy"
        else "exact originating root instances"
        if change in ("missing_origin", "foreign_instance", "extra_origin")
        else None
    )
    with pytest.MonkeyPatch.context() as guard:
        block_current(guard)
        with pytest.raises(StorageError, match=message):
            storage._restore(
                packed,
                packed["bundle_digest"],
                max_logical_bytes=None,
                component_limit=None,
            )


@pytest.mark.parametrize("compression", ("none", "gzip", "zstd"))
def test_transport_and_resave_preserve_complete_original(
    saved_exact_original, tmp_path, compression
):
    from test_card_molecule_activity_binding_offline import block_current

    import sabueso

    graph = saved_exact_original["graph"]
    with pytest.MonkeyPatch.context() as guard:
        block_current(guard)
        root = sabueso.read_exploration(
            saved_exact_original["path"],
            max_encoded_bytes=None,
            max_decoded_bytes=None,
            max_logical_bytes=None,
        )
        assert root.validation["verified_navigation_policies"] == [
            binding.ROOT_RETURN_POLICY
        ]
        path = tmp_path / ("resaved-" + compression + ".json")
        receipt = root.save(
            path,
            compression=compression,
            max_encoded_bytes=None,
            max_decoded_bytes=None,
            max_logical_bytes=None,
        )
        assert path.is_file() and receipt["bundle_digest"].startswith("sha256:")
        _receive_exact_original(
            path,
            graph,
            saved_exact_original["order"],
            tmp_path / "receiver.json",
        )
