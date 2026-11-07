# Frozen original B4 predicates from 2eb6114 / SDK200.
# Private consistency expectations only; preserve these meanings.
"""Pinned support for measurement identity and bioactivity classes (#91).

Collectors in the existing engines record their actual branches. Whole-card
grouping/glossary inputs remain explicit context: candidate uniqueness and entity
mapping cannot be justified from only the selected records. No source identity
path or per-request membership is reconstructed or invented.
"""

from copy import deepcopy

from .bioactivities import CLASS_ORDER, bioactivities_view
from .measurement_correspondence import RULE as MEASUREMENT_V2
from .measurement_correspondence import measurement_groups, validate_measurement_rule
from .measurements import half_unit
from .rules import make_derivation

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


def explain_measurement(
    card, measurement_ref, *, measurement_rule="measurement_identity@1"
):
    measurement_rule = validate_measurement_rule(measurement_rule)
    support = _Support(card)
    trace = {}
    identity = measurement_groups(
        card, measurement_rule=measurement_rule, _support=trace
    )
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
        for key in (
            (
                "ambiguous",
                "unresolved_copies",
                "review",
                "possible_correspondences",
                "copy_diagnostics",
            )
            if measurement_rule == MEASUREMENT_V2
            else ("ambiguous", "unresolved_copies", "review")
        )
    }
    return deepcopy(
        {
            "rule": make_derivation(
                "measurement_group_explanation@2"
                if measurement_rule == MEASUREMENT_V2
                else MEASUREMENT_RULE,
                inputs=[support.pin],
                parameters={
                    "measurement_ref": measurement_ref,
                    **(
                        {"measurement_rule": measurement_rule}
                        if measurement_rule == MEASUREMENT_V2
                        else {}
                    ),
                },
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
            **(
                {
                    "counting": identity["counting"],
                    "comparison_scope": identity["comparison_scope"],
                }
                if measurement_rule == MEASUREMENT_V2
                else {}
            ),
            "context": support.context(selected),
            "gaps": support.gaps,
        }
    )


def explain_bioactivity(
    card,
    molecule_ref,
    include_indirect=False,
    thresholds=None,
    *,
    classification_rule="bioactivity_class@4",
    measurement_rule="measurement_identity@1",
    target_scope_rule="bioactivity_target_scope@1",
):
    from .bioactivity_class_v4 import RULE, thresholds_in_force
    from .bioactivity_class_v4 import classification_rule as validate_rule
    from .bioactivity_target_scope import RULE as TARGET_SCOPE_V2
    from .bioactivity_target_scope import validate_target_scope_rule

    target_scope_rule = validate_target_scope_rule(target_scope_rule)
    measurement_rule = validate_measurement_rule(measurement_rule)
    classification_rule = validate_rule(classification_rule)
    if classification_rule == RULE:
        thresholds_in_force(thresholds)
    support = _Support(card)
    trace = {}
    view = bioactivities_view(
        card,
        include_indirect,
        thresholds,
        _support=trace,
        classification_rule=classification_rule,
        measurement_rule=measurement_rule,
        target_scope_rule=target_scope_rule,
    )
    item = next((i for i in view["items"] if i["molecule_ref"] == molecule_ref), None)
    selected = {m["relationship_id"] for m in item["measurements"]} if item else set()
    outside_scope = (
        target_scope_rule == TARGET_SCOPE_V2
        and item is None
        and any(
            row.get("molecule_ref") == molecule_ref and not row["included"]
            for row in trace["records"]
        )
    )
    if outside_scope:
        selected = {
            row["relationship_id"]
            for row in trace["records"]
            if row.get("molecule_ref") == molecule_ref
        }
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
                "bioactivity_explanation@4"
                if target_scope_rule == TARGET_SCOPE_V2
                else "bioactivity_explanation@3"
                if measurement_rule == MEASUREMENT_V2
                else BIOACTIVITY_RULE
                if classification_rule == "bioactivity_class@3"
                else "bioactivity_explanation@2",
                inputs=[support.pin],
                parameters={
                    **(
                        {"target_scope_rule": target_scope_rule}
                        if target_scope_rule == TARGET_SCOPE_V2
                        else {}
                    ),
                    **(
                        {"measurement_rule": measurement_rule}
                        if measurement_rule == MEASUREMENT_V2
                        or target_scope_rule == TARGET_SCOPE_V2
                        else {}
                    ),
                    **(
                        {"classification_rule": classification_rule}
                        if classification_rule != "bioactivity_class@3"
                        else {}
                    ),
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
            "status": "outside_scope"
            if outside_scope
            else "not_on_card"
            if item is None
            else "partial"
            if support.gaps
            else "on_card",
            "item": item,
            "classification": view["classification"],
            "checks": view["checks"],
            "scope": view["scope"],
            **(
                {"target_selection": view["target_selection"]}
                if target_scope_rule == TARGET_SCOPE_V2
                else {}
            ),
            "groups": groups,
            "records": [support.links[rid] for rid in sorted(selected)],
            "record_decisions": trace["records"],
            "measurement_identity": trace["identity"],
            "context": support.context(selected),
            "gaps": support.gaps,
        }
    )
