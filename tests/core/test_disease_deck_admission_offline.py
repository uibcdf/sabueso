"""Admission preserves all native context and never exports disallowed raw members."""

import json
from copy import deepcopy

import ackredit
import pytest
from test_disease_deck_support_offline import results as results

import sabueso
from sabueso.core import terms
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.source_assertion_store import make_source_assertion


def extra_statement(card, source):
    return card.source_assertion_store.add(
        make_source_assertion(
            "annotations.additional",
            "unexportable raw marker",
            source,
            "public synthetic record",
            "original retrieval",
        )
    )


def rebind_member(deck):
    card = deck.cards[0]
    basis = deck.basis(card.id)
    previous = basis["member_card_ref"]
    basis["member_card_ref"] = card.pinned_ref()
    basis["member_identity_source_assertion_refs"] = [
        ref.replace(previous, card.pinned_ref())
        for ref in basis["member_identity_source_assertion_refs"]
    ]


@pytest.mark.parametrize("kind", ["targets", "drugs"])
@pytest.mark.parametrize("use", terms.USES)
def test_all_allowed_retains_exact_native_context_and_member_identity(
    results, kind, use
):
    original = results[kind]
    before = deepcopy(original.meta)
    admitted = original.admissible(use)
    assert admitted is not original
    assert [c.pinned_ref() for c in admitted.cards] == [
        c.pinned_ref() for c in original.cards
    ]
    assert admitted.meta["support"] == original.meta["support"]
    assert admitted.meta["excluded"] == original.meta["excluded"]
    assert (
        admitted.meta["admission"]["input_deck_snapshot_id"] == original.snapshot_id()
    )
    assert admitted.meta["admission"]["terms"]["unknown"] == []
    assert (
        admitted.explain(admitted.cards[0].id)["support"]
        == original.explain(original.cards[0].id)["support"]
    )
    admitted.meta["support"]["input"]["card"]["meta"]["detached"] = True
    assert original.meta == before


@pytest.mark.parametrize("kind", ["targets", "drugs"])
@pytest.mark.parametrize(
    "source", ["Unknown raw source", "PubChem BioAssay", "Literature"]
)
def test_unused_member_content_is_not_licensed_by_an_allowed_alternative(
    results, kind, source
):
    original = deepcopy(results[kind])
    extra_statement(original.cards[0], source)
    rebind_member(original)
    assert original.terms("redistribution")["cards"][0]["status"] == "complete"
    before = deepcopy(original.meta)
    admitted = original.admissible("redistribution")
    assert admitted.cards == []
    assert "unexportable raw marker" not in json.dumps(admitted.meta)
    exclusion = admitted.meta["excluded"][-1]
    assert exclusion["candidate"] == original.cards[0].id
    assert exclusion["terms"]["unknown"][-1]["sources"] == [source]
    assert (
        exclusion["removed_member_support"]["card_ref"]
        == original.cards[0].pinned_ref()
    )
    answer = admitted.explain(original.cards[0].id)
    assert answer["support"]["status"] == "recorded"
    assert (
        answer["support"]["statements"][0]["member_identity_source_assertion_refs"]
        == []
    )
    assert original.meta == before


@pytest.mark.parametrize("role", ["input", "assertions"])
def test_unknown_embedded_content_refuses_without_mutation_and_reports_exact_scope(
    results, role
):
    deck = deepcopy(results["targets"])
    # Registry uncertainty also covers rows that were excluded or never built.
    registry = deepcopy(terms.source_terms())
    source = "MONDO" if role == "input" else "Open Targets"
    registry.pop(source)
    from unittest.mock import patch

    before = deepcopy(deck.meta)
    with patch.object(terms, "source_terms", return_value=registry):
        with pytest.raises(ArgumentError, match="shared disease support") as caught:
            deck.admissible("redistribution")
    report = caught.value.admission_report
    assert report["rule"] == "disease_deck_admission@1"
    assert source in report["unknown"]
    assert any(
        row["card_id"] == deck.meta["support"][role]["card_ref"] and row["unknown"]
        for row in report["cards"]
    )
    assert "asserted_value" not in json.dumps(report)
    assert deck.meta == before


@pytest.mark.parametrize(
    "defect", ["input", "member", "identity", "native", "missing_basis", "duplicate"]
)
def test_broken_scientific_support_cannot_be_admitted(results, defect):
    deck = deepcopy(results["targets"])
    basis = deck.basis(deck.cards[0].id)
    if defect == "input":
        deck.meta["support"]["input"]["card_ref"] += "changed"
    elif defect == "member":
        basis["member_card_ref"] += "changed"
    elif defect == "identity":
        basis["member_identity_source_assertion_refs"] = []
    elif defect == "native":
        basis["source_assertion_refs"] = []
    elif defect == "missing_basis":
        deck.meta["membership"] = {}
    else:
        deck.cards.append(deck.cards[0])
    with pytest.raises(StorageError):
        deck.admissible("redistribution")


@pytest.mark.parametrize("format", ["jsonl", "sqlite"])
@pytest.mark.parametrize("remove_member", [False, True])
def test_admission_exports_and_historical_store_reads_are_inert(
    results, format, remove_member, tmp_path, monkeypatch
):
    deck = deepcopy(results["targets"])
    if remove_member:
        extra_statement(deck.cards[0], "Unknown raw source")
        rebind_member(deck)
    member_id = deck.cards[0].id

    def forbidden(*args, **kwargs):
        pytest.fail("admission and historical reads must not acquire or credit")

    monkeypatch.setattr(sabueso, "resolve", forbidden)
    monkeypatch.setattr(ackredit, "register_item", forbidden)
    monkeypatch.setattr(ackredit, "track_item", forbidden)
    with ackredit.session("inert admission"):
        before = ackredit.get_attribution().to_dict()
        admitted = deck.admissible("redistribution")
        assert admitted.acquisition_trace is None
        path = tmp_path / f"admitted.{format}"
        getattr(admitted, f"to_{format}")(str(path))
        loaded = getattr(Deck, f"from_{format}")(str(path))
        assert loaded.snapshot_id() == admitted.snapshot_id()
        store = sabueso.KnowledgeStore(tmp_path / "history.db")
        pin = store.save_deck(loaded, "admitted")
        later = Card.from_dict(deck.meta["support"]["input"]["card"])
        later.meta["later"] = True
        store.save(later)
        restored = store.load_deck(pin)
        assert restored.explain(member_id) == admitted.explain(member_id)
        assert restored.meta["admission"] == admitted.meta["admission"]
        assert ackredit.get_attribution().to_dict() == before
        if remove_member:
            assert "unexportable raw marker" not in json.dumps(restored.meta)


def test_current_registry_is_recorded_without_rewriting_previous_decisions(
    results, monkeypatch
):
    original = results["targets"]
    admitted = original.admissible("redistribution")
    before = deepcopy(admitted.meta)
    registry = deepcopy(terms.source_terms())
    registry.pop("MONDO")
    monkeypatch.setattr(terms, "source_terms", lambda: registry)
    with pytest.raises(ArgumentError):
        admitted.admissible("redistribution")
    assert admitted.meta == before


@pytest.mark.parametrize("use", terms.USES)
def test_noncommercial_member_content_has_distinct_restricted_and_allowed_outcomes(
    results, monkeypatch, use
):
    deck = deepcopy(results["targets"])
    extra_statement(deck.cards[0], "Synthetic noncommercial source")
    rebind_member(deck)
    registry = deepcopy(terms.source_terms())
    registry["Synthetic noncommercial source"] = {
        "licence": "CC-BY-NC-4.0",
        "reviewed": "2026-10-06",
        "attribution": "Synthetic attribution",
    }
    monkeypatch.setattr(terms, "source_terms", lambda: registry)
    admitted = deck.admissible(use)
    report = admitted.meta["admission"]["terms"]
    if use == "commercial_product":
        assert admitted.cards == []
        assert report["restricted"] == ["Synthetic noncommercial source"]
        assert admitted.meta["excluded"][-1]["terms"]["lost"]
    else:
        assert admitted.cards == deck.cards
        assert report["restricted"] == []
        if use != "internal_research":
            assert "Synthetic attribution" in report["attribution"]


def test_empty_deck_still_checks_all_native_and_excluded_context(results, monkeypatch):
    original = results["targets"].filter(lambda card: False)
    assert original.cards == []
    registry = deepcopy(terms.source_terms())
    registry.pop("Open Targets")
    monkeypatch.setattr(terms, "source_terms", lambda: registry)
    with pytest.raises(ArgumentError) as caught:
        original.admissible("redistribution")
    assert "Open Targets" in caught.value.admission_report["unknown"]


def test_repeated_admission_keeps_native_pins_and_records_distinct_inputs(results):
    first = results["targets"].admissible("redistribution")
    before = deepcopy(first.meta)
    second = first.admissible("academic_publication")
    assert first.meta == before
    assert second.meta["support"] == first.meta["support"]
    assert second.meta["admission"]["input_deck_snapshot_id"] == first.snapshot_id()
    assert len(second.meta["operations"]) == len(first.meta["operations"]) + 1


def test_allowed_resolved_identity_does_not_license_its_unknown_raw_alternative(
    results,
):
    deck = deepcopy(results["targets"])
    member = deck.cards[0]
    field = member.get("identifiers.uniprot")
    identifier = member.source_assertion_store.add(
        make_source_assertion(
            "identifiers.uniprot",
            field["value"],
            "Unknown alternative",
            "public synthetic record",
            "original retrieval",
        )
    )
    member.set(
        "identifiers.uniprot",
        field["value"],
        [*field["source_assertion_ids"], identifier],
    )
    basis = deck.basis(member.id)
    old_ref = basis["member_card_ref"]
    new_ref = member.pinned_ref()
    basis["member_card_ref"] = new_ref
    basis["member_identity_source_assertion_refs"] = [
        ref.replace(old_ref, new_ref)
        for ref in basis["member_identity_source_assertion_refs"]
    ]
    basis["member_identity_source_assertion_refs"].append(new_ref + "#" + identifier)
    assert deck.terms("redistribution")["cards"][0]["status"] == "complete"
    admitted = deck.admissible("redistribution")
    assert not admitted.cards
    assert admitted.meta["admission"]["terms"]["unknown"] == ["Unknown alternative"]


def test_valid_native_basis_of_another_candidate_cannot_admit_this_member(results):
    deck = deepcopy(results["targets"])
    member = deck.cards[0]
    current = deck.basis(member.id)
    other = next(
        row
        for row in deck.meta["excluded"]
        if row["candidate"].startswith("uniprot:")
        and row["candidate"] not in current["candidate_refs"]
    )
    basis = deepcopy(other["basis"])
    basis["member_card_ref"] = current["member_card_ref"]
    basis["member_identity_source_assertion_refs"] = current[
        "member_identity_source_assertion_refs"
    ]
    deck.meta["membership"][member.id] = basis
    answer = deck.explain(member.id)
    assert answer["support"]["status"] == "partial"
    assert {"reason": "candidate_not_stated_by_member_identity"} in answer["support"][
        "gaps"
    ]
    with pytest.raises(StorageError):
        deck.admissible("redistribution")


def test_resolved_member_identifier_requires_its_original_stated_value(results):
    deck = deepcopy(results["targets"])
    member = deck.cards[0]
    field = member.get("identifiers.uniprot")
    member.set("identifiers.uniprot", "Q9UQD0", field["source_assertion_ids"])
    rebind_member(deck)
    current = deck.basis(member.id)
    other = next(
        row for row in deck.meta["excluded"] if row["candidate"] == "uniprot:Q9UQD0"
    )
    basis = deepcopy(other["basis"])
    basis["member_card_ref"] = current["member_card_ref"]
    basis["member_identity_source_assertion_refs"] = current[
        "member_identity_source_assertion_refs"
    ]
    deck.meta["membership"][member.id] = basis
    assert deck.explain(member.id)["support"]["status"] == "partial"
    with pytest.raises(StorageError):
        deck.admissible("redistribution")
