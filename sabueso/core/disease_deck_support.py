"""Exact native support for disease decks; scientific snapshots, never runtime credit."""

from copy import deepcopy

from .card import Card
from .errors import StorageError
from .relationship_store import make_derivation

FORMAT = "sabueso.disease_deck_support@1"
EXPLANATION_RULE = "disease_deck_explanation@1"


def terms_for_support(deck, use):
    """Include native support content even when a candidate was never built."""
    from .terms import _items, assertion_label, report_items

    cards = support_cards(deck.meta)
    if not cards:
        return None
    groups = [(card.id, _items(card)) for card in deck.cards]
    for card in cards.values():
        groups.append(
            (
                card.pinned_ref(),
                [
                    {
                        "kind": "source_assertion",
                        "id": card.pinned_ref() + "#" + assertion["id"],
                        "sources": [assertion_label(assertion)],
                    }
                    for assertion in card.source_assertion_store.to_list()
                ],
            )
        )
    report = report_items(groups, use)
    report["rule"] = "disease_deck_terms@1"
    report["scope"] = "members_and_all_embedded_disease_support"
    return report


class DiseaseDeckSupport:
    """Retain an unchanged disease input and a separate assertion-bearing revision."""

    def __init__(self, card, rule, limit):
        self.input = Card.from_dict(card.to_dict())
        self.assertions = Card.from_dict(card.to_dict())
        self.rule, self.limit = rule, limit

    def add(self, assertion):
        return self.assertions.source_assertion_store.add(assertion)

    def basis(self, candidate, query_ids, assertion_ids, **metadata):
        return {
            **metadata,
            "candidate_refs": [candidate],
            "source_assertion_ids": list(dict.fromkeys(assertion_ids)),
            "query_ids": list(dict.fromkeys(query_ids)),
        }

    def bind(self, basis, member=None):
        """Bind native rows and identity fields to the exact cards actually read."""
        input_ref, support_ref = self.input.pinned_ref(), self.assertions.pinned_ref()
        identity_ids = []
        for field in ("identifiers.mondo", "identifiers.equivalent_ids"):
            value = self.input.get(field) or {}
            identity_ids.extend(value.get("source_assertion_ids") or [])
        basis["source_assertion_refs"] = [
            support_ref + "#" + i for i in basis["source_assertion_ids"]
        ]
        basis["identity_source_assertion_refs"] = [
            input_ref + "#" + i for i in dict.fromkeys(identity_ids)
        ]
        basis["input_card_ref"] = input_ref
        basis["derivation"] = make_derivation(
            self.rule,
            inputs=[input_ref, *basis["source_assertion_refs"]],
            parameters={
                "limit": self.limit,
                "query_ids": basis["query_ids"],
                "identity": "source_stated_only",
            },
        )
        if member is not None:
            basis["member_card_ref"] = member.pinned_ref()
            basis["member_identity_source_assertion_refs"] = [
                member.pinned_ref() + "#" + i
                for field in (
                    "identifiers.uniprot",
                    "identifiers.chembl",
                    "identifiers.inchikey",
                )
                for i in (member.get(field) or {}).get("source_assertion_ids", [])
            ]
        return basis

    def to_dict(self):
        return {
            "format": FORMAT,
            "input": {
                "card_ref": self.input.pinned_ref(),
                "card": self.input.to_dict(),
            },
            "assertions": {
                "card_ref": self.assertions.pinned_ref(),
                "card": self.assertions.to_dict(),
            },
        }


def support_cards(meta):
    """Verify self-contained support; old decks without this format stay readable."""
    support = meta.get("support")
    if support is None:
        return {}
    if not isinstance(support, dict) or support.get("format") != FORMAT:
        if meta.get("kind") in ("disease_targets", "disease_drugs"):
            raise StorageError("Unknown disease deck support format.")
        return {}
    result = {}
    for role in ("input", "assertions"):
        try:
            entry = support[role]
            card = Card.from_dict(entry["card"])
            if card.pinned_ref() != entry["card_ref"]:
                raise StorageError(f"Disease deck {role} card does not match its pin.")
        except (KeyError, TypeError) as error:
            raise StorageError(f"Incomplete disease deck {role} support.") from error
        result[role] = card
    if result["input"].id != result["assertions"].id or result["input"].id != meta.get(
        "disease"
    ):
        raise StorageError("Disease deck support names another disease.")
    from .snapshot import snapshot_content

    original = snapshot_content(result["input"].to_dict())
    extended = snapshot_content(result["assertions"].to_dict())
    original.pop("source_assertion_store")
    extended.pop("source_assertion_store")
    if original != extended or any(
        result["assertions"].source_assertion_store.get(i) != value
        for i, value in result["input"].source_assertion_store.store.items()
    ):
        raise StorageError("Disease deck support changed its original input knowledge.")
    return result


def _candidate_matches(assertion, basis):
    """Check the native identifier/product scope, never a name or a score threshold."""
    source = assertion["source"]["name"]
    value = assertion["asserted_value"]
    candidates, queries = basis.get("candidate_refs", []), basis.get("query_ids", [])
    if source == "Open Targets":
        if "rows" in value:
            return any(
                _candidate_matches(
                    {
                        **assertion,
                        "asserted_value": {"disease": value.get("disease"), "row": row},
                    },
                    basis,
                )
                for row in value["rows"]
            )
        target = (value.get("row") or {}).get("target") or {}
        disease = (value.get("disease") or {}).get("id")
        named = str(disease).replace("_", ":")
        refs = [
            f"ensembl:{target.get('id')}",
            *[
                f"uniprot:{p.get('id')}"
                for p in target.get("proteinIds") or []
                if p.get("source") == "uniprot_swissprot"
            ],
        ]
        return named in queries and any(c in refs for c in candidates)
    if source == "Orphanet":
        return (
            f"Orphanet:{value.get('orpha_code')}" in queries
            and f"uniprot:{value.get('uniprot')}" in candidates
        )
    if source == "ChEMBL":
        from sabueso.tools.db.chembl import _names_disease

        return (
            f"chembl:{value.get('molecule_chembl_id')}" in candidates
            and _names_disease(value, queries)
        )
    return False


def _member_candidate_matches(member, basis):
    """Native candidate identifiers must be stated by the actual member's support."""
    identities = set()
    member_ref = member.pinned_ref()
    bound = set(basis.get("member_identity_source_assertion_refs", []))
    for namespace in ("uniprot", "chembl", "inchikey"):
        path = "identifiers." + namespace
        node = member.get(path) or {}
        values = node.get("value")
        values = values if isinstance(values, list) else [values]
        for identifier in node.get("source_assertion_ids", []):
            if member_ref + "#" + identifier not in bound:
                continue
            assertion = member.source_assertion_store.get(identifier)
            if assertion is None or assertion["field_path"] != path:
                continue
            stated = assertion["asserted_value"]
            stated = stated if isinstance(stated, list) else [stated]
            identities.update(
                namespace + ":" + value
                for value in values
                if isinstance(value, str) and value in stated
            )
    candidates = basis.get("candidate_refs", [])
    return bool(candidates) and set(candidates) <= identities


def explain_support(deck, card_id):
    """Inspect recorded membership/exclusion support without acquisition or new rules."""
    cards = support_cards(deck.meta)
    if not cards:
        return {
            "status": "not_recorded",
            "gaps": [{"reason": "membership_support_not_recorded"}],
        }
    by_ref = {card.pinned_ref(): card for card in cards.values()}
    by_ref.update({card.pinned_ref(): card for card in deck.cards})
    bases = (
        [deck.basis(card_id)]
        if deck.basis(card_id) is not None
        else [
            e.get("basis")
            for e in deck.meta.get("excluded", [])
            if e["candidate"] == card_id
        ]
    )
    gaps, statements = [], []
    for basis in bases:
        if basis is None:
            gaps.append({"reason": "candidate_support_not_recorded"})
            continue
        if basis.get("input_card_ref") != cards["input"].pinned_ref():
            gaps.append({"reason": "wrong_input_card"})
        expected_refs = [
            cards["assertions"].pinned_ref() + "#" + i
            for i in basis.get("source_assertion_ids", [])
        ]
        if basis.get("source_assertion_refs") != expected_refs:
            gaps.append({"reason": "source_assertion_bindings_differ"})
        identity_values = {
            (cards["input"].get("identifiers.mondo") or {}).get("value"),
            *(cards["input"].get("identifiers.equivalent_ids") or {}).get("value", []),
        }
        if not set(basis.get("query_ids", [])) <= identity_values:
            gaps.append({"reason": "disease_identity_not_on_input"})
        member = next((c for c in deck.cards if c.id == card_id), None)
        if basis.get("member_card_ref") and (
            member is None or basis["member_card_ref"] != member.pinned_ref()
        ):
            gaps.append({"reason": "wrong_member_card"})
        if member is not None and not _member_candidate_matches(member, basis):
            gaps.append({"reason": "candidate_not_stated_by_member_identity"})
        groups = {}
        for key in (
            "source_assertion_refs",
            "identity_source_assertion_refs",
            "member_identity_source_assertion_refs",
        ):
            found = []
            for ref in basis.get(key, []):
                owner, _, item = ref.rpartition("#")
                card = by_ref.get(owner)
                assertion = card.source_assertion_store.get(item) if card else None
                found.append(
                    {
                        "source_assertion_ref": ref,
                        "found": assertion is not None,
                        "assertion": deepcopy(assertion),
                    }
                )
                if assertion is None:
                    gaps.append({"reason": "missing_source_assertion", "ref": ref})
                elif key == "source_assertion_refs" and not _candidate_matches(
                    assertion, basis
                ):
                    gaps.append(
                        {"reason": "statement_does_not_support_candidate", "ref": ref}
                    )
                elif key == "identity_source_assertion_refs" and (
                    owner != cards["input"].pinned_ref()
                    or assertion["field_path"]
                    not in ("identifiers.mondo", "identifiers.equivalent_ids")
                ):
                    gaps.append(
                        {"reason": "wrong_disease_identity_support", "ref": ref}
                    )
                elif (
                    key == "member_identity_source_assertion_refs"
                    and owner != basis.get("member_card_ref")
                ):
                    gaps.append({"reason": "wrong_member_identity_support", "ref": ref})
            groups[key] = found
        if not groups["source_assertion_refs"]:
            gaps.append({"reason": "membership_statements_not_recorded"})
        if not groups["identity_source_assertion_refs"]:
            gaps.append({"reason": "disease_identity_support_not_recorded"})
        stated_ids = set()
        for item in groups["identity_source_assertion_refs"]:
            if item["assertion"] is None:
                continue
            value = item["assertion"]["asserted_value"]
            if isinstance(value, str):
                stated_ids.add(value)
            elif isinstance(value, list):
                stated_ids.update(v for v in value if isinstance(v, str))
        if not set(basis.get("query_ids", [])) <= stated_ids:
            gaps.append({"reason": "disease_identity_not_stated_by_support"})
        if (
            basis.get("member_card_ref")
            and not groups["member_identity_source_assertion_refs"]
        ):
            gaps.append({"reason": "member_identity_support_not_recorded"})
        statements.append({"basis": deepcopy(basis), **groups})
        native = {
            item["assertion"]["id"]: item["assertion"]
            for item in groups["source_assertion_refs"]
            if item["assertion"] is not None
        }
        for statement in basis.get("statements", []):
            originals = [
                native[i]
                for i in statement.get("source_assertion_ids", [])
                if i in native
            ]
            if statement.get("source") == "Open Targets":
                responses = [a for a in originals if "rows" in a["asserted_value"]]
                associations = [a for a in originals if "row" in a["asserted_value"]]
                for a in associations:
                    row = a["asserted_value"]["row"]
                    target = row.get("target") or {}
                    rank = statement.get("rank")
                    if any(
                        statement.get(k) != v
                        for k, v in {
                            "score": row.get("score"),
                            "symbol": target.get("approvedSymbol"),
                            "gene": f"ensembl:{target.get('id')}",
                            "version": a["source"].get("version"),
                        }.items()
                    ) or not any(
                        isinstance(rank, int)
                        and 0 < rank <= len(r["asserted_value"]["rows"])
                        and r["asserted_value"]["rows"][rank - 1] == row
                        for r in responses
                    ):
                        gaps.append(
                            {
                                "reason": "membership_metadata_differs_from_source",
                                "ref": a["id"],
                            }
                        )
            elif statement.get("source") == "Orphanet":
                for a in originals:
                    row = a["asserted_value"]
                    if any(
                        statement.get(k) != v
                        for k, v in {
                            "gene": row.get("gene_symbol"),
                            "association_type": row.get("association_type"),
                            "association_status": row.get("association_status"),
                            "version": a["source"].get("version"),
                        }.items()
                    ):
                        gaps.append(
                            {
                                "reason": "membership_metadata_differs_from_source",
                                "ref": a["id"],
                            }
                        )
        if "indications" in basis and basis["indications"] != [
            a["asserted_value"] for a in native.values()
        ]:
            gaps.append({"reason": "membership_metadata_differs_from_source"})
    return {
        "rule": EXPLANATION_RULE,
        "input_card_ref": cards["input"].pinned_ref(),
        "assertion_card_ref": cards["assertions"].pinned_ref(),
        "statements": statements,
        "status": "partial" if gaps else "recorded" if statements else "not_in_result",
        "gaps": gaps,
    }
