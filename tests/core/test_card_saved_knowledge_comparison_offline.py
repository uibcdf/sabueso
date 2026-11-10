"""Actual knowledge-comparison saved files and independent original receiving."""

import pytest
from test_card_knowledge_comparison_history_offline import (
    assert_saved_original,
    block_current,
    hydrate_original,
    original_navigation_ids,
)
from test_card_knowledge_comparison_original_offline import CASES
from test_card_knowledge_comparison_original_offline import original as original

import sabueso

# The archived public cases deliberately observe every row/source/parent graph.
# Their complete ensemble scope exceeds ordinary session defaults. Only these
# explicit test callers enlarge the logical allowance; transport/API defaults
# and every original member/view/request remain unchanged.
ORIGINAL_LOGICAL_LIMIT = 2 * 1024**3


def original_budgets(name):
    return (
        {"max_logical_bytes": ORIGINAL_LOGICAL_LIMIT}
        if name.startswith("public-")
        else {}
    )


@pytest.mark.parametrize("shared", [False, True])
def test_observed_question_catalog_without_executed_science_is_saved(
    tmp_path, monkeypatch, shared
):
    from test_card_knowledge_comparison_offline import options, pair

    left, right = pair()
    menu = left.explore(related_cards=[right]).questions()
    assert not menu.explorer.access._scientific_cache
    path = tmp_path / "catalog-only.json"
    if shared:
        import json

        from sabueso.core import card_exploration_storage as storage
        from sabueso.core.card_exploration_shared_values_v12 import pack

        # Exercise the shared decoder even when this small catalog costs more
        # to pack than literal JSON; no public budget or packing default changes.
        packet = storage._seal(
            pack(storage._prepare(menu), threshold=0, min_saving=-(1024**2))
        )
        assert packet["format"] == "sabueso.card_exploration@36"
        path.write_text(json.dumps(packet))
    else:
        menu.save(path)
    block_current(monkeypatch)
    saved = sabueso.read_exploration(path)
    assert saved.validation["verified_scientific_adapters"] == []
    assert "knowledge_differences" in saved.explorer._questions
    assert (
        saved.explorer.answer(
            "knowledge_differences", options=options(saved.explorer)
        ).outcome["status"]
        == "not_saved"
    )


@pytest.mark.parametrize("name", CASES)
def test_original_knowledge_comparison_file_receives_inertly(
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
    root.save(path, compression="gzip", **original_budgets(name))
    saved = sabueso.read_exploration(path, **original_budgets(name))
    assert saved.validation["verifier"] == "knowledge_comparison_exploration_binding@1"
    assert (
        "protein_knowledge_comparison_exploration@1"
        in saved.validation["verified_scientific_adapters"]
    )
    assert "sequence_changes" not in saved.validation
    assert_saved_original(saved, original, name, ids)
    if name == "machine-only":
        assert (
            saved.explorer.view(case["topic"], options=case["options"]).outcome[
                "status"
            ]
            == "not_saved"
        )
        assert (
            saved.explorer.answer(case["question"], options=case["options"]).outcome[
                "status"
            ]
            == "not_saved"
        )
    if name == "human-only":
        assert (
            saved.explorer.access.select(
                case["topic"], options=case["options"], skip_digestion=True
            )._outcome_override["status"]
            == "not_saved"
        )


@pytest.fixture(scope="module")
def logical_original(original):
    from sabueso.core import card_exploration_storage as storage

    original.cache.clear()
    nodes, records = hydrate_original(original, "zero-false")
    case = original.case("zero-false")
    return storage._prepare(nodes[case["named_views"]["root"]])


@pytest.mark.parametrize(
    "defect",
    [
        "selected-value",
        "conflict",
        "support",
        "interpretation",
        "native-item",
        "cell",
        "question",
        "access-boundary",
    ],
)
def test_fully_resealed_semantic_changes_are_refused(logical_original, defect):
    from copy import deepcopy

    from sabueso.core import card_exploration_storage as storage
    from sabueso.core.errors import StorageError

    wire = deepcopy(logical_original)
    result_ref = next(
        ref
        for ref in wire["scientific_results"]
        if wire["objects"][ref]["context"]["adapter"]
        == "protein_knowledge_comparison_exploration@1"
    )
    result = wire["objects"][result_ref]
    row = next(
        value
        for value in result["rows"].values()
        if value["label"] == "annotations.taxon_id"
    )
    if defect == "selected-value":
        row["item"]["self"] = True
    elif defect == "conflict":
        row["item"]["conflicts"] = {"self": ["foreign"]}
    elif defect == "support":
        result["support"][next(iter(result["support"]))]["inputs"][0]["role"] = (
            "foreign"
        )
    elif defect == "interpretation":
        row["interpretation"]["scope"] = "synthetic different interpretation"
    elif defect == "native-item":
        result["native_payload"]["fields"]["annotations.taxon_id"]["self"] = True
    elif defect == "cell":
        record = next(
            value
            for value in wire["views"].values()
            if value["flags"]["_record_panel"] == "protein_context"
            and value["state"]["items"]
        )
        next(iter(record["state"]["items"].values()))["cells"]["state"]["value"] = (
            "synthetic different state"
        )
    elif defect == "question":
        record = next(
            value
            for value in wire["views"].values()
            if value["flags"]["_record_panel"] == "protein_context"
            and value["flags"]["_request"]
        )
        record["flags"]["_request"]["question"] = "related_proteins"
    else:
        member = wire["knowledge_comparison_access_origins"]
        key = next(
            key
            for key, record in wire["views"].items()
            if record["origin"] is not None
            and record["explorer_origin"] == record["origin"]
            and wire["views"][record["origin"]]["flags"]["_link_panel"]
            and not record["flags"]["_context_only"]
            and wire["views"][record["origin"]]["focal"] == record["focal"]
        )
        parent = wire["views"][key]["origin"]
        member["views"][key] = dict(member["views"][parent])
        used = {ref for record in member["views"].values() for ref in record.values()}
        member["instances"] = {
            key: record for key, record in member["instances"].items() if key in used
        }
    storage._seal(wire)
    with pytest.raises(StorageError):
        storage._restore(wire, wire["bundle_digest"])


def test_unchanged_fully_resealed_logical_original_is_accepted(logical_original):
    from copy import deepcopy

    from sabueso.core import card_exploration_storage as storage

    wire = deepcopy(logical_original)
    storage._seal(wire)
    assert (
        storage._restore(wire, wire["bundle_digest"]).validation["verifier"]
        == "knowledge_comparison_exploration_binding@1"
    )


@pytest.mark.parametrize("compression", ["none", "gzip", "zstd"])
def test_original_resave_preserves_values_and_instance_manifest(
    original, monkeypatch, tmp_path, compression
):
    from sabueso.core import card_exploration_storage as storage

    original.cache.clear()
    nodes, records = hydrate_original(original, "zero-false")
    case = original.case("zero-false")
    ids = original_navigation_ids(nodes)
    root = nodes[case["named_views"]["root"]]
    first = tmp_path / "first.json.gz"
    block_current(monkeypatch)
    root.save(first, compression="gzip")
    before = sabueso.read_exploration(first)
    after_path = tmp_path / ("resaved-" + compression)
    before.save(after_path, compression=compression)
    after = sabueso.read_exploration(after_path)
    assert_saved_original(after, original, "zero-false", ids)
    previous = storage._prepare(before)["knowledge_comparison_access_origins"]
    current = storage._prepare(after)["knowledge_comparison_access_origins"]
    assert previous == current


@pytest.mark.parametrize(
    "name", ["public-unmapped-human-first", "public-supplied-map", "zero-false"]
)
def test_original_receives_in_fresh_outside_checkout_process(
    original, monkeypatch, tmp_path, name
):
    import json
    import os
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    original.cache.clear()
    nodes, records = hydrate_original(original, name)
    case = original.case(name)
    ids = original_navigation_ids(nodes)
    root = nodes[case["named_views"]["root"]]
    path = tmp_path / "receiving.json.gz"
    ids_path = tmp_path / "actual-origin-ids.json"
    ids_path.write_text(json.dumps(ids), encoding="utf-8")
    block_current(monkeypatch)
    root.save(path, compression="gzip", **original_budgets(name))
    script = r"""
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[2])
from pytest import MonkeyPatch
from test_card_knowledge_comparison_original_offline import Original
from test_card_knowledge_comparison_history_offline import block_current,assert_saved_original
import sabueso
assert not Path.cwd().resolve().is_relative_to(Path(sabueso.__file__).resolve().parents[1])
with MonkeyPatch.context() as guard:
    block_current(guard)
    saved=sabueso.read_exploration(sys.argv[1],**({'max_logical_bytes':2*1024**3} if sys.argv[4].startswith('public-') else {}))
    original=Original(Path(sys.argv[3]))
    ids=json.loads(Path(sys.argv[5]).read_text())
    assert_saved_original(saved,original,sys.argv[4],ids)
print('PASS independent fresh receiving')
"""
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    temporary_root = Path(tempfile.gettempdir())
    package_root = Path(sabueso.__file__).resolve().parents[1]
    if temporary_root.resolve().is_relative_to(package_root):
        temporary_root = (
            Path("/tmp")
            if os.name != "nt"
            else Path(os.environ["LOCALAPPDATA"]) / "Temp"
        )
    assert not temporary_root.resolve().is_relative_to(package_root)
    with tempfile.TemporaryDirectory(
        prefix="sabueso-protein-reader-", dir=temporary_root
    ) as working:
        received = subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                script,
                str(path),
                str(Path(__file__).resolve().parent),
                str(original.directory),
                name,
                str(ids_path),
            ],
            cwd=working,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
    assert received.returncode == 0, received.stdout
    assert "PASS independent fresh receiving" in received.stdout


@pytest.mark.parametrize("altered", [False, True])
def test_resealed_shared_representation_checks_original_meaning(
    logical_original, altered
):
    from copy import deepcopy

    from sabueso.core import card_exploration_storage as storage
    from sabueso.core.card_exploration_shared_values_v12 import pack
    from sabueso.core.errors import StorageError

    logical = deepcopy(logical_original)
    if altered:
        result = next(
            value
            for value in logical["objects"].values()
            if isinstance(value, dict)
            and value.get("context", {}).get("adapter")
            == "protein_knowledge_comparison_exploration@1"
            and "native_payload" in value
        )
        result["native_payload"]["fields"]["annotations.taxon_id"]["self"] = True
    packet = storage._seal(pack(logical, threshold=0, min_saving=0))
    assert packet["format"] == "sabueso.card_exploration@36"
    if altered:
        with pytest.raises(StorageError):
            storage._restore(packet, packet["bundle_digest"])
    else:
        assert (
            storage._restore(packet, packet["bundle_digest"]).validation["verifier"]
            == "knowledge_comparison_exploration_binding@1"
        )


def test_observed_older_protein_variant_and_sequence_profiles_keep_own_meaning(
    monkeypatch, tmp_path
):
    from test_card_sequence_changes_offline import synthetic

    card = synthetic()
    other = synthetic()
    explorer = card.explore(related_cards=[other])
    root = explorer.answer(
        "knowledge_differences", options={"other_ref": explorer.context["inputs"][1]}
    )
    older = explorer.answer("protein_associations")
    sequence = explorer.answer("sequence_changes")
    variant = explorer.answer("variant_tissue_context")
    path = tmp_path / "co-retained.json.gz"
    root.save(path, compression="gzip")
    block_current(monkeypatch)
    saved = sabueso.read_exploration(path)
    for question, observed in [
        ("protein_associations", older),
        ("sequence_changes", sequence),
        ("variant_tissue_context", variant),
    ]:
        retained = saved.explorer.answer(question)
        assert retained.result_ref == observed.result_ref
        assert retained.native_payload == observed.native_payload


def test_nonempty_bioactivity_catalog_crossing_keeps_original_knowledge_question(
    monkeypatch, tmp_path
):
    import json
    from copy import deepcopy

    from test_card_knowledge_diff_v2_offline import DATA, card

    from sabueso.core.aggregator import build_card_from_mapping
    from sabueso.mappings.uniprot import map_protein

    frozen = json.loads(
        (DATA / "frozen_cards/schema_0.3.9__P52270.json").read_text(encoding="utf-8")
    )
    record = next(
        row
        for row in frozen["relationship_store"]
        if row["predicate"] == "has_bioactivity"
    )
    left = build_card_from_mapping(
        map_protein(
            {"primaryAccession": "P52270", "sequence": {"value": "MAGR", "length": 4}},
            "labelled synthetic context",
        ),
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:P52270",
    )
    right = card("RIGHT")
    for assertion in frozen["source_assertion_store"]:
        if assertion["id"] in record["source_assertion_ids"]:
            left.source_assertion_store.add(deepcopy(assertion))
    left.relationship_store.add(deepcopy(record))
    explorer = left.explore(related_cards=[right])
    root = explorer.answer(
        "knowledge_differences", options={"other_ref": explorer.context["inputs"][1]}
    )
    links = root.items()[0].related()
    whole = links.filter("role", equals="whole_card_context").items()[0].open()
    activity = next(
        item for item in whole.items() if item._entry.key == "bioactivities"
    ).open()
    assert activity.request == root.request and activity.items()
    path = tmp_path / "mixed-knowledge-context.json.gz"
    activity.save(path, compression="gzip")
    block_current(monkeypatch)
    loaded = sabueso.read_exploration(path)
    assert loaded.request == root.request
    assert loaded.back().request == root.request
    assert loaded.native_payload == activity.native_payload
    assert [item.item_ref for item in loaded.items()] == [
        item.item_ref for item in activity.items()
    ]
