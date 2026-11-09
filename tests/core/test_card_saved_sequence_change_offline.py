"""Actual sequence-change files, independent receiving and semantic refusals."""

import json
import os
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest
from test_card_sequence_change_history_offline import (
    assert_saved_original,
    block_current,
    hydrate_original,
    original_navigation_ids,
)
from test_card_sequence_change_original_offline import CASES
from test_card_sequence_change_original_offline import original as original

import sabueso
from sabueso.core import card_exploration_storage as storage
from sabueso.core.card_exploration_shared_values_v10 import pack, unpack
from sabueso.core.errors import ArgumentError, StorageError


@pytest.mark.parametrize(
    "question", ["variant_tissue_context", "isoform_tissue_context"]
)
def test_observed_variant_questions_keep_exact_scope_in_sequence_bundle(
    question, monkeypatch, tmp_path
):
    from test_card_sequence_changes_offline import synthetic

    from sabueso.core.source_assertion_store import make_source_assertion
    from sabueso.core.tissue_usage import ISOFORMS, VARIANTS

    card = synthetic()
    for path, value in (
        (VARIANTS, [{"variant_id": "synthetic-variant", "assembly": "GRCh38"}]),
        (ISOFORMS, [{"isoform_id": "synthetic-isoform", "name": "synthetic"}]),
    ):
        assertion = make_source_assertion(
            path,
            value,
            "synthetic",
            path,
            "labelled synthetic mixed-panel control",
            subject_ref="uniprot:P60174",
        )
        ref = card.source_assertion_store.add(assertion)
        card.set(path, value, [ref])
    explorer = card.explore()
    observed = explorer.answer(question)
    assert observed.items()
    root = explorer.answer("sequence_changes")
    expected = observed.request
    block_current(monkeypatch)
    path = tmp_path / "mixed.json.gz"
    root.save(path, compression="gzip")
    saved = sabueso.read_exploration(path)
    retained = saved.explorer.answer(question)
    assert retained.outcome["status"] != "not_saved"
    assert retained.request == expected
    assert retained.result_ref == observed.result_ref
    assert retained.native_payload == observed.native_payload
    assert [item.item_ref for item in retained.items()] == [
        item.item_ref for item in observed.items()
    ]
    with pytest.raises(ArgumentError):
        saved.explorer.answer(question, options={"mode": "unrecognized"})


@pytest.mark.parametrize("name", CASES)
def test_original_sequence_file_receives_with_current_science_forbidden(
    original, monkeypatch, tmp_path, name
):
    original.cache.clear()
    nodes, records, accesses = hydrate_original(original, name, include_accesses=True)
    case = original.case(name)
    ids = original_navigation_ids(nodes) if nodes else {}
    root = (
        nodes[case["named_views"]["root"]]
        if nodes
        else accesses[case["root_access_node"]]._selections[
            case["queries"][0]["selection_ref"]
        ]
    )
    path = tmp_path / "original.json.gz"
    block_current(monkeypatch)
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
    assert saved.validation["verifier"] == "sequence_change_exploration_binding@1"
    assert_saved_original(saved, original, name, ids)
    if name == "machine-only":
        assert saved._machine_ref is not None
        assert saved.explorer.view("sequence_changes").outcome["status"] == "not_saved"
        assert (
            saved.explorer.answer("sequence_changes").outcome["status"] == "not_saved"
        )
    if name == "human-only":
        assert (
            saved.explorer.access.select(
                "sequence_changes", skip_digestion=True
            )._outcome_override["status"]
            == "not_saved"
        )


@pytest.fixture(scope="module")
def sequence_file(original, tmp_path_factory):
    name = "uncertain-start"
    original.cache.clear()
    nodes, _ = hydrate_original(original, name)
    ids = original_navigation_ids(nodes)
    root = nodes[original.case(name)["named_views"]["root"]]
    path = tmp_path_factory.mktemp("sequence-original-file") / "original.json"
    with pytest.MonkeyPatch.context() as guard:
        block_current(guard)
        root.save(
            path, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    logical = (
        unpack(raw, limit=None, component_limit=None)[0]
        if raw["format"] == "sabueso.card_exploration@32"
        else {
            key: value
            for key, value in raw.items()
            if key not in ("digests", "bundle_digest")
        }
    )
    return path, logical, ids


def test_unchanged_fully_resealed_sequence_file_is_accepted(sequence_file, monkeypatch):
    block_current(monkeypatch)
    packet = storage._seal(pack(sequence_file[1], None, threshold=0, min_saving=0))
    assert packet["format"] == "sabueso.card_exploration@32"
    restored = storage._restore(
        packet, packet["bundle_digest"], max_logical_bytes=None, component_limit=None
    )
    assert restored.validation["verifier"] == "sequence_change_exploration_binding@1"


@pytest.mark.parametrize(
    "mutation",
    [
        "native",
        "position",
        "alternatives",
        "missing",
        "original_location",
        "support",
        "coverage",
        "interpretation",
        "cell",
        "cell_state",
        "question",
        "source",
        "origin",
        "typed_filter",
        "access_merge",
        "access_split",
    ],
)
def test_fully_resealed_sequence_semantic_changes_are_refused(
    sequence_file, monkeypatch, mutation
):
    logical = deepcopy(sequence_file[1])
    ref = next(
        ref
        for ref in logical["scientific_results"]
        if logical["objects"][ref]["context"]["adapter"]
        == "sequence_change_exploration@1"
    )
    wire = logical["objects"][ref]
    key = next(iter(wire["rows"]))
    scientific_views = [
        view
        for view in logical["views"].values()
        if view["flags"]["_record_panel"] == "sequence_changes"
    ]
    if mutation == "native":
        wire["native_payload"]["items"][0]["description"] = "foreign"
    elif mutation == "position":
        wire["rows"][key]["start"] = 999
    elif mutation == "alternatives":
        wire["rows"][key]["alternatives"] = ["A"]
    elif mutation == "missing":
        wire["rows"][key]["missing"] = False
    elif mutation == "original_location":
        wire["rows"][key]["original_location"]["segments"][-1]["value"] = 99
    elif mutation == "support":
        wire["support"][key]["source_assertions"] = []
    elif mutation == "coverage":
        wire["coverage"]["field_states"]["natural_variant"] = "retained_empty"
    elif mutation == "interpretation":
        wire["rows"][key]["interpretation"]["row_grain"] = "unique native feature"
    elif mutation in ("cell", "cell_state"):
        item = next(iter(scientific_views[0]["state"]["items"].values()))
        item["cells"]["start"]["value" if mutation == "cell" else "state"] = (
            999 if mutation == "cell" else "unknown"
        )
    elif mutation == "question":
        scientific_views[0]["flags"]["_request"] = {
            "question": "foreign",
            "topic": "sequence_changes",
            "options": {},
        }
    elif mutation == "source":
        capture = next(iter(logical["cards"].values()))
        capture["data"]["source_assertion_store"][0]["subject_ref"] = "uniprot:FOREIGN"
    elif mutation == "origin":
        view = next(
            view
            for view in logical["views"].values()
            if view["explorer_origin"] is not None and view["origin"] is not None
        )
        view["origin"] = None
    elif mutation == "typed_filter":
        view = next(
            view
            for view in scientific_views
            if (view["flags"]["_display_request"] or {}).get("operation") == "filter"
        )
        view["flags"]["_display_request"]["column"] = "start"
        view["flags"]["_display_request"]["equals"] = 2.0
    else:
        manifest = logical["sequence_change_access_origins"]
        child = next(
            name
            for name, view in logical["views"].items()
            if view["explorer_origin"] is not None and view["origin"] is not None
        )
        original_access = manifest["views"][child]["explorer"]
        if mutation == "access_merge":
            parent = logical["views"][child]["origin"]
            parent_access = manifest["views"][parent]["explorer"]
            assert original_access != parent_access
            for binding in manifest["views"].values():
                for field, value in list(binding.items()):
                    if value == original_access:
                        binding[field] = parent_access
            del manifest["instances"][original_access]
        else:
            # A literal child must retain the access of the actual source view.
            descendant = next(
                name
                for name, view in logical["views"].items()
                if view["origin"] == child
            )
            manifest["instances"]["A99999"] = deepcopy(
                manifest["instances"][original_access]
            )
            manifest["views"][descendant] = {
                "explorer": "A99999",
                "selection": "A99999",
            }
    packet = storage._seal(pack(logical, None, threshold=0, min_saving=0))
    block_current(monkeypatch)
    with pytest.raises(StorageError):
        storage._restore(
            packet,
            packet["bundle_digest"],
            max_logical_bytes=None,
            component_limit=None,
        )


@pytest.mark.parametrize("compression", ["none", "gzip", "zstd"])
def test_sequence_resave_preserves_original_instances_and_typed_requests(
    sequence_file, original, monkeypatch, tmp_path, compression
):
    block_current(monkeypatch)
    saved = sabueso.read_exploration(
        sequence_file[0],
        max_encoded_bytes=None,
        max_decoded_bytes=None,
        max_logical_bytes=None,
    )
    target = tmp_path / ("resaved." + compression)
    saved.save(
        target,
        compression=compression,
        max_encoded_bytes=None,
        max_decoded_bytes=None,
        max_logical_bytes=None,
    )
    again = sabueso.read_exploration(
        target, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
    )
    assert_saved_original(again, original, "uncertain-start", sequence_file[2])


@pytest.mark.parametrize(
    "name",
    [
        "public-human-first",
        "public-machine-first",
        "synthetic-mixed",
        "uncertain-start",
    ],
)
def test_original_sequence_file_receives_in_fresh_outside_checkout_process(
    original, monkeypatch, tmp_path, name
):
    original.cache.clear()
    nodes, _ = hydrate_original(original, name)
    root = nodes[original.case(name)["named_views"]["root"]]
    ids = original_navigation_ids(nodes)
    path = tmp_path / "independent.json.gz"
    block_current(monkeypatch)
    root.save(
        path,
        compression="gzip",
        max_encoded_bytes=None,
        max_decoded_bytes=None,
        max_logical_bytes=None,
    )
    ids_path = tmp_path / "ids.json"
    ids_path.write_text(json.dumps(ids), encoding="utf-8")
    code = "import sys; sys.path.insert(0,sys.argv[5]); from test_card_sequence_change_history_offline import independent_receive; independent_receive(*sys.argv[1:5])"
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    with tempfile.TemporaryDirectory(
        prefix="sabueso-sequence-independent-",
        dir=os.environ.get("RUNNER_TEMP") if os.name == "nt" else "/tmp",
    ) as cwd:
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
    assert json.loads(received.stdout)["state"] == "PASS"
