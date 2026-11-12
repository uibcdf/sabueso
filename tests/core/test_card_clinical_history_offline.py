"""Immutable SDK224 native clinical/source/selection expectations, without Cards."""

import gzip
import hashlib
import importlib
import json
import shutil
import socket
import subprocess
import sys
import tarfile
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from sabueso.core.card_clinical_history_v1 import (
    expected_result,
    restore_result,
    verify_result,
)
from sabueso.core.errors import StorageError
from sabueso.core.snapshot import canonical_json

DATA = Path(__file__).with_name("data") / "clinical_live_sdk224.tar.gz"
ENCODED_SHA = "2f355f0705081bce2090e2be5265a845535793bdfcf74a184f79c9c6c38b7b50"
DECODED_SHA = "9b371e5aea112ef85adc154c945e40f4efa03bfdc459e1460be6daa94b327b39"
MANIFEST_SHA = "1c8c02d13262b95fe013b021fd77987b81e33bae110b7d751b6ed1809fe4de5b"
CASES = (
    "bare",
    "failed",
    "indications",
    "limited",
    "misbound-registry",
    "trials",
    "unknown-ledger",
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class Original:
    def __init__(self, raw):
        self.archive, self.cache = tarfile.open(raw, "r:"), OrderedDict()
        self.manifest = self.member("manifest.json")
        assert (
            self.manifest["capture_complete"] and self.manifest["genuine_live_original"]
        )
        assert (
            self.manifest["producer_head"] == "66989a407564e74758b6d0eb946ec07774ddbee3"
        )
        assert self.manifest["producer_version"] == "0.14.0+224.g66989a4"
        assert self.manifest["attempts"] == {"network": 0, "source_acquisitions": 0}
        members, expected = self.archive.getmembers(), self.manifest["files"]
        assert len(members) == len(expected) + 1 == 6394
        assert {m.name for m in members} == {*expected, "manifest.json"}
        for member in members:
            assert member.isfile() and not Path(member.name).is_absolute()
            assert ".." not in Path(member.name).parts
            with self.archive.extractfile(member) as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if member.name == "manifest.json":
                assert digest == MANIFEST_SHA
            else:
                assert digest == expected[member.name]["sha256"]
                assert member.size == expected[member.name]["bytes"]

    def member(self, name):
        if name in self.cache:
            self.cache.move_to_end(name)
        else:
            with self.archive.extractfile(name) as stream:
                self.cache[name] = json.load(stream)
            if len(self.cache) > 16:
                self.cache.popitem(last=False)
        return self.cache[name]

    def value(self, ref):
        return deepcopy(self.member(ref["path"]))

    def case(self, name):
        return self.member(self.manifest["cases"][name]["path"])

    def access(self, name):
        state = self.case(name)["access"]
        captures = {
            key: SimpleNamespace(
                pin=row["pin"],
                snapshot=row["snapshot"],
                data=self.value(row["data_ref"]),
            )
            for key, row in state["captures"].items()
        }
        return SimpleNamespace(
            _captures=captures, _inputs=state["inputs"], _focal_key=state["focal"]
        )

    def result(self, name):
        case = self.case(name)
        node = next(
            v for v in case["views"] if v["node"] == case["named_views"]["root"]
        )
        ref = node["observation"]["result_ref"]
        return ref, self.value(case["access"]["objects"][ref])

    def close(self):
        self.cache.clear()
        self.archive.close()

    def hydrate(self, name):
        """Restore captured input containers; execute no code from the archive."""
        from sabueso.core.card_access import AccessSelection, _Entry
        from sabueso.core.card_exploration import CardView
        from sabueso.core.card_exploration_storage import _access, _explorer
        from sabueso.core.card_navigation_preview_v1 import metadata

        case, inputs = self.case(name), self.access(name)
        stored = case["access"]
        objects = {key: self.value(ref) for key, ref in stored["objects"].items()}
        access = _access(
            inputs._captures,
            inputs._inputs,
            objects,
            deepcopy(stored["locations"]),
            inputs._focal_key,
        )
        access._mode, access._nonce = "live", stored["nonce"]
        access._metadata_refs = set(stored["metadata_refs"])
        result_ref, wire = self.result(name)
        result = restore_result(result_ref, wire)
        for item_ref, row in stored["scientific_items"].items():
            assert row["result_ref"] == result_ref
            access._scientific_items[item_ref] = (result, row["entry_key"])
        session = {
            "views": {},
            "explanations": {},
            "links": {},
            "presentation_metadata": metadata(),
        }
        records = {row["node"]: row for row in case["views"]}
        nodes = {}

        def selection_from(spec):
            return AccessSelection(
                access,
                spec["result_ref"],
                spec["selection_ref"],
                tuple(
                    _Entry(
                        e["location"],
                        e["key"],
                        self.value(e["value_ref"]),
                        e["ordinal"],
                    )
                    for e in spec["entries"]
                ),
                spec["context_location"],
                spec["request"]["target"],
                spec["request"]["operation"],
                spec["slice"],
                result if spec["scientific_result_ref"] else None,
                tuple(spec["request"]["fields"]),
                spec["outcome_override"],
            )

        for ref, spec in stored["selections"].items():
            access._selections[ref] = selection_from(spec)

        def node(key):
            if key is None:
                return None
            if key in nodes:
                return nodes[key]
            row = records[key]
            observer = row["observation"]
            explorer = _explorer(access, session)
            explorer._origin = node(row["explorer_origin_node"])
            spec = observer["selection"]
            entries = tuple(
                _Entry(
                    entry["location"],
                    entry["key"],
                    self.value(entry["value_ref"]),
                    entry["ordinal"],
                )
                for entry in spec["entries"]
            )
            selection = AccessSelection(
                access,
                spec["result_ref"],
                spec["selection_ref"],
                entries,
                spec["context_location"],
                spec["request"]["target"],
                spec["request"]["operation"],
                spec["slice"],
                result if spec["scientific_result_ref"] else None,
                tuple(spec["request"]["fields"]),
                spec["outcome_override"],
            )
            selected = {item["item_ref"] for item in observer["items"]}
            from sabueso.core.card_access import _handle

            subset = tuple(
                entry
                for entry in entries
                if _handle(
                    "XI_",
                    {"result_ref": selection.result_ref, "location": entry.location},
                )
                in selected
            )
            # Display order is an observation, not the underlying entry order.
            by_ref = {
                _handle(
                    "XI_",
                    {"result_ref": selection.result_ref, "location": entry.location},
                ): entry
                for entry in subset
            }
            subset = tuple(by_ref[item["item_ref"]] for item in observer["items"])
            view = CardView(
                explorer,
                selection,
                subset,
                _origin=node(row["origin_node"]),
                _native_override=self.value(observer["native_payload_ref"]),
                **row["flags"],
            )
            nodes[key] = view
            return view

        for key in records:
            node(key)
        return nodes, records

    def binding_record(self, observed):
        """Translate the original observation envelope into storage state fields."""
        items = {}
        for row in observed["items"]:
            cells = {}
            for key, cell in row["cells"].items():
                cells[key] = {
                    field: deepcopy(value)
                    for field, value in cell.items()
                    if field != "support_ref"
                }
                cells[key]["support"] = self.value(cell["support_ref"])
            items[row["item_ref"]] = {
                "label": row["label"],
                "kind": row["kind"],
                "support": self.value(row["support_ref"]),
                "cells": cells,
            }
        return {
            "state": {
                "items": items,
                "context": observed["context"],
                "schema": observed["schema"],
                "coverage": observed.get("coverage", {}),
            },
            "native_payload": self.value(observed["native_payload_ref"]),
        }


def forbidden(*args, **kwargs):
    raise AssertionError(
        "Independent clinical predicates cannot invoke mutable Cards, science, UI or sources"
    )


def block_current(monkeypatch):
    from sabueso.core.card import Card

    # Import before installing guards so mutable aliases cannot be hidden later.
    targets = {
        "clinical": ("clinical_view",),
        "knowledge_state": ("knowledge_state",),
        "card_clinical_access": ("materialize", "options_for_clinical"),
        "card_clinical_selection_v1": (
            "normalize",
            "evaluate",
            "projection",
            "sorted_entries",
            "validate_equality",
        ),
        "card_clinical_exploration": (
            "view",
            "open_item",
            "explain",
            "links",
            "follow",
            "display_filter",
            "display_sort",
        ),
    }
    modules = {
        name: importlib.import_module("sabueso.core." + name) for name in targets
    }
    for name, methods in targets.items():
        module = modules[name]
        for method in methods:
            monkeypatch.setattr(module, method, forbidden)
    for method in ("__init__", "from_dict", "clinical", "knowledge_state"):
        monkeypatch.setattr(Card, method, forbidden)
    for name, suffix in (
        ("chembl", "ChEMBL"),
        ("clinicaltrials", "ClinicalTrials"),
        ("pdb_ccd", "CCD"),
        ("unichem", "UniChem"),
    ):
        module = importlib.import_module("sabueso.tools.db." + name)
        for prefix in ("Fixture", "Online"):
            monkeypatch.setattr(
                getattr(module, prefix + suffix + "Client"), "__init__", forbidden
            )
    module = importlib.import_module("sabueso._private.argdigest.argument.item_ref")
    monkeypatch.setattr(module, "digest_item_ref", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)


@pytest.fixture(scope="module")
def original(tmp_path_factory, request):
    assert sha(DATA) == ENCODED_SHA
    directory = tmp_path_factory.mktemp("clinical-sdk224")
    raw = directory / "original.tar"
    with gzip.open(DATA, "rb") as source, raw.open("xb") as destination:
        shutil.copyfileobj(source, destination, length=1024 * 1024)
    assert raw.stat().st_size == 117739520 and sha(raw) == DECODED_SHA
    result = Original(raw)
    try:
        yield result
    finally:
        result.close()
        if request.config.getini("tmp_path_retention_policy") != "all":
            raw.unlink()


@pytest.mark.parametrize("name", CASES)
def test_original_clinical_result_is_independently_bound_to_captured_inputs(
    original, monkeypatch, name
):
    ref, wire = original.result(name)
    access = original.access(name)
    before = deepcopy(wire)
    block_current(monkeypatch)
    expected = expected_result(access, original=wire)
    assert expected.result_ref == ref
    assert canonical_json(expected.wire) == canonical_json(wire)
    verify_result(access, ref, wire)
    retained = restore_result(ref, wire)
    assert retained.wire is wire
    assert [e.key for e in retained.entries] == [e.key for e in expected.entries]
    assert wire == before


@pytest.mark.parametrize("name", CASES)
def test_every_original_machine_request_keeps_exact_typed_membership(
    original, monkeypatch, name
):
    from sabueso.core._clinical_history_v1.selection import (
        active,
        evaluate,
        normalize,
        projection,
        selection_ref,
    )
    from sabueso.core.card_access import _handle

    ref, wire = original.result(name)
    result = restore_result(ref, wire)
    block_current(monkeypatch)
    for query in original.case(name)["queries"]:
        request = query["request"]
        fields = projection(request.get("fields"))
        normalized = normalize(
            request.get("where"), request.get("item_refs"), request.get("order_by")
        )
        entries, spec = (
            evaluate(result, normalized)
            if active(normalized)
            else (result.entries, None)
        )
        selected_ref = (
            selection_ref(result, fields, spec)
            if spec is not None
            else _handle(
                "XA_",
                {
                    "format": "scientific_access_selection@1",
                    "result_ref": ref,
                    "fields": fields,
                },
            )
        )
        assert selected_ref == query["selection_ref"]
        assert len(entries) == query["count"]
        recorded = [
            row for page in query["pages"] for row in original.value(page)["items"]
        ]
        assert [row["item_ref"] for row in recorded] == [
            _handle("XI_", {"result_ref": ref, "location": e.location}) for e in entries
        ]


@pytest.mark.parametrize(
    "change",
    [
        "phase_type",
        "native_phase",
        "row_order",
        "support_role",
        "citation_id",
        "registry_state",
        "query_scope",
        "rule_scope",
    ],
)
def test_altered_clinical_wire_is_refused_independently_of_outer_hashes(
    original, monkeypatch, change
):
    ref, wire = original.result("trials")
    if change == "phase_type":
        wire["rows"]["indication:0"]["chembl_max_phase"] = 4
    elif change == "native_phase":
        wire["native_payload"]["max_phase"] = 0.0
    elif change == "row_order":
        wire["native_payload"]["indications"].reverse()
    elif change == "support_role":
        wire["support"]["registry:0"]["source_assertions"][-1]["role"] = (
            "indication_citation"
        )
    elif change == "citation_id":
        wire["rows"]["citation:0:0"]["item"]["nct_id"] = "NCT00000000"
    elif change == "registry_state":
        wire["rows"]["registry:0"]["registry_state"] = "not_found"
    elif change == "query_scope":
        wire["coverage"]["rows"][0]["state"] = "not_stated"
    else:
        wire["coverage"]["rule"]["inputs"] = []
    block_current(monkeypatch)
    with pytest.raises(StorageError):
        verify_result(original.access("trials"), ref, wire)


@pytest.mark.parametrize("name", CASES)
def test_original_human_clinical_source_and_back_graph_has_independent_predicates(
    original, monkeypatch, name
):
    from sabueso.core.card_exploration_clinical import (
        is_context,
        is_links,
        is_view,
        verify_view,
    )

    nodes, records = original.hydrate(name)
    block_current(monkeypatch)
    checked = 0
    for key, view in nodes.items():
        if not (is_view(view) or is_context(view) or is_links(view)):
            continue
        observed = records[key]["observation"]
        record = original.binding_record(observed)
        # The capture recorded context/schema/items but not a separate coverage
        # envelope. The complete original coverage lives in its retained wire.
        record["state"]["coverage"] = view.coverage
        if is_view(view):
            # Storage binds every underlying member, including display-excluded
            # members; the observation's items contain only the displayed subset.
            from sabueso.core.card_exploration_clinical import _state

            full_items = _state(view)["items"]
            for ref, observed_item in record["state"]["items"].items():
                assert canonical_json(observed_item) == canonical_json(full_items[ref])
            record["state"]["items"] = full_items
        verify_view(view, record)
        checked += 1
    assert checked > 0


@pytest.mark.parametrize("name", CASES)
def test_actual_original_clinical_file_round_trip_pilot(
    original, monkeypatch, tmp_path, name
):
    import sabueso

    nodes, _ = original.hydrate(name)
    root = nodes[original.case(name)["named_views"]["root"]]
    expected = deepcopy(root.native_payload)
    block_current(monkeypatch)
    path = tmp_path / "clinical-original.json"
    root.save(
        path, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
    )
    saved = sabueso.read_exploration(
        path, max_encoded_bytes=None, max_decoded_bytes=None, max_logical_bytes=None
    )
    assert saved.native_payload == expected
    assert saved.validation["verifier"] == "clinical_exploration_binding@1"
    assert saved.context["mode"] == "saved"
    assert saved.explorer.view("clinical").native_payload == expected
    assert_saved_original(saved, original, name)
    command = [
        sys.executable,
        "-B",
        "-c",
        "import sys; sys.path.insert(0, sys.argv[4]); "
        "from test_card_clinical_history_offline import independent_receive; "
        "independent_receive(*sys.argv[1:4])",
        str(path),
        str(original.archive.name),
        name,
        str(Path(__file__).resolve().parent),
    ]
    received = subprocess.run(
        command, cwd=tmp_path, capture_output=True, text=True, timeout=300
    )
    assert received.returncode == 0, received.stdout + received.stderr
    assert not received.stderr


def assert_saved_original(saved, original, name):
    """Compare retained original graph and all observed agent request pages."""
    from collections import Counter

    case = original.case(name)
    retained = list(saved.explorer._session["original_nodes"].values())

    def frame_locations(items, lookup):
        result = deepcopy(items)
        for row in result:
            # Only declared transport locators are session aliases. Source JSON
            # and all scientific values remain byte/typed-exact.
            for node in (row, *row.get("cells", {}).values()):
                for field in (
                    "location",
                    "payload_location",
                    "value_location",
                    "interpretation_location",
                    "support_location",
                    "context_location",
                ):
                    location = node.get(field)
                    if isinstance(location, dict) and location.get("kind") == "lookup":
                        node[field] = lookup(location)
        return result

    def signature(view):
        return (
            view.view_ref,
            view._origin.view_ref if view._origin else None,
            view._explorer._origin.view_ref if view._explorer._origin else None,
            canonical_json(view.request),
        )

    expected = Counter(
        (
            r["observation"]["view_ref"],
            r["observation"]["origin_view_ref"],
            next(
                (
                    n["observation"]["view_ref"]
                    for n in case["views"]
                    if n["node"] == r["explorer_origin_node"]
                ),
                None,
            ),
            canonical_json(r["observation"]["request"]),
        )
        for r in case["views"]
    )
    assert not (expected - Counter(signature(v) for v in retained))
    for query in case["queries"]:
        selection = saved.explorer.access.select(
            "clinical", **query["request"], skip_digestion=True
        )
        assert selection.selection_ref == query["selection_ref"]
        assert selection.count == query["count"]
        cursor = None
        for ref in query["pages"]:
            recorded = original.value(ref)
            page = selection.page(
                limit=recorded["page"]["limit"],
                max_bytes=recorded["page"]["max_bytes"],
                cursor=cursor,
                skip_digestion=True,
            )
            assert canonical_json(
                frame_locations(
                    page["items"], lambda loc: saved.explorer.access._resolve(loc)[1]
                )
            ) == canonical_json(
                frame_locations(
                    recorded["items"],
                    lambda loc: case["access"]["locations"][loc["location_ref"]],
                )
            )
            assert page["page"]["offset"] == recorded["page"]["offset"]
            assert page["page"]["total"] == recorded["page"]["total"]
            cursor = page["page"]["next_cursor"]
        assert cursor is None


def independent_receive(path, raw, name):
    """Fresh receiving outside checkout; only original data and frozen rules."""
    import sabueso

    assert sha(Path(raw)) == DECODED_SHA
    original = Original(raw)
    try:
        with pytest.MonkeyPatch.context() as guard:
            block_current(guard)
            saved = sabueso.read_exploration(
                path,
                max_encoded_bytes=None,
                max_decoded_bytes=None,
                max_logical_bytes=None,
            )
            assert_saved_original(saved, original, name)
            root = saved.explorer.view("clinical")
            question = saved.explorer.answer("clinical_context", skip_digestion=True)
            assert root.native_payload == question.native_payload
            for item in question.items():
                for detail in (item.open(), item.explain(), item.related()):
                    assert detail.back() is question
                    assert detail.request == question.request
                for link in item.related().items():
                    followed = link.open()
                    assert followed.back() is link._view
                    assert followed.request == question.request
            assert saved.validation["verifier"] == "clinical_exploration_binding@1"
    finally:
        original.close()
