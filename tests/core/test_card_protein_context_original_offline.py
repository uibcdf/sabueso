"""Immutable genuine SDK239 protein-context observations, independent of saved admission."""

import gzip
import hashlib
import json
import tarfile
from collections import Counter
from pathlib import Path

import pytest

CAPSULE = Path(__file__).with_name("data") / "protein_context_live_sdk239.tar.gz"
ENCODED_SHA256 = "b3eb6e4df386a2e3e08f63be8793c3c8bd4667a3dc62f1f9a4ec7668d7282c19"
ENCODED_BYTES = 12422238
DECODED_SHA256 = "9948675d11573d8ac66f2d6b6da020dfb47a4a07b33c7aa41de0b064b9b7363c"
DECODED_BYTES = 94382080
MANIFEST_SHA256 = "9f9378b1a1e36143676b6548ec1c6b231744a3b932cedb750d367ca589c93369"
PRODUCER = "738a42203288af2ffac9e09e576e618553db8189"
CASES = (
    "ambiguous-revisions",
    "bare",
    "deferred-values",
    "escaped-source",
    "human-only",
    "literal-key-collision",
    "machine-only",
    "malformed-channel",
    "malformed-source-id",
    "null-channel",
    "opaque-source",
    "public-human-first",
    "public-machine-first",
    "public-oma",
    "public-sequence",
    "public-uniref",
    "repeated-inputs",
    "separate-channels",
    "sequence-different",
    "sequence-identical",
    "sequence-lengths",
    "sequence-support-malformed",
    "sequence-support-missing",
    "sequence-support-value",
    "sequence-unstated",
    "supplied-only",
    "support-conflict",
    "support-derived",
    "support-field",
    "support-foreign",
    "support-missing",
    "support-subject",
    "synthetic-associations",
    "synthetic-comparative",
    "typed-conflicts",
)
MEMBERS = 8565
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
    assert wire["context"]["adapter"] == "protein_context_exploration@1"
    assert wire["native_payload"]["rule"]["rule"] == "protein_context_projection@1"
    assert (
        wire["native_payload"]["rule"]["sabueso_version"]
        == original.manifest["producer_version"]
    )
    assert case["topic"] == source["topic"]
    direct = [
        row
        for row in source["focal"]["relationship_store"]
        if row["predicate"]
        in (
            ("ortholog_of", "clustered_with")
            if case["topic"] == "comparative_context"
            else (
                "associated_with",
                "participates_in",
                "interacts_with",
                "functionally_associated_with",
            )
        )
    ]
    assert canonical(direct) == canonical(oracle["relationships"])
    if not source["sequence"]:
        assert Counter(
            canonical(row["item"])
            for row in wire["rows"].values()
            if row["kind"] == "relationship"
        ) == Counter(canonical(row) for row in direct)
        supplied = [
            row["item"]
            for row in wire["rows"].values()
            if row["kind"] == "supplied_capture"
        ]
        expected = (
            [
                {"input_index": index, "capture": capture}
                for index, capture in enumerate(root["inputs"][1:], 1)
                if original.ref(root["captures"][capture]["data_ref"])["meta"].get(
                    "entity_type"
                )
                == "protein"
            ]
            if case["topic"] == "comparative_context"
            else []
        )
        assert Counter(canonical(row) for row in supplied) == Counter(
            canonical(row) for row in expected
        )
        assert canonical(wire["native_payload"]["items"]) == canonical(
            [*direct, *expected]
        )
    else:
        (row,) = wire["rows"].values()
        assert row["kind"] == "sequence_comparison"
        assert row["basis"] == "equal_length_positions@1"
        assert canonical(oracle["sequences"]) == canonical(
            [
                c.get("sections", {}).get("sequence", {}).get("primary")
                for c in [source["focal"], *source["related"]]
            ]
        )
        left, right = oracle["sequences"][:2]
        strings = [
            node.get("value") if isinstance(node, dict) else None
            for node in (left, right)
        ]
        if all(isinstance(value, str) and value for value in strings) and len(
            strings[0]
        ) == len(strings[1]):
            count = sum(a != b for a, b in zip(*strings))
            assert (
                type(row["difference_count"]) is int
                and row["difference_count"] == count
                and row["identical"] is (count == 0)
            )
        else:
            assert row["difference_count"] is None and row["identical"] is None
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
                if entry_value["kind"] == "relationship":
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
    assert len(cached) == 1 and json.loads(cached[0]["key"])["topic"] == case["topic"]
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
                if row["kind"] == "relationship":
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
        "original_relationships": len(oracle["relationships"]),
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
    directory = tmp_path_factory.mktemp("protein-context-sdk239-original")
    observed = {}
    with tarfile.open(CAPSULE, "r|gz") as archive:
        for member in archive:
            assert len(observed) < MEMBERS and 0 <= member.size <= DECODED_BYTES
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


def test_original_clean_producer_and_rights(original):
    manifest = original.manifest
    assert manifest["format"] == "protein_context_live_original@1"
    assert (
        manifest["producer_head"] == PRODUCER
        and manifest["producer_version"] == "0.14.0+239.g738a422"
    )
    assert (
        manifest["genuine_live_original"]
        and manifest["capture_complete"]
        and manifest["source_stable"]
    )
    assert set(manifest["cases"]) == set(CASES) and len(CASES) == 35
    report = verify_members(original)
    assert report["members"] == MEMBERS and report["source_paths"] == 1288
    before = json.loads((original.directory / "source-before.json").read_text())
    assert "sabueso/core/card_protein_context_access.py" in before
    assert "sabueso/core/card_protein_context_history_v1.py" not in before
    for name in ("fixtures/NOTICE.md", "NOTICE.md", "LICENSE", "capture-script.py"):
        assert (original.directory / name).is_file()
    for name in CASES:
        assert (original.case(name)["synthetic_control"] is None) == name.startswith(
            "public-"
        )


@pytest.mark.parametrize("name", CASES)
def test_original_complete_actual_graph_and_finite_requests(original, name):
    result = verify_case(original, name)
    assert result["actual_access_instances"] >= 1


def test_original_exact_reference_closure_and_accounting(original):
    original.paths.clear()
    reports = [verify_case(original, name) for name in CASES]
    assert {
        p for p in original.manifest["files"] if p.startswith("values/")
    } <= original.paths
    expected = {
        "named_views": 2516,
        "actual_view_instances": 4363,
        "actual_access_instances": 601,
        "projection_results": 35,
        "original_relationships": 56,
        "additional_projections": 53,
        "machine_queries": 547,
        "machine_pages": 611,
        "machine_frames": 580,
        "deferred_frames": 10,
        "unavailable_explorer_views": 82,
        "exact_locations": 68852,
    }
    assert {key: sum(row[key] for row in reports) for key in expected} == expected


def test_original_typed_conflicts_and_malformed_values_remain_literal(original):
    row = next(iter(_wire(original, "typed-conflicts")["rows"].values()))
    assert canonical(row["item"]["qualifier_conflicts"]["experiments"]) == "[0,false]"
    assert row["support_state"] == "partial"
    row = next(iter(_wire(original, "malformed-channel")["rows"].values()))
    assert row["channel"] is None and type(row["item"]["qualifiers"]["channel"]) is int
    row = next(iter(_wire(original, "malformed-source-id")["rows"].values()))
    assert row["item"]["source_assertion_ids"] == [{"unknown": False}]
    assert row["support_state"] == "partial"


@pytest.mark.parametrize(
    "name,count,equality",
    [
        ("sequence-identical", 0, True),
        ("sequence-different", 1, False),
        ("sequence-lengths", None, None),
        ("sequence-unstated", None, None),
        ("sequence-support-malformed", None, None),
    ],
)
def test_original_sequence_outcomes_have_explicit_native_scope(
    original, name, count, equality
):
    row = next(iter(_wire(original, name)["rows"].values()))
    assert row["difference_count"] == count and row["identical"] is equality
    assert row["basis"] == "equal_length_positions@1"


def test_original_supplied_occurrences_and_ambiguous_revisions_do_not_merge(original):
    wire = _wire(original, "repeated-inputs")
    rows = list(wire["rows"].values())
    assert len(rows) == 3 and {row["input_index"] for row in rows} == {1, 2, 3}
    assert all(row["support_state"] == "not_a_source_statement" for row in rows)
    case = original.case("ambiguous-revisions")
    nodes = original.nodes(case)
    links = [n["observation"] for n in nodes.values() if n["flags"].get("_link_panel")]
    assert any(
        item["cells"].get("availability", {}).get("value") == "ambiguous"
        for view in links
        for item in view["items"]
    )


def test_original_source_owned_reference_lookalike_remains_literal(original):
    case = original.case("opaque-source")
    focal = original.ref(case["input"])["focal"]
    values = [
        r["qualifiers"]["source_owned"]
        for r in focal["relationship_store"]
        if "source_owned" in r["qualifiers"]
    ]
    assert len(values) == 1 and values[0]["path"] == "values/source-owned.json"
    assert canonical(values[0]["values"]) == "[false,0,0.0,null]"
    assert values[0]["sabueso_version"] == "literal-source-label"
    assert "values/source-owned.json" not in original.manifest["files"]


def test_original_human_and_machine_histories_remain_distinct(original):
    human = original.case("human-only")
    machine = original.case("machine-only")
    assert (
        human["views"]
        and not human["queries"]
        and "question" not in human["named_views"]
    )
    assert not machine["views"] and machine["queries"]
