"""Immutable SDK243 knowledge-comparison values, source and actual-origin graphs."""

import gzip
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
from collections import Counter
from pathlib import Path

import pytest

CAPSULE = Path(__file__).with_name("data") / "knowledge_comparison_live_sdk243.tar.gz"
ENCODED_SHA256 = "3a656731e69d1f1a5f04bf4b836467ffffd4f0a49d94f69e7e7ade2683335d3e"
ENCODED_BYTES = 62899169
DECODED_SHA256 = "9f66bc2c841143129643e85f989d48ea0678b1d0cf901d66e8590a1ae2b6d8ed"
DECODED_BYTES = 537989120
MANIFEST_SHA256 = "3d66f346cdebf449d28c4d6ae441812f757664407c92a3f5b8a3de4176200398"
PRODUCER = "f6d8e4a3e57944ebe1ab4ab838600870ed720e2b"
MEMBERS = 27361
CASES = (
    "ambiguous-forward",
    "ambiguous-reverse",
    "bounded-escaped-label",
    "complete-map",
    "conflict",
    "deferred-values",
    "empty-map",
    "first-exact-revision",
    "foreign-axis",
    "free-text",
    "huge-span",
    "human-only",
    "machine-only",
    "missing-source",
    "nested-types",
    "no-map",
    "one-float",
    "opaque-source-lookalikes",
    "partial-map",
    "public-supplied-map",
    "public-unmapped-human-first",
    "public-unmapped-machine-first",
    "quantity-units",
    "relationship-direction-channels",
    "repeated-inputs",
    "repeated-occurrences",
    "same-rendered-state-labels",
    "second-exact-revision",
    "structure-legs",
    "uncertain-boundary",
    "uncited-alternative",
    "unstated-axis",
    "wrong-field",
    "wrong-indexing",
    "wrong-subject",
    "wrong-value",
    "zero-false",
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


def verify_members(original):
    expected = original.manifest["files"]
    actual = {
        p.relative_to(original.directory).as_posix(): p
        for p in original.directory.rglob("*")
        if p.is_file()
    }
    assert set(actual) == set(expected) | {"manifest.json"}
    total = 0
    for name, row in expected.items():
        path = actual[name]
        assert not path.is_symlink() and path.resolve().is_relative_to(
            original.directory.resolve()
        )
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        assert path.stat().st_size == row["bytes"] and digest == row["sha256"], name
        total += row["bytes"]
    before = json.loads(
        (original.directory / "source-before.json").read_text(encoding="utf-8")
    )
    assert before == json.loads(
        (original.directory / "source-after.json").read_text(encoding="utf-8")
    )
    assert (
        original.manifest["attempts"]
        == original.manifest["preparation_attempts"]
        == {
            "network": 0,
            "source_acquisitions": 0,
            "card_reconstruction": 0,
            "assertion_creation": 0,
        }
    )
    return {
        "members": len(actual),
        "member_bytes": total + actual["manifest.json"].stat().st_size,
        "source_paths": len(before),
    }


def full_location(access, location):
    return (
        access["locations"][location["location_ref"]]
        if location["kind"] == "lookup"
        else location
    )


def raw_field(card, path):
    value = card["sections"]
    for key in path.split("."):
        value = value.get(key) if isinstance(value, dict) else None
    return value


def verify_native_inputs(source, root, wire, oracle, original):
    native = wire["native_payload"]
    cards = [source["focal"], *source["related"]]
    selected = [cards[0], cards[source["other_index"]]]
    capture_keys = [root["focal"], root["inputs"][source["other_index"]]]
    assert canonical(native) == canonical(oracle["native"])
    assert canonical(cards) == canonical(oracle["input_cards"])
    assert canonical(oracle["supplied_occurrences"]) == canonical(root["inputs"][1:])
    assert native["rule"]["rule"] == "card_knowledge_diff@2"
    assert native["rule"]["sabueso_version"] == original.manifest["producer_version"]
    assert wire["rule"]["rule"] == "protein_knowledge_projection@1"
    assert native["inputs"] == {
        role: root["captures"][key]["pin"]
        for role, key in zip(("self", "other"), capture_keys)
    }
    expected_pairs = (
        None if source["residue_map"] is None else sorted(source["residue_map"])
    )
    assert canonical(native["residue_map"]["pairs"]) == canonical(expected_pairs)
    assert native["residue_map"]["alignment_performed"] is False
    assert native["residue_map"]["scientific_correspondence_validated"] is False
    assert canonical(native["rule"]["parameters"]["residue_map"]) == canonical(
        expected_pairs
    )
    occurrences = 0
    for path, row in native["fields"].items():
        for side, card in zip(("self", "other"), selected):
            node = raw_field(card, path)
            value = (
                {"value": node.get("value"), "unit": node["unit"]}
                if node is not None and "unit" in node
                else node.get("value")
                if isinstance(node, dict)
                else None
            )
            assert canonical(row[side]) == canonical(value)
            support = row["support"][side]
            assert canonical(support["field"]) == canonical(node)
            records = {r["id"]: r for r in card["source_assertion_store"]}
            identifiers = (
                node.get("source_assertion_ids", []) if isinstance(node, dict) else []
            )
            assert canonical(support["selected_source_assertions"]) == canonical(
                [records[k] for k in identifiers if k in records]
            )
            assert support["missing_source_assertion_ids"] == [
                k for k in identifiers if k not in records
            ]
            assert canonical(support["other_field_assertions"]) == canonical(
                [
                    r
                    for r in card["source_assertion_store"]
                    if r.get("field_path") == path and r["id"] not in identifiers
                ]
            )
            assert canonical(support["quality_conflicts"]) == canonical(
                [
                    r
                    for r in card["quality"].get("conflicts", [])
                    if r.get("field") == path
                ]
            )
        if "both" in row:
            for side in ("self", "other"):
                entries = [
                    pair[side]
                    for category in ("both", "differ")
                    for pair in row[category]
                ]
                entries += [
                    entry for group in row["ambiguous"] for entry in group[side]
                ]
                entries += [
                    entry
                    for category in (
                        "only_" + side,
                        "unresolved_" + side,
                        "not_comparable_" + side,
                    )
                    for entry in row[category]
                ]
                assert sorted(entry["index"] for entry in entries) == list(
                    range(len(row[side]))
                )
                for entry in entries:
                    assert type(entry["index"]) is int and canonical(
                        entry["item"]
                    ) == canonical(row[side][entry["index"]])
                occurrences += len(entries)
    for predicate, row in native["relationships"].items():
        for side, card in zip(("self", "other"), selected):
            records = [
                r for r in card["relationship_store"] if r["predicate"] == predicate
            ]
            assert canonical(row[side + "_records"]) == canonical(records)
    for side, card in zip(("self", "other"), selected):
        ids = list(
            dict.fromkeys(
                identifier
                for row in card["relationship_store"]
                for identifier in row.get("source_assertion_ids", [])
            )
        )
        records = {r["id"]: r for r in card["source_assertion_store"]}
        support = native["relationship_sources"][side]
        assert canonical(support["assertions"]) == canonical(
            {key: records[key] for key in ids if key in records}
        )
        assert support["missing_source_assertion_ids"] == [
            key for key in ids if key not in records
        ]
    for row in native["knowledge_states"]:
        for side, state in zip(("self", "other"), native["state_inputs"]):
            assert canonical(row[side]) == canonical(
                [
                    r
                    for r in state["rows"]
                    if r["area"] == row["area"] and r["source"] == row["source"]
                ]
            )
    for row in wire["rows"].values():
        assert row["kind"] in (
            "knowledge_field",
            "knowledge_relationships",
            "knowledge_state",
            "supplied_residue_map",
        )
        assert canonical(row["item"]) == canonical(
            original.location(root, row["original_location"])
        )
        assert row["interpretation"]["rule"] == "protein_knowledge_projection@1"
        assert row["interpretation"]["identity"] == "not_inferred"
    return occurrences


def verify_case(original, name):
    original.cache.clear()
    case = original.case(name)
    source = original.ref(case["input"])
    nodes = original.nodes(case)
    accesses = original.accesses(case)
    root = accesses[case["root_access_node"]]
    assert canonical(
        original.ref(root["captures"][root["focal"]]["data_ref"])
    ) == canonical(source["focal"])
    assert canonical(source) == canonical(
        json.loads((original.directory / "inputs.json").read_text(encoding="utf-8"))[
            name
        ]
    )
    assert (
        case["route_mode"] == source["route_mode"]
        and case["route_order"] == source["route_order"]
    )
    assert set(case["named_views"].values()) <= nodes.keys() and len(nodes) == len(
        case["views"]
    )
    wire = original.ref(root["objects"][case["projection_result_ref"]])
    oracle = original.ref(case["source_oracle"])
    assert wire["context"]["adapter"] == "protein_knowledge_comparison_exploration@1"
    assert case["topic"] == source["topic"] == "comparative_context"
    assert (
        case["question"] == "knowledge_differences"
        and case["options"]["mode"] == "knowledge"
    )
    assert case["options"]["other_ref"] == root["inputs"][source["other_index"]]
    assert case["native_comparison_calls"] == 1
    occurrences = verify_native_inputs(source, root, wire, oracle, original)
    unavailable = locations = pages = frames = deferred = 0
    for node in nodes.values():
        view = node["observation"]
        access = accesses[node["access_node"]]
        selection_access = accesses[node["selection_access_node"]]
        assert access["focal"] == selection_access["focal"] == view["focal"]
        for edge in ("origin_node", "explorer_origin_node"):
            assert node[edge] is None or node[edge] in nodes
        parent = node["origin_node"] or node["explorer_origin_node"]
        assert view["back_view_ref"] == (
            nodes[parent]["observation"]["view_ref"] if parent else None
        )
        displayed = Counter(canonical(row["entry_location"]) for row in view["items"])
        underlying = Counter(
            canonical(row["location"]) for row in view["selection"]["entries"]
        )
        assert displayed <= underlying
        if (
            view["record_panel"] == "protein_context"
            and view["display_request"] is None
        ):
            assert displayed == underlying
        original.ref(view["native_payload_ref"])
        for ref in node["runtime_state_refs"].values():
            original.ref(ref)
        for entry in view["selection"]["entries"]:
            original.ref(entry["value_ref"])
        unavailable += not view["explorer_available"]
        for item in view["items"]:
            original.ref(item["support_ref"])
            entry_value = original.location(access, item["entry_location"])
            locations += 1
            original_value = (
                original.location(access, item["payload_location"])
                if item["payload_location"] is not None
                else entry_value["item"]
            )
            locations += item["payload_location"] is not None
            for column, cell in item["cells"].items():
                original.ref(cell["support_ref"])
                if view["record_panel"] == "protein_context":
                    assert cell["encoding"] == "json" and canonical(
                        cell["value"]
                    ) == canonical(entry_value[column])
            if view["record_panel"] == "protein_context":
                if True:
                    assert canonical(entry_value["item"]) == canonical(original_value)
                assert (
                    canonical(entry_value["original_location"])
                    == canonical(full_location(access, item["payload_location"]))
                    if item["payload_location"] is not None
                    else entry_value["original_location"] is None
                )
                assert (
                    item["kind"] == entry_value["kind"]
                    and item["label"] == entry_value["label"]
                )
    for access in accesses.values():
        for row in access["captures"].values():
            original.ref(row["data_ref"])
        for ref in access["objects"].values():
            original.ref(ref)
        for selection in access["selections"].values():
            for entry in selection["entries"]:
                original.ref(entry["value_ref"])
        for native in access["native_cache"]:
            original.ref(native["payload_ref"])
        for cached in access["scientific_cache"]:
            assert cached["result_ref"] in access["objects"]
    cached = [
        row
        for row in root["scientific_cache"]
        if row["result_ref"] == case["projection_result_ref"]
    ]
    assert len(cached) == 1
    cache_key = json.loads(cached[0]["key"])
    assert cache_key["adapter"] == "protein_knowledge_comparison_exploration@1"
    assert cache_key["focal"] == root["focal"] and canonical(
        cache_key["options"]
    ) == canonical(wire["context"]["options"])
    for query in case["queries"]:
        selection = root["selections"][query["selection_ref"]]
        count = 0
        keys = []
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
                binding = root["scientific_items"][frame["item_ref"]]
                keys.append(binding["entry_key"])
                row = original.location(root, frame["location"])
                payload = (
                    original.location(root, frame["payload_location"])
                    if frame["payload_location"] is not None
                    else row["item"]
                )
                locations += 1 + (frame["payload_location"] is not None)
                if True:
                    assert canonical(row["item"]) == canonical(payload)
                assert (
                    canonical(row["original_location"])
                    == canonical(full_location(root, frame["payload_location"]))
                    if frame["payload_location"] is not None
                    else row["original_location"] is None
                )
                assert (
                    set(frame["cells"]) == set(selection["request"]["fields"])
                    and frame["kind"] == row["kind"]
                )
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
                original.location(root, frame["support_location"])
                locations += 1
                for column, cell in frame["cells"].items():
                    if cell["value_included"]:
                        assert canonical(cell["value"]) == canonical(row[column])
                    else:
                        assert "value" not in cell
                    original.location(root, cell["value_location"])
                    locations += 1
                    assert canonical(
                        original.location(
                            root,
                            cell.get(
                                "interpretation_location",
                                frame["interpretation_location"],
                            ),
                        )
                    ) == canonical(row["interpretation"])
                    locations += 1
        assert count == query["count"] == len(selection["entries"])
        assert keys == [row["key"] for row in selection["entries"]]
    for event in case["api_order"]:
        if "view_node" in event:
            assert event["view_node"] in nodes
        if event["operation"] == "select":
            assert event["selection_ref"] in root["selections"]
    first = next(
        event
        for event in case["api_order"]
        if event["operation"] in ("select", "human")
    )
    assert first["operation"] == (
        "select" if case["route_order"] == "machine_first" else "human"
    )
    if case["route_mode"] == "machine_only":
        assert (
            not nodes
            and not case["named_views"]
            and not any(e["operation"] == "human" for e in case["api_order"])
        )
    if case["route_mode"] == "human_only":
        assert (
            not case["queries"]
            and "question" not in case["named_views"]
            and not any(e["operation"] == "select" for e in case["api_order"])
        )
    return {
        "named_views": len(case["named_views"]),
        "actual_view_instances": len(nodes),
        "actual_access_instances": len(accesses),
        "projection_results": 1,
        "native_fields": len(wire["native_payload"]["fields"]),
        "original_item_occurrences": occurrences,
        "additional_projections": len(
            {r["result_ref"] for r in root["scientific_cache"]}
            - {case["projection_result_ref"]}
        ),
        "machine_queries": len(case["queries"]),
        "machine_pages": pages,
        "machine_frames": frames,
        "deferred_frames": deferred,
        "unavailable_explorer_views": unavailable,
        "exact_locations": locations,
        "synthetic_control": case["synthetic_control"],
    }


def verify_batches(original):
    batches = original.manifest.get("capture_batches", [])
    seen = set()
    for ref in batches:
        batch = original.ref(ref)
        assert batch["producer_head"] == original.manifest["producer_head"]
        assert batch["producer_version"] == original.manifest["producer_version"]
        assert (
            batch["source_stable"]
            and batch["capture_complete"]
            and batch["genuine_live_original"]
        )
        assert not any(batch["attempts"].values()) and not any(
            batch["preparation_attempts"].values()
        )
        assert (
            batch["prepared_inputs_sha256"]
            == original.manifest["prepared_inputs_sha256"]
        )
        assert not seen & set(batch["cases"])
        seen.update(batch["cases"])
        for path, row in batch["files"].items():
            assert original.manifest["files"][path] == row
        for name, row in batch["cases"].items():
            assert original.manifest["cases"][name] == row
    if batches:
        assert len(batches) == 4 and seen == set(original.manifest["cases"])
    return len(batches)


def main():
    directory = Path(sys.argv[1])
    original = Original(directory)
    assert original.manifest["format"] == "knowledge_comparison_live_original@1"
    report = {
        "state": "PASS",
        "scope": "SDK-free complete byte/declared-reference/actual-parent/access/direct-input/native occurrence/compact-frame accounting. No scientific recomputation or saved-reader admission.",
        **verify_members(original),
    }
    report["capture_batches"] = verify_batches(original)
    report["cases"] = {
        name: verify_case(original, name) for name in original.manifest["cases"]
    }
    report["declared_references"] = original.references
    report["unreferenced_value_members"] = len(
        {p for p in original.manifest["files"] if p.startswith("values/")}
        - original.paths
    )
    assert report["unreferenced_value_members"] == 0
    report["totals"] = {
        key: sum(row[key] for row in report["cases"].values())
        for key in next(iter(report["cases"].values()))
        if key != "synthetic_control"
    }
    directory.parent.joinpath(
        directory.name + "-independent-verification.json"
    ).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()


class DigestingReader:
    """Hash the complete decoded tar while extraction stays streaming."""

    def __init__(self, stream):
        self.stream = stream
        self.digest = hashlib.sha256()
        self.bytes = 0

    def read(self, size=-1):
        block = self.stream.read(size)
        self.digest.update(block)
        self.bytes += len(block)
        return block


@pytest.fixture(scope="module")
def original(tmp_path_factory, request):
    assert CAPSULE.stat().st_size == ENCODED_BYTES
    with CAPSULE.open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == ENCODED_SHA256
    directory = tmp_path_factory.mktemp("knowledge-original-sdk243")
    names = set()
    with gzip.open(CAPSULE, "rb") as stream:
        reader = DigestingReader(stream)
        with tarfile.open(fileobj=reader, mode="r|") as archive:
            for member in archive:
                path = Path(member.name)
                assert member.isfile() and not path.is_absolute()
                assert ".." not in path.parts and member.name not in names
                target = directory / path
                assert target.resolve().is_relative_to(directory.resolve())
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
                names.add(member.name)
        while reader.read(1024 * 1024):
            pass
    assert reader.bytes == DECODED_BYTES
    assert reader.digest.hexdigest() == DECODED_SHA256
    with (directory / "manifest.json").open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == MANIFEST_SHA256
    result = Original(directory)
    assert len(names) == MEMBERS
    assert set(result.manifest["cases"]) == set(CASES)
    assert result.manifest["producer_head"] == PRODUCER
    assert result.manifest["producer_version"] == "0.14.0+243.gf6d8e4a"
    try:
        yield result
    finally:
        result.cache.clear()
        if request.config.getini("tmp_path_retention_policy") != "all":
            shutil.rmtree(directory)


def test_complete_original_members_and_batch_provenance(original):
    assert verify_members(original)["members"] == MEMBERS
    assert verify_batches(original) == 4
    source = json.loads(
        (original.directory / "source-before.json").read_text(encoding="utf-8")
    )
    assert len(source) == 1318
    assert "sabueso/core/card_knowledge_comparison_history_v1.py" not in source
    assert "sabueso/core/card_knowledge_diff_v2.py" in source


@pytest.mark.parametrize("name", CASES)
def test_all_original_native_values_sources_and_actual_graphs(original, name):
    result = verify_case(original, name)
    assert result["projection_results"] == 1
    assert result["additional_projections"] == 0


def original_native(original, name):
    original.cache.clear()
    case = original.case(name)
    root = original.accesses(case)[case["root_access_node"]]
    return original.ref(root["objects"][case["projection_result_ref"]])[
        "native_payload"
    ]


def test_original_types_quantities_and_complete_candidate_groups(original):
    row = original_native(original, "zero-false")["fields"]["annotations.taxon_id"]
    assert type(row["self"]) is int and row["self"] == 0
    assert row["other"] is False and row["status"] == "differs"
    row = original_native(original, "one-float")["fields"]["annotations.taxon_id"]
    assert type(row["self"]) is int and type(row["other"]) is float
    assert row["status"] == "differs"
    row = original_native(original, "quantity-units")["fields"][
        "sequence.molecular_weight"
    ]
    assert row["self"] == {"value": 3.5, "unit": "dalton"}
    assert row["other"] == {"value": 4.5, "unit": "dalton"}
    for name in ("ambiguous-forward", "ambiguous-reverse"):
        row = original_native(original, name)["fields"][
            "features_positional.active_site"
        ]
        assert row["status"] == "partial" and not row["both"] and not row["differ"]
        assert len(row["ambiguous"][0]["other"]) == 2
    assert original_native(original, "no-map")["residue_map"]["pairs"] is None
    assert original_native(original, "empty-map")["residue_map"]["pairs"] == []


def test_actual_equal_focal_access_instances_are_not_collapsed(original):
    original.cache.clear()
    case = original.case("public-supplied-map")
    accesses = original.accesses(case)
    by_focal = Counter(row["focal"] for row in accesses.values())
    assert max(by_focal.values()) > 1
    assert len(accesses) == len(case["accesses"])
    nodes = original.nodes(case)
    actual_pairs = {
        (row["access_node"], row["selection_access_node"]) for row in nodes.values()
    }
    assert len(actual_pairs) > 2
    assert set(case["named_views"].values()) <= nodes.keys()


def test_source_owned_reference_and_version_lookalikes_remain_literal(original):
    native = original_native(original, "opaque-source-lookalikes")
    value = native["fields"]["annotations.synthetic_record"]["self"]
    assert value["path"] == "values/source-owned.json"
    assert value["format"] == "source-owned@99"
    assert value["sabueso_version"] == "literal-source-label"
    assert canonical(value["values"]) == "[false,0,0.0,null]"
    assert value["path"] not in original.manifest["files"]
    assert value["path"] not in original.paths


def test_actual_public_original_in_fresh_sdk_forbidden_process(original, tmp_path):
    script = r"""
import importlib.abc
import json
import runpy
import socket
import sys

attempts = {"sdk": 0, "network": 0}
class ForbidSDK(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in ("sabueso", "molsysmt"):
            attempts["sdk"] += 1
            raise RuntimeError("Original verification must remain SDK-free")
sys.meta_path.insert(0, ForbidSDK())
def network(*args, **kwargs):
    attempts["network"] += 1
    raise RuntimeError("Original verification must remain offline")
socket.create_connection = socket.socket.connect = network
assert not any(name.split(".")[0] in ("sabueso", "molsysmt") for name in sys.modules)
module = runpy.run_path(sys.argv[1], run_name="sdk_free_original_verification")
original = module["Original"](sys.argv[2])
module["verify_members"](original)
module["verify_batches"](original)
result = module["verify_case"](original, "public-supplied-map")
assert result["actual_view_instances"] > 0 and result["machine_queries"] > 0
assert not any(attempts.values())
assert not any(name.split(".")[0] in ("sabueso", "molsysmt") for name in sys.modules)
print(json.dumps({"state": "PASS", "attempts": attempts}))
"""
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            script,
            str(Path(__file__).resolve()),
            str(original.directory),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {
        "state": "PASS",
        "attempts": {"sdk": 0, "network": 0},
    }
