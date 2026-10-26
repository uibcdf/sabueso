"""Compact agents share human site science; examples here are explicitly synthetic."""

import importlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest
from test_card_ligand_site_comparisons_offline import TOPIC, forbidden, protein

from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.snapshot import canonical_json


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    importlib.import_module("sabueso.core.ligand_explanation")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def frames(selection, **kwargs):
    cursor = None
    while True:
        frame = selection.page(cursor=cursor, **kwargs)
        assert len(canonical_json(frame).encode("utf-8")) <= kwargs.get(
            "max_bytes", 65536
        )
        yield frame
        cursor = frame["page"]["next_cursor"]
        if cursor is None:
            break


def items(selection, **kwargs):
    return [item for frame in frames(selection, **kwargs) for item in frame["items"]]


@pytest.mark.parametrize("first", ["human", "agent"])
def test_same_capture_one_native_evaluation_original_item_ids_and_explanations(
    first, monkeypatch
):
    native = importlib.import_module("sabueso.core.ligand_sites")
    importlib.import_module("sabueso.core.ligand_explanation")
    original, calls = native.ligand_sites_view, []

    def count(*a, **k):
        calls.append(1)
        return original(*a, **k)

    monkeypatch.setattr(native, "ligand_sites_view", count)
    explorer = protein().explore()
    if first == "human":
        human = explorer.view(TOPIC)
        original_explanation = explorer.access.explain(human.items()[0].item_ref)
        assert original_explanation.count > 0
    else:
        selected = explorer.access.select(TOPIC)
    assert len(calls) == 1
    monkeypatch.setattr(native, "ligand_sites_view", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    selected = explorer.access.select(TOPIC)
    human = explorer.view(TOPIC)
    assert selected.result_ref == human.result_ref
    page = selected.page()
    record = page["items"][0]
    assert record["item_ref"] == human.items()[0].item_ref
    assert (
        record["cells"]["site_class"]["value"]
        == human.native_payload["items"][0]["site_class"]
    )
    assert page["context"]["adapter"] == "ligand_site_exploration@1"
    explanation = explorer.access.explain(record["item_ref"])
    assert (
        explorer.access._resolve(explanation._target["location"])[0]
        == human.items()[0].explain().native_payload
    )
    assert len(calls) == 1


def test_exact_typed_filters_membership_order_and_display_exclusions():
    explorer = protein().explore()
    full = explorer.access.select(TOPIC)
    member = items(full)[0]["item_ref"]
    selected = explorer.access.select(
        TOPIC,
        fields=["site_class"],
        where={"comparison_status": "computed"},
        item_refs=[member],
        order_by={"column": "ligand_ref", "descending": True},
    )
    assert items(selected)[0]["item_ref"] == member
    assert set(items(selected)[0]["cells"]) == {"site_class"}
    assert explorer.access.selection(selected.selection_ref) is selected
    empty = explorer.access.select(
        TOPIC, fields=[], where={"comparison_status": "COMPUTED"}
    )
    assert empty.count == 0 and empty.result_ref == full.result_ref
    assert empty.page()["outcome"] == full.page()["outcome"]
    request = explorer.access._resolve(empty._context_location)[0]["request"]
    assert request["selection"]["format"] == "ligand_site_access_selection@1"
    assert request["selection"]["underlying_count"] == 1
    assert len(request["selection"]["display_exclusions"]) == 1
    with pytest.raises(ArgumentError, match="outside"):
        explorer.access.select(TOPIC, item_refs=["XI_" + "0" * 64])


@pytest.mark.parametrize(
    "query",
    [
        {"where": {"ligand_ref": 1}},
        {"where": {"ligand_ref": True}},
        {"where": {"site_class": None}},
        {"where": {"missing": "x"}},
        {"where": {"ligand_ref": "\ud800"}},
        {"fields": ["ligand_ref", "ligand_ref"]},
        {"fields": [False]},
        {"options": {"region": [1, 2]}},
        {"options": []},
        {"item_refs": "XI_" + "0" * 64},
        {"order_by": {"column": "ligand_ref", "descending": 1}},
        {"order_by": {"column": "ligand_ref", "unit": "angstrom"}},
    ],
)
def test_invalid_requests_rejected_before_science_even_without_digestion(
    query, monkeypatch
):
    access = protein().access()
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.ligand_sites"),
        "ligand_sites_view",
        forbidden,
    )
    with pytest.raises(ArgumentError):
        access.select(TOPIC, **query, skip_digestion=True)


@pytest.mark.parametrize(
    "kwargs,status",
    [
        ({}, "computed"),
        ({"molecule": "P52270-2"}, "not_computed"),
        ({"annotation": False}, "not_computed"),
    ],
)
def test_zero_projection_cannot_erase_comparison_scope_or_original_support(
    kwargs, status
):
    explorer = protein(**kwargs).explore()
    selected = explorer.access.select(TOPIC, fields=[])
    item = items(selected)[0]
    assert item["cells"] == {}
    assert item["interpretation"]["comparison"]["status"] == status
    assert "not a count of ligand" in item["interpretation"]["scope"]
    assert (
        "not independently identified physical sites"
        in item["interpretation"]["annotation_count_semantics"]
    )
    support = explorer.access._resolve(item["support_location"])[0]
    assert support == explorer.view(TOPIC).items()[0].support[0]
    assert item["support"]["source_assertions"] == support["source_assertions"]
    assert item["subject_ref"] == "uniprot:P52270"
    assert (
        explorer.access._resolve(item["interpretation_location"])[0]
        == item["interpretation"]
    )


def test_large_atomic_comparison_is_deferred_without_changing_complete_native_scope():
    card = protein()
    node = card.get("features_positional.active_site")
    for i in range(40):
        row = deepcopy(node["value"][0])
        row["description"] = f"Explicit synthetic annotation {i} · " + "🧬" * 400
        node["value"].append(row)
    explorer = card.explore()
    selected = explorer.access.select(TOPIC)
    page = selected.page(max_bytes=4096)
    assert len(canonical_json(page).encode("utf-8")) <= 4096
    record = page["items"][0]
    assert not record["value_included"] and record["inspection_required"]
    assert "interpretation" not in record
    assert "support" not in record
    assert not page["page"]["values_complete"]
    assert all(
        not cell["value_included"] and "value" not in cell
        for cell in record["cells"].values()
    )
    exact = explorer.access._resolve(record["interpretation_location"])[0]
    assert exact["comparison"]["status"] == "partial"
    assert len(exact["comparison"]["compared_annotation_indices"]) == 1
    assert len(exact["comparison"]["uncomputed_annotation_indices"]) == 40
    full = selected.page(max_bytes=1048576)
    assert full["items"][0]["interpretation"] == exact


def test_catalog_is_lazy_and_unverified_new_science_still_cannot_save(
    tmp_path, monkeypatch
):
    explorer = protein().explore()
    native = importlib.import_module("sabueso.core.ligand_sites")
    with monkeypatch.context() as guard:
        guard.setattr(native, "ligand_sites_view", forbidden)
        catalog = explorer.access.catalog()
        descriptor = next(
            entry.value for entry in catalog._entries if entry.key == TOPIC
        )
        assert descriptor["default_fields"] == [
            "ligand_ref",
            "comparison_status",
            "site_class",
        ]
        assert TOPIC in explorer.access.capabilities["scientific_topics"]
    selection = explorer.access.select(TOPIC)
    assert not selection.capabilities["save"]
    with pytest.raises(StorageError):
        selection.save(tmp_path / "unsupported.json")
    assert not (tmp_path / "unsupported.json").exists()
    sources_path = tmp_path / "supported-sources.json"
    explorer.view("sources").save(sources_path)
    assert sources_path.is_file()


def test_literal_only_saved_session_advertises_not_saved_without_running_adapter(
    tmp_path, monkeypatch
):
    explorer = protein().explore()
    path = tmp_path / "sources.json"
    explorer.view("sources").save(path)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.ligand_sites"),
        "ligand_sites_view",
        forbidden,
    )
    import sabueso

    saved = sabueso.read_exploration(path)
    assert TOPIC in saved.explorer.access.capabilities["not_saved_topics"]
    descriptor = next(
        entry.value
        for entry in saved.explorer.access.catalog()._entries
        if entry.key == TOPIC
    )
    assert descriptor["availability"] == "not_saved"
    missing = saved.explorer.access.select(TOPIC)
    assert missing.page()["outcome"]["status"] == "not_saved"


def test_public_historical_card_human_machine_filters_pages_and_cursor_isolation(
    monkeypatch,
):
    card = Card.from_dict(
        json.loads(Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text())
    )
    expected = card.ligand_sites()
    explorer = card.explore()
    human = explorer.view(TOPIC)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.ligand_sites"),
        "ligand_sites_view",
        forbidden,
    )
    monkeypatch.setattr(Card, "from_dict", forbidden)
    selected = explorer.access.select(
        TOPIC,
        fields=["ligand_ref"],
        order_by={"column": "ligand_ref", "descending": True},
    )
    records = items(selected, limit=1, max_bytes=8192)
    assert len(records) == len(expected["items"]) > 1
    assert [row["item_ref"] for row in records] == [
        row.item_ref for row in human.sort("ligand_ref", descending=True).items()
    ]
    first = selected.page(limit=1, max_bytes=8192)
    cursor = first["page"]["next_cursor"]
    assert cursor is not None
    assert selected.page(cursor=cursor, limit=1, max_bytes=8192) == selected.page(
        cursor=cursor, limit=1, max_bytes=8192
    )
    other = explorer.access.select(TOPIC, fields=[])
    with pytest.raises(ArgumentError):
        other.page(cursor=cursor)
    row = human.items()[0]
    restricted = explorer.access.select(
        TOPIC,
        where={"ligand_ref": row.cells["ligand_ref"].value},
        item_refs=[row.item_ref],
    )
    assert [item["item_ref"] for item in items(restricted)] == [row.item_ref]
    assert human.native_payload == expected


def test_empty_membership_and_mutated_caller_inputs_do_not_change_retained_request():
    explorer = protein().explore()
    where = {"comparison_status": "computed"}
    selected = explorer.access.select(TOPIC, where=where)
    where["comparison_status"] = "not_computed"
    assert selected.count == 1
    assert (
        explorer.access.select(TOPIC, where={"comparison_status": "computed"})
        is selected
    )
    page = selected.page()
    page["items"][0]["interpretation"].clear()
    page["items"][0]["cells"]["site_class"]["value"] = "mutated"
    assert (
        selected.page()["items"][0]["interpretation"]["comparison"]["status"]
        == "computed"
    )
    assert (
        selected.page()["items"][0]["cells"]["site_class"]["value"]
        == "overlaps_annotated_site"
    )
    empty = explorer.access.select(TOPIC, item_refs=[])
    assert empty.count == 0 and empty.page()["outcome"]["status"] == "ok"
    location = empty.page()["context"]["context_location"]
    spec = explorer.access._resolve(location)[0]["request"]["selection"]
    assert spec["selected_count"] == 0 and spec["underlying_count"] == 1


@pytest.mark.parametrize(
    "nature,pinned,status",
    [
        ("protein", False, "missing_prerequisite"),
        ("small_molecule", False, "not_applicable"),
        ("protein", True, "empty"),
    ],
)
def test_missing_identity_nonprotein_and_no_declarations_have_distinct_outcomes(
    nature, pinned, status
):
    card = protein() if pinned else Card(meta={"entity_type": nature})
    if pinned:
        from sabueso.core.relationship_store import RelationshipStore

        card.relationship_store = RelationshipStore()
    selected = card.access().select(TOPIC)
    assert selected.count == 0
    assert selected.page()["outcome"]["status"] == status
