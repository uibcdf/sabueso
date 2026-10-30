"""Original assembly findings and exact human/agent requests survive inert reading."""

import gzip
import hashlib
import importlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_capture import _Capture
from sabueso.core.card_exploration_history import _require_matches
from sabueso.core.card_exploration_storage import _access, _seal
from sabueso.core.errors import StorageError

TOPIC = "assembly_generation"
OPTIONS = {"structure_ref": "pdb:2V5B"}
CAPSULE = Path(__file__).parent / "data/assembly_live_v1.json.gz"


def forbidden(*args, **kwargs):
    raise AssertionError("No live Card, scientific reader, catalog or acquisition")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def originals():
    return json.loads(gzip.decompress(CAPSULE.read_bytes()))


@pytest.fixture
def card(originals):
    return Card.from_dict(deepcopy(originals["cases"]["2V5B"]["card"]))


def inert(monkeypatch):
    monkeypatch.setattr(Card, "__init__", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    for name, methods in {
        "assembly_generation_v1": ["generation"],
        "assembly_generation_v2": ["generation"],
        "assembly_generation_v3": ["generation"],
        "assembly_generation_v4": ["generation"],
        "assembly_operations_v1": ["parse", "expand"],
        "assembly_occurrences_v1": ["prepare", "preflight", "materialize"],
        "assembly_component_binding_v1": ["bind"],
        "assembly_operator_binding_v1": ["bind"],
        "assembly_requests": ["budget", "check_work"],
        "card_assembly_exploration": [
            "_materialize",
            "_rows",
            "links",
            "support",
            "options_for_assembly",
        ],
        "card_assembly_access": ["materialize", "descriptor", "defer_frame"],
    }.items():
        module = importlib.import_module("sabueso.core." + name)
        for method in methods:
            monkeypatch.setattr(module, method, forbidden)
        if name == "card_assembly_exploration":
            monkeypatch.setattr(module, "HEADERS", None)


def test_genuine_original_live_capsule_matches_independent_frozen_predicates(
    originals, monkeypatch
):
    from sabueso.core.card_assembly_history_v1 import expected_result
    from sabueso.core.snapshot import snapshot_id

    assert (
        hashlib.sha256(CAPSULE.read_bytes()).hexdigest()
        == "36621bd303a20f3a5f87cb5fd5b63d4e94d946cfb7fa6e95dcf0035861ebd018"
    )
    assert (
        hashlib.sha256(gzip.decompress(CAPSULE.read_bytes())).hexdigest()
        == "4acfab29f54eb2f153eb4c2674d9cdf4c4580f6441c4b66885d64d8c8899e912"
    )
    assert originals["producer"]["source"] == "77fd770e4d2a8fa94eea3fbd723a84fc90875efb"
    assert originals["producer"]["sdk"] == "0.14.0+135.g77fd770"
    inert(monkeypatch)
    for case in originals["cases"].values():
        data = case["card"]
        snapshot = snapshot_id(data)
        pin = data["meta"]["card_id"] + "@" + snapshot
        capture = _Capture(data, snapshot, pin)
        access = _access({pin: capture}, (pin,), {}, {}, pin)
        access._mode = "live"
        expected = expected_result(access, case["wire"]["context"]["options"])
        assert expected.result_ref == case["result_ref"]
        _require_matches(
            case["wire"], expected.wire, "genuine original assembly live output"
        )


@pytest.mark.parametrize(
    "root_kind",
    [
        "question",
        "topic",
        "detail",
        "filter",
        "sort",
        "detail_filter",
        "machine",
        "raw_explanation",
    ],
)
def test_original_roundtrip_and_navigation_are_inert(
    card, root_kind, tmp_path, monkeypatch
):
    explorer = card.explore()
    view = (
        explorer.view(TOPIC, options=OPTIONS)
        if root_kind == "topic"
        else explorer.answer(TOPIC, options=OPTIONS)
    )
    root = view
    if root_kind == "detail":
        root = view.items()[0].open()
    elif root_kind == "filter":
        root = view.filter("declaration_count", equals=2)
    elif root_kind == "sort":
        root = view.sort("declaration_count", descending=True)
    elif root_kind == "detail_filter":
        root = view.items()[0].open().filter("declaration_count", equals=999)
    elif root_kind == "machine":
        root = explorer.access.select(
            TOPIC,
            options=OPTIONS,
            fields=["declaration_count"],
            where={"declaration_count": 2},
            order_by={"column": "label"},
        )
    elif root_kind == "raw_explanation":
        root = explorer.access.explain(view.items()[0].item_ref)
    native = (
        None if root_kind in ("machine", "raw_explanation") else root.native_payload
    )
    path = tmp_path / "original.json"
    receipt = root.save(path)
    assert json.loads(path.read_text())["format"] == "sabueso.card_exploration@5"
    inert(monkeypatch)
    restored = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert (
        restored.validation["verifier"] == "assembly_generation_exploration_binding@1"
    )
    assert (
        "rcsb_assembly_generation@4" in restored.validation["verified_scientific_rules"]
    )
    if native is not None:
        assert restored.native_payload == native
        assert [i.item_ref for i in restored.items()] == [
            i.item_ref for i in root.items()
        ]
    if root_kind not in ("machine", "raw_explanation"):
        for item in restored.items():
            assert item.explain().back() is restored
            related = item.related()
            assert related.back() is restored
            for link in related.items():
                destination = link.open()
                assert destination.back() is related
                assert destination.native_payload is not None
    if root_kind == "machine":
        selected = restored.explorer.access.select(
            TOPIC,
            options=OPTIONS,
            fields=["declaration_count"],
            where={"declaration_count": 2},
            order_by={"column": "label"},
        )
        assert selected.count == 1
        frame = selected.page(max_bytes=8192)["items"][0]
        assert frame["cells"]["declaration_count"]["value"] == 2
        assert frame["interpretation"]["physical_membership"] == "not_computed"
        assert (
            restored.explorer.access.select(
                TOPIC, options=OPTIONS, fields=["reason"]
            ).page()["outcome"]["status"]
            == "not_saved"
        )
    elif root_kind == "question":
        assert (
            restored.explorer.answer(TOPIC, options=OPTIONS).native_payload
            == view.native_payload
        )
        assert (
            restored.explorer.answer(
                TOPIC, options={**OPTIONS, "expand_occurrences": True}
            ).outcome["status"]
            == "not_saved"
        )
    elif root_kind == "topic":
        assert (
            restored.explorer.view(TOPIC, options=OPTIONS).native_payload
            == view.native_payload
        )
    assert str(restored) and restored._repr_html_()


def test_factored_counts_and_explicit_expansion_options_stay_original(
    card, tmp_path, monkeypatch
):
    assertion = next(
        s
        for s in card.source_assertion_store.store.values()
        if s.get("source", {}).get("name") == "RCSB PDB"
    )
    assertion["asserted_value"]["assembly_generation_inputs"]["assemblies"][0][
        "pdbx_struct_assembly_gen"
    ][0]["oper_expression"] = "1-100000000000000000000"
    explorer = card.explore()
    view = explorer.answer(TOPIC, options={**OPTIONS, "operation_budget": None})
    root = view.filter("declaration_count", equals=None).sort(
        "declaration_count", descending=True
    )
    path = tmp_path / "factored.json"
    root.save(path)
    inert(monkeypatch)
    restored = sabueso.read_exploration(path)
    item = restored.items()[0]
    assert item.cells["declaration_count"].state == "factored"
    assert item.cells["declaration_count"].value is None
    assert restored.context["options"]["operation_budget"] is None
    assert restored.native_payload == root.native_payload


@pytest.mark.parametrize(
    "change",
    [
        "count",
        "row_count",
        "basis",
        "binding",
        "rule",
        "source",
        "pointer",
        "options",
        "cell_state",
        "manifest",
        "policy",
        "question",
    ],
)
def test_resealed_tampering_cannot_become_original_science(
    card, change, tmp_path, monkeypatch
):
    view = card.explore().answer(TOPIC, options=OPTIONS)
    path = tmp_path / "tampered.json"
    view.save(path)
    bundle = json.loads(path.read_text())
    wire = bundle["objects"][view.result_ref]
    key = next(iter(wire["rows"]))
    if change == "count":
        wire["native_payload"]["sources"][0]["assemblies"][0]["generators"][0][
            "occurrence_plan"
        ]["declared_occurrence_count"] = 0
    elif change == "row_count":
        wire["rows"][key]["declaration_count"] = 0
    elif change == "basis":
        wire["rows"][key]["interpretation"]["count_basis"] = (
            "distinct_physical_molecules"
        )
    elif change == "binding":
        wire["rows"][key]["item"]["component_scope"] = "resolved"
    elif change == "rule":
        wire["native_payload"]["occurrence_rule"] = "source_assembly_occurrence@99"
    elif change == "source":
        wire["support"][key]["source_assertions"] = []
    elif change == "pointer":
        wire["explanations"][key]["original_input_location"] = wire["explanations"][
            key
        ]["source_request_context_location"]
    elif change == "options":
        wire["context"]["options"]["expand_occurrences"] = True
    elif change == "cell_state":
        state = bundle["views"][bundle["root_navigation_ref"]]["state"]
        next(iter(state["items"].values()))["cells"]["declaration_count"]["state"] = (
            "factored"
        )
    elif change == "manifest":
        bundle["scientific_results"][view.result_ref]["unrecognized"] = True
    elif change == "policy":
        record = bundle["views"][bundle["root_navigation_ref"]]
        record["selection"]["fields"] = []
    else:
        bundle["views"][bundle["root_navigation_ref"]]["flags"]["_request"]["options"][
            "expand_operations"
        ] = True
    _seal(bundle)
    path.write_text(json.dumps(bundle))
    inert(monkeypatch)
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_true_old_scientific_bundle_does_not_run_new_interpretation(
    tmp_path, monkeypatch
):
    path = tmp_path / "old.json"
    path.write_bytes(
        gzip.decompress(
            (CAPSULE.parent / "card_exploration_quaternary_v1.json.gz").read_bytes()
        )
    )
    inert(monkeypatch)
    restored = sabueso.read_exploration(path)
    assert (
        restored.explorer.answer(TOPIC, options=OPTIONS).outcome["status"]
        == "not_saved"
    )
    assert (
        restored.explorer.access.select(TOPIC, options=OPTIONS).page()["outcome"][
            "status"
        ]
        == "not_saved"
    )


def assertion(card):
    return next(
        s
        for s in card.source_assertion_store.store.values()
        if s.get("source", {}).get("name") == "RCSB PDB"
    )


def test_duplicate_parent_positions_keep_original_order_after_json_sorting(
    card, tmp_path, monkeypatch
):
    inputs = assertion(card)["asserted_value"]["assembly_generation_inputs"]
    inputs["assemblies"] = [deepcopy(inputs["assemblies"][0]) for _ in range(12)]
    view = card.explore().answer(TOPIC, options=OPTIONS)
    expected = [i.item_ref for i in view.items()]
    assert len(expected) == 12
    path = tmp_path / "duplicates.json"
    view.save(path)
    inert(monkeypatch)
    restored = sabueso.read_exploration(path)
    assert [i.item_ref for i in restored.items()] == expected
    assert [i._entry.value["parent_index"] for i in restored.items()] == list(range(12))


@pytest.mark.parametrize("budget", [100_000, None])
def test_original_expansion_and_unrestricted_budget_are_not_changed(
    card, budget, tmp_path, monkeypatch
):
    options = {
        **OPTIONS,
        "expand_operations": True,
        "expand_occurrences": True,
        "operation_budget": budget,
    }
    view = card.explore().answer(TOPIC, options=options)
    path = tmp_path / "expanded.json"
    view.save(path)
    inert(monkeypatch)
    restored = sabueso.read_exploration(path)
    assert restored.native_payload == view.native_payload
    assert restored.request["options"] == options | {"relationship_id": None}
    assert restored.native_payload["expanded_occurrence_count"] == 6


def test_saved_projection_and_atomic_deferral_keep_full_read_paths(
    card, tmp_path, monkeypatch
):
    parent = assertion(card)["asserted_value"]["assembly_generation_inputs"][
        "assemblies"
    ][0]
    parent["rcsb_assembly_container_identifiers"]["assembly_id"] = "SYNTHETIC" * 1000
    parent["pdbx_struct_assembly_gen"][0]["assembly_id"] = parent[
        "rcsb_assembly_container_identifiers"
    ]["assembly_id"]
    root = card.explore().access.select(TOPIC, options=OPTIONS, fields=["label"])
    expected = root.page(max_bytes=4096, limit=1)
    path = tmp_path / "bounded.json"
    root.save(path)
    inert(monkeypatch)
    restored = sabueso.read_exploration(path)
    selection = restored.explorer.access.select(
        TOPIC, options=OPTIONS, fields=["label"]
    )
    page = selection.page(max_bytes=4096, limit=1)

    def full_locations(value, access):
        if isinstance(value, dict):
            if (
                value.get("format") == "card_access_location@1"
                and value.get("kind") == "lookup"
            ):
                return access._resolve(value)[1]
            return {key: full_locations(item, access) for key, item in value.items()}
        if isinstance(value, list):
            return [full_locations(item, access) for item in value]
        return value

    assert full_locations(page["items"], selection._access) == full_locations(
        expected["items"], root._access
    )
    assert (
        len(
            json.dumps(
                page, ensure_ascii=False, separators=(",", ":"), sort_keys=True
            ).encode()
        )
        <= 4096
    )
    frame = page["items"][0]
    assert frame["inspection_required"] and not frame["value_included"]
    assert "interpretation" not in frame and "support" not in frame
    assert restored.explorer.access.read(frame["support_location"]).page(
        max_bytes=8192
    )["page"]
    assert restored.explorer.access.read(frame["interpretation_location"]).page(
        max_bytes=8192
    )["page"]
    if page["page"]["next_cursor"]:
        assert selection.page(
            max_bytes=4096, limit=1, cursor=page["page"]["next_cursor"]
        )["items"]


def test_missing_source_and_historical_unknown_remain_unavailable(
    card, originals, tmp_path, monkeypatch
):
    missing = assertion(card)["id"]
    card.source_assertion_store.store.pop(missing)
    view = card.explore().answer(TOPIC, options=OPTIONS)
    path = tmp_path / "missing.json"
    view.save(path)
    inert(monkeypatch)
    restored = sabueso.read_exploration(path)
    assert restored.native_payload == view.native_payload
    assert restored.items()[0].cells["declaration_count"].value is None
    assert any(
        i._entry.value["availability"] == "missing_prerequisite"
        for i in restored.items()[0].related().items()
    )


def test_source_values_named_like_generated_version_are_never_ignored(card, tmp_path):
    assertion(card)["asserted_value"]["accession_info"]["sabueso_version"] = (
        "SYNTHETIC-SOURCE-VALUE"
    )
    view = card.explore().answer(TOPIC, options=OPTIONS)
    path = tmp_path / "source-version.json"
    view.save(path)
    bundle = json.loads(path.read_text())
    bundle["objects"][view.result_ref]["native_payload"]["sources"][0][
        "entry_revision"
    ]["sabueso_version"] = "FORGED"
    _seal(bundle)
    path.write_text(json.dumps(bundle))
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_swapped_support_operations_have_no_valid_original_origin(card, tmp_path):
    view = card.explore().answer(TOPIC, options=OPTIONS)
    path = tmp_path / "swapped.json"
    view.save(path)
    bundle = json.loads(path.read_text())
    links = bundle["navigation"]["links"]
    first, second = list(links)[:2]
    links[first], links[second] = links[second], links[first]
    _seal(bundle)
    path.write_text(json.dumps(bundle))
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_mixed_scientific_topics_keep_their_original_verifiers(
    card, tmp_path, monkeypatch
):
    explorer = card.explore()
    view = explorer.answer(TOPIC, options=OPTIONS)
    quaternary = explorer.answer("quaternary_interpretation")
    structures = explorer.view("structures")
    path = tmp_path / "mixed.json"
    view.save(path)
    inert(monkeypatch)
    restored = sabueso.read_exploration(path)
    assert (
        restored.explorer.answer("quaternary_interpretation").native_payload
        == quaternary.native_payload
    )
    assert (
        restored.explorer.view("structures").native_payload == structures.native_payload
    )
    assert restored.native_payload == view.native_payload


def test_repeated_saving_does_not_grow_automatic_support(card, tmp_path, monkeypatch):
    path, second = tmp_path / "first.json", tmp_path / "second.json"
    view = card.explore().answer(TOPIC, options=OPTIONS)
    view.save(path)
    original = json.loads(path.read_text())
    inert(monkeypatch)
    restored = sabueso.read_exploration(path)
    restored.save(second)
    later = json.loads(second.read_text())
    assert len(later["views"]) == len(original["views"])
    assert len(later["objects"]) == len(original["objects"])
    assert sabueso.read_exploration(second).native_payload == view.native_payload


def test_fresh_process_outside_checkout_needs_no_card_or_source_inputs(card, tmp_path):
    path = tmp_path / "independent.json"
    view = card.explore().answer(TOPIC, options=OPTIONS)
    receipt = view.save(path)
    script = """
import importlib, socket, sys
from pathlib import Path
import sabueso
from sabueso.core.card import Card
def forbidden(*args, **kwargs):
    raise AssertionError("Current Card/science/acquisition forbidden")
Card.__init__ = forbidden
Card.from_dict = forbidden
socket.socket.connect = forbidden
socket.create_connection = forbidden
for name, methods in {
    "assembly_generation_v4": ["generation"],
    "assembly_requests": ["budget", "check_work"],
    "assembly_operations_v1": ["parse", "expand"],
    "card_assembly_exploration": ["_materialize", "_rows", "links", "support", "options_for_assembly"],
    "card_assembly_access": ["materialize", "descriptor", "defer_frame"],
}.items():
    module = importlib.import_module("sabueso.core." + name)
    for method in methods: setattr(module, method, forbidden)
    if name == "card_assembly_exploration": module.HEADERS = None
assert not Path("temp_data").exists()
assert not Path.cwd().is_relative_to(Path(sabueso.__file__).resolve().parents[1])
view = sabueso.read_exploration(sys.argv[1], expected_digest=sys.argv[2])
assert view.validation["verifier"] == "assembly_generation_exploration_binding@1"
assert [i.cells["declaration_count"].value for i in view.items()] == [4, 2]
assert view.explorer.answer("assembly_generation", options={"structure_ref":"pdb:2V5B"}).native_payload == view.native_payload
assert view.items()[0].explain().native_payload["request"]["structure_ref"] == "pdb:2V5B"
assert view.items()[0].related().items()[0].open().native_payload
assert str(view) and view._repr_html_()
print("PASS: independent original assembly reading")
"""
    outside_parent = None if sys.platform == "win32" else "/tmp"
    with TemporaryDirectory(
        prefix="sabueso-assembly-reader-", dir=outside_parent
    ) as outside:
        result = subprocess.run(
            [sys.executable, "-c", script, str(path), receipt["bundle_digest"]],
            cwd=outside,
            capture_output=True,
            text=True,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: independent original assembly reading" in result.stdout


def test_explanation_keeps_its_exact_literal_request(card, tmp_path):
    root = card.explore().answer(TOPIC, options=OPTIONS).items()[0].explain()
    path = tmp_path / "explanation-request.json"
    root.save(path)
    bundle = json.loads(path.read_text())
    bundle["views"][bundle["root_navigation_ref"]]["selection"]["operation"] = "fields"
    _seal(bundle)
    path.write_text(json.dumps(bundle))
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


@pytest.mark.parametrize(
    "topic", ["quaternary_interpretation", "ligand_site_comparisons"]
)
@pytest.mark.parametrize(
    "change", ["operation", "slice", "fields", "context", "target_owner", "target_size"]
)
def test_original_specialized_readers_reject_inconsistent_explanation_requests(
    topic, change, tmp_path
):
    from test_card_ligand_site_comparisons_offline import protein
    from test_card_quaternary_interpretation_offline import sample

    card = sample() if topic == "quaternary_interpretation" else protein()
    root = card.explore().answer(topic).items()[0].explain()
    path = tmp_path / "old-explanation-request.json"
    root.save(path)
    bundle = json.loads(path.read_text())
    assert bundle["format"] == (
        "sabueso.card_exploration@4"
        if topic == "quaternary_interpretation"
        else "sabueso.card_exploration@3"
    )
    record = bundle["views"][bundle["root_navigation_ref"]]
    if change == "operation":
        record["selection"]["operation"] = "fields"
    elif change == "slice":
        record["selection"]["slice"] = {"start": 0, "stop": 1}
    elif change == "fields":
        record["selection"]["fields"] = ["label"]
    elif change == "context":
        record["selection"]["context_location"] = record["selection"]["target"][
            "location"
        ]
    elif change == "target_owner":
        record["selection"]["target"]["owner"] = {}
    else:
        record["selection"]["target"]["size"] = 0
    _seal(bundle)
    path.write_text(json.dumps(bundle))
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_resealed_coherent_result_identity_still_needs_original_inputs(card):
    from sabueso.core.card_access import _handle
    from sabueso.core.card_exploration_assembly import verify_objects

    explorer = card.explore()
    view = explorer.answer(TOPIC, options=OPTIONS)
    wire = deepcopy(explorer.access._objects[view.result_ref])
    wire["native_payload"]["sources"][0]["assemblies"][0]["generators"][0][
        "occurrence_plan"
    ]["declared_occurrence_count"] = 999
    forged = _handle(
        "XR_",
        {
            "adapter": "assembly_generation_exploration@1",
            "focal": explorer.access._focal_key,
            "options": wire["context"]["options"],
            "native": {
                key: val
                for key, val in wire["native_payload"].items()
                if key != "sabueso_version"
            },
        },
    )
    assert forged != view.result_ref
    bundle = {
        "scientific_results": {forged: {"focal": explorer.access._focal_key}},
        "objects": {forged: wire},
    }
    with pytest.raises(StorageError, match="identity"):
        verify_objects(bundle, {explorer.access._focal_key: explorer.access})


@pytest.mark.parametrize(
    "nature", ["legacy", "missing_identity", "empty", "small_molecule"]
)
def test_unavailable_and_nonapplicable_saved_scopes_remain_explicit(
    nature, originals, tmp_path, monkeypatch
):
    card = (
        Card.from_dict(deepcopy(originals["cases"]["legacy"]["card"]))
        if nature == "legacy"
        else Card(
            meta={
                "entity_type": "small_molecule",
                "card_id": "sabueso:small_molecule:pubchem:1",
            }
        )
        if nature == "small_molecule"
        else Card(meta={"entity_type": "protein"})
        if nature == "missing_identity"
        else Card(
            meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:P52270"}
        )
    )
    view = card.explore().view(TOPIC)
    path = tmp_path / "unavailable.json"
    view.save(path)
    inert(monkeypatch)
    restored = sabueso.read_exploration(path)
    assert restored.native_payload == view.native_payload
    assert restored.outcome == view.outcome
    assert all(i.cells["declaration_count"].value is None for i in restored.items())
    if nature == "small_molecule":
        assert restored.outcome["status"] == "not_applicable"
    elif nature == "missing_identity":
        assert restored.outcome["status"] == "missing_prerequisite"


@pytest.mark.parametrize("name", ["expand_operations", "expand_occurrences"])
def test_question_option_types_are_not_coerced_by_python_equality(name):
    from dataclasses import replace

    from sabueso.core.card_exploration_assembly import verify_view
    from sabueso.core.card_exploration_storage import _freeze_view

    view = (
        Card(meta={"entity_type": "protein"})
        .explore()
        .answer(TOPIC, options={"operation_budget": 1})
    )
    record = _freeze_view(view, {id(view): "N0"})
    request = deepcopy(view.request)
    request["options"][name] = 0
    altered = replace(view, _request=request)
    with pytest.raises(StorageError):
        verify_view(altered, record)


@pytest.mark.parametrize("role", ["original_input", "source_context"])
def test_nested_original_context_navigation_can_be_saved(
    card, role, tmp_path, monkeypatch
):
    view = card.explore().answer(TOPIC, options=OPTIONS)
    related = view.items()[0].related()
    destination = next(
        item for item in related.items() if item._entry.value["role"] == role
    ).open()
    nested = destination.items()[0].related()
    expected = nested.native_payload
    path = tmp_path / "nested.json"
    nested.save(path)
    inert(monkeypatch)
    restored = sabueso.read_exploration(path)
    assert restored.native_payload == expected
    assert restored.back().native_payload == nested.back().native_payload
    assert (
        restored.validation["verifier"] == "assembly_generation_exploration_binding@1"
    )
