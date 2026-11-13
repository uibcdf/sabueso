"""Deck composition reuses source-bound Card navigation, not new identity rules."""

import json
import socket
from pathlib import Path

import pytest

from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion


@pytest.fixture(autouse=True)
def no_acquisition(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Captured Deck context cannot acquire sources")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def card(ref="uniprot:synthetic-A", nature="protein", name="Synthetic"):
    return Card(
        meta={"card_id": f"sabueso:{nature}:{ref}", "entity_type": nature},
        sections={
            "names": {"canonical_name": {"value": name, "source_assertion_ids": []}}
        },
    )


def edge(owner, target, predicate="associated_with", *, missing=False):
    source = make_source_assertion(
        "relationships." + predicate,
        target,
        "Synthetic",
        "deck-context-control",
        "2026-11-13",
        subject_ref=owner.id.split(":", 2)[2],
    )
    if not missing:
        owner.source_assertion_store.add(source)
    relation = make_relationship(
        source["subject_ref"], predicate, target, source_assertion_ids=[source["id"]]
    )
    owner.relationship_store.add(relation)
    return relation


def relation(explorer, ref=None):
    store = next(
        i for i in explorer.inspect().items() if i.label == "Relationships"
    ).open()
    return next(i for i in store.items() if ref is None or i._entry.key == ref)


def role(links, name="object"):
    return links.filter("role", equals=name).items()[0]


def test_shared_capture_opens_every_focal_without_card_construction_or_recapture(
    monkeypatch,
):
    first, other = card(), card("mondo:synthetic-B", "disease")
    edge(first, "mondo:synthetic-B")
    expected = other.pinned_ref()
    deck = Deck([other, first, first])
    explorer = deck.explore()
    root = explorer.overview()
    other.sections["names"]["canonical_name"]["value"] = "caller mutation"
    deck.cards.clear()

    def forbidden(*args, **kwargs):
        pytest.fail("Opening a Deck member must reuse its already validated capture")

    monkeypatch.setattr(Card, "to_dict", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr("sabueso.core.card_access._capture_cards", forbidden)
    monkeypatch.setattr("sabueso.core.deck_exploration._capture_cards", forbidden)
    first_visit = root.items()[1].open()
    direct_other = root.items()[0].open()
    assert first_visit.explorer.access._captures is explorer._captures
    assert direct_other.explorer.access._captures is explorer._captures
    assert first_visit.explorer._session is not direct_other.explorer._session
    assert first_visit.explorer.context["inputs"] == list(explorer._inputs)
    assert direct_other.explorer.context["inputs"] == list(explorer._inputs)
    assert first_visit.explorer is root.items()[2].open().explorer
    destination = role(relation(first_visit.explorer).related()).open()
    assert destination.context["card_ref"] == expected
    assert "caller mutation" not in str(destination)
    assert first_visit.back() is root


def test_public_mondo_parent_is_available_even_outside_the_deck_display_filter():
    from sabueso.tools.card.disease import resolve_disease_card
    from sabueso.tools.db.mondo import FixtureMONDOClient

    client = FixtureMONDOClient("temp_data")
    child = resolve_disease_card("MONDO:0001444", mondo_client=client)[0]
    parent = resolve_disease_card("MONDO:0000940", mondo_client=client)[0]
    root = Deck([parent, child, child]).explore().overview()
    selected = root.sort("label").filter("0001444")
    entry = selected.items()[1].open()
    classification = entry.explorer.view("classification")
    parent_row = classification.filter(
        "object_ref", equals="mondo:MONDO:0000940"
    ).items()[0]
    links = parent_row.related()
    target_link = role(links)
    selected_links = target_link.back()
    destination = target_link.open()
    assert destination.context["card_ref"] == parent.pinned_ref()
    assert destination.explorer.profile == "disease"
    assert (
        role(links, "source").open().native_payload["id"]
        in next(
            row
            for row in child.relationships("subclass_of")
            if row["object_ref"] == "mondo:MONDO:0000940"
        )["source_assertion_ids"]
    )
    assert destination.back() is selected_links and selected_links.back() is links
    assert entry.back() is selected
    assert len(selected.items()) == 2 and len(root.items()) == 3


def test_duplicate_occurrences_do_not_choose_between_different_target_revisions():
    source = card()
    first = card("mondo:synthetic-B", "disease", "first")
    second = card("mondo:synthetic-B", "disease", "second")
    edge(source, "mondo:synthetic-B")
    root = Deck([source, second, first, first]).access()
    entry = root.items()[0].open()
    choices = role(relation(entry.explorer).related()).open()
    assert choices.outcome["status"] == "ambiguous"
    assert len(choices.items()) == 2
    assert {i.open().context["card_ref"] for i in choices.items()} == {
        first.pinned_ref(),
        second.pinned_ref(),
    }
    assert len({i.member_ref for i in root.items()}) == 4
    assert all(i.open().back() is choices for i in choices.items())
    assert entry.back() is root


@pytest.mark.parametrize(
    "predicate,missing",
    [("same_as", True), ("possibly_same_as", False), ("ortholog_of", False)],
)
def test_deck_membership_never_supplies_missing_identity_support(predicate, missing):
    source, target = card(), card("inchikey:synthetic-X", "small_molecule")
    edge(source, "chembl:synthetic-X")
    edge(target, "chembl:synthetic-X", predicate, missing=missing)
    expected = role(relation(source.explore(related_cards=[target])).related()).open()
    actual = role(
        relation(Deck([source, target]).access().items()[0].open().explorer).related()
    ).open()
    assert actual.outcome == expected.outcome
    assert actual.native_payload == expected.native_payload
    assert actual.explorer is None


def test_matching_name_and_sequence_do_not_invent_a_destination():
    source, lookalike = card(), card("uniprot:synthetic-B")
    for item in (source, lookalike):
        item.sections["sequence"] = {
            "primary": {"value": "SAME", "source_assertion_ids": []}
        }
    edge(source, "uniprot:synthetic-C")
    result = role(
        relation(
            Deck([source, lookalike]).access().items()[0].open().explorer
        ).related()
    ).open()
    assert (
        result.explorer is None and result.outcome["status"] == "context_not_supplied"
    )


@pytest.mark.parametrize("case", ["exact_record", "missing_pin", "missing_record"])
def test_pins_and_source_records_keep_native_no_fallback_semantics(case):
    source, target = card(), card("mondo:synthetic-B", "disease")
    edge(target, "mondo:synthetic-C", "subclass_of")
    assertion = target.to_dict()["source_assertion_store"][0]
    endpoint = target.pinned_ref() + "#" + assertion["id"]
    if case == "missing_pin":
        endpoint = target.id + "@sha256:" + "0" * 64
    elif case == "missing_record":
        endpoint = target.pinned_ref() + "#SA_missing"
    edge(source, endpoint)
    result = role(
        relation(Deck([source, target]).access().items()[0].open().explorer).related()
    ).open()
    if case == "exact_record":
        assert (
            result.native_payload == assertion
            and result.context["card_ref"] == target.pinned_ref()
        )
    else:
        assert result.explorer is None and result.outcome["status"] in {
            "context_not_supplied",
            "missing_prerequisite",
        }


def test_cross_card_reading_saves_and_reopens_without_cards_or_live_science(
    tmp_path, monkeypatch
):
    import sabueso

    source, target = card(), card("mondo:synthetic-B", "disease")
    edge(source, "mondo:synthetic-B")
    root = Deck([source, target, source]).access()
    entry = root.items()[2].open()
    links = relation(entry.explorer).related()
    destination = role(links).open()
    expected, context = destination.native_payload, destination.context
    path = tmp_path / "original.json.gz"
    receipt = destination.save(path, compression="gzip")

    def forbidden(*args, **kwargs):
        pytest.fail("An original Card reading must not reconstruct current Cards")

    monkeypatch.setattr(Card, "__init__", forbidden)
    monkeypatch.setattr("sabueso.core.card_access._capture_cards", forbidden)
    saved = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert saved.native_payload == expected
    assert saved.context["card_ref"] == context["card_ref"]
    assert saved.context["inputs"] == context["inputs"]
    assert saved.back().native_payload == links.native_payload
    assert entry.back() is root


def test_nonfirst_focal_scientific_and_literal_views_match_native_card_scope():
    protein = Card.from_dict(
        json.loads(Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text())
    )
    other = card("mondo:synthetic-B", "disease")
    edge(other, "uniprot:P52270")
    native_root = other.explore(related_cards=[protein])
    expected = role(relation(native_root).related()).open().explorer
    entry = Deck([other, protein]).access().items()[1].open().explorer
    assert entry.context["card_ref"] == expected.context["card_ref"]
    for topic in ("function", "structures", "sequence"):
        actual, native = entry.view(topic), expected.view(topic)
        assert actual.native_payload == native.native_payload
        assert actual.outcome == native.outcome
    assert entry.context["inputs"][0] == other.pinned_ref()
