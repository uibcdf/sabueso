"""Pinned support for measurement identity and bioactivity classes (#91).

Collectors in the existing engines record their actual branches. Whole-card
grouping/glossary inputs remain explicit context: candidate uniqueness and entity
mapping cannot be justified from only the selected records. No source identity
path or per-request membership is reconstructed or invented.
"""

from copy import deepcopy

from .bioactivities import CLASS_ORDER, bioactivities_view
from .measurements import half_unit, measurement_groups
from .relationship_store import make_derivation

MEASUREMENT_RULE = "measurement_group_explanation@1"
BIOACTIVITY_RULE = "bioactivity_explanation@1"
GLOSSARY_PREDICATES = {
    "same_as",
    "has_ligand_site",
    "engages",
    "has_bioactivity",
    "has_structure",
}


class _Support:
    def __init__(self, card):
        self.card = card
        self.pin = card.pinned_ref()
        self.gaps = []
        self.links = {
            rel["id"]: self.relationship(rel)
            for rel in card.relationships()
            if rel["predicate"] in GLOSSARY_PREDICATES
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
                for key in sorted(self.card.entity_identities)
            ],
        }


def _group(identity, ref, info):
    gid = identity["group_of"].get(ref, ref)
    group = next((g for g in identity["groups"] if g["id"] == gid), None)
    if group is None and ref in identity["group_of"]:
        group = {
            "id": gid,
            "records": [ref],
            "sources": [info[ref]["source"]],
            "basis": ["single_record"],
        }
    return group


def _joins(identity, trace, selected):
    rows = []
    for a, b, basis in trace["edges"]:
        if not ({a, b} & selected):
            continue
        ia, ib = trace["info"][a], trace["info"][b]
        selector = trace["selectors"].get(
            (a, b), {"basis": "shared_statement", "precision_used": True}
        )
        ma, mb = ia["measurement"], ib["measurement"]
        na, nb = ma.get("normalized") or {}, mb.get("normalized") or {}
        precision = None
        if (
            selector["precision_used"]
            and na
            and nb
            and na.get("unit") == nb.get("unit")
        ):
            ha, hb = half_unit(ma), half_unit(mb)
            precision = {
                "values": [na, nb],
                "half_last_digit": [
                    None if h is None else {"value": h, "unit": na["unit"]}
                    for h in (ha, hb)
                ],
                "tolerance": {
                    "value": max(h for h in (ha, hb, 0.0) if h is not None),
                    "unit": na["unit"],
                },
                "numerical_slack": {"value": 1e-9, "unit": na["unit"]},
            }
        rows.append(
            {
                "records": [a, b],
                "basis": basis,
                "selector": selector,
                "accepted": identity["group_of"][a] == identity["group_of"][b],
                "shared_publications": [
                    {"namespace": ns, "id": identifier}
                    for ns, identifier in sorted(
                        ia["publications"] & ib["publications"]
                    )
                ],
                "shared_molecule_keys": sorted(ia["molecules"] & ib["molecules"]),
                "precision": precision,
            }
        )
    return rows


def explain_measurement(card, measurement_ref):
    support = _Support(card)
    trace = {}
    identity = measurement_groups(card, _support=trace)
    group = _group(identity, measurement_ref, trace["info"])
    selected = set(group["records"]) if group else set()
    diagnostics = {
        key: [
            row
            for row in identity[key]
            if selected
            & (
                {row.get("record")}
                | set(row.get("records") or [])
                | set(row.get("candidates") or [])
            )
        ]
        for key in ("ambiguous", "unresolved_copies", "review")
    }
    return deepcopy(
        {
            "rule": make_derivation(
                MEASUREMENT_RULE,
                inputs=[support.pin],
                parameters={"measurement_ref": measurement_ref},
            ),
            "card_ref": support.pin,
            "measurement_ref": measurement_ref,
            "status": "not_on_card"
            if group is None
            else "partial"
            if support.gaps
            else "on_card",
            "group": group,
            "grouping_rule": identity["rule"],
            "joins": _joins(identity, trace, selected),
            "records": [support.links[rid] for rid in sorted(selected)],
            "diagnostics": diagnostics,
            "context": support.context(selected),
            "gaps": support.gaps,
        }
    )


def explain_bioactivity(card, molecule_ref, include_indirect=False, thresholds=None):
    support = _Support(card)
    trace = {}
    view = bioactivities_view(card, include_indirect, thresholds, _support=trace)
    item = next((i for i in view["items"] if i["molecule_ref"] == molecule_ref), None)
    selected = {m["relationship_id"] for m in item["measurements"]} if item else set()
    groups = []
    for decision in trace["groups"]:
        if decision["molecule_ref"] != molecule_ref:
            continue
        identity = _group(
            trace["identity"], decision["group"], trace["identity_support"]["info"]
        )
        if identity is None:  # A singleton is selected by its relationship id.
            identity = _group(
                trace["identity"],
                decision["records"][0],
                trace["identity_support"]["info"],
            )
        groups.append(
            {
                **decision,
                "identity": identity,
                "joins": _joins(
                    trace["identity"],
                    trace["identity_support"],
                    set(identity["records"]),
                ),
            }
        )
    return deepcopy(
        {
            "rule": make_derivation(
                BIOACTIVITY_RULE,
                inputs=[support.pin],
                parameters={
                    "molecule_ref": molecule_ref,
                    "include_indirect": include_indirect,
                    "thresholds": {
                        name: view["classification"]["parameters"][name]
                        for name in ("active_max", "weak_max", "single_point_min")
                    },
                    "class_order": list(CLASS_ORDER),
                    "group_class": "one voter class, otherwise inconclusive",
                    "molecule_class": "strongest group class",
                    "discordance": "active or weak groups together with inactive groups",
                },
            ),
            "card_ref": support.pin,
            "molecule_ref": molecule_ref,
            "status": "not_on_card"
            if item is None
            else "partial"
            if support.gaps
            else "on_card",
            "item": item,
            "classification": view["classification"],
            "checks": view["checks"],
            "scope": view["scope"],
            "groups": groups,
            "records": [support.links[rid] for rid in sorted(selected)],
            "record_decisions": trace["records"],
            "measurement_identity": trace["identity"],
            "context": support.context(selected),
            "gaps": support.gaps,
        }
    )
