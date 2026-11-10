"""Captured protein relationships and explicit sequence comparison journeys."""

import json
import socket
from pathlib import Path

import pytest

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.relationship_store import make_derivation, make_relationship
from sabueso.core.snapshot import canonical_json
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.uniprot import map_protein

DATA = Path(__file__).resolve().parents[2] / "temp_data"
if not (DATA / "P60174.json").exists():
    DATA = Path.cwd() / "temp_data"


def forbidden(*args, **kwargs):
    raise AssertionError(
        "Captured protein context must not acquire data or reconstruct Cards"
    )


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    from sabueso.tools.db import _http

    monkeypatch.setattr(_http, "_urlopen", forbidden)


def protein(accession="P60174", sequence="MAGR"):
    return build_card_from_mapping(
        map_protein(
            {
                "primaryAccession": accession,
                "sequence": {"value": sequence, "length": len(sequence)},
            },
            "labelled synthetic context",
        ),
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:" + accession,
    )


def relationship(
    card, predicate, target="uniprot:P52270", *, channel="knowledge", derived=False
):
    original = {
        "object_ref": target,
        "channel": channel,
        "literal": "synthetic <statement>",
    }
    assertion = make_source_assertion(
        "relationships." + predicate,
        original,
        "synthetic",
        target,
        "synthetic context",
        subject_ref=card.id.split(":", 2)[2],
    )
    ref = card.source_assertion_store.add(assertion)
    row = make_relationship(
        card.id.split(":", 2)[2],
        predicate,
        target,
        qualifiers={"channel": channel, "original": original},
        source_assertion_ids=[] if derived else [ref],
        derivation=make_derivation("synthetic_relationship@1", inputs=[ref])
        if derived
        else None,
    )
    card.relationship_store.add(row)
    return row, ref


def public(accession):
    data = json.loads((DATA / (accession + ".json")).read_text(encoding="utf-8"))
    return build_card_from_mapping(
        map_protein(data, "frozen public input"),
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:" + accession,
    )


def frames(selection, **kwargs):
    cursor, result = None, []
    while True:
        page = selection.page(cursor=cursor, **kwargs)
        assert len(canonical_json(page).encode()) <= kwargs.get("max_bytes", 65536)
        result.extend(page["items"])
        cursor = page["page"]["next_cursor"]
        if cursor is None:
            return result


@pytest.mark.parametrize(
    "predicate",
    [
        "associated_with",
        "participates_in",
        "interacts_with",
        "functionally_associated_with",
        "ortholog_of",
        "clustered_with",
    ],
)
def test_original_relationships_share_human_agent_source_and_direction(
    predicate, monkeypatch
):
    card = protein()
    original, ref = relationship(card, predicate)
    explorer = card.explore()
    before = card.to_dict()
    monkeypatch.setattr(Card, "__init__", forbidden)
    topic = (
        "comparative_context"
        if predicate in ("ortholog_of", "clustered_with")
        else "associations"
    )
    view = explorer.view(topic)
    machine = explorer.access.select(topic)
    assert len(view.items()) == machine.count == 1
    item = view.items()[0]
    assert item.item_ref == frames(machine)[0]["item_ref"]
    assert item.kind == "relationship"
    assert item.cells["predicate"].value == predicate
    assert item.cells["subject_ref"].value == "uniprot:P60174"
    assert item.cells["object_ref"].value == "uniprot:P52270"
    assert item.open().native_payload == original
    assert item.open().back() is view
    assert item.explain().native_payload["support"]["source_assertions"][0]["id"] == ref
    links = item.related()
    source = links.filter("role", equals="source").items()[0].open()
    assert source.native_payload == card.source_assertion_store.get(ref)
    assert source.back() is not None
    filtered = links.filter("role", equals="object")
    absent = filtered.items()[0].open()
    assert absent.explorer is None and absent.back() is filtered
    assert filtered.back() is links
    assert explorer.access.explain(item.item_ref).page()["outcome"]["status"] == "ok"
    assert card.to_dict() == before


def test_public_interactions_preserve_intact_scope_and_complete_qualifiers():
    card = public("P60174")
    expected = card.relationships(predicate="interacts_with")
    view = card.explore().answer("protein_associations")
    rows = view.filter("predicate", equals="interacts_with")
    assert expected and [i.open().native_payload for i in rows.items()] == expected
    assert "IntAct" in canonical_json(view.native_payload)
    assert all(
        i.cells["support_state"].value == "retained_references" for i in rows.items()
    )
    assert "&lt;" not in repr(view)  # Plain text remains distinct from HTML.


def test_supplied_occurrences_do_not_claim_relationship_or_merge_identity():
    left, right = protein(), protein("P52270")
    explorer = left.explore(related_cards=[right, right])
    view = explorer.answer("related_proteins")
    assert [i.cells["input_index"].value for i in view.items()] == [1, 2]
    assert all(i.cells["predicate"].value is None for i in view.items())
    assert all(i.support[0]["state"] == "not_a_source_statement" for i in view.items())
    assert len({i.item_ref for i in view.items()}) == 2
    links = view.items()[0].related()
    filtered = links.filter("role", equals="supplied_capture")
    destination = filtered.items()[0].open()
    assert destination.explorer.context["card_ref"].startswith(right.id + "@")
    assert destination.back() is filtered
    assert filtered.back() is links
    compared = links.filter("role", equals="question").items()[0].open()
    assert compared.request["question"] == "sequence_differences"
    assert compared.items()[0].cells["identical"].value is True
    assert len(explorer.access._captures) == 2


@pytest.mark.parametrize(
    "sequences,basis",
    [
        (("MAGR", "MAVR"), None),
        (("MAGR", "MAGR"), None),
        (("MA", "MAGR"), "different_lengths"),
        (("", "MAGR"), "sequence_not_stated"),
    ],
)
def test_comparison_reuses_native_rule_and_exact_pins_without_card_construction(
    sequences, basis, monkeypatch
):
    from sabueso.core import sequences as native

    left, right = protein(sequence=sequences[0]), protein("P52270", sequences[1])
    expected = left.sequence_differences(right)
    explorer = left.explore(related_cards=[right])
    target = explorer.context["inputs"][1]
    original = native.sequence_differences_view
    calls = []

    def call(*args):
        calls.append(1)
        return original(*args)

    monkeypatch.setattr(native, "sequence_differences_view", call)
    monkeypatch.setattr(Card, "__init__", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    human = explorer.answer("sequence_differences", options={"other_ref": target})
    machine = explorer.access.select(
        "comparative_context", options={"mode": "sequence", "other_ref": target}
    )
    assert len(calls) == 1 and human.result_ref == machine.result_ref
    assert human.request["options"] == {"mode": "sequence", "other_ref": target}
    assert human.items()[0].open().native_payload["native_result"] == expected
    assert expected.get("basis") == basis
    row = human.items()[0]
    assert row.cells["difference_count"].value == (
        len(expected["differences"]) if "differences" in expected else None
    )
    assert row.cells["identical"].value is expected.get("identical")
    assert "correspondence" in repr(human)
    links = row.related()
    sources = links.filter("role", equals="source")
    assert len(sources.items()) == sum(
        len((card.get("sequence.primary") or {}).get("source_assertion_ids", []))
        for card in (left, right)
    )
    assert all(i.open().request == human.request for i in sources.items())


def test_public_sequence_pair_matches_existing_reader():
    left, right = public("P52270"), public("Q4DV43")
    expected = left.sequence_differences(right)
    explorer = left.explore(related_cards=[right])
    root = explorer.answer(
        "sequence_differences", options={"other_ref": explorer.context["inputs"][1]}
    )
    assert root.items()[0].open().native_payload["native_result"] == expected
    assert expected["differences"]


@pytest.mark.parametrize(
    "where",
    [
        {"input_index": True},
        {"input_index": 1.0},
        {"difference_count": -1},
        {"identical": 1},
        {"predicate": []},
        {"unknown": "x"},
    ],
)
def test_invalid_typed_selection_refuses_before_native_work(where, monkeypatch):
    from sabueso.core import sequences

    left, right = protein(), protein("P52270")
    explorer = left.explore(related_cards=[right])
    monkeypatch.setattr(sequences, "sequence_differences_view", forbidden)
    with pytest.raises(ArgumentError):
        explorer.access.select(
            "comparative_context",
            options={"mode": "sequence", "other_ref": explorer.context["inputs"][1]},
            where=where,
        )


@pytest.mark.parametrize(
    "options",
    [
        {},
        {"other_ref": "uniprot:P52270"},
        {"other_ref": "missing"},
        {"other_ref": 1},
        {"mode": "relationships", "other_ref": "x"},
    ],
)
def test_explicit_question_rejects_unknown_or_implicit_comparator(options):
    explorer = protein().explore(related_cards=[protein("P52270")])
    with pytest.raises(ArgumentError):
        explorer.answer("sequence_differences", options=options)


@pytest.mark.parametrize(
    "damage", ["missing", "subject", "field", "foreign", "conflict", "derived"]
)
def test_support_uncertainties_and_original_derivations_stay_visible(damage):
    card = protein()
    original, ref = relationship(card, "associated_with")
    data = card.to_dict()
    record = next(r for r in data["source_assertion_store"] if r["id"] == ref)
    if damage == "missing":
        data["source_assertion_store"].remove(record)
    elif damage == "subject":
        record["subject_ref"] = "uniprot:OTHER"
    elif damage == "field":
        record["field_path"] = "unrelated"
    elif damage == "foreign":
        data["relationship_store"][0]["subject_ref"] = "uniprot:OTHER"
    elif damage == "conflict":
        data["relationship_store"][0]["qualifier_conflicts"] = {
            "channel": ["knowledge", "text_mining"]
        }
    elif damage == "derived":
        data["relationship_store"][0].pop("source_assertion_ids")
        data["relationship_store"][0]["derivation"] = make_derivation(
            "synthetic_relationship@1", inputs=[ref]
        )
    item = Card.from_dict(data).explore().view("associations").items()[0]
    assert item.cells["support_state"].value == (
        "derivation_only" if damage == "derived" else "partial"
    )
    assert item.open().native_payload == data["relationship_store"][0]
    assert item.support[0]["basis"] == (
        "recorded_derivation" if damage == "derived" else "recorded_source_references"
    )


def test_channels_and_opposite_directions_are_never_conflated():
    card = protein()
    relationship(card, "associated_with", channel="knowledge")
    relationship(card, "associated_with", channel="text_mining")
    view = card.explore().view("associations")
    assert len(view.items()) == 2
    assert len(view.filter("channel", equals="text_mining").items()) == 1
    machine = view.explorer.access.select(
        "associations",
        where={"channel": "knowledge"},
        order_by={"column": "label", "descending": True},
    )
    assert machine.count == 1 and len(machine._scientific.entries) == 2


def test_html_escaping_and_atomic_agent_deferral_keep_originals():
    card = protein()
    relationship(card, "interacts_with", target="uniprot:<script>" + "x" * 30000)
    explorer = card.explore()
    view = explorer.view("associations")
    assert "<script>" not in view._repr_html_()
    selection = explorer.access.select("associations", fields=["label", "object_ref"])
    page = selection.page(max_bytes=8000)
    assert len(canonical_json(page).encode()) <= 8000
    assert not page["items"][0]["value_included"]
    assert all("value" not in cell for cell in page["items"][0]["cells"].values())
    assert "<script>" in view.items()[0].open().native_payload["object_ref"]


def test_save_refusal_and_unrelated_literal_saving_are_explicit(tmp_path):
    card = protein()
    relationship(card, "interacts_with")
    isolated = card.explore()
    isolated.inspect("identifiers.uniprot").save(tmp_path / "literal.json")
    explorer = card.explore()
    view = explorer.view("associations")
    assert not view.capabilities["save"]
    assert not explorer.access.select("associations").capabilities["save"]
    for root in (
        view,
        view.items()[0].open(),
        view.items()[0].explain(),
        view.items()[0].related(),
        explorer.inspect("identifiers.uniprot"),
    ):
        assert not root.capabilities["save"]
        with pytest.raises(StorageError):
            root.save(tmp_path / "unsupported.json")
        assert not (tmp_path / "unsupported.json").exists()
    explorer.access.export_card(tmp_path / "card.json")
    exported = json.loads((tmp_path / "card.json").read_text(encoding="utf-8"))
    assert exported["relationship_store"] == card.to_dict()["relationship_store"]


def test_public_cluster_relationships_remain_distinct_from_supplied_sequence_question():
    from sabueso.mappings.uniref import map_uniref

    clusters = json.loads(
        (DATA / "uniref/clusters_P52270.json").read_text(encoding="utf-8")
    )
    members = json.loads(
        (DATA / "uniref/members_UniRef90_P52270.json").read_text(encoding="utf-8")
    )
    mapping, _ = map_uniref(
        clusters["record"],
        members["record"],
        "P52270",
        "frozen public input",
        members["version"],
    )
    left = build_card_from_mapping(
        mapping,
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:P52270",
    )
    expected = left.relationships(predicate="clustered_with")
    root = left.explore(related_cards=[public("Q4DV43")]).answer("related_proteins")
    records = root.filter("kind", equals="relationship")
    assert expected and [i.open().native_payload for i in records.items()] == expected
    assert all(
        i.cells["basis"].value == "recorded_source_references" for i in records.items()
    )
    assert all(i.cells["identical"].state == "not_applicable" for i in records.items())
    assert len(root.explorer.access._captures) == 2


@pytest.mark.parametrize(
    "mode", ["missing_assertions", "different_value", "malformed_sequence"]
)
def test_sequence_support_gaps_never_turn_into_supported_equality(mode, monkeypatch):
    from sabueso.core import sequences

    left, right = protein(), protein("P52270")
    data = right.to_dict()
    node = data["sections"]["sequence"]["primary"]
    if mode == "missing_assertions":
        node["source_assertion_ids"] = []
    elif mode == "different_value":
        node["value"] = "MMMM"
    else:
        node["value"] = [1, 2]
        monkeypatch.setattr(sequences, "sequence_differences_view", forbidden)
    explorer = left.explore(related_cards=[Card.from_dict(data)])
    root = explorer.answer(
        "sequence_differences", options={"other_ref": explorer.context["inputs"][1]}
    )
    assert root.items()[0].cells["support_state"].value == "partial"
    if mode == "malformed_sequence":
        assert root.items()[0].cells["identical"].value is None
        assert root.items()[0].open().native_payload["native_result"] is None


def test_multiple_revisions_remain_ambiguous_for_relationship_navigation():
    left, first, second = protein(), protein("P52270"), protein("P52270", "MVGR")
    relationship(left, "interacts_with")
    root = left.explore(related_cards=[first, second]).view("associations")
    links = root.items()[0].related().filter("role", equals="object")
    original = links.items()[0]._entry.value
    assert original["availability"] == "ambiguous" and len(original["candidates"]) == 2
    opened = links.items()[0].open()
    assert opened._status == "ambiguous" and opened.back() is links
    assert len(root.explorer.access._captures) == 3


def test_input_keys_cannot_overwrite_literal_relationship_ids():
    card = protein()
    row, _ = relationship(card, "clustered_with")
    raw = card.to_dict()
    raw["relationship_store"][0]["id"] = "input:1"
    root = (
        Card.from_dict(raw)
        .explore(related_cards=[protein("P52270")])
        .view("comparative_context")
    )
    assert {i.kind for i in root.items()} == {"relationship", "supplied_capture"}
    assert root.items()[0].open().native_payload["id"] == "input:1"


def test_named_relationship_question_cannot_silently_switch_to_comparison():
    root = protein().explore(related_cards=[protein("P52270")])
    with pytest.raises(ArgumentError):
        root.answer(
            "related_proteins",
            options={"mode": "sequence", "other_ref": root.context["inputs"][1]},
        )


def test_raw_null_and_malformed_channels_keep_original_values():
    card = protein()
    relationship(card, "associated_with", channel=0)
    item = card.explore().view("associations").items()[0]
    assert (
        item.cells["channel"].value is None
        and item.cells["channel"].state == "unrecognized_shape"
    )
    assert item.open().native_payload["qualifiers"]["channel"] == 0


def test_public_oma_relationships_keep_source_inferences_without_identity_merge():
    from sabueso.mappings.oma import map_orthologs

    record = json.loads(
        (DATA / "oma/orthologs_P60174.json").read_text(encoding="utf-8")
    )
    mapping, _ = map_orthologs(record, {}, "P60174", "frozen public input", 100)
    card = build_card_from_mapping(
        mapping,
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:P60174",
    )
    expected = card.relationships(predicate="ortholog_of")
    view = card.explore().view("comparative_context")
    assert expected and [i.open().native_payload for i in view.items()] == expected
    assert all(i.cells["source"].value == "OMA" for i in view.items())
    assert all(i.cells["predicate"].value == "ortholog_of" for i in view.items())


def test_malformed_source_reference_is_literal_uncertainty():
    card = protein()
    relationship(card, "associated_with")
    raw = card.to_dict()
    raw["relationship_store"][0]["source_assertion_ids"] = [{"unknown": False}]
    item = Card.from_dict(raw).explore().view("associations").items()[0]
    assert item.cells["support_state"].value == "partial"
    assert item.support[0]["source_assertions"][0]["state"] == "unrecognized_shape"
    assert item.open().native_payload["source_assertion_ids"] == [{"unknown": False}]
    assert (
        item.related().filter("role", equals="source").items()[0].open().explorer
        is None
    )
