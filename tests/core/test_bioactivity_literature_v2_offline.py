"""Clean SDK202 scalar originals and the explicit Bio/Lit format19 boundary."""

import gzip
import hashlib
import importlib
import io
import json
import socket
import subprocess
import sys
import tarfile
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_exploration_storage import _prepare, _restore, _seal
from sabueso.core.errors import StorageError
from sabueso.core.snapshot import canonical_json

ARCHIVE = (
    Path(__file__).with_name("data") / "bioactivity_literature_scalars_sdk202.tar.gz"
)
ENCODED_SHA = "861cff367985eb68dee581c0033dbe8021bde3b71d601a8725cce2bda8148691"
DECODED_SHA = "14b1d95be5894895cc7ff03b9ed965a5237eb682283785fdb72e1275e5ce060f"
MANIFEST_SHA = "ae10189753c6a4cfca0bb4a97dba491ba9ad901d5606686c62930f32ebb83b3e"
CASES = ("false", "integer_zero", "float_zero", "null")


def sha(value):
    return hashlib.sha256(value).hexdigest()


def forbidden(*args, **kwargs):
    raise AssertionError("Saved knowledge must not execute current science or sources")


def block_current(monkeypatch):
    specifications = (
        (
            "card_bioactivity_access",
            ("materialize", "_native", "options_for_bioactivities"),
        ),
        ("card_literature_access", ("materialize", "options_for_literature")),
        ("card_literature_exploration", ("materialize", "view")),
        ("card_bioactivity_exploration", ("materialize", "view")),
        ("card_molecule_activity_access", ("materialize",)),
        ("card_molecule_activity_exploration", ("materialize", "view")),
        ("literature", ("literature_view",)),
        ("literature_explanation", ("explain_literature",)),
        ("bioactivities", ("bioactivities_view",)),
        ("bioactivity_explanation", ("explain_bioactivity", "explain_measurement")),
        ("entities", ("build_entities",)),
    )
    # Import each reader before replacing any helper: a later import must not
    # bind a temporary forbidden helper into an otherwise restored module.
    targets = [
        (importlib.import_module("sabueso.core." + module), names)
        for module, names in specifications
    ]
    for name in (
        "__init__",
        "from_dict",
        "entities",
        "bioactivities",
        "explain_bioactivity",
        "explain_measurement",
        "literature",
        "explain_literature",
        "knowledge_state",
    ):
        monkeypatch.setattr(Card, name, forbidden)
    for target, names in targets:
        for name in names:
            monkeypatch.setattr(target, name, forbidden)
    profiles = importlib.import_module("sabueso.core.card_exploration_profiles")
    monkeypatch.setattr(profiles, "NATURE_TOPICS", {})
    monkeypatch.setattr(profiles, "COMMON_QUESTIONS", {})
    monkeypatch.setattr(profiles, "QUESTIONS", {})
    for module, suffix in (
        ("uniprot", "UniProt"),
        ("chembl", "ChEMBL"),
        ("europepmc", "EuropePMC"),
    ):
        target = importlib.import_module("sabueso.tools.db." + module)
        for prefix in ("Fixture", "Online"):
            monkeypatch.setattr(
                getattr(target, prefix + suffix + "Client"), "__init__", forbidden
            )
    for name in (
        "publication_ref",
        "item_ref",
        "molecule_ref",
        "measurement_ref",
        "include_indirect",
        "thresholds",
    ):
        target = importlib.import_module("sabueso._private.argdigest.argument." + name)
        monkeypatch.setattr(target, "digest_" + name, forbidden)


class Original:
    def __init__(self):
        encoded = ARCHIVE.read_bytes()
        assert sha(encoded) == ENCODED_SHA
        decoded = gzip.decompress(encoded)
        assert len(decoded) == 16506880 and sha(decoded) == DECODED_SHA
        with tarfile.open(fileobj=io.BytesIO(decoded), mode="r:") as archive:
            self.members = {}
            for member in archive.getmembers():
                assert member.isfile() and not Path(member.name).is_absolute()
                assert (
                    ".." not in Path(member.name).parts
                    and member.name not in self.members
                )
                self.members[member.name] = archive.extractfile(member).read()
        assert sha(self.members["manifest.json"]) == MANIFEST_SHA
        self.manifest = json.loads(self.members["manifest.json"])
        expected = self.manifest["files"]
        assert len(expected) == 755 and set(self.members) == {
            *expected,
            "manifest.json",
        }
        assert sum(item["bytes"] for item in expected.values()) == 15795152
        for name, item in expected.items():
            assert (
                len(self.members[name]) == item["bytes"]
                and sha(self.members[name]) == item["sha256"]
            )

    def value(self, ref):
        return json.loads(self.members[ref["path"]])

    def case(self, name):
        return self.value(self.manifest["cases"][name])

    def access(self, name):
        state = self.case(name)["access_state"]
        return SimpleNamespace(
            _focal_key=state["focal"],
            _inputs=state["inputs"],
            _captures={
                key: SimpleNamespace(
                    pin=row["pin"],
                    snapshot=row["snapshot"],
                    data=self.value(row["data_ref"]),
                )
                for key, row in state["captures"].items()
            },
        )


@pytest.fixture(scope="module")
def original():
    return Original()


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def scalar_from_summary(summary, assertion_id):
    return next(
        row["value"]
        for row in summary["supports"]
        if row["source_assertion_id"] == assertion_id
    )


def publication_context(view):
    links = view.items()[0].related()
    link = next(
        item
        for item in links.items()
        if item.cells["role"].value == "publication_context"
    )
    return link.open()


def prepare(original, case_name, mixed):
    case = original.case(case_name)
    card = Card.from_dict(original.value(case["input_card_ref"]))
    explorer = card.explore()
    root = explorer.answer("measured_molecules")
    groups = root.items()[0].open()
    records = groups.items()[0].open()
    records.items()[0].open()
    context = publication_context(root)
    explorer.access.select("bioactivities", fields=["molecule_ref", "record_count"])
    if mixed:
        explorer.answer("publications")
        explorer.view(
            "literature",
            options={"publication_ref": case["declaration"]["publication_ref"]},
        )
    return root, context, case["declaration"]


def test_complete_scalar_original_precedes_bio_v2_predicates(original):
    manifest = original.manifest
    assert manifest["producer_head"] == "1145ea364a558b6f03d3823dfd1be4a6839663e5"
    assert manifest["producer_version"] == "0.14.0+202.g1145ea3"
    assert manifest["capture_complete"] and not manifest["admitted_saved_format"]
    assert manifest["attempts"] == {"network": 0, "source_acquisitions": 0}
    assert not manifest["source_producer"]["status"]
    source_files = json.loads(original.members["source-files.json"])
    assert not any(
        "_history_v2" in name and "bioactivity" in name for name in source_files
    )
    assert set(manifest["cases"]) == set(CASES)


def assert_scalar(actual, expected):
    assert type(actual) is type(expected)
    assert actual == expected


def scientific_wires(original, case):
    state = case["access_state"]
    for ref, record in state["objects"].items():
        if ref in state["metadata_refs"]:
            continue
        wire = original.value(record)
        if (
            isinstance(wire, dict)
            and isinstance(wire.get("context"), dict)
            and wire["context"].get("adapter")
            in ("bioactivity_exploration@1", "literature_exploration@1")
        ):
            yield ref, wire


@pytest.mark.parametrize("case_name", CASES)
def test_all_original_grains_and_publication_wrapper_are_exact_and_inert(
    original, case_name, monkeypatch
):
    from sabueso.core.card_bioactivity_history_v2 import (
        expected_publication,
        expected_result,
        restore_result,
    )
    from sabueso.core.card_literature_history_v1 import (
        expected_result as expected_literature,
    )

    case, access = original.case(case_name), original.access(case_name)
    block_current(monkeypatch)
    grains, literature = set(), 0
    for ref, wire in scientific_wires(original, case):
        bioactivity = wire["context"]["adapter"] == "bioactivity_exploration@1"
        expected = (expected_result if bioactivity else expected_literature)(
            access, wire["context"]["options"], original=wire
        )
        assert expected.result_ref == ref
        assert canonical_json(expected.wire) == canonical_json(wire)
        if bioactivity:
            restored = restore_result(ref, wire)
            assert restored.wire is wire
            assert [entry.key for entry in restored.entries] == [
                entry.key for entry in expected.entries
            ]
            grains.add(wire["context"]["grain"])
        else:
            literature += 1
    assert grains == {"molecule", "group", "record"} and literature == 2
    wrapper = original.value(case["native"]["bioactivity_publication_wrapper_ref"])
    assert canonical_json(
        expected_publication(access, wrapper["publication_ref"], original=wrapper)
    ) == canonical_json(wrapper)
    declaration = case["declaration"]
    assert_scalar(
        scalar_from_summary(
            wrapper["original_summary"], declaration["synthetic_assertion"]["id"]
        ),
        declaration["scalar"],
    )


def logical_bundle(path):
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if bundle["format"] == "sabueso.card_exploration@20":
        from sabueso.core.card_exploration_shared_values_v4 import unpack

        bundle, _ = unpack(bundle)
    elif bundle["format"] == "sabueso.card_exploration@18":
        from sabueso.core.card_exploration_shared_values_v3 import unpack

        bundle, _ = unpack(bundle)
    return bundle


def retained_source(view, declaration):
    return next(
        row
        for row in view._explorer.access._focal.data["source_assertion_store"]
        if row["id"] == declaration["synthetic_assertion"]["id"]
    )


@pytest.mark.parametrize("case_name", CASES)
@pytest.mark.parametrize("mixed", (False, True), ids=("bioactivity", "mixed"))
def test_new_save_read_resave_keeps_original_scalar_context_and_scope(
    original, case_name, mixed, tmp_path, monkeypatch
):
    root, live_context, declaration = prepare(original, case_name, mixed)
    native, context_native, request = (
        root.native_payload,
        live_context.native_payload,
        root.request,
    )
    block_current(monkeypatch)
    path = tmp_path / "captured.json"
    root.save(path)
    physical = json.loads(path.read_text(encoding="utf-8"))
    assert physical["format"] in (
        "sabueso.card_exploration@19",
        "sabueso.card_exploration@20",
    )
    bundle = logical_bundle(path)
    assert bundle["format"] == "sabueso.card_exploration@19"
    saved = sabueso.read_exploration(path)
    assert saved.native_payload == native and saved.request == request
    assert (
        saved.validation["bioactivities"] == "original_frozen_v2_consistency_verified"
    )
    assert ("literature" in saved.validation) is mixed
    assert canonical_json(retained_source(saved, declaration)) == canonical_json(
        declaration["synthetic_assertion"]
    )
    opaque = retained_source(saved, declaration)["asserted_value"]
    assert_scalar(opaque["value"], declaration["scalar"])
    assert opaque["context"] is False and opaque["native_payload"] is None
    assert opaque["sabueso_version"] == "opaque source-owned scalar-control label"
    assert retained_source(saved, declaration)["source_metadata"][
        "sabueso_version"
    ] == ("source-owned metadata label must remain literal")
    context = publication_context(saved)
    assert context.native_payload == context_native
    assert (
        context.back()._link_panel and context.back().back().view_ref == saved.view_ref
    )
    assert context.request == request
    summary = context.native_payload["publication"]
    assert_scalar(
        scalar_from_summary(summary, declaration["synthetic_assertion"]["id"]),
        declaration["scalar"],
    )
    selection = saved.explorer.access.select(
        "bioactivities", fields=["molecule_ref", "record_count"]
    )
    assert selection.count == 1
    if mixed:
        publications = saved.explorer.answer("publications")
        assert publications.outcome["status"] != "not_saved"
        assert publications.request["options"] == {"publication_ref": None}
        focused = saved.explorer.view(
            "literature", options={"publication_ref": declaration["publication_ref"]}
        )
        assert focused.native_payload == context_native
    else:
        assert saved.explorer.answer("publications").outcome["status"] == "not_saved"
        assert saved.explorer.view("literature").outcome["status"] == "not_saved"
        assert saved.explorer.access.select("literature").page()["outcome"][
            "status"
        ] == ("not_saved")
    resaved = tmp_path / "resaved.json"
    context.save(resaved)
    again = sabueso.read_exploration(resaved)
    assert logical_bundle(resaved)["format"] == "sabueso.card_exploration@19"
    assert again.native_payload == context_native and again.request == request
    assert again.back().back().view_ref == saved.view_ref
    assert canonical_json(retained_source(again, declaration)) == canonical_json(
        declaration["synthetic_assertion"]
    )
    if case_name == "false" and mixed:
        from sabueso.core.card_exploration_shared_values_v4 import pack

        unsealed = {
            key: value
            for key, value in bundle.items()
            if key not in ("digests", "bundle_digest")
        }
        shared = _seal(pack(unsealed, threshold=0, min_saving=0))
        assert shared["format"] == "sabueso.card_exploration@20"
        represented = _restore(shared, None)
        assert represented.native_payload == native and represented.request == request
        assert publication_context(represented).native_payload == context_native


@pytest.mark.parametrize("case_name", CASES)
def test_resealed_bioactivity_summary_cannot_substitute_scalar_type(
    original, case_name, monkeypatch
):
    root, _, declaration = prepare(original, case_name, True)
    block_current(monkeypatch)
    bundle = _prepare(root)
    assert bundle["format"] == "sabueso.card_exploration@19"
    ref = next(
        ref
        for ref in bundle["scientific_results"]
        if bundle["objects"][ref]["context"]["adapter"] == "bioactivity_exploration@1"
        and bundle["objects"][ref]["context"]["grain"] == "molecule"
    )
    wire = deepcopy(bundle["objects"][ref])
    bundle["objects"][ref] = wire
    publication = next(
        row
        for row in wire["literature"]["publications"]
        if row["publication_ref"] == declaration["publication_ref"]
    )
    support = next(
        row
        for row in publication["supports"]
        if row["source_assertion_id"] == declaration["synthetic_assertion"]["id"]
    )
    assert_scalar(support["value"], declaration["scalar"])
    support["value"] = {
        "false": 0,
        "integer_zero": False,
        "float_zero": 0,
        "null": False,
    }[case_name]
    with pytest.raises(
        StorageError,
        match="SDK202 whole bioactivity|SDK202 bioactivity result identity",
    ):
        _restore(_seal(bundle), None)


def test_fresh_process_reads_and_resaves_without_current_science(original, tmp_path):
    root, context, declaration = prepare(original, "float_zero", True)
    path, output = tmp_path / "fresh.json", tmp_path / "fresh-resaved.json"
    root.save(path)
    script = """
import importlib.util, json, socket, sys
from pathlib import Path
import pytest, sabueso
spec = importlib.util.spec_from_file_location('original_scalar_tests', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with pytest.MonkeyPatch.context() as guard:
    module.block_current(guard)
    guard.setattr(socket.socket, 'connect', module.forbidden)
    guard.setattr(socket, 'create_connection', module.forbidden)
    saved = sabueso.read_exploration(sys.argv[2])
    context = module.publication_context(saved)
    expected = json.loads(sys.argv[4])
    module.assert_scalar(module.scalar_from_summary(context.native_payload['publication'], sys.argv[5]), expected)
    assert saved.validation['bioactivities'] == 'original_frozen_v2_consistency_verified'
    context.save(sys.argv[3])
    again = sabueso.read_exploration(sys.argv[3])
    assert again.native_payload == context.native_payload
    assert again.request == context.request
    assert module.logical_bundle(Path(sys.argv[3]))['format'] == 'sabueso.card_exploration@19'
    print(json.dumps({'status': 'passed', 'scalar_type': type(expected).__name__}))
"""
    child = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            str(Path(__file__).resolve()),
            str(path),
            str(output),
            json.dumps(declaration["scalar"]),
            declaration["synthetic_assertion"]["id"],
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert child.returncode == 0, child.stdout + child.stderr
    assert json.loads(child.stdout) == {"status": "passed", "scalar_type": "float"}
    assert sabueso.read_exploration(output).native_payload == context.native_payload


ORIGINAL17 = (
    Path(__file__).with_name("data") / "bioactivity_saved_original17_sdk202.json.gz"
)
ORIGINAL17_ENCODED_SHA = (
    "6875c898ccc6b8fcdd52669ba97db956176eb265c2399dd708db1e2de90252d0"
)
ORIGINAL17_DECODED_SHA = (
    "9db610457051ea94efa95f56c47449a5641ffe2429a04feb28afc5aab262d080"
)


def original17_bundle():
    encoded = ORIGINAL17.read_bytes()
    assert sha(encoded) == ORIGINAL17_ENCODED_SHA
    decoded = gzip.decompress(encoded)
    assert len(decoded) == 5711652 and sha(decoded) == ORIGINAL17_DECODED_SHA
    bundle = json.loads(decoded)
    assert bundle["format"] == "sabueso.card_exploration@17"
    return bundle, decoded


def block_v2(monkeypatch):
    block_current(monkeypatch)
    for name in ("card_bioactivity_history_v2", "card_exploration_bioactivity_v2"):
        target = importlib.import_module("sabueso.core." + name)
        monkeypatch.setattr(target, "expected_result", forbidden)
        monkeypatch.setattr(target, "expected_publication", forbidden)
    target = importlib.import_module("sabueso.core.card_bioactivity_history_v2")
    monkeypatch.setattr(target, "restore_result", forbidden)


def test_original17_read_and_resave_retains_original_binding(tmp_path, monkeypatch):
    _, decoded = original17_bundle()
    path = tmp_path / "original17.json"
    path.write_bytes(decoded)
    block_v2(monkeypatch)
    saved = sabueso.read_exploration(path)
    assert (
        saved.validation["bioactivities"] == "original_frozen_v1_consistency_verified"
    )
    native = saved.native_payload
    output = tmp_path / "resaved17.json"
    saved.save(output)
    assert logical_bundle(output)["format"] == "sabueso.card_exploration@17"
    assert sabueso.read_exploration(output).native_payload == native


def test_original17_explicit_shared18_derivation_preserves_original_binding(
    tmp_path, monkeypatch
):
    from sabueso.core.card_exploration_shared_values_v3 import pack

    original, _ = original17_bundle()
    unsealed = {
        key: value
        for key, value in original.items()
        if key not in ("digests", "bundle_digest")
    }
    # This is a declared representation derivation from the retained original
    # semantic @17 file, not a claim of another genuine original @18 capture.
    shared = _seal(pack(unsealed, threshold=0, min_saving=0))
    assert shared["format"] == "sabueso.card_exploration@18"
    path = tmp_path / "derived18.json"
    path.write_text(canonical_json(shared), encoding="utf-8")
    block_v2(monkeypatch)
    saved = sabueso.read_exploration(path)
    assert (
        saved.validation["bioactivities"] == "original_frozen_v1_consistency_verified"
    )
    output = tmp_path / "resaved18.json"
    saved.save(output)
    assert logical_bundle(output)["format"] == "sabueso.card_exploration@17"
    assert sabueso.read_exploration(output).native_payload == saved.native_payload


def test_fresh_cross_card_bioactivity_question_keeps_own_exact_request(
    original, tmp_path, monkeypatch
):
    from sabueso.core.relationship_store import make_relationship
    from sabueso.core.source_assertion_store import make_source_assertion

    statement = make_source_assertion(
        "relationships.interacts_with",
        {"target": "uniprot:P52270"},
        "Synthetic cross-Card control",
        "public-input-scope",
        "2026-11-07",
        subject_ref="uniprot:P60174",
    )
    relation = make_relationship(
        "uniprot:P60174", "interacts_with", "uniprot:P52270", {}, [statement["id"]]
    )
    first = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:P60174"},
        source_assertion_store=[statement],
        relationship_store=[relation],
    )
    second = Card.from_dict(original.value(original.case("false")["input_card_ref"]))
    explorer = first.explore(related_cards=[second])
    relations = explorer.inspect(
        locator={
            "format": "card_access_location@1",
            "kind": "card",
            "card_ref": explorer.context["card_ref"],
            "snapshot_id": explorer.context["snapshot_id"],
            "segments": [{"type": "Key", "value": "relationship_store"}],
        }
    )
    links = relations.items()[0].related()
    link = next(
        item
        for item in links.items()
        if item.cells["target_ref"].value == "uniprot:P52270"
    )
    destination = links.follow(link.item_ref)
    question = destination.explorer.answer("measured_molecules")
    assert question._origin.request is None
    focused = question.items()[0].open()
    expected_request, expected_native = question.request, question.native_payload
    expected_focal = second.pinned_ref()
    assert focused.request == expected_request
    block_current(monkeypatch)
    path = tmp_path / "new-bioactivity-question.json"
    question.save(path)
    saved = sabueso.read_exploration(path)
    assert saved.request == expected_request and saved.native_payload == expected_native
    assert saved.context["card_ref"] == expected_focal
    assert saved.back().request is None
    assert saved.items()[0].open().request == expected_request
    bundle = logical_bundle(path)
    bundle["views"][bundle["root_navigation_ref"]]["flags"]["_request"]["options"][
        "include_indirect"
    ] = True
    with pytest.raises(StorageError):
        _restore(_seal(bundle), None)


def test_same_molecule_on_foreign_snapshot_cannot_supply_focus_origin(
    original, tmp_path, monkeypatch
):
    from dataclasses import replace

    from sabueso.core.card_exploration_storage import _explorer

    first = Card.from_dict(original.value(original.case("false")["input_card_ref"]))
    second = Card.from_dict(
        original.value(original.case("integer_zero")["input_card_ref"])
    )
    assert first.id == second.id and first.pinned_ref() != second.pinned_ref()
    explorer = first.explore(related_cards=[second])
    root = explorer.view("bioactivities")
    focused = root.items()[0].open()
    foreign_explorer = _explorer(
        explorer.access._for_capture(second.pinned_ref()), explorer._session
    )
    foreign = foreign_explorer.view("bioactivities")
    assert root.context["snapshot_id"] != foreign.context["snapshot_id"]
    assert (
        root.items()[0].cells["molecule_ref"].value
        == foreign.items()[0].cells["molecule_ref"].value
    )
    forged = replace(focused, _origin=foreign)
    block_current(monkeypatch)
    with pytest.raises(StorageError, match="foreign focal capture"):
        forged.save(tmp_path / "foreign-snapshot.json")
