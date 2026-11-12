"""Original SDK200 controls and current SDK202 saved bioactivity receiving."""

import gzip
import hashlib
import importlib
import inspect
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import pyunitwizard as puw
from pyunitwizard import QuantityRecord

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_capture import _Capture
from sabueso.core.card_exploration_storage import _access, _restore, _seal
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.snapshot import canonical_json

DATA = Path(__file__).with_name("data") / "bioactivity_live_v1.json.gz"
ENCODED_SHA = "65a6108769ba1f178a8c13be0096689ba783ade038bb90382895450c93ad38f0"
DECODED_SHA = "2aed16cd0884049cca506e7831cf4897d7a149f92dd812959c6c1c9e92a0c7f0"
MANIFEST_SHA = "509ee7369f5a0cf53d5d40e872db33a19a5f2e075588e677dbfca7010f670ab6"
TOPIC = "bioactivities"
BTS = "chembl:CHEMBL1161789"
BENZ = "chembl:CHEMBL110"
BUDGETS = {
    "max_encoded_bytes": 128 * 1024**2,
    "max_decoded_bytes": 128 * 1024**2,
    # The measured complete graph is 709,616,078 logical bytes; keep the default
    # refusal and opt in explicitly for this original full-session workload.
    "max_logical_bytes": 1024**3,
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Original:
    def __init__(self, raw):
        self.raw, self.payload, self._cache = raw, raw["payload"], {}

    def value(self, encoded):
        """Detach only the requested value, preserving sharing inside that copy."""
        return deepcopy(self._shared_decode(encoded))

    def _shared_decode(self, encoded):
        """Decode immutable original nodes once without copying their children."""
        tag, value = encoded
        if tag == "literal":
            return value
        assert tag == "ref"
        if value not in self._cache:
            node = self.raw["values"][value]
            if node["kind"] == "dict":
                decoded = {
                    key: self._shared_decode(item) for key, item in node["body"].items()
                }
            else:
                assert node["kind"] == "list"
                decoded = [self._shared_decode(item) for item in node["body"]]
            assert sha(canonical_json(decoded).encode("utf-8")) == value
            self._cache[value] = decoded
        return self._cache[value]

    def native(self, name):
        return self.value(self.payload["native"][name])

    def card(self):
        return self.value(self.payload["card"])

    def access(self):
        pin = self.payload["original_manifest"]["card_ref"]
        capture = _Capture(self.card(), pin.split("@", 1)[1], pin)
        return _access({pin: capture}, [pin], {}, {}, pin)


def forbidden(*args, **kwargs):
    pytest.fail(
        "Independent saved reading cannot construct Cards, use current science or acquire sources"
    )


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def original():
    encoded = DATA.read_bytes()
    assert sha(encoded) == ENCODED_SHA
    decoded = gzip.decompress(encoded)
    assert len(decoded) == 20525099 and sha(decoded) == DECODED_SHA
    raw = json.loads(decoded)
    assert raw["format"] == "sabueso.bioactivity_live_original_projection@1"
    projection = raw["projection"]
    assert projection["source_manifest_sha256"] == MANIFEST_SHA
    assert (
        projection["original_members"] == 157
        and projection["original_total_bytes"] == 745483187
    )
    assert projection["machine_request_records"] == 16
    assert projection["unselected_item_cell_records_omitted"] == 1020
    manifest = raw["payload"]["original_manifest"]
    assert manifest["source_head"] == "2eb611463c0f8ab990039ec017833f5b33ae2711"
    assert manifest["producer_version"] == "0.14.0+200.g2eb6114"
    assert manifest["save_supported_at_capture"] is False
    assert manifest["network_attempts"] == manifest["source_acquisitions"] == 0
    return Original(raw)


@pytest.fixture
def card(original):
    return Card.from_dict(original.card())


def block_current(monkeypatch):
    """Import every target before from-imports can capture temporary guard aliases."""
    modules = {
        "bioactivities": ("bioactivities_view",),
        "bioactivity_explanation": ("explain_bioactivity", "explain_measurement"),
        "bioactivity_class_v4": ("classify",),
        "measurements": ("measurement_groups",),
        "measurement_correspondence": ("measurement_groups",),
        "bioactivity_target_scope": ("target_scope",),
        "entities": ("entity_view",),
        "literature": ("literature_view",),
        "literature_explanation": ("explain_literature",),
        "card_bioactivity_access": ("materialize", "options_for_bioactivities"),
        "card_bioactivity_exploration": (
            "materialize",
            "view",
            "open_item",
            "display_filter",
            "display_sort",
        ),
        "card_molecule_activity_access": ("materialize", "make_derivation"),
        "card_molecule_activity_exploration": ("view", "materialize"),
        "card_sequence_change_access": ("materialize", "make_derivation"),
        "card_sequence_change_exploration": ("view", "materialize"),
        "card_protein_context_access": ("materialize", "make_derivation"),
        "card_protein_context_exploration": ("view", "materialize"),
        "card_variant_access": ("materialize",),
        "card_variant_exploration": ("view", "materialize"),
        "card_knowledge_comparison_access": ("materialize", "make_derivation"),
        "card_knowledge_comparison_exploration": ("view", "materialize"),
        "card_knowledge_diff_v2": ("compare", "make_derivation"),
        "card_disease_association_access": ("materialize", "make_derivation"),
        "card_disease_association_exploration": ("view", "materialize"),
        "relationship_store": ("make_derivation",),
    }
    loaded_modules = {
        module: importlib.import_module("sabueso.core." + module) for module in modules
    }
    clients = [
        getattr(importlib.import_module(module), name)
        for module, name in (
            ("sabueso.resolver", "FixtureUniProtClient"),
            ("sabueso.tools.db.chembl", "FixtureChEMBLClient"),
        )
    ]
    for name in (
        "__init__",
        "from_dict",
        "bioactivities",
        "explain_bioactivity",
        "explain_measurement",
        "knowledge_state",
        "literature",
        "explain_literature",
    ):
        monkeypatch.setattr(Card, name, forbidden)
    for module, names in modules.items():
        loaded = loaded_modules[module]
        for name in names:
            if hasattr(loaded, name):
                monkeypatch.setattr(loaded, name, forbidden)
    for client in clients:
        monkeypatch.setattr(client, "__init__", forbidden)


def test_frozen_predicates_match_all_nine_original_wires_without_current_engines(
    original, monkeypatch
):
    from sabueso.core.card_bioactivity_history_v1 import expected_result

    access = original.access()
    block_current(monkeypatch)
    assert len(original.payload["wires"]) == 9
    for ref, encoded in original.payload["wires"].items():
        wire = original.value(encoded)
        expected = expected_result(access, wire["context"]["options"], original=wire)
        assert expected.result_ref == ref and expected.wire == wire
    native = original.native("native.bioactivities.json")
    assert sum(item["record_count"] for item in native["items"]) == 493
    assert native["excluded"] == []


def test_frozen_publication_keeps_the_original_459_link_context(original, monkeypatch):
    from sabueso.core.card_bioactivity_history_v1 import expected_publication

    access = original.access()
    block_current(monkeypatch)
    assert len(original.payload["publication_wrappers"]) == 2
    for encoded in original.payload["publication_wrappers"].values():
        wrapper = original.value(encoded)
        assert (
            expected_publication(access, wrapper["publication_ref"], original=wrapper)
            == wrapper
        )
    assert (
        len(original.native("native.explain_literature.pubmed_20889239.json")["links"])
        == 459
    )


def named(view, molecule_ref):
    return next(
        item
        for item in view.items()
        if item.cells["molecule_ref"].value == molecule_ref
    )


@pytest.fixture(scope="module")
def saved_session(original, tmp_path_factory):
    card = Card.from_dict(original.card())
    before = card.to_dict()
    explorer = card.explore()
    root = explorer.answer("measured_molecules")
    queries = [
        {
            "fields": ["molecule_ref", "class", "measurement"],
            "where": {"molecule_ref": BTS},
        },
        {"fields": [], "where": {"molecule_ref": "chembl:ABSENT"}},
        {
            "options": {"molecule_ref": BTS},
            "where": {"measurement": {"value": 33, "unit": "micromolar"}},
            "order_by": {"column": "measurement", "unit": "nanomolar"},
        },
        {
            "options": {
                "molecule_ref": BTS,
                "thresholds": {"active_max": {"value": 33, "unit": "micromolar"}},
            },
            "fields": ["measurement_ref", "class", "measurement"],
        },
        {
            "options": {
                "measurement_rule": "measurement_identity@2",
                "target_scope_rule": "bioactivity_target_scope@2",
            },
            "fields": ["molecule_ref", "measurement_count", "record_count"],
        },
    ]
    selections = [explorer.access.select(TOPIC, **query) for query in queries]
    trails = []
    for molecule_ref in (BTS, BENZ):
        groups = named(root, molecule_ref).open()
        for group in groups.items():
            records = group.open()
            for record in records.items():
                detail, explanation, links = (
                    record.open(),
                    record.explain(),
                    record.related(),
                )
                contexts = [item.open() for item in links.items()]
                trails.append(
                    {
                        "molecule": molecule_ref,
                        "group": group.cells["measurement_ref"].value,
                        "relationship": record.cells["relationship_id"].value,
                        "records": records,
                        "detail": detail,
                        "explanation": explanation,
                        "links": links,
                        "contexts": contexts,
                    }
                )
    path = tmp_path_factory.mktemp("saved-bioactivity") / "session.json"
    receipt = root.save(path, **BUDGETS)
    physical = json.loads(path.read_text(encoding="utf-8"))
    assert physical["format"] == "sabueso.card_exploration@20"
    assert 256 * 1024**2 < physical["logical_bytes"] <= BUDGETS["max_logical_bytes"]
    del physical
    # The shared header refuses the default workload before rebuilding the graph.
    with pytest.raises(ArgumentError, match="max_logical_bytes"):
        sabueso.read_exploration(
            path,
            max_encoded_bytes=BUDGETS["max_encoded_bytes"],
            max_decoded_bytes=BUDGETS["max_decoded_bytes"],
            max_logical_bytes=256 * 1024**2,
        )
    assert card.to_dict() == before
    return {
        "path": path,
        "receipt": receipt,
        "root": root,
        "queries": queries,
        "selections": selections,
        "trails": trails,
        "card": before,
    }


def read(path, **kwargs):
    return sabueso.read_exploration(path, **BUDGETS, **kwargs)


def logical_bundle(path, *, bioactivity=True):
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if bundle["format"] == "sabueso.card_exploration@20":
        from sabueso.core.card_exploration_shared_values_v4 import unpack

        bundle, _ = unpack(
            bundle,
            limit=BUDGETS["max_logical_bytes"],
            component_limit=BUDGETS["max_decoded_bytes"],
        )
    if bioactivity:
        assert bundle["format"] == "sabueso.card_exploration@19"
    return bundle


def test_saved_root_and_exact_machine_requests_keep_full_science(saved_session):
    saved = read(
        saved_session["path"], expected_digest=saved_session["receipt"]["bundle_digest"]
    )
    live = saved_session["root"]
    assert saved.native_payload == live.native_payload
    assert saved.rows() == live.rows()
    assert [item.item_ref for item in saved.items()] == [
        item.item_ref for item in live.items()
    ]
    assert sum(item["record_count"] for item in saved.native_payload["items"]) == 493
    assert saved.exclusions == live.exclusions
    reopened = saved.explorer.answer("measured_molecules")
    assert reopened.native_payload == saved.native_payload
    assert reopened.context["options"] == saved.context["options"]

    def semantic_locations(access, value):
        if isinstance(value, dict):
            if (
                set(value) == {"format", "kind", "location_ref"}
                and value["format"] == "card_access_location@1"
                and value["kind"] == "lookup"
            ):
                return access._resolve(value)[1]
            return {
                key: semantic_locations(access, item) for key, item in value.items()
            }
        if isinstance(value, list):
            return [semantic_locations(access, item) for item in value]
        return value

    for query, original in zip(saved_session["queries"], saved_session["selections"]):
        selected = saved.explorer.access.select(TOPIC, **query)
        assert (
            selected.selection_ref == original.selection_ref
            and selected.count == original.count
        )
        retained_items = selected.page()["items"]
        assert semantic_locations(
            saved.explorer.access, retained_items
        ) == semantic_locations(live.explorer.access, original.page()["items"])
        if retained_items:
            assert (
                saved.explorer.access.read(retained_items[0]["payload_location"]).count
                > 0
            )
        assert selected.page()["outcome"] == original.page()["outcome"]
    missing = saved.explorer.access.select(
        TOPIC,
        fields=["label"],
        options={"thresholds": {"active_max": {"value": 32, "unit": "micromolar"}}},
    )
    assert missing.page()["outcome"]["status"] == "not_saved"


def test_saved_three_grains_context_back_and_full_publication_are_original(
    saved_session,
):
    saved = read(saved_session["path"])
    for original in saved_session["trails"]:
        groups = named(saved, original["molecule"]).open()
        group = next(
            item
            for item in groups.items()
            if item.cells["measurement_ref"].value == original["group"]
        )
        records = group.open()
        record = next(
            item
            for item in records.items()
            if item.cells["relationship_id"].value == original["relationship"]
        )
        assert records.native_payload == original["records"].native_payload
        assert record.open().native_payload == original["detail"].native_payload
        assert record.open().back().view_ref == records.view_ref
        assert record.explain().native_payload == original["explanation"].native_payload
        links = record.related()
        assert links.native_payload == original["links"].native_payload
        for source, context in zip(links.items(), original["contexts"]):
            opened = source.open()
            assert opened.native_payload == context.native_payload
            assert opened.back().view_ref == links.view_ref
            if (
                source.cells["role"].value == "publication_context"
                and original["molecule"] == BENZ
            ):
                assert len(opened.native_payload["links"]) == 459
        assert records.request == original["records"].request
        assert records.context["options"]["include_indirect"] is False


def test_saved_quantities_and_custom_threshold_are_exact(saved_session):
    saved = read(saved_session["path"])
    selected = saved.explorer.access.select(TOPIC, **saved_session["queries"][2])
    cell = selected.page()["items"][0]["cells"]["measurement"]
    quantity = QuantityRecord.from_dict(cell["value"]).to_quantity(
        field="relationships.has_bioactivity.measurement.normalized",
        unit="nanomolar",
        form="pint",
    )
    assert puw.get_value(quantity, to_unit="nanomolar") == 33000
    custom = saved.explorer.access.select(TOPIC, **saved_session["queries"][3])
    assert custom.page()["items"][0]["cells"]["class"]["value"] == "active"
    assert custom.result_ref != selected.result_ref
    with pytest.raises(ArgumentError):
        saved.explorer.view(TOPIC, options={"molecule_ref": BENZ}).sort(
            "measurement", unit="nanomolar"
        )


@pytest.fixture(scope="module")
def focused_saved(original, tmp_path_factory):
    card = Card.from_dict(original.card())
    selected = card.access().select(TOPIC, options={"molecule_ref": BTS})
    path = tmp_path_factory.mktemp("focused-bioactivity") / "focused.json"
    selected.save(path, **BUDGETS)
    return path


@pytest.mark.parametrize("compression", ["none", "gzip", "zstd"])
def test_supported_transport_and_resave_keep_science_and_queries(
    focused_saved, tmp_path, compression
):
    saved = read(focused_saved)
    path = tmp_path / "again"
    saved.save(path, compression=compression, **BUDGETS)
    again = read(path)
    assert again.native_payload == saved.native_payload
    assert again.rows() == saved.rows()
    assert again.request == saved.request


@pytest.mark.parametrize(
    "change",
    [
        "value",
        "unit",
        "class",
        "rule",
        "support",
        "doi",
        "source_version",
        "count",
        "manifest",
        "selection",
        "request",
    ],
)
def test_resealed_changes_cannot_replace_original_science_or_scope(
    focused_saved, change
):
    bundle = logical_bundle(focused_saved)
    ref = next(
        ref
        for ref in bundle["scientific_results"]
        if bundle["objects"][ref]["context"]["grain"] == "group"
    )
    wire = bundle["objects"][ref]
    record = bundle["views"][bundle["root_navigation_ref"]]
    if change == "value":
        wire["native_payload"]["item"]["measurements"][0]["value"] = 1
    elif change == "unit":
        wire["native_payload"]["item"]["measurements"][0]["normalized"]["unit"] = (
            "percent"
        )
    elif change == "class":
        next(iter(wire["rows"].values()))["class"] = "active"
    elif change == "rule":
        wire["native_payload"]["classification"]["rule"] = "bioactivity_class@99"
    elif change == "support":
        next(iter(wire["support"].values()))["source_assertion_ids"].clear()
    elif change == "doi":
        wire["native_payload"]["records"][0]["relationship"]["qualifiers"]["document"][
            "doi"
        ] = "10.0000/synthetic-forgery"
    elif change == "source_version":
        wire["native_payload"]["records"][0]["relationship"]["qualifiers"]["document"][
            "sabueso_version"
        ] = "source-owned-metadata"
    elif change == "count":
        wire["native_payload"]["item"]["record_count"] += 1
    elif change == "manifest":
        bundle["scientific_results"].pop(ref)
    elif change == "selection":
        record["selected"].clear()
    else:
        record["flags"]["_request"] = {
            "topic": TOPIC,
            "question": "measured_molecules",
            "options": {"include_indirect": True},
        }
    with pytest.raises(StorageError):
        _restore(
            _seal(bundle),
            None,
            max_logical_bytes=BUDGETS["max_logical_bytes"],
            component_limit=BUDGETS["max_decoded_bytes"],
        )


def test_fresh_saved_reader_has_no_current_engines_catalog_or_source_clients(
    saved_session, tmp_path
):
    script = (
        """
import importlib, socket, sys
import pytest
import sabueso
from sabueso.core.card import Card

def forbidden(*args, **kwargs):
    raise AssertionError("No current Card, science, source client or network")
"""
        + inspect.getsource(block_current)
        + """
with pytest.MonkeyPatch.context() as guard:
 block_current(guard)
 guard.setattr(socket.socket, 'connect', forbidden)
 guard.setattr(socket, 'create_connection', forbidden)
 profiles = importlib.import_module('sabueso.core.card_exploration_profiles')
 profiles.NATURE_TOPICS = profiles.QUESTIONS = {}
 view = sabueso.read_exploration(sys.argv[1], max_encoded_bytes=134217728, max_decoded_bytes=134217728, max_logical_bytes=1073741824)
 assert view.explorer.answer('measured_molecules').native_payload == view.native_payload
 assert sum(item['record_count'] for item in view.native_payload['items']) == 493
 for molecule_ref in ('chembl:CHEMBL1161789', 'chembl:CHEMBL110'):
  item = next(item for item in view.items() if item.cells['molecule_ref'].value == molecule_ref)
  for group in item.open().items():
   for record in group.open().items():
    assert record.open().native_payload['relationship']
    assert record.explain().native_payload
    for source in record.related().items(): source.open()
 missing = view.explorer.view('bioactivities', options={'include_indirect': True})
 assert missing.outcome['status'] == 'not_saved'
 view.save(sys.argv[2], max_encoded_bytes=134217728, max_decoded_bytes=134217728, max_logical_bytes=1073741824)
 print('independent original bioactivity receiving passed')
"""
    )
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            script,
            str(saved_session["path"]),
            str(tmp_path / "again.json"),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        # The complete original session takes about 330 s to save and 80 s to
        # read on the declared single-core profile; this child does both.
        timeout=600,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "independent original bioactivity receiving passed" in result.stdout


@pytest.mark.parametrize(
    "context", [{"adapter": "bioactivity_exploration@1"}, False, None]
)
def test_literal_scientific_lookalikes_preserve_false_zero_and_null(tmp_path, context):
    explorer = Card(meta={"entity_type": "protein"}).explore()
    explorer.view(TOPIC)
    opaque = {
        "context": context,
        "native_payload": {
            "flag": False,
            "count": 0,
            "missing": None,
            "unit_string": "nanomolar",
        },
    }
    literal = explorer._metadata(opaque, "Literal bioactivity lookalike")
    path = tmp_path / "literal.json"
    literal.save(path, **BUDGETS)
    saved = read(path)
    assert saved.native_payload == opaque
    bundle = logical_bundle(path, bioactivity=False)
    ref = next(ref for ref, value in bundle["objects"].items() if value == opaque)
    bundle.setdefault("scientific_results", {})[ref] = {"focal": bundle["inputs"][0]}
    with pytest.raises(StorageError):
        _restore(_seal(bundle), None, max_logical_bytes=BUDGETS["max_logical_bytes"])


@pytest.mark.parametrize(
    "status,expected",
    [(None, "not_queried"), ("error", "unavailable"), ("added", "empty")],
)
def test_saved_request_coverage_does_not_turn_into_source_absence(
    original, tmp_path, status, expected
):
    card = Card.from_dict(original.card())
    card.relationship_store.store.clear()
    card.quality["enrichments"] = (
        []
        if status is None
        else [
            {
                "source": "ChEMBL",
                "identifier": "CHEMBL5834",
                "status": status,
                "count": 0,
                "detail": "Explicit synthetic saved-coverage control",
            }
        ]
    )
    live = card.explore().view(TOPIC)
    path = tmp_path / "coverage.json"
    live.save(path, **BUDGETS)
    saved = read(path)
    assert saved.outcome == live.outcome and saved.outcome["status"] == expected
    assert saved.native_payload == live.native_payload
    assert not saved.items()
    with pytest.raises(ArgumentError):
        saved.filter("unknown_column", equals=True)
    if expected != "empty":
        with pytest.raises(ArgumentError):
            saved.filter("class", equals="weak")


def test_supplied_other_nature_stays_separate_from_protein_activity_scope(
    original, tmp_path
):
    protein = Card.from_dict(original.card())
    disease = Card(
        meta={"entity_type": "disease", "card_id": "sabueso:disease:mondo:0000001"}
    )
    before = protein.to_dict(), disease.to_dict()
    selection = protein.access(related_cards=[disease]).select(
        TOPIC, options={"molecule_ref": BTS}
    )
    path = tmp_path / "mixed.json"
    selection.save(path, **BUDGETS)
    saved = read(path)
    captures = saved.explorer.access._captures
    assert {capture.data["meta"]["entity_type"] for capture in captures.values()} == {
        "protein",
        "disease",
    }
    assert saved.explorer.profile == "protein"
    assert saved.native_payload["molecule_ref"] == BTS
    assert (protein.to_dict(), disease.to_dict()) == before


def test_original_projection_keeps_named_requests_three_grains_and_complete_publication(
    original,
):
    human = original.payload["human"]
    names = original.value(human["named_views"])

    def route(name):
        return original.value(human["views"][names[name]])

    assert route("measured_molecules")["native_payload"] == original.native(
        "native.bioactivities.json"
    )
    assert route("bts_public_case.groups")["native_payload"] == original.native(
        "native.explain_bioactivity.bts_public_case.json"
    )
    assert route("benznidazole.groups")["native_payload"]["item"]["record_count"] == 2
    for role, activity in (
        ("bts_public_case", 24815542),
        ("benznidazole", 5108414),
        ("benznidazole", 5108641),
    ):
        prefix = role + ".activity." + str(activity)
        detail = route(prefix + ".detail")
        assert (
            detail["native_payload"]["relationship"]["qualifiers"]["activity_id"]
            == activity
        )
        assert detail["origin"] == names[prefix + ".records"]
    custom = route("bts_public_case.explicit_threshold_33_micromolar")
    assert custom["context"]["options"]["thresholds"]["active_max"] == {
        "value": 33,
        "unit": "micromolar",
    }
    assert custom["native_payload"]["item"]["class"] == "active"
    opted = route("explicit_opt_in_grouping_and_target_scope_2")
    assert opted["context"]["options"]["measurement_rule"] == "measurement_identity@2"
    assert (
        opted["context"]["options"]["target_scope_rule"] == "bioactivity_target_scope@2"
    )


def test_resealed_publication_cannot_replace_459_links_with_selected_molecule_count(
    saved_session,
):
    bundle = logical_bundle(saved_session["path"])
    wrapper = next(
        value
        for value in bundle["objects"].values()
        if isinstance(value, dict)
        and value.get("publication_ref") == "pubmed:20889239"
        and "original_explanation" in value
    )
    assert len(wrapper["original_explanation"]["links"]) == 459
    wrapper["original_summary"]["measurements"] = 2
    wrapper["original_explanation"]["links"] = wrapper["original_explanation"]["links"][
        :2
    ]
    with pytest.raises(StorageError):
        _restore(
            _seal(bundle),
            None,
            max_logical_bytes=BUDGETS["max_logical_bytes"],
            component_limit=BUDGETS["max_decoded_bytes"],
        )
