"""Public original controls and deliberate synthetic chemical-context changes."""

import gzip
import hashlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from sabueso.core.card import Card
from sabueso.core.card_capture import _Capture
from sabueso.core.chemical_classification_v1 import interpret
from sabueso.core.errors import ArgumentError
from sabueso.core.snapshot import canonical_json

ORIGINAL = Path(__file__).parent / "data/chemical_native_sdk192.json.gz"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Exploration must use retained inputs without source requests")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture
def originals():
    encoded = ORIGINAL.read_bytes()
    assert (
        hashlib.sha256(encoded).hexdigest()
        == "d5977cd011813b8baac493a88553b9a2750c59ae0e0f5c411a2daa9735ce2291"
    )
    return json.loads(gzip.decompress(encoded))


@pytest.fixture
def card(originals):
    return Card.from_dict(deepcopy(originals["cases"]["vincristine"]["card"]))


def named(view, label):
    return next(item for item in view.items() if item.label == label)


def values(selection):
    return [item["value"] for item in selection.page()["items"]]


@pytest.mark.parametrize("case", ["vincristine", "pga"])
def test_original_native_bytes_are_identical_without_live_card_or_mapping(
    originals, case, monkeypatch
):
    import sabueso.mappings.molecule_identity as mapping

    def forbidden(*args, **kwargs):
        pytest.fail("The frozen kernel must not call the current identity mapping")

    monkeypatch.setattr(mapping, "is_standard_inchikey", forbidden)
    original = originals["cases"][case]
    native = original["native"]
    result = interpret(
        _Capture(deepcopy(original["card"]), native["snapshot_id"], native["card_ref"])
    )
    assert canonical_json(result) == canonical_json(native)
    assert (
        hashlib.sha256(canonical_json(result).encode()).hexdigest()
        == original["native_sha256"]
    )


@pytest.mark.parametrize("case", ["vincristine", "pga"])
def test_public_human_question_and_agent_rows_share_original_science(originals, case):
    original = originals["cases"][case]
    card = Card.from_dict(deepcopy(original["card"]))
    before = card.to_dict()
    explorer = card.explore()
    assert "Chemical classes and source-stated roles" in str(explorer.topics())
    question = next(
        item
        for item in explorer.questions().items()
        if item._entry.key == "classification"
    )
    human = question.open()
    assert human.native_payload == original["native"]
    assert human.request["question"] == "classification"
    assert "not target-specific activity" in str(human)
    assert "Molecule:" in str(human) and original["native"]["focal_ref"] in str(human)
    assert "Which chemical classes and source-stated roles are retained?" in str(human)
    assert "Saving preserves the original chemical interpretation" in str(human)
    assert "CHEBI:" in human._repr_html_()
    agent = explorer.access.select(
        "chemical_classification", fields=["term_ref", "assignment", "application"]
    )
    assert agent.result_ref == human.result_ref
    frames = agent.page()["items"]
    assert len(frames) == len(human.items()) == len(original["native"]["rows"])
    for item, frame, native in zip(human.items(), frames, original["native"]["rows"]):
        assert item.item_ref == frame["item_ref"]
        assert item.open().native_payload == native
        assert frame["interpretation"]["assignment"] == native["assignment"]
        assert frame["interpretation"]["scope"] == original["native"]["scope"]
        assert item.back() is human
        assert item.open().back() is human
    assert card.to_dict() == before


def test_original_source_membership_identity_and_back_are_inspectable(card):
    view = card.explore().answer("classification")
    item = named(view, "antineoplastic agent")
    assert item.cells["assignment"].value == "direct"
    assert item.cells["application"].value is True
    assert named(view, "Bronsted base").cells["assignment"].value == "inherited"
    detail = item.open()
    assert "Directly assigned role" in str(detail)
    assert "Application: yes" in str(detail)
    explanation = item.explain()
    assert explanation.back() is view
    assert {source._entry.value["field_path"] for source in explanation.items()} == {
        "annotations.chemical_roles",
        "relationships.same_as",
    }
    links = item.related()
    assert links.back() is view
    assert {link.cells["role"].value for link in links.items()} >= {
        "source",
        "original_member",
        "identity_context",
        "original_field",
    }
    for link in links.items():
        opened = link.open()
        assert opened.outcome["status"] in ("ok", "empty")
        assert opened.back() is links
        if link.cells["role"].value == "original_field":
            assert opened.native_payload["original_node"]["value"][0][
                "chebi_id"
            ].startswith("CHEBI:")


def test_one_captured_interpretation_is_reused_and_detached(card, monkeypatch):
    import sabueso.core.card_chemical_access as adapter

    original, calls = adapter.interpret, []

    def counted(capture):
        calls.append(capture.snapshot)
        return original(capture)

    monkeypatch.setattr(adapter, "interpret", counted)
    explorer = card.explore()
    native = card.chemical_classification()
    card.get("annotations.chemical_roles")["value"].clear()
    human = explorer.answer("classification")
    agent = explorer.access.select("chemical_classification")
    assert len(calls) == 1
    assert human.native_payload == native
    assert agent.count == len(native["rows"])
    returned = human.native_payload
    returned["rows"].clear()
    assert human.native_payload == native
    item = human.items()[0]
    item.support[0].clear()
    item.cells["label"].value
    assert item.support[0]["rule"] == native["rule"]


def test_exact_typed_category_filter_projection_order_and_membership(card):
    explorer = card.explore()
    view = explorer.view("classification")
    human = view.filter("application", equals=True).sort("label")
    agent = explorer.access.select(
        "chemical_classification",
        fields=["label", "application"],
        where={"application": True},
        order_by={"column": "label"},
    )
    assert [item.item_ref for item in human.items()] == [
        frame["item_ref"] for frame in agent.page()["items"]
    ]
    assert all(item.cells["application"].value is True for item in human.items())
    assert set(agent.page()["items"][0]["cells"]) == {"label", "application"}
    chosen = human.items()[0].item_ref
    subset = explorer.access.select(
        "chemical_classification", fields=[], item_refs=[chosen]
    )
    frame = subset.page()["items"][0]
    assert frame["item_ref"] == chosen and frame["cells"] == {}
    assert frame["interpretation"]["rule_names"] == [
        "chemical_classification_context@1"
    ]
    assert frame["support"]["source_assertions"]
    assert frame["support"]["basis"] == "source_bound_chemical_classification"
    assert explorer.access.read(frame["interpretation_location"]).count > 0
    assert explorer.access.explain(chosen).count > 0
    assert (
        explorer.access.select(
            "chemical_classification", where={"application": False}
        ).count
        > 0
    )
    unknown = explorer.access.select(
        "chemical_classification", where={"application": None}
    )
    assert unknown.count == 8  # Original class rows carry no role category flags.
    assert len(view.filter("application", equals=None).items()) == unknown.count


@pytest.mark.parametrize(
    "kwargs",
    [
        {"where": {"application": 0}},
        {"where": {"application": "false"}},
        {"where": {"assignment": True}},
        {"where": {"unknown_column": "x"}},
        {"fields": ["application", "application"]},
        {"fields": ["unknown"]},
        {"options": {"infer_activity": True}},
        {"order_by": {"column": "application", "descending": 1}},
        {"order_by": {"column": "assignment", "unit": "angstrom"}},
    ],
)
def test_invalid_selection_is_rejected_before_interpretation(card, kwargs, monkeypatch):
    import sabueso.core.card_chemical_access as adapter

    def forbidden(*args, **kw):
        pytest.fail("Invalid input must be refused before interpretation")

    monkeypatch.setattr(adapter, "interpret", forbidden)
    with pytest.raises(ArgumentError):
        card.access().select("chemical_classification", **kwargs)


def test_changed_selected_value_does_not_gain_source_assignment(card):
    role = card.get("annotations.chemical_roles")["value"][0]
    role["direct"] = not role["direct"]
    role["name"] = "Synthetic altered role"
    view = card.explore().view("classification")
    item = named(view, "Synthetic altered role")
    assert view.outcome["status"] == "partial"
    assert item.cells["assignment"].value == "unknown"
    assert item.cells["application"].value is None
    assert "Original support not established" in str(item.open())
    filtered = view.filter("label", equals="does not occur")
    assert not filtered.items() and filtered.outcome == view.outcome
    assert "not target-specific activity" in str(filtered)
    assert "Partly supported or incompletely stated" in str(filtered)
    assert item.explain().native_payload["original_member"]["source_memberships"] == []


@pytest.mark.parametrize(
    "value,state",
    [(None, "retained_null"), ([], "retained_empty"), (False, "unrecognized_shape")],
)
def test_unavailable_and_explicit_empty_field_states_are_human_readable(
    card, value, state
):
    for path in ("annotations.chemical_roles", "annotations.chemical_classes"):
        card.get(path)["value"] = value
    view = card.explore().view("classification")
    assert not view.items()
    assert all(row["state"] == state for row in view.native_payload["fields"].values())
    assert "not establish" in str(view)
    assert view.outcome["status"] == (
        "empty" if state == "retained_empty" else "unknown"
    )


def test_duplicate_original_positions_remain_separate(card):
    node = card.get("annotations.chemical_roles")
    node["value"].append(deepcopy(node["value"][0]))
    view = card.explore().view("classification")
    duplicates = [
        item for item in view.items() if item.label == node["value"][0]["name"]
    ]
    assert len(duplicates) == 2
    assert duplicates[0].item_ref != duplicates[1].item_ref
    assert (
        duplicates[0].open().native_payload["source_memberships"]
        == duplicates[1].open().native_payload["source_memberships"]
    )


def test_large_label_is_explicitly_deferred_with_scope_and_source_destinations(card):
    card.get("annotations.chemical_classes")["value"][0]["name"] = "synthetic " * 4000
    access = card.access()
    selection = access.select("chemical_classification", fields=[])
    page = selection.page(limit=1, max_bytes=8192)
    assert len(canonical_json(page).encode()) <= 8192
    frame = page["items"][0]
    assert frame["inspection_required"] is True
    assert frame["value_included"] is False
    assert "interpretation" not in frame and "support" not in frame
    assert frame["reason"] == "value_and_interpretation_exceed_response_budget"
    assert access.read(frame["interpretation_location"]).count > 0
    assert access.read(frame["support_location"]).count > 0
    assert page["page"]["next_cursor"]
    next_page = selection.page(limit=1, cursor=page["page"]["next_cursor"])
    assert next_page["items"][0]["item_ref"] != frame["item_ref"]


def test_chemical_save_capabilities_and_raw_export_remain_explicit(card, tmp_path):
    from sabueso import read_exploration

    explorer = card.explore()
    view = explorer.view("classification")
    selection = explorer.access.select("chemical_classification")
    assert view.capabilities["save"] and selection.capabilities["save"]
    for index, query in enumerate(
        (view, selection, view.items()[0].open(), view.items()[0].related())
    ):
        path = tmp_path / f"supported-{index}.json"
        query.save(path)
        saved = read_exploration(path)
        assert saved.native_payload == (
            view.native_payload if query is selection else query.native_payload
        )
    explorer.access.export_card(tmp_path / "original-card.json")
    assert (
        json.loads((tmp_path / "original-card.json").read_text())["sections"]
        == card.to_dict()["sections"]
    )


def test_independent_literal_save_after_chemical_visit_remains_supported(
    card, tmp_path
):
    from sabueso import read_exploration

    explorer = card.explore()
    explorer.answer("classification").items()[0].related()
    chemistry = explorer.view("chemistry")
    path = tmp_path / "literal.json"
    chemistry.save(path)
    original = read_exploration(path)
    assert original.native_payload == chemistry.native_payload
    assert (
        original.explorer.view("classification").native_payload
        == card.chemical_classification()
    )


def test_original_session_reads_in_fresh_process_without_live_engines(
    originals, tmp_path
):
    path = tmp_path / "original.json"
    path.write_text(canonical_json(originals["cases"]["pga"]["saved_original"]))
    script = """
import socket, sys
import sabueso
from sabueso.core.card import Card
import sabueso.core.card_chemical_access as adapter
import sabueso.core.chemical_classification_v1 as kernel
import sabueso.mappings.chebi as mapping
def forbidden(*a, **k):
    raise AssertionError("No Card construction, mapping, scientific computation or source request")
Card.__init__ = forbidden
adapter.interpret = kernel.interpret = forbidden
mapping.map_chebi_identity = forbidden
socket.socket.connect = socket.create_connection = forbidden
view = sabueso.read_exploration(sys.argv[1])
assert view.explorer.mode == "saved"
assert view.explorer.view("classification").outcome["status"] == "not_saved"
assert view.native_payload
print("original SDK192 saved receiving passed")
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "original SDK192 saved receiving passed" in result.stdout


@pytest.mark.parametrize("case", ["vincristine", "pga"])
def test_genuine_sdk192_saved_molecule_keeps_original_menu_and_science(
    originals, case, tmp_path, monkeypatch
):
    import sabueso.core.card_chemical_access as adapter
    from sabueso import read_exploration

    def forbidden(*args, **kwargs):
        pytest.fail(
            "Original saved reading must never evaluate the new chemical reader"
        )

    monkeypatch.setattr(adapter, "interpret", forbidden)
    original = originals["cases"][case]
    path = tmp_path / "original.json"
    path.write_text(canonical_json(original["saved_original"]))
    saved = read_exploration(path)
    assert "classification" not in saved.explorer.capabilities["question_keys"]
    # Original retained catalogues keep their original rows/text. A fresh saved
    # catalogue may show newer destinations explicitly marked not_saved.
    for expected in original["saved_original"]["views"].values():
        if expected["flags"]["_route_catalog"]:
            retained = [
                view
                for view in saved.explorer._session["views"].values()
                if view._route_catalog
                and view.title == expected["flags"]["title"]
                and view.native_payload == expected["native_payload"]
            ]
            assert retained
            assert all("classification" not in view.native_payload for view in retained)
    assert "not_saved" in str(saved.explorer.topics())
    assert saved.explorer.view("classification").outcome["status"] == "not_saved"
    assert (
        saved.explorer.access.select("chemical_classification").page()["outcome"][
            "status"
        ]
        == "not_saved"
    )
