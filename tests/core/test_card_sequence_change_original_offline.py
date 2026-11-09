"""Immutable genuine SDK234 observations; byte/graph checks without saved admission."""

import gzip
import hashlib
import json
import tarfile
from collections import Counter
from pathlib import Path

import pytest

CAPSULE = Path(__file__).with_name("data") / "sequence_change_live_sdk234.tar.gz"
ENCODED_SHA256 = "9720c900281d9fd2f97d82c9ee4f943ae78ca71cba102a193f29bd0cfabdfb02"
ENCODED_BYTES = 6593645
DECODED_SHA256 = "0139902cd995efe2f6b77c5c74150b4ce8577cd30fb606c84417e17a62f0eba2"
DECODED_BYTES = 54845440
MANIFEST_SHA256 = "d6cfb5e48a258d95b2393d25a93b36c8b037a38736141ee99b54ad11f0847b99"
PRODUCER = "87537f5c70f51f540bb82044fdc080bd5c78b547"
CASES = (
    "bare",
    "deferred-values",
    "equal-card-occurrences",
    "escaped-source",
    "foreign-molecule",
    "human-only",
    "input-revisions",
    "machine-only",
    "malformed-alternatives",
    "malformed-bool",
    "malformed-field",
    "malformed-float",
    "malformed-missing",
    "malformed-substitution",
    "missing-end",
    "multiple-native-contexts",
    "opaque-source",
    "public-human-first",
    "public-machine-first",
    "retained-empty",
    "stated-deletion",
    "stated-false",
    "support-conflict",
    "support-field",
    "support-missing",
    "support-normalized-value",
    "support-subject",
    "synthetic-mixed",
    "uncertain-start",
    "unknown-start",
    "unstated-change",
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
        str(p.relative_to(original.directory)): p
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
        == {"network": 0, "source_acquisitions": 0}
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
    assert (
        case["route_mode"] == source["route_mode"]
        and case["route_order"] == source["route_order"]
    )
    assert set(case["named_views"].values()) <= nodes.keys() and len(nodes) == len(
        case["views"]
    )
    wire = original.ref(root["objects"][case["projection_result_ref"]])
    oracle = original.ref(case["source_oracle"])
    assert wire["context"]["adapter"] == "sequence_change_exploration@1"
    assert wire["native_payload"]["rule"]["rule"] == "sequence_change_projection@1"
    assert (
        wire["native_payload"]["rule"]["sabueso_version"]
        == original.manifest["producer_version"]
    )
    assert canonical(wire["native_payload"]["items"]) == canonical(oracle["items"])
    assert canonical(oracle["field_inputs"]) == canonical(
        source["focal"].get("sections", {}).get("features_positional", {})
    )
    assert canonical([row["item"] for row in wire["rows"].values()]) == canonical(
        oracle["items"]
    )
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
            view["record_panel"] == "sequence_changes"
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
            original_value = original.location(access, item["payload_location"])
            locations += 1
            for column, cell in item["cells"].items():
                original.ref(cell["support_ref"])
                if view["record_panel"] == "sequence_changes":
                    assert cell["encoding"] == "json" and canonical(
                        cell["value"]
                    ) == canonical(entry_value[column])
            if view["record_panel"] == "sequence_changes":
                assert canonical(entry_value["item"]) == canonical(original_value)
                assert canonical(entry_value["original_location"]) == canonical(
                    full_location(access, item["payload_location"])
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
    assert (
        len(cached) == 1 and json.loads(cached[0]["key"])["topic"] == "sequence_changes"
    )
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
                payload = original.location(root, frame["payload_location"])
                locations += 2
                assert canonical(row["item"]) == canonical(payload)
                assert canonical(row["original_location"]) == canonical(
                    full_location(root, frame["payload_location"])
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
                        original.location(root, cell["interpretation_location"])
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
        "annotation_occurrences": len(oracle["items"]),
        "structural_sidecars": len(
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


def _sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@pytest.fixture(scope="module")
def original(tmp_path_factory):
    assert CAPSULE.stat().st_size == ENCODED_BYTES
    assert _sha(CAPSULE) == ENCODED_SHA256
    digest, size = hashlib.sha256(), 0
    with gzip.open(CAPSULE, "rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
            assert size <= DECODED_BYTES
    assert size == DECODED_BYTES and digest.hexdigest() == DECODED_SHA256
    directory = tmp_path_factory.mktemp("sequence-sdk234-original")
    observed = {}
    with tarfile.open(CAPSULE, "r|gz") as archive:
        for member in archive:
            assert len(observed) < 4344 and 0 <= member.size <= DECODED_BYTES
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
    return result


def _wire(original, name):
    case = original.case(name)
    access = original.accesses(case)[case["root_access_node"]]
    return original.ref(access["objects"][case["projection_result_ref"]])


def test_original_clean_producer_rights_and_member_scope(original):
    manifest = original.manifest
    assert manifest["format"] == "sequence_change_live_original@1"
    assert manifest["producer_head"] == PRODUCER
    assert manifest["producer_version"] == "0.14.0+234.g87537f5"
    assert manifest["genuine_live_original"] and manifest["capture_complete"]
    assert manifest["source_stable"]
    assert set(manifest["cases"]) == set(CASES) and len(CASES) == 31
    report = verify_members(original)
    assert report == {"members": 4344, "member_bytes": 51586742, "source_paths": 1262}
    before = json.loads(
        (original.directory / "source-before.json").read_text(encoding="utf-8")
    )
    assert "sabueso/core/card_sequence_change_access.py" in before
    assert "sabueso/core/card_sequence_change_history_v1.py" not in before
    assert "sabueso/core/card_exploration_sequence_change.py" not in before
    for name in ("fixtures/NOTICE.md", "NOTICE.md", "LICENSE", "capture-script.py"):
        assert (original.directory / name).is_file()
    assert "CC BY 4.0" in (original.directory / "NOTICE.md").read_text(encoding="utf-8")
    for name in CASES:
        assert (original.case(name)["synthetic_control"] is None) == name.startswith(
            "public-"
        )


@pytest.mark.parametrize("name", CASES)
def test_original_actual_view_access_parent_input_and_machine_graph(original, name):
    report = verify_case(original, name)
    assert report["projection_results"] == 1
    assert report["actual_access_instances"] >= 1


def test_original_complete_reference_closure_and_finite_counts(original):
    # Visit every declared edge, without treating source-owned values as edges.
    original.paths.clear()
    reports = [verify_case(original, name) for name in CASES]
    assert {
        path for path in original.manifest["files"] if path.startswith("values/")
    } <= original.paths
    expected = {
        "named_views": 1677,
        "actual_view_instances": 2952,
        "actual_access_instances": 283,
        "projection_results": 31,
        "annotation_occurrences": 47,
        "structural_sidecars": 9,
        "machine_queries": 483,
        "machine_pages": 513,
        "machine_frames": 397,
        "deferred_frames": 2,
        "unavailable_explorer_views": 2,
        "exact_locations": 29605,
    }
    assert {key: sum(row[key] for row in reports) for key in expected} == expected


def test_original_public_annotation_grain_and_multiple_native_contexts(original):
    for name in ("public-human-first", "public-machine-first"):
        rows = list(_wire(original, name)["rows"].values())
        assert len(rows) == 8 and {row["feature_type"] for row in rows} == {
            "natural_variant"
        }
    mixed = list(_wire(original, "synthetic-mixed")["rows"].values())
    assert {row["feature_type"] for row in mixed} == {"natural_variant", "mutagenesis"}
    assert len(mixed) == 2 and all(row["alternatives"] == ["A", "G"] for row in mixed)
    duplicate = list(_wire(original, "equal-card-occurrences")["rows"].values())
    assert len(duplicate) == 2 and canonical(duplicate[0]["item"]) == canonical(
        duplicate[1]["item"]
    )
    assert duplicate[0]["original_location"] != duplicate[1]["original_location"]
    case = original.case("multiple-native-contexts")
    focal = original.ref(case["input"])["focal"]
    assert len(_wire(original, "multiple-native-contexts")["rows"]) == 1
    # Native input statements remain two; this is not unique feature correspondence.
    native = [
        row
        for row in focal["source_assertion_store"]
        if row.get("field_path") == "features_positional.natural_variant"
    ]
    assert native
    assert "second original native context" in canonical(native)


def test_original_typed_flags_positions_and_uncertainty_are_literal(original):
    def row(name):
        return next(iter(_wire(original, name)["rows"].values()))

    assert row("stated-deletion")["missing"] is True
    assert row("stated-false")["missing"] is False
    assert row("unstated-change")["missing"] is None
    assert row("stated-false")["alternatives"] == []
    assert type(row("malformed-bool")["item"]["location"]["sequence"]["start"]) is bool
    assert (
        type(row("malformed-float")["item"]["location"]["sequence"]["start"]) is float
    )
    assert row("malformed-missing")["item"]["substitution"]["missing"] == "false"
    for name, column in (
        ("malformed-bool", "start"),
        ("malformed-float", "start"),
        ("malformed-missing", "missing"),
    ):
        assert row(name)[column] is None
        case = original.case(name)
        view = original.nodes(case)[case["named_views"]["root"]]["observation"]
        assert view["items"][0]["cells"][column]["state"] == "unrecognized_shape"
    assert row("uncertain-start")["start_modifier"] == "LESS_THAN"
    assert row("unknown-start")["start_modifier"] == "UNKNOWN"
    assert row("missing-end")["end"] is None
    assert row("foreign-molecule")["context_state"] == "unsupported"
    for name in ("malformed-bool", "malformed-float", "uncertain-start"):
        assert row(name)["context_state"] != "ready"


def test_original_source_question_and_explicit_structural_replacement(original):
    inherited = {
        "question": "sequence_changes",
        "topic": "sequence_changes",
        "options": {},
    }
    source_descendants = structural = blocked = 0
    for name in CASES:
        case = original.case(name)
        nodes = original.nodes(case)
        for label, node in case["named_views"].items():
            if not label.startswith("question:item-"):
                continue
            view = nodes[node]["observation"]
            if view["request"] and view["request"]["question"] == "region_coverage":
                structural += 1
                assert name in ("public-human-first", "synthetic-mixed")
                assert view["request"]["topic"] == "structures"
            else:
                assert view["request"] == inherited
                source_descendants += ":child-" in label
                blocked += view["outcome"]["status"] == "unsupported"
    assert source_descendants > 0 and structural > 0 and blocked > 0


def test_original_human_only_machine_only_and_creation_orders(original):
    human = original.case("human-only")
    machine = original.case("machine-only")
    assert human["named_views"] and not human["queries"]
    assert "question" not in human["named_views"]
    assert not machine["views"] and not machine["named_views"] and machine["queries"]
    for name, operation in (
        ("public-human-first", "human"),
        ("public-machine-first", "select"),
    ):
        event = next(
            e
            for e in original.case(name)["api_order"]
            if e["operation"] in ("select", "human")
        )
        assert event["operation"] == operation


def test_original_opaque_source_values_and_supplied_input_revisions(original):
    case = original.case("opaque-source")
    focal = original.ref(case["input"])["focal"]
    opaque = []

    def visit(value):
        if isinstance(value, dict):
            if value.get("format") == "source-owned@99":
                opaque.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(focal)
    assert opaque
    for value in opaque:
        assert canonical(value["values"]) == "[false,0,0.0,null]"
        assert (
            value["context"] is False
            and value["sabueso_version"] == "literal-source-label"
        )
        assert value["reference_lookalike"] == {
            "bytes": 0,
            "path": "values/source-owned.json",
            "sha256": "source-owned",
        }
    case = original.case("input-revisions")
    related = original.ref(case["input"])["related"]
    assert len(related) == 3 and canonical(related[0]) == canonical(related[1])
    assert canonical(related[1]) != canonical(related[2])
    assert len(original.accesses(case)[case["root_access_node"]]["captures"]) == 2
