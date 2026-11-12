"""Complete SDK202 originals and independent saved literature receiving."""

import gzip
import hashlib
import importlib
import importlib.util
import inspect
import json
import socket
import subprocess
import sys
import tarfile
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_exploration_storage import _restore, _seal
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.snapshot import canonical_json

DATA = Path(__file__).with_name("data") / "literature_live_sdk202.tar.gz"
ENCODED_SHA = "34a157d630df43245e55039968025f2eb847c6d05e5719d2116b5a40d57edfb1"
DECODED_SHA = "baa1857bfe9411a815af8c4f2694b42da68727d623cb26cacdf2a29584a9675e"
MANIFEST_SHA = "da63a041dc872bc5b3c2532faae409c7e3cfdb605df32b18d00b32b61a967ef5"
DECODED_BYTES = 66058240
TOPIC = "literature"
BENZ_PAPER, BTS_PAPER = "pubmed:20889239", "pubmed:35189560"
LOCATED_PAPER, MISSING_PAPER = "pubmed:40832834", "pubmed:999999999"
CASES = (
    "bare",
    "disease",
    "empty",
    "failed",
    "located",
    "mixed",
    "molecule",
    "search",
    "tctim",
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Original:
    """Read exact members and detach requested roots without expanding refs."""

    def __init__(self, path):
        self.archive, self.cache = tarfile.open(path, "r:"), OrderedDict()
        self.manifest = self.member("manifest.json")
        assert self.manifest["capture_complete"]
        assert (
            self.manifest["producer_head"] == "1145ea364a558b6f03d3823dfd1be4a6839663e5"
        )
        assert self.manifest["producer_version"] == "0.14.0+202.g1145ea3"
        members, expected = self.archive.getmembers(), self.manifest["files"]
        assert {m.name for m in members} == {*expected, "manifest.json"}
        assert len(members) == len(expected) + 1 == 3819
        assert sum(row["bytes"] for row in expected.values()) == 62493260
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
            if len(self.cache) > 24:
                self.cache.popitem(last=False)
        return self.cache[name]

    def value(self, ref):
        return deepcopy(self.member(ref["path"]))

    def case(self, name):
        return self.member(self.manifest["cases"][name]["path"])

    def card(self, name):
        state = self.case(name)["access_state"]
        return self.value(state["captures"][state["focal"]]["data_ref"])

    def access(self, name):
        state = self.case(name)["access_state"]
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

    def wires(self, name):
        for ref, record in self.case(name)["access_state"]["objects"].items():
            value = self.member(record["path"])
            if (
                isinstance(value, dict)
                and isinstance(value.get("context"), dict)
                and value["context"].get("adapter") == "literature_exploration@1"
                and "native_payload" in value
            ):
                yield ref, deepcopy(value)

    def native(self, name, human="overview"):
        return self.value(self.case(name)["human"][human]["native_payload_ref"])

    def close(self):
        self.cache.clear()
        self.archive.close()


def forbidden(*args, **kwargs):
    raise AssertionError(
        "Original saved reading cannot use mutable Cards, science or sources"
    )


def block_current(monkeypatch):
    """Preimport targets before temporary guards can poison imported aliases."""
    targets = {
        "literature": ("literature_view",),
        "literature_explanation": ("explain_literature", "literature_basis"),
        "knowledge_state": ("knowledge_state",),
        "card_literature_access": ("materialize", "options_for_literature"),
        "card_literature_selection_v1": (
            "projection",
            "normalize",
            "evaluate",
            "sorted_entries",
            "validate_equality",
        ),
        "card_literature_exploration": (
            "materialize",
            "view",
            "open_item",
            "explain",
            "links",
            "follow",
            "support",
            "display_filter",
            "display_sort",
        ),
        "relationship_store": ("make_derivation",),
    }
    modules = {
        name: importlib.import_module("sabueso.core." + name) for name in targets
    }
    clients = []
    for module, suffix in (
        ("uniprot", "UniProt"),
        ("rcsb", "RCSB"),
        ("chembl", "ChEMBL"),
        ("europepmc", "EuropePMC"),
        ("mondo", "MONDO"),
    ):
        loaded = importlib.import_module("sabueso.tools.db." + module)
        clients.extend(
            getattr(loaded, prefix + suffix + "Client")
            for prefix in ("Fixture", "Online")
        )
    for name in (
        "__init__",
        "from_dict",
        "literature",
        "explain_literature",
        "knowledge_state",
        "explain",
    ):
        monkeypatch.setattr(Card, name, forbidden)
    for name, exports in targets.items():
        for export in exports:
            monkeypatch.setattr(modules[name], export, forbidden)
    for client in clients:
        monkeypatch.setattr(client, "__init__", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def original(tmp_path_factory, request):
    with DATA.open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == ENCODED_SHA
    path = tmp_path_factory.mktemp("sdk202-original") / "original.tar"
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


def publication(view, ref):
    return next(
        item for item in view.items() if item.cells["publication_ref"].value == ref
    )


def frames(selection):
    cursor, rows = None, []
    while True:
        page = selection.page(cursor=cursor)
        assert page["page"]["blocked"] is None
        rows.extend(page["items"])
        cursor = page["page"]["next_cursor"]
        if cursor is None:
            return rows


def semantic_locations(access, value):
    if isinstance(value, dict):
        if (
            set(value) == {"format", "kind", "location_ref"}
            and value["format"] == "card_access_location@1"
            and value["kind"] == "lookup"
        ):
            return access._resolve(value)[1]
        return {key: semantic_locations(access, item) for key, item in value.items()}
    if isinstance(value, list):
        return [semantic_locations(access, item) for item in value]
    return value


def compare_original_native(actual, expected):
    """Only a declared generated explanation producer may name a newer SDK."""
    expected = deepcopy(expected)
    if "rule" in expected:
        assert (
            actual["rule"]["rule"]
            == expected["rule"]["rule"]
            == "literature_explanation@1"
        )
        expected["rule"]["sabueso_version"] = actual["rule"]["sabueso_version"]
    assert canonical_json(actual) == canonical_json(expected)


def test_archive_keeps_every_original_member_and_pre_reader_boundary(original):
    assert set(original.manifest["cases"]) == set(CASES)
    assert original.manifest["admitted_saved_format"] is False
    assert original.manifest["attempts"] == {"network": 0, "source_acquisitions": 0}
    assert sum(len(list(original.wires(name))) for name in CASES) == 13
    assert sum(len(original.case(name)["machine"]) for name in CASES) == 65
    assert len(original.native("tctim", BENZ_PAPER)["links"]) == 459
    assert len(original.native("tctim", BTS_PAPER)["links"]) == 9
    assert original.native("bare", MISSING_PAPER)["status"] == "not_on_card"


@pytest.mark.parametrize("case", CASES)
def test_frozen_predicates_match_complete_sdk202_wires_without_current_engines(
    original, monkeypatch, case
):
    from sabueso.core.card_literature_history_v1 import expected_result, restore_result

    access = original.access(case)
    block_current(monkeypatch)
    for ref, wire in original.wires(case):
        expected = expected_result(access, wire["context"]["options"], original=wire)
        assert canonical_json(expected.wire) == canonical_json(wire)
        assert expected.result_ref == ref
        retained = restore_result(ref, wire)
        assert retained.wire is wire
        assert [entry.key for entry in retained.entries] == [
            entry.key for entry in expected.entries
        ]


def replay_original_queries(original, case, explorer):
    """Replay every original request, preserving exact publication membership."""
    executed = []
    captured_case = original.case(case)
    for captured in captured_case["machine"]:
        query = deepcopy(captured["query"])
        if query.get("item_refs"):
            keys = captured_case["access_state"]["scientific_items"]
            current = {
                row["support"]["ref"]: row["item_ref"]
                for row in frames(
                    explorer.access.select(TOPIC, options=query.get("options"))
                )
            }
            query["item_refs"] = [
                current[keys[ref]["entry_key"]] for ref in query["item_refs"]
            ]
        selected = explorer.access.select(TOPIC, **query)
        original_pages = original.value(captured["pages_ref"])
        pages, cursor = [], None
        for retained_page in original_pages:
            page = selected.page(
                limit=retained_page["page"]["limit"],
                max_bytes=retained_page["page"]["max_bytes"],
                cursor=cursor,
            )
            assert canonical_json(page["outcome"]) == canonical_json(
                retained_page["outcome"]
            )
            for name in (
                "blocked",
                "complete",
                "offset",
                "returned",
                "total",
                "values_complete",
            ):
                assert canonical_json(page["page"][name]) == canonical_json(
                    retained_page["page"][name]
                )
            pages.append(page)
            cursor = page["page"]["next_cursor"]
        assert cursor is None
        items = [item for page in pages for item in page["items"]]
        assert [row["support"]["ref"] for row in items] == [
            entry["key"] for entry in captured["selection"]["entries"]
        ]
        original_items = [item for page in original_pages for item in page["items"]]
        for actual, retained in zip(items, original_items, strict=True):
            assert set(actual["cells"]) == set(retained["cells"])
            for column, cell in actual["cells"].items():
                names = ("value", "state", "reason", "value_included")
                actual_cell = {name: cell[name] for name in names if name in cell}
                original_cell = {
                    name: retained["cells"][column][name]
                    for name in names
                    if name in retained["cells"][column]
                }
                assert canonical_json(actual_cell) == canonical_json(original_cell)
        executed.append(
            {
                "query": query,
                "selection_ref": selected.selection_ref,
                "result_ref": selected.result_ref,
                "items": semantic_locations(explorer.access, items),
                "outcome": selected.page()["outcome"],
            }
        )
    return executed


def produce(
    original,
    case,
    path,
    options=None,
    queries=(),
    *,
    question=False,
    visit=(),
    original_queries=False,
):
    card = Card.from_dict(original.card(case))
    before = card.to_dict()
    explorer = card.explore()
    view = explorer.view(TOPIC, options=options)
    if question:
        assert (
            explorer.answer("publications", options=options).native_payload
            == view.native_payload
        )
    executed = (
        replay_original_queries(original, case, explorer) if original_queries else []
    )
    for query in queries:
        selected = explorer.access.select(TOPIC, **query)
        executed.append(
            {
                "query": deepcopy(query),
                "selection_ref": selected.selection_ref,
                "result_ref": selected.result_ref,
                "items": semantic_locations(explorer.access, frames(selected)),
                "outcome": selected.page()["outcome"],
            }
        )
    if view.items():
        items = [view.items()[0], *(publication(view, ref) for ref in visit)]
        for item in items:
            item.open()
            item.explain()
            links = item.related()
            for link in links.items():
                link.open()
    native, request = deepcopy(view.native_payload), deepcopy(view.request)
    receipt = view.save(path)
    assert card.to_dict() == before
    return {
        "path": path,
        "receipt": receipt,
        "native": native,
        "request": request,
        "queries": executed,
        "options": options,
    }


def assert_retained_queries(explorer, records):
    for record in records:
        selected = explorer.access.select(TOPIC, **record["query"])
        assert selected.result_ref == record["result_ref"]
        assert selected.selection_ref == record["selection_ref"]
        assert canonical_json(
            semantic_locations(explorer.access, frames(selected))
        ) == canonical_json(record["items"])
        assert canonical_json(selected.page()["outcome"]) == canonical_json(
            record["outcome"]
        )


@pytest.fixture(scope="module")
def focused_saved(original, tmp_path_factory):
    options = {"publication_ref": BTS_PAPER}
    queries = [
        {
            "options": options,
            "fields": ["publication_ref", "year", "measurement_count"],
            "where": {"measurement_count": 9},
            "order_by": {"column": "year"},
        },
        {"options": options, "fields": [], "where": {"title": None}},
        {"options": options},
    ]
    return produce(
        original,
        "tctim",
        tmp_path_factory.mktemp("saved-literature") / "focused.json",
        options,
        queries,
        question=True,
    )


@pytest.fixture(scope="module")
def whole_saved(original, tmp_path_factory):
    """Reuse one TcTIM save for source scope and full publication context.

    The graph exceeds the default 64 MiB transport envelope. This workload
    declares 128 MiB for transport and keeps the 256 MiB logical default.
    """
    budgets = {"max_encoded_bytes": 128 * 1024**2, "max_decoded_bytes": 128 * 1024**2}
    card = Card.from_dict(original.card("tctim"))
    before = card.to_dict()
    explorer = card.explore()
    root = explorer.view(TOPIC)
    queries = replay_original_queries(original, "tctim", explorer)
    detail = publication(root, BENZ_PAPER).open()
    assert len(detail.native_payload["links"]) == 459
    detail.items()[0].explain()
    links = detail.items()[0].related()
    for role in ("source", "original_relationship"):
        next(item for item in links.items() if item.cells["role"].value == role).open()
    options = {"publication_ref": BTS_PAPER}
    focus = explorer.view(TOPIC, options=options)
    assert len(focus.native_payload["links"]) == 9
    root_native = deepcopy(root.native_payload)
    compare_original_native(root_native, original.native("tctim"))
    path = tmp_path_factory.mktemp("whole-publication") / "whole-publication.json"
    receipt = root.save(path, **budgets)
    assert card.to_dict() == before
    return {
        "path": path,
        "receipt": receipt,
        "native": deepcopy(focus.native_payload),
        "root_native": root_native,
        "request": deepcopy(focus.request),
        "queries": queries,
        "options": options,
        "budgets": budgets,
    }


@pytest.mark.parametrize("case", CASES)
def test_saved_original_card_scopes_keep_native_and_source_uncertainty(
    original, case, tmp_path, monkeypatch, request
):
    focus = {"tctim": BTS_PAPER, "located": LOCATED_PAPER, "bare": MISSING_PAPER}.get(
        case
    )
    options = {"publication_ref": focus}
    record = (
        request.getfixturevalue("whole_saved")
        if case == "tctim"
        else produce(
            original, case, tmp_path / "case.json", options, original_queries=True
        )
    )
    assert len(record["queries"]) == len(original.case(case)["machine"])
    expected = original.native(case, focus or "overview")
    compare_original_native(record["native"], expected)
    block_current(monkeypatch)
    saved = sabueso.read_exploration(
        record["path"],
        expected_digest=record["receipt"]["bundle_digest"],
        **record.get("budgets", {}),
    )
    if case == "tctim":
        saved = saved.explorer.view(TOPIC, options=options)
    assert saved.native_payload == record["native"]
    assert saved.context["options"] == options
    assert saved.request == record["request"]
    assert_retained_queries(saved.explorer, record["queries"])
    if case == "bare":
        assert saved.outcome["status"] == "empty" and not saved.items()
        assert saved.native_payload["status"] == "not_on_card"
    if case in ("disease", "molecule"):
        assert not saved.items() and saved.native_payload["publications"] == []
    coverage = saved.coverage
    original_wire = next(
        wire
        for _, wire in original.wires(case)
        if wire["context"]["options"] == options
    )
    assert coverage["rows"] == original_wire["coverage"]["rows"]
    assert (
        coverage["quality_source_original"]
        == original_wire["coverage"]["quality_source_original"]
    )


def test_saved_exact_machine_requests_and_projection_are_original(
    focused_saved, monkeypatch
):
    block_current(monkeypatch)
    saved = sabueso.read_exploration(focused_saved["path"])
    assert saved.native_payload == focused_saved["native"]
    assert saved.capabilities["save"] is True
    for record in focused_saved["queries"]:
        selected = saved.explorer.access.select(TOPIC, **record["query"])
        assert selected.result_ref == record["result_ref"]
        assert selected.selection_ref == record["selection_ref"]
        assert (
            semantic_locations(saved.explorer.access, frames(selected))
            == record["items"]
        )
        assert selected.page()["outcome"] == record["outcome"]


def test_saved_related_original_sources_locators_and_return_paths(
    focused_saved, monkeypatch
):
    block_current(monkeypatch)
    saved = sabueso.read_exploration(focused_saved["path"])
    item = saved.items()[0]
    assert item.open().native_payload == saved.native_payload
    assert item.explain().native_payload == saved.native_payload
    links = item.related()
    roles = {link.cells["role"].value for link in links.items()}
    assert {
        "source",
        "original_relationship",
        "publication_summary",
        "publication_explanation",
    } <= roles
    for link in links.items():
        opened = link.open()
        assert opened.back() is links
        assert opened.request == saved.request
        if link.cells["role"].value == "original_relationship":
            assert opened.native_payload["predicate"] == "has_bioactivity"
        elif link.cells["role"].value == "source":
            assert opened.native_payload["id"] == link.cells["target_ref"].value
    assert item.open().back() is saved


@pytest.mark.parametrize("compression", ["none", "gzip", "zstd"])
def test_transport_and_resave_keep_complete_original_science(
    focused_saved, monkeypatch, tmp_path, compression
):
    block_current(monkeypatch)
    saved = sabueso.read_exploration(focused_saved["path"])
    path = tmp_path / "resaved"
    receipt = saved.save(path, compression=compression)
    again = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert again.native_payload == saved.native_payload
    assert semantic_locations(
        again.explorer.access, again.rows()
    ) == semantic_locations(saved.explorer.access, saved.rows())
    assert again.request == saved.request


def test_unvisited_publication_request_stays_not_saved_despite_complete_input_card(
    focused_saved, monkeypatch
):
    block_current(monkeypatch)
    saved = sabueso.read_exploration(focused_saved["path"])
    missing = saved.explorer.view(TOPIC, options={"publication_ref": BENZ_PAPER})
    assert missing.outcome["status"] == "not_saved"
    assert saved.native_payload["publication_ref"] == BTS_PAPER
    assert (
        saved.explorer.answer(
            "publications", options={"publication_ref": BTS_PAPER}
        ).native_payload
        == saved.native_payload
    )


def logical_bundle(path):
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if bundle["format"] == "sabueso.card_exploration@20":
        from sabueso.core.card_exploration_shared_values_v4 import unpack

        bundle, _ = unpack(bundle)
    assert bundle["format"] == "sabueso.card_exploration@19"
    return bundle


@pytest.mark.parametrize(
    "change",
    [
        "title",
        "count",
        "state",
        "support",
        "relationship",
        "unit",
        "source_version",
        "coverage",
        "manifest",
        "selection",
    ],
)
def test_resealed_edits_cannot_replace_original_science_or_membership(
    focused_saved, change
):
    bundle = logical_bundle(focused_saved["path"])
    ref = next(
        ref
        for ref in bundle["scientific_results"]
        if bundle["objects"][ref].get("context", {}).get("adapter")
        == "literature_exploration@1"
    )
    wire = bundle["objects"][ref]
    key = next(iter(wire["rows"]))
    if change == "title":
        wire["rows"][key]["title"] = "Synthetic forged title"
    elif change == "count":
        wire["rows"][key]["measurement_count"] += 1
    elif change == "state":
        wire["rows"][key]["state"] = "partial"
    elif change == "support":
        wire["support"][key]["source_assertion_ids"].clear()
    elif change == "relationship":
        wire["explanations"][key]["links"][0]["relationship"]["object_ref"] = (
            "chembl:FOREIGN"
        )
    elif change == "unit":
        wire["explanations"][key]["links"][0]["relationship"]["qualifiers"][
            "measurement"
        ]["units"] = "percent"
    elif change == "source_version":
        wire["explanations"][key]["links"][0]["relationship"]["qualifiers"]["document"][
            "sabueso_version"
        ] = "provider-owned-value"
    elif change == "coverage":
        wire["coverage"]["rows"][0]["state"] = "forged_source_state"
    elif change == "manifest":
        bundle["scientific_results"].pop(ref)
    else:
        bundle["views"][bundle["root_navigation_ref"]]["selected"].clear()
    with pytest.raises(StorageError):
        _restore(_seal(bundle), None)


def test_fresh_reader_ignores_mutable_profiles_and_resaves_inertly(
    focused_saved, tmp_path
):
    script = (
        """
import importlib, socket, sys
import pytest
import sabueso
from sabueso.core.card import Card

def forbidden(*a, **k): raise AssertionError('No mutable Card/science/source/network')
"""
        + inspect.getsource(block_current)
        + """
with pytest.MonkeyPatch.context() as guard:
 block_current(guard)
 profiles = importlib.import_module('sabueso.core.card_exploration_profiles')
 profiles.NATURE_TOPICS = profiles.QUESTIONS = profiles.COMMON_QUESTIONS = {}
 saved = sabueso.read_exploration(sys.argv[1])
 assert saved.native_payload['publication_ref'] == 'pubmed:35189560'
 assert len(saved.native_payload['links']) == 9
 assert saved.explorer.answer('publications', options={'publication_ref':'pubmed:35189560'}).native_payload == saved.native_payload
 item = saved.items()[0]
 assert item.open().native_payload == item.explain().native_payload == saved.native_payload
 for link in item.related().items(): link.open()
 saved.save(sys.argv[2])
 assert sabueso.read_exploration(sys.argv[2]).native_payload == saved.native_payload
 print('original SDK202 literature receiving passed')
"""
    )
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            script,
            str(focused_saved["path"]),
            str(tmp_path / "again.json"),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=240,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "original SDK202 literature receiving passed" in result.stdout


def test_original_locators_both_structural_legs_and_source_types_survive(
    original, tmp_path, monkeypatch
):
    record = produce(
        original,
        "located",
        tmp_path / "located.json",
        {"publication_ref": LOCATED_PAPER},
    )
    expected = original.native("located", LOCATED_PAPER)
    block_current(monkeypatch)
    saved = sabueso.read_exploration(record["path"])
    links = saved.items()[0].related()
    roles = {item.cells["role"].value for item in links.items()}
    assert {
        "mentions",
        "structure_mentions",
        "annotation_requests",
        "unlinked_pdb_mentions",
    } <= roles
    structural = next(
        row
        for row in expected["links"]
        if row["relationship"]["predicate"] == "structure_mentioned_in"
    )
    context = structural["structure_contexts"][0]["context"]
    targets = [item.open() for item in links.items()]
    for identifier in [*context["relationship_ids"], *context["source_assertion_ids"]]:
        target = next(
            view
            for view in targets
            if isinstance(view.native_payload, dict)
            and view.native_payload.get("id") == identifier
        )
        assert target.native_payload["id"] == identifier and target.back() is links
    assert len(saved.native_payload["unlinked_pdb_mentions"]) == 3
    assert saved.native_payload["publication"]["curated"] == []


def test_full_459_context_and_all_original_queries_round_trip(
    original, whole_saved, tmp_path, monkeypatch
):
    """Read and resave all 459 links and nine exact TcTIM queries."""
    record, budgets = whole_saved, whole_saved["budgets"]
    block_current(monkeypatch)
    saved = sabueso.read_exploration(
        record["path"], expected_digest=record["receipt"]["bundle_digest"], **budgets
    )
    assert canonical_json(saved.native_payload) == canonical_json(record["root_native"])
    for ref, count in ((BENZ_PAPER, 459), (BTS_PAPER, 9)):
        native = publication(saved, ref).open().native_payload
        assert len(native["links"]) == count
        compare_original_native(native, original.native("tctim", ref))
    assert_retained_queries(saved.explorer, record["queries"])
    again = tmp_path / "whole-again.json"
    receipt = saved.save(again, **budgets)
    reread = sabueso.read_exploration(
        again, expected_digest=receipt["bundle_digest"], **budgets
    )
    assert canonical_json(reread.native_payload) == canonical_json(
        record["root_native"]
    )
    compare_original_native(
        publication(reread, BENZ_PAPER).open().native_payload,
        original.native("tctim", BENZ_PAPER),
    )


def test_saved_counts_nulls_and_original_false_are_not_coerced(
    original, tmp_path, monkeypatch
):
    record = produce(
        original, "search", tmp_path / "search.json", visit=("pubmed:39044810",)
    )
    block_current(monkeypatch)
    saved = sabueso.read_exploration(record["path"])
    false = publication(saved, "pubmed:39044810").open().native_payload
    assert any(row["open_access"] is False for row in false["publication"]["mentions"])
    unknown = publication(saved, "pubmed:16502470")
    assert (
        unknown.cells["title"].state == "unknown"
        and unknown.cells["title"].value is None
    )
    assert unknown.cells["measurement_count"].value == 0
    assert type(unknown.cells["measurement_count"].value) is int
    assert saved.filter("title", equals=None).items()
    with pytest.raises(ArgumentError):
        saved.filter("measurement_count", equals=False)
    with pytest.raises(ArgumentError):
        saved.filter("year", equals=2025)


def test_literature_report_has_only_verified_manifest_rules(focused_saved):
    from sabueso.core.card_exploration_literature import verification_report

    bundle = logical_bundle(focused_saved["path"])
    expected = verification_report(bundle)
    assert expected["verified_scientific_adapters"] == ["literature_exploration@1"]
    assert set(expected["verified_scientific_rules"]) == {
        "knowledge_state@5",
        "literature_explanation@1",
    }
    assert "bioactivities" not in expected and "chemical_classification" not in expected
    bundle["objects"]["literal-metadata-control"] = {
        "adapter": "bioactivity_exploration@1",
        "rule": "chemical_classification_context@1",
        "source_metadata": {"rule": "literal-provider-rule@99"},
    }
    assert verification_report(bundle) == expected


def test_structure_and_literature_report_has_no_inherited_bio_or_chemical_claims(
    original, tmp_path
):
    card = Card.from_dict(original.card("tctim"))
    explorer = card.explore()
    explorer.view("structures")
    literature = explorer.view(TOPIC, options={"publication_ref": BTS_PAPER})
    path = tmp_path / "structure-and-literature.json"
    literature.save(path)
    saved = sabueso.read_exploration(path)
    adapters = saved.validation["verified_scientific_adapters"]
    assert (
        "structure_exploration@1" in adapters and "literature_exploration@1" in adapters
    )
    assert "bioactivity_exploration@1" not in adapters
    assert "chemical_classification_exploration@1" not in adapters
    assert (
        "bioactivities" not in saved.validation
        and "chemical_classification" not in saved.validation
    )
    assert (
        "chemical_classification_context@1"
        not in saved.validation["verified_scientific_rules"]
    )


@pytest.mark.parametrize(
    "context", [False, None, {"adapter": "literature_exploration@1"}]
)
def test_literal_lookalikes_keep_original_format_and_typed_values(
    tmp_path, context, monkeypatch
):
    card = Card()
    opaque = {
        "context": context,
        "native_status": False,
        "value": 0,
        "rule": "literature_explanation@1",
        "unit": "nanomolar",
    }
    card.unknown_stored["literal"] = opaque
    path = tmp_path / "literal.json"
    card.explore().inspect().save(path)
    assert (
        json.loads(path.read_text(encoding="utf-8"))["format"]
        == "sabueso.card_exploration@1"
    )
    block_current(monkeypatch)
    saved = sabueso.read_exploration(path)
    assert canonical_json(saved.native_payload["literal"]) == canonical_json(opaque)
    assert saved.validation.get("verified_scientific_adapters", []) == []


def test_fresh_cross_card_publication_question_keeps_destination_and_exact_request(
    tmp_path, monkeypatch
):
    from sabueso.core.relationship_store import make_relationship
    from sabueso.core.source_assertion_store import make_source_assertion

    statement = make_source_assertion(
        "relationships.interacts_with",
        {"target": "uniprot:P60174"},
        "Synthetic cross-Card control",
        "public-input-scope",
        "2026-11-07",
        subject_ref="uniprot:P52270",
    )
    relationship = make_relationship(
        "uniprot:P52270", "interacts_with", "uniprot:P60174", {}, [statement["id"]]
    )
    first = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:P52270"},
        source_assertion_store=[statement],
        relationship_store=[relationship],
    )
    proof = make_source_assertion(
        "annotations.function",
        {"description": "Synthetic cross-Card request control"},
        "Synthetic cross-Card control",
        "public-input-scope",
        "2026-11-07",
        subject_ref="uniprot:P60174",
    )
    proof["source_metadata"] = {
        "eco": [{"source": "PubMed", "id": "8061610", "code": "ECO:0000269"}]
    }
    second = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:P60174"},
        source_assertion_store=[proof],
    )
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
    target = next(
        item
        for item in links.items()
        if item.cells["target_ref"].value == "uniprot:P60174"
    )
    destination = links.follow(target.item_ref)
    assert destination.request is None
    question = destination.explorer.answer("publications")
    expected_request, expected_native = question.request, question.native_payload
    expected_focal = question.context["card_ref"]
    path = tmp_path / "cross-card.json"
    question.save(path)
    block_current(monkeypatch)
    saved = sabueso.read_exploration(path)
    assert saved.request == expected_request and saved.native_payload == expected_native
    assert saved.context["card_ref"] == expected_focal
    assert saved.back().request is None
    # The observed current protein route catalog owns the @35 access binding.
    # Genuine earlier literature controls keep the strict @19/@20 helper above.
    bundle = json.loads(path.read_text(encoding="utf-8"))
    assert bundle["format"] == "sabueso.card_exploration@35"
    bundle["views"][bundle["root_navigation_ref"]]["flags"]["_request"]["options"][
        "publication_ref"
    ] = "pubmed:8061610"
    with pytest.raises(StorageError):
        _restore(_seal(bundle), None)


def test_same_publication_on_foreign_card_cannot_supply_focused_origin(tmp_path):
    from dataclasses import replace

    from sabueso.core.source_assertion_store import make_source_assertion

    cards = []
    for accession in ("P52270", "P60174"):
        ref = "uniprot:" + accession
        statement = make_source_assertion(
            "annotations.function",
            {"description": "Synthetic shared-publication scope control"},
            "Synthetic foreign-focal control",
            accession,
            "2026-11-07",
            subject_ref=ref,
        )
        statement["source_metadata"] = {
            "eco": [{"source": "PubMed", "id": "8061610", "code": "ECO:0000269"}]
        }
        cards.append(
            Card(
                meta={"entity_type": "protein", "card_id": "sabueso:protein:" + ref},
                source_assertion_store=[statement],
            )
        )
    options = {"publication_ref": "pubmed:8061610"}
    first_root = cards[0].explore(related_cards=[cards[1]]).view(TOPIC)
    first = publication(first_root, options["publication_ref"]).open()
    second = cards[1].explore(related_cards=[cards[0]]).view(TOPIC)
    assert (
        first.native_payload["publication_ref"]
        == second.native_payload["publications"][0]["publication_ref"]
    )
    assert first.context["card_ref"] != second.context["card_ref"]
    forged = replace(first, _origin=second)
    with pytest.raises(StorageError):
        forged.save(tmp_path / "foreign-focal.json")


@pytest.mark.parametrize("missing", ["assertion", "relationship"])
def test_saved_missing_structural_support_stays_partial_and_explicit(
    original, tmp_path, monkeypatch, missing
):
    from sabueso.core.quantities import seal

    data = original.card("located")
    structural = next(
        row
        for row in data["relationship_store"]
        if row["predicate"] == "structure_mentioned_in"
    )
    context = structural["qualifiers"]["structure_context"]
    store = "source_assertion_store" if missing == "assertion" else "relationship_store"
    identifier = context[
        "source_assertion_ids" if missing == "assertion" else "relationship_ids"
    ][0]
    # Deliberately broken public support, not an original provider observation.
    data[store] = [row for row in data[store] if row["id"] != identifier]
    data["quantities"] = seal(data)
    view = (
        Card.from_dict(data)
        .explore()
        .view(TOPIC, options={"publication_ref": LOCATED_PAPER})
    )
    expected = deepcopy(view.native_payload)
    assert view.outcome["status"] == expected["status"] == "partial"
    assert expected["reason"] == "missing_stored_support"
    related = view.items()[0].related()
    missing_link = next(
        item
        for item in related.items()
        if item.cells["availability"].value == "missing_prerequisite"
        and identifier in item.cells["target_ref"].value
    )
    assert missing_link.open().outcome["status"] == "missing_prerequisite"
    path = tmp_path / "partial.json"
    view.save(path)
    block_current(monkeypatch)
    saved = sabueso.read_exploration(path)
    assert saved.native_payload == expected and saved.outcome["status"] == "partial"
    related = saved.items()[0].related()
    link = next(
        item
        for item in related.items()
        if item.cells["target_ref"].value == missing_link.cells["target_ref"].value
    )
    assert link.cells["availability"].value == "missing_prerequisite"
    assert link.open().outcome["status"] == "missing_prerequisite"
    assert link.open().back() is related
