"""Literal SDK230 source-value access and comparative support fields."""


def assertion_value(assertion):
    """Value used for resolution: the normalized value when present, else the asserted one."""
    if "normalized_value" in assertion:
        return assertion["normalized_value"]
    return assertion.get("asserted_value")


GLOSSARY_PREDICATES = {
    "same_as",
    "has_ligand_site",
    "engages",
    "has_bioactivity",
    "has_structure",
}


class _Support:
    def __init__(self, card, *, predicates=GLOSSARY_PREDICATES):
        self.card = card
        self.pin = card.pinned_ref()
        self.gaps = []
        self.links = {
            rel["id"]: self.relationship(rel)
            for rel in card.relationships()
            if rel["predicate"] in predicates
        }

    def relationship(self, rel):
        ref = f"{self.pin}#{rel['id']}"
        ids = rel.get("source_assertion_ids") or []
        if not ids and not rel.get("derivation"):
            self.gaps.append(
                {"reason": "no_relationship_support", "relationship_ref": ref}
            )
        assertions = self.assertions(ids)
        return {
            "relationship_ref": ref,
            "relationship": rel,
            "source_assertions": assertions,
        }

    def assertions(self, ids):
        assertions = [
            {**row, "source_assertion_ref": f"{self.pin}#{row['id']}"}
            for row in self.card.explain(sorted(set(ids)), skip_digestion=True)
        ]
        self.gaps.extend(
            {
                "reason": "missing_source_assertion",
                "source_assertion_ref": row["source_assertion_ref"],
            }
            for row in assertions
            if not row["found"]
        )
        return assertions

    def field(self, path):
        node = self.card.get(path)
        if node is None:
            return {"field_path": path, "stored": False}
        ids = node.get("source_assertion_ids") or []
        if not ids:
            self.gaps.append(
                {
                    "reason": "no_selected_source_assertion",
                    "field_path": path,
                    "card_ref": self.pin,
                }
            )
        conflicts = [
            c
            for c in self.card.quality.get("conflicts") or []
            if c.get("field") == path
        ]

        def flatten(ids):
            for value in ids:
                if isinstance(value, str):
                    yield value
                else:
                    yield from flatten(value)

        return {
            "field_path": path,
            "stored": True,
            "node": node,
            "source_assertions": self.assertions(ids),
            "alternatives": self.assertions(
                [
                    a["id"]
                    for a in self.card.source_assertion_store.to_list()
                    if a.get("field_path") == path and a["id"] not in ids
                ]
            ),
            "conflicts": conflicts,
            "conflict_source_assertions": self.assertions(
                list(flatten([c.get("source_assertion_ids") or [] for c in conflicts]))
            ),
            "selection_rules": self.card.selection_rules,
        }

    def context(self, selected):
        entities = self.card.entities()
        return {
            "scope": "whole_card_grouping_and_glossary_inputs",
            "relationships": [
                link for rid, link in self.links.items() if rid not in selected
            ],
            "entities": entities,
            "stored_identities": [
                {
                    "locator": {
                        "card_ref": self.pin,
                        "field_path": "entities",
                        "key": key,
                    },
                    "record": entities[key],
                    "basis": "stored_identity_record",
                    "source_assertion_membership": "not_recorded",
                }
                # A registered anchor may be a record of another indexed entity.
                # Context locators describe the actual serialized glossary at this pin.
                for key in sorted(entities)
                if entities[key].get("identity")
            ],
        }
