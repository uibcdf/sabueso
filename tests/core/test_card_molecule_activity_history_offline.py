"""Independent predicates against every complete immutable SDK205 original wire."""

import gzip
import hashlib
import importlib
import json
import socket
import tarfile
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from sabueso.core.errors import StorageError
from sabueso.core.snapshot import canonical_json

DATA = Path(__file__).with_name("data") / "molecule_activity_live_sdk205.tar.gz"
ENCODED_SHA = "61a5556a3d9cc75485a321c707341f2233954606b14c2e917bd5cd627b3d123f"
DECODED_SHA = "47f4a14976c345a9ad52f3eeefd7c7ef5d358685b9cd8deaeee4b8280bb48b10"
MANIFEST_SHA = "c6fc262c3a02d3756e771709c622a14d932130182b914c758260a138615cf9eb"
DECODED_BYTES = 1720330240
CASES = (
    "benz",
    "bts",
    "conflicting-anchors",
    "copy-1-joined",
    "copy-1-unjoined",
    "copy-2-joined",
    "copy-2-unjoined",
    "duplicate-molecules",
    "duplicate-targets",
    "empty",
    "explicit-physical-thresholds",
    "failed",
    "foreign-target-identity",
    "full-molecule-deck",
    "include-indirect",
    "incoherent-molecule-anchor",
    "missing-context",
    "missing-identity",
    "missing-identity-support",
    "mixed-source-states",
    "multiple-aliases",
    "nonprotein-context",
    "optin-policies",
    "original-classification",
    "two-target-snapshots",
    "unmatched-alias-opaque",
    "unqueried",
    "unsupported-context",
    "wrong-focal-nature",
)
ADAPTER = "molecule_activity_context_exploration@1"
SUPPLEMENT = DATA.with_name("molecule_activity_multifocal_live_sdk208.tar.gz")
SUPPLEMENT_SHA = "599a755df31fa5b17b4d39d899bf02adae80bd9f7e55c5140aeb02f6d562a699"
SUPPLEMENT_DECODED_SHA = (
    "9f9679cb4589790e7171c7beace3e845e4aae44c737afaeb3cf8193cf4947cf3"
)
SUPPLEMENT_MANIFEST_SHA = (
    "c7e1bdec2c438e2b2c255b728ec485c8f72491f74c00a3809dd02f16565e15c9"
)
SUPPLEMENT_DECODED_BYTES = 454113280
SUPPLEMENT_CASES = ("bts-to-benz", "benz-to-bts", "bts-to-same-id-snapshot")


class Original:
    """Seek in one plain tar; never re-expand gzip for each random member."""

    def __init__(self, path):
        self.archive, self.cache = tarfile.open(path, "r:"), OrderedDict()
        self.manifest = self.member("manifest.json")
        assert self.manifest["capture_complete"]
        assert (
            self.manifest["producer_head"] == "ddc1fc83725d10c2cc5fe569341ae1b761dddc8d"
        )
        assert self.manifest["producer_version"] == "0.14.0+205.gddc1fc8"
        assert set(self.manifest["cases"]) == set(CASES)
        members, expected = self.archive.getmembers(), self.manifest["files"]
        assert len(members) == len(expected) + 1 == 6035
        assert {m.name for m in members} == {*expected, "manifest.json"}
        for member in members:
            assert member.isfile() and not Path(member.name).is_absolute()
            assert ".." not in Path(member.name).parts
            with self.archive.extractfile(member) as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if member.name == "manifest.json":
                assert digest == MANIFEST_SHA
            else:
                assert member.size == expected[member.name]["bytes"]
                assert digest == expected[member.name]["sha256"]

    def member(self, name):
        if name in self.cache:
            self.cache.move_to_end(name)
        else:
            with self.archive.extractfile(name) as stream:
                self.cache[name] = json.load(stream)
            if len(self.cache) > 12:
                self.cache.popitem(last=False)
        return self.cache[name]

    def value(self, ref):
        return deepcopy(self.member(ref["path"]))

    def case(self, name):
        return self.member(self.manifest["cases"][name]["path"])

    def access(self, name):
        case = self.case(name)
        focal = case["human"]["root"]["focal"]
        state = case["access_states"][focal]
        keys = list(dict.fromkeys([*state["inputs"], *state["captures"]]))
        captures = {
            key: SimpleNamespace(
                pin=state["captures"][key]["pin"],
                snapshot=state["captures"][key]["snapshot"],
                data=self.value(state["captures"][key]["data_ref"]),
            )
            for key in keys
        }
        return SimpleNamespace(
            _captures=captures,
            _inputs=state["inputs"],
            _focal_key=state["focal"],
            _nonce=state["nonce"],
        )

    def wires(self, name):
        case = self.case(name)
        state = case["access_states"][case["human"]["root"]["focal"]]
        for ref, member in state["objects"].items():
            value = self.member(member["path"])
            if (
                isinstance(value, dict)
                and isinstance(value.get("context"), dict)
                and value["context"].get("adapter") == ADAPTER
                and "native_payload" in value
            ):
                yield ref, deepcopy(value)

    def crossings(self, name):
        seen = set()
        for view in self.case(name)["human"].values():
            context = view["context"]
            if context.get("activity_context") != "native_ligand_crossing":
                continue
            key = (context["target_card_ref"], view["native_payload_ref"]["path"])
            if key not in seen:
                seen.add(key)
                yield context, self.value(view["native_payload_ref"])

    def close(self):
        self.cache.clear()
        self.archive.close()


class MultiFocalOriginal(Original):
    """Read the complete corrected supplement with its own producer binding."""

    def __init__(self, path):
        self.archive, self.cache = tarfile.open(path, "r:"), OrderedDict()
        self.manifest = self.member("manifest.json")
        assert self.manifest["capture_complete"]
        assert not self.manifest["admitted_saved_format"]
        assert (
            self.manifest["producer_head"] == "142618d305d7d0c732f3ebdbf2d49ee6a9bbb65c"
        )
        assert self.manifest["producer_version"] == "0.14.0+208.g142618d"
        assert not any(self.manifest["attempts"].values())
        assert self.manifest["parent_original"]["sha256"] == ENCODED_SHA
        assert set(self.manifest["cases"]) == set(SUPPLEMENT_CASES)
        members, expected = self.archive.getmembers(), self.manifest["files"]
        assert len(members) == len(expected) + 1 == 1740
        assert {m.name for m in members} == {*expected, "manifest.json"}
        for member in members:
            assert member.isfile() and not Path(member.name).is_absolute()
            assert ".." not in Path(member.name).parts
            with self.archive.extractfile(member) as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if member.name == "manifest.json":
                assert digest == SUPPLEMENT_MANIFEST_SHA
            else:
                assert member.size == expected[member.name]["bytes"]
                assert digest == expected[member.name]["sha256"]

    def focal_access(self, name, focal):
        state = self.case(name)["access_states"][focal]
        keys = list(dict.fromkeys([*state["inputs"], *state["captures"]]))
        return SimpleNamespace(
            _captures={
                key: SimpleNamespace(
                    pin=state["captures"][key]["pin"],
                    snapshot=state["captures"][key]["snapshot"],
                    data=self.value(state["captures"][key]["data_ref"]),
                )
                for key in keys
            },
            _inputs=state["inputs"],
            _focal_key=focal,
            _nonce=state["nonce"],
        )


@pytest.fixture(scope="module")
def multifocal_original(tmp_path_factory, request):
    with SUPPLEMENT.open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == SUPPLEMENT_SHA
    path = tmp_path_factory.mktemp("sdk208-multifocal-original") / "original.tar"
    digest, total = hashlib.sha256(), 0
    with gzip.open(SUPPLEMENT, "rb") as source, path.open("xb") as target:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
            total += len(chunk)
            assert total <= SUPPLEMENT_DECODED_BYTES
            target.write(chunk)
    assert total == SUPPLEMENT_DECODED_BYTES
    assert digest.hexdigest() == SUPPLEMENT_DECODED_SHA
    control = MultiFocalOriginal(path)
    try:
        yield control
    finally:
        control.close()
        if request.config.getini("tmp_path_retention_policy") != "all":
            path.unlink()


@pytest.mark.parametrize("case", SUPPLEMENT_CASES)
def test_corrected_multifocal_original_keeps_independent_exact_capture_crossings(
    multifocal_original, case, monkeypatch
):
    block_current(monkeypatch)
    from sabueso.core._molecule_activity_history_v1.adapter import defer_frame
    from sabueso.core.card_molecule_activity_history_v1 import (
        expected_result,
        expected_selection,
    )

    original, expected = multifocal_original, {}
    recorded = original.case(case)
    assert len(recorded["native_crossing_cache"]) == 2
    assert len(recorded["target_bioactivity_calls"]) == 1
    for prefix in ("first", "second"):
        crossing = recorded["crossings"][prefix]
        focal, pin = crossing["focal"], crossing["molecule_pin"]
        access = original.focal_access(case, focal)
        assert access._captures[focal].pin == pin
        state = recorded["access_states"][focal]
        for ref, member in state["objects"].items():
            value = original.value(member)
            if (
                not isinstance(value, dict)
                or not isinstance(value.get("context"), dict)
                or value["context"].get("adapter") != ADAPTER
                or value["context"].get("molecule_card_ref") != pin
                or "native_payload" not in value
            ):
                continue
            result = expected_result(
                access, value["context"]["options"], original=value
            )
            assert result.result_ref == ref
            assert canonical_json(result.wire) == canonical_json(value)
            expected[ref] = result
        source_ref = recorded["human"][prefix + "/root"]["selection"][
            "scientific_result_ref"
        ]
        result = expected[source_ref]
        native, location = result.native_crossing(crossing["target_pin"])
        assert canonical_json(native) == canonical_json(
            original.value(crossing["oracle_ref"])
        )
        wrapper = result._access._objects[location["result_ref"]]
        assert canonical_json(wrapper) == canonical_json(
            original.value(crossing["wrapper_ref"])
        )
        assert canonical_json(location) == canonical_json(crossing["payload_location"])
        assert wrapper["molecule_card_ref"] == pin
    assert len({c["molecule_pin"] for c in recorded["crossings"].values()}) == 2
    assert len({c["focal"] for c in recorded["crossings"].values()}) == 2
    for request in recorded["machine"]:
        selection, query = request["selection"], request["query"]
        result = expected[selection["scientific_result_ref"]]
        assert result._access._focal_key == request["focal"]
        ref, entries, fields, _ = expected_selection(result, **query)
        assert ref == selection["selection_ref"]
        assert [entry.key for entry in entries] == [
            entry["key"] for entry in selection["entries"]
        ]
        assert list(fields) == selection["request"]["fields"]
        for page in original.value(request["pages_ref"]):
            assert page["page"]["total"] == len(entries)
            for index, frame in enumerate(page["items"], start=page["page"]["offset"]):
                actual = result.frame(
                    result._access, SimpleNamespace(_fields=fields), entries[index]
                )
                if not frame["value_included"]:
                    actual = defer_frame(actual)
                assert canonical_json(actual) == canonical_json(frame)


def forbidden(*args, **kwargs):
    raise AssertionError(
        "Original expectations cannot call current Cards, science or sources"
    )


def block_current(monkeypatch):
    """Import targets first; aliases in a new kernel must never use these APIs."""
    import sabueso
    from sabueso.core.card import Card
    from sabueso.core.deck import Deck

    targets = {
        "card_molecule_activity_access": (
            "materialize",
            "options_for_activity_context",
        ),
        "card_molecule_activity_selection_v1": (
            "normalize",
            "evaluate",
            "projection",
            "sorted_entries",
        ),
        "card_bioactivity_access": (
            "materialize",
            "_native",
            "options_for_bioactivities",
        ),
        "bioactivities": ("bioactivities_view", "resolve_thresholds"),
        "bioactivity_explanation": ("explain_bioactivity", "explain_measurement"),
        "ligands": ("ligands_view",),
        "ligand_explanation": ("explain_ligand", "explain_ligand_site"),
        "ligand_sites": ("ligand_sites_view", "annotated_sites"),
        "ligand_site_scope": ("reference", "annotation", "contact"),
        "literature": ("literature_view",),
        "literature_explanation": ("explain_literature",),
        "knowledge_state": ("knowledge_state",),
        "relationship_store": ("make_derivation",),
    }
    modules = {
        name: importlib.import_module("sabueso.core." + name) for name in targets
    }
    clients = []
    for name, suffix in (
        ("uniprot", "UniProt"),
        ("rcsb", "RCSB"),
        ("chembl", "ChEMBL"),
        ("pdb_ccd", "CCD"),
        ("europepmc", "EuropePMC"),
    ):
        module = importlib.import_module("sabueso.tools.db." + name)
        clients.extend(
            getattr(module, prefix + suffix + "Client")
            for prefix in ("Fixture", "Online")
        )
    for module in (
        "target_card_ref",
        "item_ref",
        "include_indirect",
        "thresholds",
        "molecule_ref",
        "measurement_ref",
        "classification_rule",
        "measurement_rule",
        "target_scope_rule",
    ):
        loaded = importlib.import_module(
            "sabueso._private.argdigest.argument." + module
        )
        monkeypatch.setattr(loaded, "digest_" + module, forbidden)
    for name in (
        "__init__",
        "from_dict",
        "bioactivities",
        "explain_bioactivity",
        "explain_measurement",
        "ligands",
        "explain_ligand",
        "literature",
        "explain_literature",
        "knowledge_state",
        "explain",
    ):
        monkeypatch.setattr(Card, name, forbidden)
    monkeypatch.setattr(Deck, "__init__", forbidden)
    for name, exports in targets.items():
        for export in exports:
            monkeypatch.setattr(modules[name], export, forbidden)
    for client in clients:
        monkeypatch.setattr(client, "__init__", forbidden)
    for name in ("resolve", "refresh_card"):
        monkeypatch.setattr(sabueso, name, forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def retained_keys(control, case, ref, wire):
    """Find complete original row order in actual unfiltered observations."""
    recorded = control.case(case)
    candidates = [
        view["selection"]
        for view in recorded["human"].values()
        if view["selection"]["request"]["operation"] == "read"
    ]
    candidates.extend(
        query["selection"]
        for query in recorded["machine"]
        if not any(
            query["query"].get(key) is not None
            for key in ("where", "item_refs", "order_by")
        )
    )
    for selection in candidates:
        if selection["scientific_result_ref"] != ref:
            continue
        keys = [entry["key"] for entry in selection["entries"]]
        if len(keys) == len(wire["rows"]) and set(keys) == set(wire["rows"]):
            return keys
    raise AssertionError("Complete original order must have an observed witness")


def retained_crossings(control, case, ref):
    """Read actual visited crossing wrappers, without evaluating native science."""
    recorded, result = control.case(case), {}
    for view in recorded["human"].values():
        context = view["context"]
        navigation = context.get("molecule_activity_navigation", {})
        if (
            context.get("activity_context") != "native_ligand_crossing"
            or navigation.get("source_result_ref") != ref
        ):
            continue
        state = recorded["access_states"][view["focal"]]
        location = view["selection"]["request"]["target"]["location"]
        if location["kind"] == "lookup":
            location = state["locations"][location["location_ref"]]
        pin = context["target_card_ref"]
        result[pin] = {
            "wrapper": control.value(state["objects"][location["result_ref"]]),
            "location": location,
            "inputs": state["inputs"],
            "policies": {
                key: value
                for key, value in navigation["scientific_options"].items()
                if key not in ("target_card_ref", "molecule_ref", "measurement_ref")
            },
        }
    return result


def restored_original_results(control, case):
    """Expose each original wire using only inert input and retained facades."""
    from sabueso.core._molecule_activity_history_v1.inputs import _FrozenAccess
    from sabueso.core.card_molecule_activity_history_v1 import restore_result

    recorded, seen = control.case(case), set()
    for focal, state in recorded["access_states"].items():
        pin = state["captures"][focal]["pin"]
        for ref, member in state["objects"].items():
            wire = control.value(member)
            if (
                ref in seen
                or not isinstance(wire, dict)
                or not isinstance(wire.get("context"), dict)
                or wire["context"].get("adapter") != ADAPTER
                or wire["context"].get("molecule_card_ref") != pin
                or "native_payload" not in wire
            ):
                continue
            seen.add(ref)
            access = (
                control.focal_access(case, focal)
                if isinstance(control, MultiFocalOriginal)
                else control.access(case)
            )
            access = _FrozenAccess(access)
            keys = retained_keys(control, case, ref, wire)
            crossings = retained_crossings(control, case, ref)
            result = restore_result(
                access, ref, wire, entry_keys=keys, native_crossings=crossings
            )
            assert result.wire is wire
            assert [entry.key for entry in result.entries] == keys
            yield ref, result, crossings


@pytest.mark.parametrize(
    "source,case",
    [("sdk205", case) for case in CASES]
    + [("sdk208", case) for case in SUPPLEMENT_CASES],
)
def test_retained_restoration_replays_original_members_and_frames_without_science(
    request, source, case, monkeypatch
):
    control = request.getfixturevalue(
        "original" if source == "sdk205" else "multifocal_original"
    )
    block_current(monkeypatch)
    import sabueso.core._molecule_activity_history_v1.adapter as adapter
    import sabueso.core.card_bioactivity_history_v2 as bioactivity
    import sabueso.core.card_molecule_activity_history_v1 as history

    for owner, names in (
        (history, ("expected_result", "materialize")),
        (adapter, ("materialize",)),
        (bioactivity, ("expected_result", "materialize")),
    ):
        for name in names:
            monkeypatch.setattr(owner, name, forbidden)
    results = {}
    for ref, result, crossings in restored_original_results(control, case):
        results[ref] = result
        for entry in result.entries:
            recorded = entry.value["native_member_occurrences"]
            if result.wire["context"]["grain"] == "record":
                recorded = recorded[:1]
            assert [
                {"result_ref": native.result_ref, "entry_key": member.key}
                for _, native, member in result.native_members(entry.key)
            ] == [
                {key: occurrence[key] for key in ("result_ref", "entry_key")}
                for occurrence in recorded
            ]
        for pin, crossing in crossings.items():
            native, location = result.native_crossing(pin)
            assert canonical_json(native) == canonical_json(
                crossing["wrapper"]["native_payload"]
            )
            assert location == crossing["location"]
            native["restored_copy_probe"] = True
            assert "restored_copy_probe" not in result.native_crossing(pin)[0]
        with pytest.raises(StorageError, match="not retained"):
            result.native_crossing("unsupplied-original-target")
    assert results
    for query in control.case(case)["machine"]:
        selection, options = query["selection"], query["query"]
        result = results[selection["scientific_result_ref"]]
        ref, entries, fields, _ = history.expected_selection(
            result, **{key: value for key, value in options.items() if key != "options"}
        )
        assert ref == selection["selection_ref"]
        assert [entry.key for entry in entries] == [
            entry["key"] for entry in selection["entries"]
        ]
        for page in control.value(query["pages_ref"]):
            assert page["page"]["total"] == len(entries)
            for index, frame in enumerate(page["items"], start=page["page"]["offset"]):
                actual = result.frame(
                    result._access, SimpleNamespace(_fields=fields), entries[index]
                )
                if not frame["value_included"]:
                    actual = adapter.defer_frame(actual)
                assert canonical_json(actual) == canonical_json(frame)


@pytest.mark.parametrize("mutation", ("focal", "inputs", "policies", "location"))
def test_restored_native_crossing_refuses_foreign_exact_scope(
    multifocal_original, monkeypatch, mutation
):
    block_current(monkeypatch)
    import sabueso.core.card_molecule_activity_history_v1 as history

    monkeypatch.setattr(history, "expected_result", forbidden)
    monkeypatch.setattr(history, "materialize", forbidden)
    case = "bts-to-same-id-snapshot"
    _, result, crossings = next(
        record
        for record in restored_original_results(multifocal_original, case)
        if record[2]
    )
    pin = next(iter(crossings))
    changed = deepcopy(crossings)
    if mutation == "focal":
        changed[pin]["wrapper"]["molecule_card_ref"] = next(
            item["molecule_pin"]
            for item in multifocal_original.case(case)["crossings"].values()
            if item["molecule_pin"] != result._access._focal.pin
        )
    elif mutation == "inputs":
        changed[pin]["inputs"].reverse()
    elif mutation == "policies":
        changed[pin]["policies"]["include_indirect"] = True
    else:
        changed[pin]["location"]["result_ref"] = "XR_foreign"
    restored = history.restore_result(
        result._access,
        result.result_ref,
        result.wire,
        entry_keys=[entry.key for entry in result.entries],
        native_crossings=changed,
    )
    with pytest.raises(StorageError, match="foreign capture or scope"):
        restored.native_crossing(pin)


@pytest.fixture(scope="module")
def original(tmp_path_factory, request):
    with DATA.open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == ENCODED_SHA
    path = tmp_path_factory.mktemp("sdk205-original") / "original.tar"
    digest, total = hashlib.sha256(), 0
    with gzip.open(DATA, "rb") as source, path.open("xb") as target:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
            total += len(chunk)
            assert total <= DECODED_BYTES
            target.write(chunk)
    assert total == DECODED_BYTES and digest.hexdigest() == DECODED_SHA
    control = Original(path)
    try:
        yield control
    finally:
        control.close()
        if request.config.getini("tmp_path_retention_policy") != "all":
            path.unlink()


@pytest.mark.parametrize("case", CASES)
def test_every_original_result_and_native_crossing_is_independent(
    original, case, monkeypatch
):
    block_current(monkeypatch)
    from sabueso.core._molecule_activity_history_v1.adapter import defer_frame
    from sabueso.core.card_molecule_activity_history_v1 import (
        expected_result,
        expected_selection,
    )

    access, expected, originals = original.access(case), {}, {}
    for ref, wire in original.wires(case):
        result = expected_result(access, wire["context"]["options"], original=wire)
        assert result.result_ref == ref
        assert canonical_json(result.wire) == canonical_json(wire)
        expected[ref], originals[ref] = result, wire
    assert expected
    for request in original.case(case)["machine"]:
        recorded, query = request["selection"], request["query"]
        result = expected[recorded["scientific_result_ref"]]
        ref, entries, fields, spec = expected_selection(
            result, **{key: value for key, value in query.items() if key != "options"}
        )
        assert ref == recorded["selection_ref"]
        assert list(fields) == recorded["request"]["fields"]
        assert [entry.key for entry in entries] == [
            entry["key"] for entry in recorded["entries"]
        ]
        for page in original.value(request["pages_ref"]):
            start = page["page"]["offset"]
            assert page["page"]["total"] == len(entries)
            assert page["result_ref"] == result.result_ref
            for index, frame in enumerate(page["items"], start=start):
                actual = result.frame(
                    result._access, SimpleNamespace(_fields=fields), entries[index]
                )
                if not frame["value_included"]:
                    actual = defer_frame(actual)
                assert canonical_json(actual) == canonical_json(frame)
        if spec is not None:
            assert spec["selected_count"] == len(entries)
    crossings = list(original.crossings(case))
    if case in (
        "bts",
        "benz",
        "full-molecule-deck",
        "duplicate-molecules",
        "multiple-aliases",
    ):
        assert crossings
    for context, native in crossings:
        ref = context["molecule_activity_navigation"]["source_result_ref"]
        result = expected[ref]
        value, location = result.native_crossing(context["target_card_ref"])
        assert canonical_json(value) == canonical_json(native)
        assert location["kind"] == "result"
        assert location["segments"][-1] == {"type": "Key", "value": "native_payload"}
    # Expected calculations never rewrite the sealed source inputs.
    after = original.access(case)
    assert canonical_json(
        {k: c.data for k, c in access._captures.items()}
    ) == canonical_json({k: c.data for k, c in after._captures.items()})


@pytest.mark.parametrize(
    "mutation",
    ("count", "membership", "quantity", "class", "support", "identity-support"),
)
def test_modified_scientific_and_support_fields_are_refused(
    original, mutation, monkeypatch
):
    block_current(monkeypatch)
    from sabueso.core.card_molecule_activity_history_v1 import verify_result

    case = "unmatched-alias-opaque" if mutation == "identity-support" else "bts"
    access = original.access(case)
    ref, wire = next(
        (r, w) for r, w in original.wires(case) if w["context"]["grain"] == "target"
    )
    row_key = next(iter(wire["rows"]))
    row = wire["rows"][row_key]
    if mutation == "count":
        row["record_count"] += 1
    elif mutation == "membership":
        row["interpretation"]["identity_membership"][
            "included_relationship_ids"
        ].append("REL_synthetic_foreign")
    elif mutation == "quantity":
        row["measurement"]["unit"] = "percent"
    elif mutation == "class":
        row["class"] = "active"
    elif mutation == "support":
        wire["support"][row_key]["source_assertions"] = []
    else:
        edge = wire["native_payload"]["identity"]["focal_edges"]
        synthetic = next(e for e in edge if e["record_ref"] == "chembl:CHEMBL999999999")
        synthetic["source_assertions"][0]["state"] = "not_retained"
    with pytest.raises(StorageError, match="differs"):
        verify_result(access, ref, wire)


def test_opaque_source_metadata_and_scalar_types_stay_literal(original, monkeypatch):
    block_current(monkeypatch)
    from sabueso.core.card_molecule_activity_history_v1 import expected_result

    access = original.access("unmatched-alias-opaque")
    sources = access._captures[access._focal_key].data["source_assertion_store"]
    statement = next(
        s
        for s in sources
        if isinstance(s.get("asserted_value"), dict)
        and "opaque_source_metadata" in s["asserted_value"]
    )
    value = statement["asserted_value"]
    before = canonical_json(value)
    assert [type(v) for v in value["synthetic_control"]] == [
        bool,
        int,
        float,
        type(None),
    ]
    assert value["opaque_source_metadata"] == {
        "adapter": "source-owned@9",
        "context": False,
        "format": "source-owned@999",
        "rule": "source-owned@7",
        "version": 0,
    }
    _, wire = next(original.wires("unmatched-alias-opaque"))
    expected_result(access, wire["context"]["options"], original=wire)
    assert canonical_json(value) == before
