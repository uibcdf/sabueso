"""Byte/graph/native-frame accounting of genuine SDK230 observations, not saved admission."""

import gzip
import hashlib
import json
import shutil
import tarfile
from collections import Counter
from pathlib import Path

import pytest

CAPSULE = Path(__file__).with_name("data") / "variant_tissue_context_live_sdk230.tar.gz"
ENCODED_SHA256 = "27fe90cb9ea17dcb4ce4672c2f485b90cd6fd6477cf85d1d1b1e2b248f950708"
DECODED_SHA256 = "1dab591cce87444ce2d99a25a0b22b9920cad1755f28bd188bbcd84cd0330bac"
DECODED_BYTES = 425492480
PRODUCER = "c5b573b15f61619ff0a3f52ba3c3275807fcd8ba"
MANIFEST_SHA256 = "cdd19ea46e6fd12c1be65e907ee053a133813c3dc6cd8608800c60a74ff50406"
CASES = (
    "bare-isoforms",
    "bare-variants",
    "deferred-values",
    "escaped-source",
    "input-revisions",
    "isoforms-conflicting_tissue",
    "isoforms-equal-occurrences",
    "isoforms-foreign_assembly",
    "isoforms-foreign_chromosome",
    "isoforms-foreign_transcript",
    "isoforms-foreign_version",
    "isoforms-missing_assembly",
    "isoforms-missing_cds",
    "isoforms-support-field",
    "isoforms-support-missing",
    "isoforms-support-subject",
    "machine-first",
    "opaque-source",
    "public-isoforms",
    "public-variants",
    "source-conflict",
    "synthetic-isoforms",
    "synthetic-variants",
    "threshold-float-first",
    "threshold-integer-first",
    "variants-conflicting_tissue",
    "variants-equal-occurrences",
    "variants-foreign_assembly",
    "variants-foreign_chromosome",
    "variants-missing_assembly",
    "variants-support-field",
    "variants-support-missing",
    "variants-support-subject",
)
ENCODER = json.JSONEncoder(
    ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
)


def canonical(value):
    return ENCODER.encode(value)


class Original:
    """Resolve packaging references only at declared protocol edges.

    Scientific/source values are literal JSON. A source-owned dictionary shaped
    like a reference is never interpreted as a packaging reference.
    """

    def __init__(self, directory):
        self.directory = Path(directory)
        self.manifest = json.loads(
            (self.directory / "manifest.json").read_text(encoding="utf-8")
        )
        self.cache, self.paths, self.references = {}, set(), 0

    def ref(self, ref):
        assert set(ref) == {"path", "bytes", "sha256"}
        assert ref["path"] in self.manifest["files"]
        assert {k: ref[k] for k in ("bytes", "sha256")} == self.manifest["files"][
            ref["path"]
        ]
        self.references += 1
        self.paths.add(ref["path"])
        if ref["path"] not in self.cache:
            self.cache[ref["path"]] = json.loads(
                (self.directory / ref["path"]).read_text(encoding="utf-8")
            )
        return self.cache[ref["path"]]

    def case(self, name):
        return self.ref(self.manifest["cases"][name])

    def nodes(self, case):
        return {
            row["node"]: {**row, "observation": self.ref(row["observation_ref"])}
            for row in case["views"]
        }

    def accesses(self, case):
        return {
            key: {
                "focal": row["focal"],
                "nonce": row["nonce"],
                **{name: self.ref(ref) for name, ref in row["fields"].items()},
            }
            for key, row in case["accesses"].items()
        }

    def location(self, access, location):
        if location["kind"] == "lookup":
            location = access["locations"][location["location_ref"]]
        assert location["format"] == "card_access_location@1"
        if location["kind"] == "card":
            candidates = [
                c
                for c in access["captures"].values()
                if c["pin"] == location["card_ref"]
                and c["snapshot"] == location["snapshot_id"]
            ]
            assert len(candidates) == 1
            value = self.ref(candidates[0]["data_ref"])
        else:
            assert location["kind"] == "result"
            value = self.ref(access["objects"][location["result_ref"]])
        for segment in location["segments"]:
            if segment["type"] == "Key":
                value = value[segment["value"]]
            elif segment["type"] == "Index":
                assert type(segment["value"]) is int and segment["value"] >= 0
                value = value[segment["value"]]
            else:
                assert segment["type"] == "Record"
                candidates = [r for r in value if r.get("id") == segment["value"]]
                assert len(candidates) == 1
                value = candidates[0]
        return value


def verify_case(original, name):
    original.cache.clear()
    case = original.case(name)
    source = original.ref(case["input"])
    nodes = original.nodes(case)
    accesses = original.accesses(case)
    assert canonical(source["options"]) == canonical(case["options"])
    focal = accesses[case["root_access_node"]]
    assert canonical(
        original.ref(focal["captures"][focal["focal"]]["data_ref"])
    ) == canonical(source["focal"])
    assert len(nodes) == len(case["views"])
    assert set(case["named_views"].values()) <= nodes.keys()
    assert case["root_access_node"] in accesses
    unavailable, frames, pages, deferred, locations = 0, 0, 0, 0, 0
    for node in nodes.values():
        view = node["observation"]
        own = accesses[node["access_node"]]
        selected = accesses[node["selection_access_node"]]
        assert (
            own["focal"] == selected["focal"] == view["focal"]
            and view["focal"] in own["captures"]
        )
        for key in ("origin_node", "explorer_origin_node"):
            assert node[key] is None or node[key] in nodes
        parent = node["origin_node"] or node["explorer_origin_node"]
        assert view["back_view_ref"] == (
            nodes[parent]["observation"]["view_ref"] if parent is not None else None
        )
        displayed = Counter(
            canonical(item["payload_location"]) for item in view["items"]
        )
        underlying = Counter(
            canonical(entry["location"]) for entry in view["selection"]["entries"]
        )
        assert displayed <= underlying
        if view["record_panel"] == "variants" and view["display_request"] is None:
            assert displayed == underlying
        original.ref(view["native_payload_ref"])
        for entry in view["selection"]["entries"]:
            original.ref(entry["value_ref"])
        unavailable += not view["explorer_available"]
        if not view["explorer_available"]:
            assert view["outcome"]["status"] == "missing_prerequisite"
        for item in view["items"]:
            original.ref(item["support_ref"])
            value = original.location(own, item["payload_location"])
            locations += 1
            for column, cell in item["cells"].items():
                original.ref(cell["support_ref"])
                if view["record_panel"] == "variants":
                    assert cell["encoding"] == "json" and canonical(
                        cell["value"]
                    ) == canonical(value[column])
            if view["record_panel"] == "variants":
                assert item["kind"] == value["kind"] and item["label"] == value["label"]
    for access in accesses.values():
        for capture in access["captures"].values():
            original.ref(capture["data_ref"])
        for ref in access["objects"].values():
            original.ref(ref)
        for selection in access["selections"].values():
            for entry in selection["entries"]:
                original.ref(entry["value_ref"])
        for native in access["native_cache"]:
            original.ref(native["payload_ref"])
        for cached in access["scientific_cache"]:
            assert cached["result_ref"] in access["objects"]
    root_access = accesses[case["root_access_node"]]
    native_objects = {
        canonical(json.loads(row["key"][2])): original.ref(
            root_access["objects"][row["result_ref"]]
        )
        for row in root_access["scientific_cache"]
    }
    for oracle in original.ref(case["native_oracles"]):
        assert canonical(
            native_objects[canonical(oracle["options"])]["native_payload"]
        ) == canonical(oracle["native_payload"])
    assert [
        canonical(json.loads(row["key"][2])) for row in root_access["scientific_cache"]
    ] == [canonical(options) for options in case["warm_order"]]
    if "api_order" in case:
        calls = [
            event
            for event in case["api_order"]
            if event["operation"] != "native_oracle"
        ]
        assert calls[0]["operation"] == (
            "select" if case["route_order"] == "machine_first" else "human"
        )
        for event in case["api_order"]:
            if "view_node" in event:
                assert event["view_node"] in nodes
            if event["operation"] == "select":
                assert event["selection_ref"] in root_access["selections"]
    for query in case["queries"]:
        selection = root_access["selections"][query["selection_ref"]]
        count, keys = 0, []
        for index, ref in enumerate(query["pages"]):
            page = original.ref(ref)
            pages += 1
            assert (
                len(canonical(page).encode("utf-8"))
                <= query["page_options"]["max_bytes"]
            )
            assert (
                page["selection_ref"] == query["selection_ref"]
                and page["page"]["blocked"] is None
            )
            assert (page["page"]["next_cursor"] is None) == (
                index == len(query["pages"]) - 1
            )
            count += len(page["items"])
            for frame in page["items"]:
                frames += 1
                binding = root_access["scientific_items"][frame["item_ref"]]
                keys.append(binding["entry_key"])
                row = original.location(root_access, frame["location"])
                locations += 1
                payload = original.location(root_access, frame["payload_location"])
                locations += 1
                assert canonical(row["item"]) == canonical(payload)
                assert set(frame["cells"]) == set(selection["request"]["fields"])
                assert frame["kind"] == row["kind"]
                if frame["value_included"]:
                    assert frame["label"] == row["label"] and canonical(
                        frame["interpretation"]
                    ) == canonical(row["interpretation"])
                else:
                    deferred += 1
                    assert (
                        "label" not in frame
                        and "interpretation" not in frame
                        and "support" not in frame
                    )
                    assert frame["inspection_required"]
                original.location(root_access, frame["support_location"])
                locations += 1
                for column, cell in frame["cells"].items():
                    if cell["value_included"]:
                        assert canonical(cell["value"]) == canonical(row[column])
                    else:
                        assert "value" not in cell
                    original.location(root_access, cell["value_location"])
                    locations += 1
                    assert canonical(
                        original.location(root_access, cell["interpretation_location"])
                    ) == canonical(row["interpretation"])
                    locations += 1
        assert count == query["count"] == len(selection["entries"])
        assert keys == [entry["key"] for entry in selection["entries"]]
    root = nodes[case["named_views"]["root"]]["observation"]
    assert canonical(original.ref(root["native_payload_ref"])) == canonical(
        native_objects[canonical(case["options"])]["native_payload"]
    )
    return {
        "named_views": len(case["named_views"]),
        "actual_view_instances": len(nodes),
        "actual_access_instances": len(accesses),
        "native_requests": len(case["warm_order"]),
        "machine_queries": len(case["queries"]),
        "machine_pages": pages,
        "machine_frames": frames,
        "deferred_frames": deferred,
        "unavailable_explorer_views": unavailable,
        "exact_locations": locations,
        "synthetic_control": case["synthetic_control"],
    }


def _sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@pytest.fixture(scope="module")
def original(tmp_path_factory, request):
    assert _sha(CAPSULE) == ENCODED_SHA256
    digest, size = hashlib.sha256(), 0
    with gzip.open(CAPSULE, "rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    assert size == DECODED_BYTES and digest.hexdigest() == DECODED_SHA256
    directory = tmp_path_factory.mktemp("variant-sdk230-original")
    observed = {}
    with tarfile.open(CAPSULE, "r|gz") as archive:
        for member in archive:
            assert member.isfile() and member.name not in observed
            target = directory / member.name
            assert target.resolve().is_relative_to(directory.resolve())
            assert member.name == target.relative_to(directory).as_posix()
            target.parent.mkdir(parents=True, exist_ok=True)
            digest, count = hashlib.sha256(), 0
            with archive.extractfile(member) as source, target.open("xb") as output:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
                    count += len(chunk)
                    output.write(chunk)
            assert count == member.size
            observed[member.name] = {"bytes": count, "sha256": digest.hexdigest()}
    result = Original(directory)
    assert set(observed) == set(result.manifest["files"]) | {"manifest.json"}
    assert {
        k: v for k, v in observed.items() if k != "manifest.json"
    } == result.manifest["files"]
    assert observed["manifest.json"]["sha256"] == MANIFEST_SHA256
    try:
        yield result
    finally:
        result.cache.clear()
        if request.config.getini("tmp_path_retention_policy") != "all":
            shutil.rmtree(directory)


def _root(original, name):
    case = original.case(name)
    nodes = original.nodes(case)
    view = nodes[case["named_views"]["root"]]["observation"]
    return view, original.ref(view["native_payload_ref"])


def test_original_clean_producer_rights_scope_and_all_member_bytes(original):
    manifest = original.manifest
    assert manifest["format"] == "variant_tissue_context_live_original@1"
    assert manifest["producer_head"] == PRODUCER
    assert manifest["producer_version"] == "0.14.0+230.gc5b573b"
    assert (
        manifest["genuine_live_original"]
        and manifest["capture_complete"]
        and manifest["source_stable"]
    )
    assert (
        manifest["attempts"]
        == manifest["preparation_attempts"]
        == {"network": 0, "source_acquisitions": 0}
    )
    assert (
        set(manifest["cases"]) == set(CASES)
        and len(CASES) == 33
        and len(manifest["files"]) + 1 == 25714
    )
    before = json.loads(
        (original.directory / "source-before.json").read_text(encoding="utf-8")
    )
    assert before == json.loads(
        (original.directory / "source-after.json").read_text(encoding="utf-8")
    )
    assert len(before) == 1231 and "sabueso/_version.py" in before
    assert "sabueso/core/card_variant_access.py" in before
    assert "sabueso/core/card_variant_history_v1.py" not in before
    assert "sabueso/core/card_exploration_variant.py" not in before
    assert (
        (original.directory / "fixtures/NOTICE.md").is_file()
        and (original.directory / "NOTICE.md").is_file()
        and (original.directory / "LICENSE").is_file()
    )
    for name in CASES:
        assert (original.case(name)["synthetic_control"] is None) == name.startswith(
            "public-"
        )


@pytest.mark.parametrize("name", CASES)
def test_original_actual_view_access_native_and_machine_graph(original, name):
    report = verify_case(original, name)
    assert report["native_requests"] in (3, 4)
    assert report["actual_access_instances"] == 1
    assert report["machine_queries"] == (
        56 if name.startswith("threshold-") else 43 if name == "machine-first" else 42
    )


def test_original_public_and_uncertain_genomic_transcript_scope(original):
    _, variants = _root(original, "public-variants")
    _, isoforms = _root(original, "public-isoforms")
    assert len(variants["items"]) == 15 and len(isoforms["items"]) == 3
    assert all(
        row["coordinate_scope"]["assembly"] == "GRCh38" for row in variants["items"]
    )
    assert [row["isoform"] for row in isoforms["items"]] == [
        "P60174-1",
        "P60174-3",
        "P60174-4",
    ]
    for mode in ("variants", "isoforms"):
        view, native = _root(original, "synthetic-" + mode)
        assert native["items"][0]["pext"]["by_tissue"]["liver"] == 0.0
        assert native["items"][0]["pext"]["by_tissue"]["brain"] is None
        if mode == "variants":
            assert (
                native["items"][0]["coordinate_scope"]["position"] == 15
                and native["items"][0]["location"]["start"] == 999
            )
        for defect in ("foreign_assembly", "foreign_chromosome", "missing_assembly"):
            view, native = _root(original, mode + "-" + defect)
            assert view["outcome"]["status"] == "partial"
            assert all(not row["pext"].get("by_tissue") for row in native["items"])
        view, native = _root(original, mode + "-conflicting_tissue")
        assert all(row["pext"]["by_tissue"]["liver"] is None for row in native["items"])
        view, native = _root(original, "bare-" + mode)
        assert (
            view["outcome"]["status"] == "missing_prerequisite" and not native["items"]
        )
    for defect in ("missing_cds", "foreign_transcript", "foreign_version"):
        view, native = _root(original, "isoforms-" + defect)
        assert (
            view["outcome"]["status"] == "partial"
            and not native["variable_regions_complete"]
        )


def test_original_source_membership_conflicts_and_literal_metadata_stay_distinct(
    original,
):
    for mode in ("variants", "isoforms"):
        for defect in ("subject", "field", "missing"):
            view, _ = _root(original, mode + "-support-" + defect)
            assert view["outcome"]["status"] == "partial"
            assert view["items"][0]["cells"]["support_state"]["value"] == "partial"
            support = original.ref(view["items"][0]["support_ref"])[0]
            assert any(
                row["state"] != "present" for row in support["source_assertions"]
            )
    case = original.case("source-conflict")
    access = original.accesses(case)[case["root_access_node"]]
    scientific = {row["result_ref"] for row in access["scientific_cache"]}
    metadata = []
    for key, ref in access["objects"].items():
        value = original.ref(ref)
        if (
            isinstance(value, dict)
            and isinstance(value.get("context"), dict)
            and value["context"].get("adapter")
            == "variant_tissue_context_exploration@1"
            and key not in scientific
        ):
            metadata.append(value)
    assert any("native_payload" not in value for value in metadata)
    assert all(
        "native_payload" in original.ref(access["objects"][key]) for key in scientific
    )
    root, _ = _root(original, "source-conflict")
    assert root["outcome"]["status"] == "partial"


def test_original_typed_cutoff_creation_orders_remain_distinct(original):
    for name, types in [
        ("threshold-integer-first", (int, float)),
        ("threshold-float-first", (float, int)),
    ]:
        case = original.case(name)
        access = original.accesses(case)[case["root_access_node"]]
        assert [type(opts["threshold"]) for opts in case["warm_order"][:2]] == list(
            types
        )
        rows = access["scientific_cache"]
        assert rows[0]["result_ref"] != rows[1]["result_ref"]
        for row, kind in zip(rows[:2], types, strict=True):
            wire = original.ref(access["objects"][row["result_ref"]])
            assert type(wire["context"]["options"]["threshold"]) is kind
            assert (
                type(wire["native_payload"]["rule"]["parameters"]["threshold"]) is kind
            )


def test_original_opaque_values_escaping_and_atomic_deferral(original):
    case = original.case("opaque-source")
    data = original.ref(case["input"])["focal"]
    opaque = data["sections"]["annotations"]["population_variants"]["value"][0][
        "source_payload"
    ]
    assert opaque == {
        "format": "source-owned@999",
        "rule": "source-owned@7",
        "adapter": "source-owned@9",
        "version": 0,
        "context": False,
        "values": [False, 0, 0.0, None],
    }
    assert [type(value) for value in opaque["values"]] == [bool, int, float, type(None)]
    view, native = _root(original, "escaped-source")
    assert "<script>" not in view["html"] and "&lt;script&gt;" in view["html"]
    assert "<script>" in native["items"][0]["variant_id"]
    case = original.case("deferred-values")
    frames = [
        frame
        for query in case["queries"]
        for ref in query["pages"]
        for frame in original.ref(ref)["items"]
    ]
    deferred = [frame for frame in frames if not frame["value_included"]]
    assert len(deferred) == 12 and all(
        "interpretation" not in frame and "label" not in frame for frame in deferred
    )


def test_original_input_occurrences_and_machine_first_order_are_explicit(original):
    case = original.case("input-revisions")
    source = original.ref(case["input"])
    access = original.accesses(case)[case["root_access_node"]]
    assert len(source["related"]) == 3 and len(access["captures"]) == 2
    case = original.case("machine-first")
    calls = [
        event for event in case["api_order"] if event["operation"] != "native_oracle"
    ]
    assert (
        calls[0]["operation"] == "select"
        and case["queries"][0]["label"] == "first-executed-machine"
    )
    assert any(
        event["operation"] == "human" and event["label"] == "root"
        for event in calls[1:]
    )
