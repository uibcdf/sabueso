"""Actual disease transports, exact source navigation and resealed refusals."""

import json
from copy import deepcopy

import pytest
from test_card_disease_association_history_offline import (
    assert_saved_original,
    block_current,
    hydrate_original,
    original_navigation_ids,
)
from test_card_disease_association_original_offline import original as original

import sabueso
from sabueso.core import card_exploration_storage as storage
from sabueso.core.card_exploration_shared_values_v8 import pack, unpack
from sabueso.core.errors import StorageError


@pytest.fixture(scope="module")
def disease_file(original, tmp_path_factory):
    nodes, _ = hydrate_original(original, "support-missing")
    root = nodes[original.case("support-missing")["named_views"]["root"]]
    ids = original_navigation_ids(nodes)
    path = tmp_path_factory.mktemp("disease-original-file") / "original.json"
    with pytest.MonkeyPatch.context() as guard:
        block_current(guard)
        root.save(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    logical = (
        unpack(raw, limit=None, component_limit=None)[0]
        if raw["format"] == "sabueso.card_exploration@28"
        else {
            key: value
            for key, value in raw.items()
            if key not in ("digests", "bundle_digest")
        }
    )
    return path, logical, ids


def test_unchanged_resealed_disease_control_is_accepted(disease_file, monkeypatch):
    sealed = storage._seal(pack(disease_file[1], None, threshold=0, min_saving=0))
    block_current(monkeypatch)
    saved = storage._restore(
        sealed, sealed["bundle_digest"], max_logical_bytes=None, component_limit=None
    )
    assert saved.validation["verifier"] == "disease_association_exploration_binding@1"


@pytest.mark.parametrize(
    "mutation",
    (
        "identity",
        "source_role",
        "direction",
        "native_count",
        "coverage",
        "cell",
        "question",
        "request",
    ),
)
def test_resealed_disease_semantic_changes_are_refused(
    disease_file, monkeypatch, mutation
):
    logical = deepcopy(disease_file[1])
    ref = next(
        ref
        for ref in logical["scientific_results"]
        if logical["objects"][ref]["context"]["adapter"]
        == "disease_association_exploration@1"
    )
    wire = logical["objects"][ref]
    key = next(
        key
        for key, row in wire["rows"].items()
        if row["kind"] == "association_statement"
    )
    root = logical["views"][logical["root_navigation_ref"]]
    if mutation == "identity":
        wire["native_payload"]["identity"]["focal"] = "MONDO:OTHER"
    elif mutation == "source_role":
        wire["support"][key]["source_assertions"][0]["role"] = (
            "synthetic incorrect role"
        )
    elif mutation == "direction":
        wire["rows"][key]["subject_ref"], wire["rows"][key]["object_ref"] = (
            wire["rows"][key]["object_ref"],
            wire["rows"][key]["subject_ref"],
        )
    elif mutation == "native_count":
        wire["native_payload"]["matched_occurrences"] += 1
    elif mutation == "coverage":
        wire["coverage"]["contexts"][0]["matched_occurrences"] += 1
    elif mutation == "cell":
        cell = next(
            value
            for value in root["state"]["items"].values()
            if value["kind"] == "association_statement"
        )["cells"]["support_state"]
        cell["value"] = "retained"
    elif mutation == "question":
        root["flags"]["_request"] = {
            "question": "definition",
            "topic": "definition",
            "options": {},
        }
    else:
        machine = next(
            view for view in logical["views"].values() if view["flags"]["_machine_ref"]
        )
        machine["selection"]["fields"] = ["source", "source"]
    sealed = storage._seal(pack(logical, None, threshold=0, min_saving=0))
    block_current(monkeypatch)
    with pytest.raises(StorageError):
        storage._restore(
            sealed,
            sealed["bundle_digest"],
            max_logical_bytes=None,
            component_limit=None,
        )


@pytest.mark.parametrize("compression", ("none", "gzip", "zstd"))
def test_disease_transport_resave_and_exact_original_graph(
    disease_file, original, monkeypatch, tmp_path, compression
):
    block_current(monkeypatch)
    saved = sabueso.read_exploration(disease_file[0])
    target = tmp_path / (compression + ".json")
    saved.save(target, compression=compression)
    received = sabueso.read_exploration(target)
    assert (
        received.validation["verifier"] == "disease_association_exploration_binding@1"
    )
    assert_saved_original(received, original, "support-missing", disease_file[2])


def test_saved_disease_finite_requests_frozen_catalogs_and_new_source_reading(
    disease_file, monkeypatch
):
    from sabueso.core import card_exploration as human
    from sabueso.core import card_exploration_profiles as profiles

    block_current(monkeypatch)
    saved = sabueso.read_exploration(disease_file[0])
    monkeypatch.setattr(human, "_TOPICS", {})
    monkeypatch.setattr(profiles, "NATURE_TOPICS", {})
    monkeypatch.setattr(profiles, "QUESTIONS", {})
    monkeypatch.setattr(profiles, "COMMON_QUESTIONS", {})
    assert "associations" in saved.explorer.topics().native_payload
    assert "retained_associations" in saved.explorer.questions().native_payload
    assert (
        saved.explorer.answer("retained_associations").native_payload
        == saved.native_payload
    )
    missing = saved.explorer.access.select(
        "associations",
        where={"source": "a request never executed"},
        skip_digestion=True,
    )
    assert missing.count == 0 and missing.page()["outcome"]["status"] == "not_saved"
    parent = saved.explorer.answer("retained_associations").filter(
        "kind", equals="association_statement"
    )
    item = parent.items()[0]
    assert item.open().back() is parent and item.explain().back() is parent
    links = item.related()
    assert links.back() is parent
    for link in links.items():
        destination = link.open()
        assert destination.back() is links
        assert destination.request == parent.request
        if link._entry.value["candidates"]:
            assert destination.explorer.overview().back() is links
        else:
            assert destination.outcome["status"] == "missing_prerequisite"
            assert destination.explorer is None


def test_human_only_disease_save_does_not_invent_machine_requests(original, tmp_path):
    from sabueso.core.card import Card

    case = original.ref(original.case("ontology-only")["input"])
    explorer = Card.from_dict(case["focal"]).explore()
    root = explorer.answer("retained_associations")
    path = tmp_path / "human-only.json"
    root.save(path)
    saved = sabueso.read_exploration(path)
    assert (
        saved.explorer.answer("retained_associations").native_payload
        == root.native_payload
    )
    missing = saved.explorer.access.select("associations")
    assert missing.page()["outcome"]["status"] == "not_saved"


def test_machine_first_disease_save_does_not_invent_human_question(original, tmp_path):
    from sabueso.core.card import Card

    case = original.ref(original.case("ontology-only")["input"])
    access = Card.from_dict(case["focal"]).access()
    selection = access.select("associations")
    path = tmp_path / "machine-only.json"
    selection.save(path)
    saved = sabueso.read_exploration(path)
    assert (
        saved.explorer.access.select("associations").selection_ref
        == selection.selection_ref
    )
    assert (
        saved.explorer.answer("retained_associations").outcome["status"] == "not_saved"
    )


@pytest.mark.parametrize(
    "topics",
    (("clinical",), ("clinical", "classification"), ("clinical", "activity_context")),
)
def test_mixed_original_disease_and_supplied_molecule_views(original, tmp_path, topics):
    from sabueso.core.card import Card

    case = original.ref(original.case("public-molecule")["input"])
    disease = Card.from_dict(case["focal"])
    molecule = Card.from_dict(case["related"][0])
    root = disease.explore(related_cards=[molecule]).answer("retained_associations")
    row = next(item for item in root.items() if item.kind == "indication_statement")
    links = row.related()
    whole = next(
        item
        for item in links.items()
        if item._entry.value["role"] == "whole_card_context"
    ).open()
    explorer = whole.explorer
    questions = {
        "clinical": "clinical_context",
        "classification": "classification",
        "activity_context": "measured_targets",
    }
    expected = {}
    for topic in topics:
        view = explorer.answer(questions[topic])
        expected[topic] = deepcopy(view.native_payload)
        explorer.access.select(
            "chemical_classification" if topic == "classification" else topic
        )
    path = tmp_path / "mixed-disease.json"
    root.save(path)
    saved = sabueso.read_exploration(path)
    assert saved.validation["verifier"] == "disease_association_exploration_binding@1"
    retained = saved.explorer._session["original_nodes"].values()
    for topic, payload in expected.items():
        assert any(
            view._record_panel
            == ("chemical_classification" if topic == "classification" else topic)
            and view.native_payload == payload
            for view in retained
        )


def test_explicit_other_disease_focal_keeps_both_results_and_original_return(
    original, tmp_path
):
    from sabueso.core.card import Card

    data = original.ref(original.case("focal-outgoing")["input"])
    root = (
        Card.from_dict(data["focal"])
        .explore(related_cards=[Card.from_dict(row) for row in data["related"]])
        .answer("retained_associations")
    )
    peer_pin = next(
        capture.pin
        for capture in root.explorer.access._captures.values()
        if capture.data["meta"]["card_id"] == data["related"][0]["meta"]["card_id"]
    )
    context = next(
        item
        for item in root.items()
        if item.kind == "association_context"
        and item.cells["context_card_ref"].value == peer_pin
    )
    links = context.related()
    peer = next(
        item
        for item in links.items()
        if item._entry.value["role"] == "whole_card_context"
    ).open()
    other = peer.explorer.answer("retained_associations")
    assert other.context["card_ref"] != root.context["card_ref"]
    assert other.back() is links
    path = tmp_path / "two-diseases.json"
    root.save(path)
    saved = sabueso.read_exploration(path)
    results = [
        view
        for view in saved.explorer._session["original_nodes"].values()
        if view._record_panel == "associations"
    ]
    assert {view.context["card_ref"] for view in results} == {
        root.context["card_ref"],
        other.context["card_ref"],
    }
