"""One shared native knowledge result for LIVE human and compact-agent use."""

import pytest
from test_card_knowledge_diff_v2_offline import (
    annotation,
    card,
    stated,
)
from test_card_knowledge_diff_v2_offline import (
    offline as offline,
)
from test_card_knowledge_diff_v2_offline import (
    public_cards as public_cards,
)

import sabueso
from sabueso.core import card_knowledge_diff_v2 as native
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.core.snapshot import canonical_json

ADAPTER = "protein_knowledge_comparison_exploration@1"


def pair():
    left, right = card(), card("RIGHT")
    stated(left, "annotations.taxon_id", 0)
    stated(right, "annotations.taxon_id", False)
    return left, right


def options(explorer, mapping=None):
    return {
        "mode": "knowledge",
        "other_ref": explorer.context["inputs"][1],
        "residue_map": mapping,
    }


def question(explorer, mapping=None):
    return explorer.answer("knowledge_differences", options=options(explorer, mapping))


@pytest.mark.parametrize("first", ["human", "agent"])
def test_human_agent_share_one_exact_native_execution(first, monkeypatch):
    left, right = pair()
    expected = left.compare_knowledge(right, comparison_rule="card_knowledge_diff@2")
    before = [c.to_dict() for c in (left, right)]
    explorer = left.explore(related_cards=[right])
    calls = []
    original = native.compare

    def observed(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Captured comparison must not reconstruct or call a live Card"
        )

    monkeypatch.setattr(native, "compare", observed)
    monkeypatch.setattr(Card, "__init__", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(Card, "compare_knowledge", forbidden)
    if first == "human":
        human = question(explorer)
        machine = explorer.access.select(
            "comparative_context", options=options(explorer)
        )
    else:
        machine = explorer.access.select(
            "comparative_context", options=options(explorer)
        )
        human = question(explorer)
    assert canonical_json(human.native_payload) == canonical_json(expected)
    assert human.result_ref == machine.result_ref
    assert human._selection._scientific is machine._scientific
    assert calls == [1]
    assert [c.to_dict() for c in (left, right)] == before
    frames = machine.page(max_bytes=65536)["items"]
    assert frames and all(f["adapter"] == ADAPTER for f in frames)


def test_visible_typed_values_and_complete_original_source_routes():
    left, right = pair()
    explorer = left.explore(related_cards=[right])
    view = question(explorer)
    row = next(i for i in view.items() if i.label == "annotations.taxon_id")
    assert row.cells["state"].value == "differs"
    opened = row.open()
    assert opened.native_payload["self"] == 0
    assert opened.native_payload["other"] is False
    assert opened.back() is view
    assert "0" in str(view) and "False" in str(view)
    assert "card_knowledge_diff@2" in str(view)
    explanation = row.explain()
    assert explanation.back() is view
    assert explanation.native_payload["original_native"]["other"] is False
    links = row.related()
    source = next(
        i
        for i in links.items()
        if i._entry.value["role"] == "source"
        and i._entry.value["candidates"][0]["capture"] == explorer.context["inputs"][1]
    )
    destination = source.open()
    assert destination.explorer.context["card_ref"] == explorer.context["inputs"][1]
    assert destination.request == view.request
    assert destination.back() is links


def test_field_filters_and_order_preserve_the_shared_native_result():
    left, right = pair()
    explorer = left.explore(related_cards=[right])
    view = question(explorer)
    filtered = view.filter("state", equals="differs")
    assert all(i.cells["state"].value == "differs" for i in filtered.items())
    ordered = filtered.sort("label", descending=True)
    assert [i.label for i in ordered.items()] == sorted(
        [i.label for i in filtered.items()], reverse=True
    )
    assert (
        ordered.result_ref == view.result_ref
        and ordered.native_payload == view.native_payload
    )
    selection = explorer.access.select(
        "comparative_context",
        options=options(explorer),
        fields=["label", "state"],
        where={"label": "annotations.taxon_id"},
    )
    (frame,) = selection.page(max_bytes=65536)["items"]
    assert frame["cells"]["state"]["value"] == "differs"
    assert frame["interpretation"]["native_rule"] == "card_knowledge_diff@2"


@pytest.mark.parametrize("mapping", [None, [], [[1, 2], [2, 3]], {1: 2, 2: 3}])
def test_supplied_mapping_and_unavailable_scope_are_original(mapping):
    left, right = card(sequence="MA"), card("RIGHT", "AMA")
    stated(left, "features_positional.active_site", [annotation()])
    stated(right, "features_positional.active_site", [annotation("RIGHT", 2)])
    explorer = left.explore(related_cards=[right])
    view = question(explorer, mapping)
    field = view.native_payload["fields"]["features_positional.active_site"]
    if mapping is None:
        assert field["status"] == "not_compared"
    elif not mapping:
        assert field["status"] == "partial"
    else:
        assert field["status"] == "same"
        assert view.request["options"]["residue_map"] == [[1, 2], [2, 3]]
        assert view.native_payload["residue_map"]["pairs"] == [[1, 2], [2, 3]]
    assert not view.native_payload["residue_map"]["alignment_performed"]
    map_item = next(i for i in view.items() if i.kind == "supplied_residue_map")
    assert map_item.cells["support_state"].value == (
        "not_supplied" if mapping is None else "caller_supplied"
    )


@pytest.mark.parametrize(
    "mapping",
    [[[1, 1], [1, 2]], [[1, 1], [2, 1]], [[True, 1]], [[1, 0]], {"1": 1}, "alignment"],
)
def test_invalid_mapping_is_refused_before_native_execution(monkeypatch, mapping):
    left, right = pair()
    explorer = left.explore(related_cards=[right])
    monkeypatch.setattr(
        native,
        "compare",
        lambda *a, **k: pytest.fail("Invalid request reached science"),
    )
    with pytest.raises(ArgumentError):
        question(explorer, mapping)


@pytest.mark.parametrize("ref", [None, "P60174", "uniprot:RIGHT", "not-a-capture"])
def test_unknown_or_implicit_capture_is_refused(ref, monkeypatch):
    left, right = pair()
    explorer = left.explore(related_cards=[right])
    monkeypatch.setattr(
        native,
        "compare",
        lambda *a, **k: pytest.fail("Invalid capture reached science"),
    )
    with pytest.raises(ArgumentError):
        explorer.answer("knowledge_differences", options={"other_ref": ref})


def test_sources_conflicts_and_unqueried_states_are_inspectable():
    left, right = pair()
    left.quality["conflicts"] = [
        {"field": "annotations.taxon_id", "reason": "literal source conflict"}
    ]
    view = question(left.explore(related_cards=[right]))
    row = next(i for i in view.items() if i.label == "annotations.taxon_id")
    assert (
        row.open().native_payload["support"]["self"]["quality_conflicts"]
        == left.quality["conflicts"]
    )
    assert row.explain().native_payload["input_scope"]["source_assertions"]
    assert "source claim" in row.explain().native_payload["input_scope"]["basis"]


def test_save_retains_all_observed_new_context_with_independent_binding(tmp_path):
    left, right = pair()
    explorer = left.explore(related_cards=[right])
    view = question(explorer)
    item = next(i for i in view.items() if i.label == "annotations.taxon_id")
    selection = explorer.access.select("comparative_context", options=options(explorer))
    for index, target in enumerate(
        (
            view,
            item.open(),
            item.explain(),
            item.related(),
            explorer.topics(),
            selection,
        )
    ):
        path = tmp_path / f"retained-{index}.json"
        assert target.capabilities["save"] is True
        target.save(path)
        saved = sabueso.read_exploration(path)
        assert (
            saved.validation["verifier"] == "knowledge_comparison_exploration_binding@1"
        )
        assert canonical_json(saved.native_payload) == canonical_json(
            target._scientific.native if target is selection else target.native_payload
        )
    fresh = left.explore().inspect()
    path = tmp_path / "fresh.json"
    fresh.save(path)
    assert sabueso.read_exploration(path).capabilities["save"]


def test_atomic_compact_deferral_does_not_leak_partial_support():
    left, right = pair()
    stated(left, "annotations.literal", "x" * 20000)
    stated(right, "annotations.literal", "y" * 20000)
    explorer = left.explore(related_cards=[right])
    selection = explorer.access.select(
        "comparative_context",
        options=options(explorer),
        where={"label": "annotations.literal"},
    )
    page = selection.page(max_bytes=16000)
    (frame,) = page["items"]
    assert frame["value_included"] is False and frame["inspection_required"]
    assert "support" not in frame and "interpretation" not in frame
    assert all(
        c["value_included"] is False and "value" not in c
        for c in frame["cells"].values()
    )
    assert page["outcome"]["status"] == "ok"
    assert len(canonical_json(page).encode("utf-8")) <= 16000


def test_old_relationship_and_sequence_modes_still_have_their_own_capability(tmp_path):
    left, right = pair()
    explorer = left.explore(related_cards=[right])
    view = explorer.answer("related_proteins")
    assert view.context["adapter"] == "protein_context_exploration@1"
    assert view.capabilities["save"]
    path = tmp_path / "existing.json"
    view.save(path)
    saved = sabueso.read_exploration(path)
    assert saved.validation["verifier"] == "protein_context_exploration_binding@1"
    with pytest.raises(ArgumentError):
        saved.explorer.answer(
            "knowledge_differences",
            options={"other_ref": explorer.context["inputs"][1]},
        )


def test_public_tim_native_output_and_quantity_source_bindings_remain_exact(
    public_cards,
):
    left, right = public_cards
    mapping = {12: 12, 14: 14, 96: 96, 168: 166}
    expected = left.compare_knowledge(
        right, residue_map=mapping, comparison_rule="card_knowledge_diff@2"
    )
    explorer = left.explore(related_cards=[right])
    actual = question(explorer, mapping)
    assert canonical_json(actual.native_payload) == canonical_json(expected)
    assert "Knowledge" in actual.title
    assert "supplied" in str(actual)


def test_public_tim_comparison_saves_with_default_production_budgets(
    public_cards, tmp_path
):
    left, right = public_cards
    explorer = left.explore(related_cards=[right])
    view = question(explorer)
    machine = explorer.access.select("comparative_context", options=options(explorer))
    path = tmp_path / "public-comparison.json.gz"
    view.save(path, compression="gzip")
    saved = sabueso.read_exploration(path)
    assert canonical_json(saved.native_payload) == canonical_json(view.native_payload)
    assert (
        saved.explorer.access.select(
            "comparative_context", options=options(saved.explorer)
        ).selection_ref
        == machine.selection_ref
    )


def test_knowledge_mode_cannot_replace_an_association_question(monkeypatch):
    left, right = pair()
    explorer = left.explore(related_cards=[right])
    monkeypatch.setattr(
        native, "compare", lambda *a, **k: pytest.fail("Wrong topic reached comparison")
    )
    with pytest.raises(ArgumentError):
        explorer.answer("protein_associations", options=options(explorer))


def test_equal_rendered_state_labels_keep_distinct_native_occurrences():
    from sabueso.core.source_assertion_store import make_source_assertion

    left, right = card(), card("RIGHT")
    for path, source in (("annotations.a · b", "c"), ("annotations.a", "b · c")):
        assertion = make_source_assertion(
            path,
            "original",
            source,
            "public synthetic",
            "time",
            subject_ref="uniprot:LEFT",
        )
        left.source_assertion_store.add(assertion)
        left.set(path, "original", [assertion["id"]])
    view = question(left.explore(related_cards=[right]))
    states = [item for item in view.items() if item.kind == "knowledge_state"]
    assert len(states) == 2 and states[0].label == states[1].label
    assert states[0].item_ref != states[1].item_ref
    assert {item.open().native_payload["area"] for item in states} == {
        "annotations.a · b",
        "annotations.a",
    }


def test_unselected_field_assertion_keeps_its_exact_source_destination():
    from sabueso.core.source_assertion_store import make_source_assertion

    left, right = pair()
    alternative = make_source_assertion(
        "annotations.taxon_id",
        "an alternative",
        "synthetic alternative",
        "record",
        "time",
        subject_ref="uniprot:LEFT",
    )
    left.source_assertion_store.add(alternative)
    view = question(left.explore(related_cards=[right]))
    item = next(i for i in view.items() if i.label == "annotations.taxon_id")
    links = item.related()
    source = next(
        i
        for i in links.items()
        if i._entry.value.get("role") == "source" and alternative["id"] in i.label
    )
    opened = source.open()
    assert opened.native_payload["asserted_value"] == "an alternative"
    assert opened.request == view.request and opened.back() is links


def test_old_saved_reading_does_not_capture_a_temporary_forbidden_native_alias(
    monkeypatch, tmp_path
):
    left, right = pair()
    old = left.explore(related_cards=[right]).answer("related_proteins")
    path = tmp_path / "old.json"
    old.save(path)
    with monkeypatch.context() as guard:
        guard.setattr(
            native,
            "compare",
            lambda *a, **k: pytest.fail(
                "Historical receiving ran current native comparison"
            ),
        )
        assert sabueso.read_exploration(path).native_payload == old.native_payload
    assert (
        question(left.explore(related_cards=[right])).native_payload["rule"]["rule"]
        == "card_knowledge_diff@2"
    )


def test_long_literal_scope_labels_are_bounded_and_html_escaped():
    left, right = pair()
    path = "annotations.<script>" + "x" * 5000 + "</script>"
    stated(left, path, "original self")
    stated(right, path, "original other")
    view = question(left.explore(related_cards=[right]))
    item = next(i for i in view.items() if i.label == path)
    assert item.open().native_payload["self"] == "original self"
    assert len(str(view)) < 12000
    html = view._repr_html_()
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_observed_new_question_catalog_advertises_its_actual_saving_boundary(tmp_path):
    left, right = pair()
    explorer = left.explore(related_cards=[right])
    menu = explorer.questions()
    related = explorer.answer("related_proteins")
    for index, target in enumerate((menu, related, related.items()[0].open())):
        assert target.capabilities["save"] is True
        path = tmp_path / f"new-menu-{index}.json"
        target.save(path)
        saved = sabueso.read_exploration(path)
        assert (
            saved.validation["verifier"] == "knowledge_comparison_exploration_binding@1"
        )
        assert "knowledge_differences" in saved.explorer._questions
        assert (
            saved.explorer.answer(
                "knowledge_differences", options=options(saved.explorer)
            ).outcome["status"]
            == "not_saved"
        )
    exported = tmp_path / "captured-card.json"
    explorer.access.export_card(exported)
    assert exported.exists()
    fresh = left.explore(related_cards=[right]).answer("related_proteins")
    assert fresh.capabilities["save"] is True
    fresh.save(tmp_path / "existing-mode.json")


def test_uncited_alternatives_do_not_become_selected_field_support():
    left, right = pair()
    left.get("annotations.taxon_id")["source_assertion_ids"] = []
    view = question(left.explore(related_cards=[right]))
    item = next(i for i in view.items() if i.label == "annotations.taxon_id")
    assert item.cells["support_state"].value == "partial"
    scope = item.open().native_payload["support"]["self"]
    assert not scope["selected_source_assertions"] and scope["other_field_assertions"]
