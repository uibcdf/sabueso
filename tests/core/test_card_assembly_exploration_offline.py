"""Shared human/agent assembly navigation; modified inputs are synthetic."""

import gzip
import importlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

TOPIC = "assembly_generation"
OPTIONS = {"structure_ref": "pdb:2V5B"}


def forbidden(*a, **k):
    raise AssertionError("No acquisition, caller recapture or repeated science")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def originals():
    out = {}
    for pdb, acc in [("1SUX", "P52270"), ("2V5B", "P52270"), ("1HTI", "P60174")]:
        card, _ = sabueso.resolve(
            acc,
            resolver=EntityResolver(
                FixtureUniProtClient("temp_data"),
                rcsb_client=FixtureRCSBClient("temp_data/rcsb_assembly_generation"),
            ),
            structures=[pdb],
        )
        out[pdb] = card.to_dict()
    return out


@pytest.fixture
def card(originals):
    return Card.from_dict(deepcopy(originals["2V5B"]))


def source(card):
    return next(
        s
        for s in card.source_assertion_store.store.values()
        if s.get("source", {}).get("name") == "RCSB PDB"
    )


def generator(card):
    return source(card)["asserted_value"]["assembly_generation_inputs"]["assemblies"][
        0
    ]["pdbx_struct_assembly_gen"][0]


@pytest.mark.parametrize("first", ["human", "agent"])
def test_one_capture_and_native_result_shared_across_entry_orders(
    card, monkeypatch, first
):
    expected = card.assembly_generation(**OPTIONS)
    explorer = card.explore()
    backend = importlib.import_module("sabueso.core.assembly_generation_v4")
    original = backend.generation
    calls = []

    def spy(*a, **k):
        calls.append(1)
        return original(*a, **k)

    monkeypatch.setattr(backend, "generation", spy)
    monkeypatch.setattr(card, "to_dict", forbidden)
    generator(card)["oper_expression"] = "SYNTHETIC-CHANGE-AFTER-CAPTURE"
    if first == "human":
        view = explorer.answer(TOPIC, options=OPTIONS)
        selection = explorer.access.select(TOPIC, options=OPTIONS)
    else:
        selection = explorer.access.select(TOPIC, options=OPTIONS)
        view = explorer.answer(TOPIC, options=OPTIONS)
    assert calls == [1]
    assert view.native_payload == expected
    assert (
        view.result_ref
        == selection.result_ref
        == explorer.view(TOPIC, options=OPTIONS).result_ref
    )
    assert view.request["options"] == view.context["options"]
    assert [i.cells["declaration_count"].value for i in view.items()] == [4, 2]
    assert view.capabilities["save"] and selection.capabilities["save"]
    assert view.capabilities["scientific_adapter"]


@pytest.mark.parametrize(
    "pdb,counts", [("1SUX", [12]), ("2V5B", [4, 2]), ("1HTI", [3])]
)
def test_public_controls_have_readable_scoped_text_and_html(originals, pdb, counts):
    card = Card.from_dict(deepcopy(originals[pdb]))
    before = card.to_dict()
    explorer = card.explore()
    view = explorer.answer(TOPIC, options={"structure_ref": f"pdb:{pdb}"})
    assert [i.cells["declaration_count"].value for i in view.items()] == counts
    text, html = str(view), view._repr_html_()
    assert "Declared combinations" in text and "distinct physical molecules" in text
    assert "Assembly components and operations" in html and "Keys matched" in html
    assert "Inventory sequence coverage" not in text
    assert TOPIC in explorer.capabilities["topics"]
    assert TOPIC in explorer.questions().native_payload
    assert card.to_dict() == before


def test_open_explain_and_related_preserve_exact_support_and_return(card):
    explorer = card.explore()
    view = explorer.answer(TOPIC, options=OPTIONS)
    item = view.items()[0]
    detail = item.open()
    assert detail.back() is view and detail.native_payload == item._entry.value["item"]
    assert "Original operation expression: 1,2" in str(detail)
    assert "A: Keys matched" in str(detail) and "B: Keys unresolved" in str(detail)
    assert item.support[0]["source_assertions"][0]["id"] == source(card)["id"]
    assert (
        "rcsb_assembly_generation@4"
        in item.cells["declaration_count"].support[0]["rule_names"]
    )
    explanation = item.explain()
    assert (
        explanation.back() is view
        and explanation.native_payload["request"] == view.context["options"]
    )
    for key in [
        "original_input_location",
        "source_context_location",
        "source_request_context_location",
        "native_result_location",
    ]:
        assert explorer.access.read(explanation.native_payload[key]).page(
            max_bytes=8192
        )["page"]
    links = item.related()
    assert links.back() is view and len(links.items()) >= 5
    for link in links.items():
        target = link.open()
        assert target.back() is links and target.native_payload is not None


def test_human_filter_and_agent_typed_membership_share_exact_rows(card):
    explorer = card.explore()
    view = explorer.view(TOPIC, options=OPTIONS)
    human = view.filter("declaration_count", equals=4)
    machine = explorer.access.select(
        TOPIC,
        options=OPTIONS,
        fields=["declaration_count"],
        where={"declaration_count": 4},
    )
    page = machine.page(max_bytes=8192)
    assert len(human.items()) == machine.count == 1
    assert page["items"][0]["item_ref"] == human.items()[0].item_ref
    assert (
        page["items"][0]["interpretation"]["count_basis"]
        == "source_declaration_positions_not_distinct_molecules"
    )
    assert page["items"][0]["interpretation"]["physical_membership"] == "not_computed"
    ordered = explorer.access.select(
        TOPIC,
        options=OPTIONS,
        order_by={"column": "declaration_count", "descending": True},
    )
    assert [e.value["declaration_count"] for e in ordered._entries] == [4, 2]
    member = explorer.access.select(
        TOPIC, options=OPTIONS, item_refs=[view.items()[1].item_ref]
    )
    assert member.count == 1
    assert explorer.access.explain(view.items()[0].item_ref).page(max_bytes=8192)[
        "page"
    ]


def test_projection_cannot_remove_mandatory_scope_or_source_membership(card):
    selection = card.explore().access.select(TOPIC, options=OPTIONS, fields=[])
    item = selection.page(max_bytes=8192)["items"][0]
    assert item["cells"] == {} and item["interpretation"]["rule_names"]
    assert (
        item["support"]["source_assertions"]
        and item["support"]["source_reference_state"] == "retained"
    )


def test_factored_count_is_not_an_unknown_or_zero_scalar(card):
    generator(card)["oper_expression"] = "1-100000000000000000000"
    explorer = card.explore()
    view = explorer.view(TOPIC, options=OPTIONS)
    first = view.items()[0]
    assert (
        first.cells["declaration_count"].state == "factored"
        and first.cells["declaration_count"].value is None
    )
    assert "Exact count retained as factors" in str(view)
    frame = explorer.access.select(
        TOPIC,
        options=OPTIONS,
        fields=["declaration_count"],
        where={"count_state": "factored"},
    ).page(max_bytes=8192)["items"][0]
    assert frame["cells"]["declaration_count"]["state"] == "factored"
    assert explorer.access.read(frame["interpretation"]["exact_factors_location"]).page(
        max_bytes=8192
    )["page"]
    assert len(view.filter("declaration_count", equals=None).items()) == 1
    assert (
        view.sort("declaration_count", descending=True)
        .items()[-1]
        .cells["count_state"]
        .value
        == "factored"
    )


def test_small_pages_defer_values_support_and_interpretation_atomically(card):
    raw = source(card)["asserted_value"]["assembly_generation_inputs"]["assemblies"][0]
    raw["rcsb_assembly_container_identifiers"]["assembly_id"] = "SYNTHETIC" * 500
    raw["pdbx_struct_assembly_gen"][0]["assembly_id"] = raw[
        "rcsb_assembly_container_identifiers"
    ]["assembly_id"]
    explorer = card.explore()
    selection = explorer.access.select(TOPIC, options=OPTIONS, fields=["label"])
    page = selection.page(max_bytes=4096, limit=1)
    assert (
        len(
            json.dumps(
                page, ensure_ascii=False, separators=(",", ":"), sort_keys=True
            ).encode()
        )
        <= 4096
    )
    frame = page["items"][0]
    assert not frame["value_included"] and frame["inspection_required"]
    assert (
        "interpretation" not in frame
        and "support" not in frame
        and "value" not in frame["cells"]["label"]
    )
    assert explorer.access.read(frame["interpretation_location"]).page(max_bytes=8192)[
        "page"
    ]
    assert selection.page(max_bytes=4096, limit=1) == page


@pytest.mark.parametrize(
    "options",
    [
        {"operation_budget": True},
        {"operation_budget": 0},
        {"expand_occurrences": 1},
        {"expand_operations": None},
        {"relationship_id": "R_X"},
        {"structure_ref": "2V5B"},
        {"generation_rule": "rcsb_assembly_generation@3"},
    ],
)
def test_options_are_validated_before_materialization_even_on_empty_cards(
    monkeypatch, options
):
    backend = importlib.import_module("sabueso.core.card_assembly_exploration")
    monkeypatch.setattr(backend, "_materialize", forbidden)
    card = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:P52270"}
    )
    with pytest.raises(ArgumentError):
        card.explore().access.select(TOPIC, options=options)


@pytest.mark.parametrize(
    "query",
    [
        {"where": {"declaration_count": True}},
        {"where": {"declaration_count": 2.0}},
        {"where": {"status": None}},
        {"fields": ["unknown"]},
        {"order_by": {"column": "declaration_count", "unit": "angstrom"}},
        {"where": {"unknown": "x"}},
    ],
)
def test_display_queries_are_validated_before_scientific_work(card, monkeypatch, query):
    backend = importlib.import_module("sabueso.core.card_assembly_exploration")
    monkeypatch.setattr(backend, "_materialize", forbidden)
    with pytest.raises(ArgumentError):
        card.explore().access.select(TOPIC, **query)


@pytest.mark.parametrize("limit", [1000, None])
def test_explicit_expansion_options_are_shared_and_retained(card, limit):
    explorer = card.explore()
    options = {**OPTIONS, "operation_budget": limit, "expand_occurrences": True}
    view = explorer.answer(TOPIC, options=options)
    assert view.native_payload["expanded_occurrence_count"] == 6
    assert view.request["options"]["expand_occurrences"] is True
    assert view.result_ref == explorer.access.select(TOPIC, options=options).result_ref


def test_source_gaps_and_missing_statements_are_visible_without_backfill(card):
    missing = source(card)["id"]
    card.source_assertion_store.store.pop(missing)
    explorer = card.explore()
    view = explorer.view(TOPIC, options=OPTIONS)
    assert view.items() and all(
        i.cells["declaration_count"].value is None for i in view.items()
    )
    assert any(
        s["id"] == missing and s["state"] == "not_retained"
        for i in view.items()
        for basis in i.support
        for s in basis["source_assertions"]
    )
    assert any(
        link._entry.value["availability"] == "missing_prerequisite"
        for i in view.items()
        for link in i.related().items()
    )


def test_output_edits_cannot_change_the_capture_or_other_views(card):
    before = card.to_dict()
    explorer = card.explore()
    view = explorer.view(TOPIC, options=OPTIONS)
    native = view.native_payload
    native["sources"].clear()
    support = view.items()[0].support
    support[0]["source_assertions"].clear()
    cells = view.items()[0].cells["declaration_count"].to_dict()
    cells["support"].clear()
    frame = explorer.access.select(TOPIC, options=OPTIONS).page(max_bytes=8192)
    frame["items"][0]["interpretation"]["scope"] = "LOCAL"
    assert (
        view.native_payload["sources"]
        and view.items()[0].support[0]["source_assertions"]
    )
    assert card.to_dict() == before


def test_foreign_item_refs_are_not_rebound_to_equal_source_labels(card):
    explorer = card.explore()
    view = explorer.view(TOPIC, options=OPTIONS)
    other = explorer.access.select(TOPIC, options={**OPTIONS, "operation_budget": 1000})
    with pytest.raises(ArgumentError, match="outside"):
        explorer.access.select(
            TOPIC,
            options=OPTIONS,
            item_refs=[other.page(max_bytes=8192)["items"][0]["item_ref"]],
        )
    hidden = view.filter("declaration_count", equals=999)
    assert hidden.item(view.items()[0].item_ref).open().native_payload


def test_scientific_persistence_keeps_original_result_and_navigation(card, tmp_path):
    explorer = card.explore()
    view = explorer.view(TOPIC, options=OPTIONS)
    item = view.items()[0]
    paths = []
    for i, obj in enumerate(
        [
            view,
            item.open(),
            item.explain(),
            item.related(),
            explorer.access.select(TOPIC, options=OPTIONS),
            explorer.access.read(item.related()._selection._target["location"]),
        ]
    ):
        path = tmp_path / f"unsupported-{i}.json"
        paths.append(path)
        assert obj.capabilities["save"]
        receipt = obj.save(path)
        restored = sabueso.read_exploration(
            path, expected_digest=receipt["bundle_digest"]
        )
        expected = (
            obj.native_payload
            if hasattr(obj, "native_payload")
            else explorer.access._resolve(obj._target["location"])[0]
        )
        assert restored.native_payload == expected
    assert all(p.exists() for p in paths)
    path = tmp_path / "original-card.json"
    explorer.access.export_card(path)
    assert json.loads(path.read_text()) == explorer.access._focal.data


def test_unrelated_literal_saving_stays_available_in_the_same_session(card, tmp_path):
    explorer = card.explore()
    explorer.view(TOPIC, options=OPTIONS)
    literal = explorer.inspect(field_path="names.canonical_name")
    path = tmp_path / "literal.json"
    literal.save(path)
    assert sabueso.read_exploration(path).native_payload == literal.native_payload


def test_genuine_old_saved_reading_never_materializes_new_assembly_science(
    tmp_path, monkeypatch
):
    path = tmp_path / "original.json"
    path.write_bytes(
        gzip.decompress(
            (
                Path(__file__).parent / "data/card_exploration_quaternary_v1.json.gz"
            ).read_bytes()
        )
    )
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.assembly_generation_v4"),
        "generation",
        forbidden,
    )
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_assembly_exploration"),
        "_materialize",
        forbidden,
    )
    saved = sabueso.read_exploration(path)
    explorer = saved.explorer
    assert explorer.answer(TOPIC, options=OPTIONS).outcome["status"] == "not_saved"
    assert explorer.view(TOPIC, options=OPTIONS).outcome["status"] == "not_saved"
    assert (
        explorer.access.select(TOPIC, options=OPTIONS).page()["outcome"]["status"]
        == "not_saved"
    )


def test_nonprotein_topic_is_explicitly_not_applicable():
    card = Card(
        meta={
            "entity_type": "small_molecule",
            "card_id": "sabueso:small_molecule:pubchem:1",
        }
    )
    explorer = card.explore()
    view = explorer.view(TOPIC)
    assert view.outcome["status"] == "not_applicable" and not view.items()
    assert TOPIC not in explorer.capabilities["topics"]


def test_original_source_text_is_escaped_and_previewed_in_html(card):
    raw = source(card)["asserted_value"]["assembly_generation_inputs"]["assemblies"][0]
    text = "<script>alert('SYNTHETIC')</script>"
    raw["rcsb_assembly_container_identifiers"]["assembly_id"] = text
    raw["pdbx_struct_assembly_gen"][0]["assembly_id"] = text
    view = card.explore().view(TOPIC, options=OPTIONS)
    assert "<script>" not in view._repr_html_()
    assert "<script>" not in view.items()[0].open()._repr_html_()
    assert "&lt;script&gt;" in view._repr_html_()


def test_missing_capture_identity_is_not_a_zero_count(monkeypatch):
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.assembly_generation_v4"),
        "generation",
        forbidden,
    )
    view = Card(meta={"entity_type": "protein"}).explore().view(TOPIC)
    assert view.outcome["status"] == "missing_prerequisite" and not view.items()
