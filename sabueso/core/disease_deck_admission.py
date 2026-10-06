"""Conservative admission of whole disease support and unchanged member cards."""

from copy import deepcopy

from .disease_deck_support import explain_support, support_cards
from .errors import ArgumentError, StorageError
from .terms import _items, assertion_label, report_items

RULE = "disease_deck_admission@1"
SCOPE = "whole_embedded_support_and_unchanged_member_content"


def _content_items(card):
    # Resolved alternatives are not interchangeable with the raw statements that
    # remain in an unchanged export. Judge every statement separately, including
    # unused statements. Service terms never stand in for depositor/article terms.
    card_ref = card.pinned_ref()
    return [
        *_items(card),
        *[
            {
                "kind": "source_assertion",
                "id": card_ref + "#" + assertion["id"],
                "sources": [assertion_label(assertion)],
            }
            for assertion in card.source_assertion_store.to_list()
        ],
    ]


def admit(deck, use):
    """Retain exact support, or refuse; filter members without rewriting knowledge.

    The original acquisition/attribution sidecars belong to the original deck.
    This operation neither acquires nor credits and creates no runtime trace.
    """
    from .deck import Deck

    support = support_cards(deck.meta)
    if len({card.id for card in deck.cards}) != len(deck.cards):
        raise StorageError("Disease deck admission requires unique member cards.")
    for card in deck.cards:
        basis = deck.basis(card.id) or {}
        card_ref = card.pinned_ref()
        expected_identity = [
            card_ref + "#" + identifier
            for field in (
                "identifiers.uniprot",
                "identifiers.chembl",
                "identifiers.inchikey",
            )
            for identifier in (card.get(field) or {}).get("source_assertion_ids", [])
        ]
        if (
            basis.get("member_card_ref") != card_ref
            or not expected_identity
            or basis.get("member_identity_source_assertion_refs") != expected_identity
        ):
            raise StorageError(
                "Disease deck admission requires complete pinned support."
            )
    for candidate in [
        *[card.id for card in deck.cards],
        *[row["candidate"] for row in deck.meta.get("excluded", [])],
    ]:
        if explain_support(deck, candidate)["status"] != "recorded":
            raise StorageError(
                "Disease deck admission requires complete pinned support."
            )
    report = report_items(
        [
            *[(card.pinned_ref(), _content_items(card)) for card in deck.cards],
            *[(card.pinned_ref(), _content_items(card)) for card in support.values()],
        ],
        use,
    )
    report.update(rule=RULE, scope=SCOPE)
    decisions = {row["card_id"]: row for row in report["cards"]}
    blocked = [
        card.pinned_ref()
        for card in support.values()
        if decisions[card.pinned_ref()]["status"] != "complete"
    ]
    if blocked:
        error = ArgumentError(
            argument="use",
            value=use,
            caller="Deck.admissible",
            reason="shared disease support is not fully admissible; source pruning is not supported",
        )
        # Exact item locators and registry declarations, never copied raw values.
        error.admission_report = deepcopy(report)
        raise error
    kept, removed = [], []
    meta = deepcopy(deck.meta)
    membership = meta.get("membership") or {}
    for card in deck.cards:
        decision = decisions[card.pinned_ref()]
        if decision["status"] == "complete":
            kept.append(card)
            continue
        basis = membership.pop(card.id)
        historical = {
            "card_ref": basis.pop("member_card_ref"),
            "identity_source_assertion_refs": basis.pop(
                "member_identity_source_assertion_refs"
            ),
        }
        removed.append(historical)
        meta.setdefault("excluded", []).append(
            {
                "candidate": card.id,
                "reason": "partially_admissible"
                if decision["status"] == "partial"
                else "not_admissible",
                "by": RULE,
                "basis": basis,
                "removed_member_support": historical,
                "terms": deepcopy(decision),
            }
        )
    meta["membership"] = membership
    meta.setdefault("operations", []).append(
        {"operation": "admissible", "parameters": {"use": use, "rule": RULE}}
    )
    meta["admission"] = {
        "rule": RULE,
        "input_deck_snapshot_id": deck.snapshot_id(),
        "input_member_card_refs": [card.pinned_ref() for card in deck.cards],
        "retained_support_card_refs": [card.pinned_ref() for card in support.values()],
        "removed_member_support": removed,
        "terms": report,
    }
    return Deck(kept, meta=meta)
