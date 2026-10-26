"""Immutable original site-comparison verifier inputs, never new knowledge.

The scientific predicates and presentation recipe below freeze the qualified
original implementation. Readers compare retained output with these expectations;
they never substitute it for the original result or call live scientific engines.
"""

from copy import deepcopy
from dataclasses import dataclass
from types import SimpleNamespace

from ._card_ligand_site_native_v1 import ANNOTATED_SITES
from .card_access import _Entry, _handle
from .card_exploration_history import _rule
from .card_exploration_verification import _historical_resolution
from .card_ligand_site_selection_v1 import COLUMNS as AGENT_COLUMNS
from .card_ligand_site_selection_v1 import DEFAULT_FIELDS, item_ref
from .card_ligand_site_selection_v1 import FORMAT as SELECTION_POLICY

GLOSSARY_PREDICATES = {
    "same_as",
    "has_ligand_site",
    "engages",
    "has_bioactivity",
    "has_structure",
}
RULE = "retained_context_links@2"
SUPPORT_FORMAT = "ligand_site_support_membership@1"


def _rule_identity(rule):
    return {key: value for key, value in rule.items() if key != "sabueso_version"}


TOPIC = "ligand_site_comparisons"

ADAPTER = "ligand_site_exploration@1"

LINK_RULE = "ligand_site_context_links@1"

COLUMNS = ("ligand_ref", "comparison_status", "outcome", "matched_sites", "reason")

HEADERS = (
    "Index",
    "Ligand",
    "Ligand reference",
    "Comparison",
    "Finding",
    "Matched sites",
    "Context",
)

SCOPE = (
    "One retained protein–ligand contact declaration per item, not a count of ligand "
    "molecules. Source-declared sequence numbering only; atomic proximity and sequence "
    "revision agreement are not established. Unknown comparison is not a negative "
    "overlap. Aggregated contacts, structure-local instances and assemblies remain "
    "separate contexts. Source/request coverage: explorer.view('coverage')."
)

OUTCOMES = {
    "overlaps_annotated_site": "Overlap with a retained annotated site",
    "no_annotated_overlap": "No overlap among retained comparable sites",
    "no_annotated_sites": "No annotated sites retained on this Card",
    "numbering_not_comparable": "Contact numbering is not comparable",
    "comparison_not_computed": "Comparison not computed",
}

REASONS = {
    "annotation_axis_not_canonical": "The annotation is not placed on the focal canonical sequence.",
    "annotation_positions_uncertain_or_invalid": "Annotation bounds are uncertain or invalid.",
    "annotation_sequence_revision_differs": "Annotation and reference revisions are invalid or inconsistent.",
    "canonical_identity_sequence_or_length_unavailable": "Canonical identity, sequence or length is unavailable or inconsistent.",
    "conflicting_canonical_inputs": "Canonical reference inputs conflict.",
    "conflicting_annotation_inputs": "Annotation inputs conflict.",
    "canonical_source_support_unavailable": "Canonical reference source support is unavailable.",
    "annotation_source_support_unavailable": "Annotation source support is unavailable.",
    "contact_numbering_not_comparable": "The original contact numbering is not canonical UniProt numbering.",
    "contact_positions_unstated_or_invalid": "Contact positions are unstated, uncertain or invalid.",
    "native_annotation_scope_not_retained": "The original annotation coordinate context was not retained.",
}

SITE_LABELS = {
    "active_site": "Active site",
    "binding_site": "Binding site",
    "family_site": "Family-model site",
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
                for key in sorted(self.card.entity_identities)
            ],
        }


def _explain_ligand_site(card, ligand_site_ref, view):
    """Explain an already evaluated view over the same private captured Card."""
    support = _Support(card)
    item = next(
        (i for i in view["items"] if i["relationship_id"] == ligand_site_ref), None
    )
    fields = [support.field(path) for path in ANNOTATED_SITES.values()]
    reference_fields = [
        support.field(path)
        for path in ("identifiers.uniprot", "sequence.primary", "sequence.length")
    ]
    for annotation in view["annotated_sites"]:
        if not annotation["source_assertion_id"]:
            support.gaps.append(
                {
                    "reason": "no_matching_annotation_assertion",
                    "annotation": annotation,
                    "card_ref": support.pin,
                }
            )
    return deepcopy(
        {
            "rule": _rule(
                "ligand_site_explanation@1",
                inputs=[support.pin],
                parameters={"ligand_site_ref": ligand_site_ref},
            ),
            "card_ref": support.pin,
            "ligand_site_ref": ligand_site_ref,
            "status": "not_on_card"
            if item is None
            else "partial"
            if support.gaps
            else "on_card",
            "item": item,
            "classification": view["classification"],
            "classification_inputs": {
                "numbering": (
                    (support.links.get(ligand_site_ref) or {}).get("relationship") or {}
                )
                .get("qualifiers", {})
                .get("numbering"),
                "annotated_site_count": len(view["annotated_sites"]),
                "annotated_sites": view["annotated_sites"],
                "fields": fields,
                "reference_fields": reference_fields,
                "coordinate_reference": view["canonical_reference"],
                "absence_basis": "stored annotated positions only; never external source absence",
            },
            "site": support.links.get(ligand_site_ref) if item else None,
            "context": {
                "scope": "whole_card_stored_inputs",
                "relationships": [
                    link
                    for rid, link in support.links.items()
                    if rid != ligand_site_ref
                ],
                "curated_engagements": view["curated_engagements"],
                "reports": [
                    {
                        "locator": {
                            "card_ref": support.pin,
                            "field_path": "quality.enrichments",
                            "index": i,
                        },
                        "record": record,
                    }
                    for i, record in enumerate(card.quality.get("enrichments") or [])
                ],
                "instance_basis": "stored has_structure ligand instances; aggregate residue chains never imply spanning",
            },
            "gaps": support.gaps,
        }
    )


def _row(item, native):
    comparison = item["comparison"]
    missing = comparison["uncomputed_annotation_indices"]
    reasons = [comparison["contact_scope"].get("reason")]
    reasons.extend(native["annotated_sites"][i]["scope"].get("reason") for i in missing)
    reasons = list(dict.fromkeys(reason for reason in reasons if reason))
    reason = " ".join(
        REASONS.get(
            code,
            "Coordinate context could not be admitted; inspect its original scope and reason code.",
        )
        for code in reasons
    )
    if item["site_class"] == "no_annotated_sites":
        reason = "No retained annotation is available for comparison; this is not external source absence."
    if not reason:
        reason = "Compared using source-declared canonical numbering; unstated revisions do not establish agreement."
    outcome = OUTCOMES.get(item["site_class"], "Unrecognized retained classification")
    if comparison["status"] == "partial":
        outcome += "; other annotations were not compared"
    matches = "; ".join(
        f"{SITE_LABELS.get(row['kind'], row['kind'])}: {row.get('description') or 'Unnamed annotation'} ({row.get('source') or 'source not retained'})"
        for row in item["annotated_overlap"]
    ) or (
        "None among comparable retained annotations"
        if comparison["status"] == "computed"
        else "Not computed"
    )
    return {
        "label": item["name"]
        if isinstance(item.get("name"), str) and item["name"]
        else item["ligand_ref"],
        "ligand_ref": item["ligand_ref"],
        "comparison_status": comparison["status"],
        "outcome": outcome,
        "matched_sites": matches,
        "reason": reason,
        "item": deepcopy(item),
    }


def _location(access, store, ref):
    return {
        **access._card_location(),
        "segments": [
            {"type": "Key", "value": store},
            {"type": "Record", "value": ref},
        ],
    }


def _statement(access, ref):
    location = _location(access, "source_assertion_store", ref)
    from .errors import ArgumentError

    try:
        access._resolve(location)
    except ArgumentError:
        return {"id": ref, "state": "not_retained", "location": None}
    return {"id": ref, "state": "present", "location": location}


def _support(access, item, native):
    def references(value):
        return (
            [ref for ref in value if isinstance(ref, str)]
            if isinstance(value, list)
            else []
        )

    ids = set(native["canonical_reference"].get("inputs", []))
    ids.update(
        references(item["comparison"]["contact_scope"].get("source_assertion_ids"))
    )
    for annotation in native["annotated_sites"]:
        refs = annotation["scope"].get("field_source_assertion_ids")
        if isinstance(refs, list):
            ids.update(ref for ref in refs if isinstance(ref, str))
    relationships = {r["id"]: r for r in access._focal.data["relationship_store"]}
    for ref in item["structure_support"]["relationship_ids"]:
        ids.update(references(relationships[ref].get("source_assertion_ids")))
    return {
        "basis": "derived_ligand_site_comparison",
        "rule": deepcopy(native["classification"]),
        "coordinate_scope_rule": "ligand_site_coordinate_scope@1",
        "relationship_location": _location(
            access, "relationship_store", item["relationship_id"]
        ),
        "source_assertions": [_statement(access, ref) for ref in sorted(ids)],
        "scope": "Original classification inputs; source context is not independent support for a project conclusion.",
    }


def _materialize(access):
    from .card_exploration_history import _HistoricalInput as _CapturedCard

    native, rows, explanations, support = {}, {}, {}, {}
    status, reason = "not_applicable", "Ligand-site comparisons require a protein Card."
    if access.profile == "protein" and not access._focal.pin:
        status, reason = (
            "missing_prerequisite",
            "A captured protein identity is required; inspect the original content.",
        )
    elif access.profile == "protein":
        from ._card_ligand_site_native_v1 import ligand_sites_view

        card = _CapturedCard(access._focal)
        native = ligand_sites_view(card)
        for item in native["items"]:
            key = item["relationship_id"]
            rows[key] = _row(item, native)
            explanations[key] = _explain_ligand_site(card, key, native)
            support[key] = _support(access, item, native)
        status = "ok" if rows else "empty"
        reason = (
            None
            if rows
            else "No ligand contact declarations are retained; inspect source/request coverage rather than inferring no binding."
        )
    identity = deepcopy(native)
    if "classification" in identity:
        identity["classification"] = _rule_identity(identity["classification"])
    ref = _handle(
        "XR_",
        {"adapter": ADAPTER, "focal": access._focal_key, "native": identity},
    )
    for key, row in rows.items():

        def result_location(*keys):
            return {
                "format": "card_access_location@1",
                "kind": "result",
                "result_ref": ref,
                "segments": [{"type": "Key", "value": value} for value in keys],
            }

        row["support_location"] = result_location("support", key)
        row["explanation_location"] = result_location("explanations", key)
        row["interpretation"] = {
            "scope": SCOPE,
            "classification_rule": native["classification"]["rule"],
        }
    payload = {
        "context": {
            **access.context,
            "adapter": ADAPTER,
            "options": {},
            "used_captures": [access._focal_key],
        },
        "native_payload": native,
        "rows": rows,
        "explanations": explanations,
        "support": support,
        "scope": SCOPE,
        "outcome": {"status": status, "reason": reason},
    }
    access._objects[ref] = payload
    return ref


def payload(item):
    return item._view.explorer.access._objects[item._entry.location["result_ref"]]


def support(item):
    return [deepcopy(payload(item)["support"][item._entry.key])]


def links(item):
    """Exact retained inputs and structure context, without aggregate/instance joins."""

    explorer = item._view.explorer
    basis = support(item)
    rows = []
    for statement in basis[0]["source_assertions"]:
        if statement["state"] == "present":
            rows.append(
                _link(
                    explorer,
                    "source",
                    statement["id"],
                    basis,
                    location=statement["location"],
                )
            )
        else:
            rows.append(
                {
                    "role": "source",
                    "label": "Unavailable original input · " + statement["id"],
                    "target_ref": statement["id"],
                    "support": deepcopy(basis),
                    "rule": LINK_RULE,
                    "candidates": [],
                    "paths": [],
                    "blocked_paths": [],
                    "availability": "missing_prerequisite",
                }
            )
    native = item._entry.value["item"]
    seen = set()
    for annotation in payload(item)["native_payload"].get("annotated_sites", []):
        context = annotation["scope"]
        field, index = context["field_path"], context["index"]
        if (field, index) in seen:
            continue
        seen.add((field, index))
        location = explorer._location("sections", *field.split("."), "value")
        if index is not None:
            location["segments"].append({"type": "Index", "value": index})
        link = _link(
            explorer, "annotation", explorer.access._focal.pin, basis, location=location
        )
        link["label"] = (
            "Original annotation · "
            + annotation["kind"]
            + " · "
            + str(annotation.get("description") or "Unnamed annotation")
        )
        rows.append(link)
    rel_id = native["relationship_id"]
    rows.append(
        _link(
            explorer,
            "contact",
            rel_id,
            basis,
            location=_location(explorer.access, "relationship_store", rel_id),
        )
    )
    rows.append(_link(explorer, "object", native["ligand_ref"], basis))
    for ref in native["structure_support"]["relationship_ids"]:
        location = _location(explorer.access, "relationship_store", ref)
        link = _link(
            explorer,
            "structure",
            ref,
            basis,
            location=location,
        )
        link["label"] = "Original structure context · " + ref
        rows.append(link)
        record = explorer.access._resolve(location)[0]
        conflicts = record.get("qualifier_conflicts")
        if conflicts:
            link["label"] += " · conflicting qualifiers"
        focal = payload(item)["native_payload"]["canonical_reference"]["sequence_ref"]
        if not isinstance(focal, str) or record["subject_ref"] != focal:
            continue
        qualifiers = record.get("qualifiers") or {}
        context_support = explorer._support(location)
        if "assemblies" in qualifiers:
            assembly_location = {
                **location,
                "segments": [
                    *location["segments"],
                    {"type": "Key", "value": "qualifiers"},
                    {"type": "Key", "value": "assemblies"},
                ],
            }
            assembly = _link(
                explorer,
                "assembly_context",
                record["object_ref"],
                context_support,
                location=assembly_location,
            )
            assembly["label"] = "Original assembly context · " + record["object_ref"]
            if conflicts:
                assembly["label"] += " · conflicting qualifiers"
            rows.append(assembly)
        ligands = qualifiers.get("ligands")
        for ligand_index, ligand in enumerate(
            ligands if isinstance(ligands, list) else []
        ):
            if (
                not isinstance(ligand, dict)
                or not isinstance(ligand.get("comp_id"), str)
                or "pdb.ligand:" + ligand["comp_id"] != native["ligand_ref"]
            ):
                continue
            instances = ligand.get("instances")
            for instance_index, instance in enumerate(
                instances if isinstance(instances, list) else []
            ):
                instance_location = {
                    **location,
                    "segments": [
                        *location["segments"],
                        {"type": "Key", "value": "qualifiers"},
                        {"type": "Key", "value": "ligands"},
                        {"type": "Index", "value": ligand_index},
                        {"type": "Key", "value": "instances"},
                        {"type": "Index", "value": instance_index},
                    ],
                }
                context = _link(
                    explorer,
                    "instance_context",
                    record["object_ref"],
                    context_support,
                    location=instance_location,
                )
                context["label"] = (
                    f"Structure-local context · {record['object_ref']} · component {ligand['comp_id']} · original occurrence {instance_index + 1}"
                )
                if conflicts:
                    context["label"] += " · conflicting qualifiers"
                context["component_scope"] = {
                    "rule": LINK_RULE,
                    "component_ref": native["ligand_ref"],
                    "basis": "same source-declared PDB component only; no aggregate-to-instance correspondence or assembly projection",
                    "qualifier_conflicts": deepcopy(conflicts),
                }
                rows.append(context)
    rows = [{**row, "rule": LINK_RULE} for row in rows]
    return _link_view(
        explorer,
        rows,
        item._view,
        f"Original context for {item.label}",
        source_location=item.payload_location,
        rule=LINK_RULE,
    )


def _link(explorer, role, target, support, *, location=None):
    label = f"{role.capitalize()} · {target}"
    if role == "source" and location:
        original, _ = explorer.access._resolve(location)
        fields = {
            "sequence.checksums": "reference sequence checksums",
            "sequence.primary": "reference primary sequence",
            "identifiers.uniprot": "reference UniProt identity",
            "sequence.length": "reference sequence length",
            "annotations.isoforms": "UniProt isoform declaration",
            "relationships.has_predicted_structure": "predicted model metadata",
        }
        if isinstance(original, dict) and original.get("field_path") in fields:
            label = f"Source · {fields[original['field_path']]} · {target}"
    resolution = (
        {
            "candidates": [
                {
                    "location": location,
                    "capture": explorer.access._focal_key,
                    "basis": "exact_retained_node",
                }
            ],
            "paths": [],
            "blocked_paths": [],
            "availability": "available",
        }
        if location
        else _historical_resolution(explorer.access, target)
    )
    return {
        "role": role,
        "label": label,
        "target_ref": target,
        "support": deepcopy(support),
        "rule": RULE,
        **resolution,
    }


def _source_membership(access, original):
    """One exact source-store path, with complete original member IDs/states.

    All comparison inputs are retained on this focal capture. A present member's
    full location appends Record(id) to this container; absent members have no
    destination. The original per-statement locations remain in support_location.
    """
    return {
        "format": SUPPORT_FORMAT,
        "basis": original["basis"],
        "source_store_location": access._card_location(
            segments=[{"type": "Key", "value": "source_assertion_store"}]
        ),
        "source_assertions": [
            {"id": statement["id"], "state": statement["state"]}
            for statement in original["source_assertions"]
        ],
    }


@dataclass(frozen=True)
class _SiteResult:
    result_ref: str
    wire: dict
    entries: tuple

    @property
    def native(self):
        return self.wire["native_payload"]

    @property
    def options(self):
        return {}

    def native_item(self, key):
        return self.wire["rows"][key]["item"]

    def location(self, *keys):
        return {
            "format": "card_access_location@1",
            "kind": "result",
            "result_ref": self.result_ref,
            "segments": [{"type": "Key", "value": key} for key in keys],
        }

    def value(self, key, column):
        row = self.wire["rows"][key]
        return (
            "ligand_contact_comparison"
            if column == "kind"
            else row["item"]["site_class"]
            if column == "site_class"
            else row[column]
        )

    def frame(self, access, selection, entry):
        key = entry.key
        row = self.wire["rows"][key]
        original_support = self.wire["support"][key]
        interpretation_location = access._location(
            self.location("rows", key, "interpretation")
        )
        return {
            "item_ref": item_ref(self, entry),
            "kind": "ligand_contact_comparison",
            "label": row["label"],
            "location": access._location(entry.location),
            "payload_location": access._location(self.location("rows", key, "item")),
            "relationship_ref": key,
            "subject_ref": access._resolve(original_support["relationship_location"])[
                0
            ]["subject_ref"],
            "state": "present",
            "support_location": access._location(self.location("support", key)),
            "support": {
                "ref": key,
                **_source_membership(access, original_support),
            },
            "interpretation": deepcopy(row["interpretation"]),
            "interpretation_location": interpretation_location,
            "cells": {
                column: {
                    "state": "present",
                    "reason": None,
                    "value": deepcopy(self.value(key, column)),
                    "field": {"adapter": ADAPTER, "column": column},
                    "support_basis": "derived_ligand_site_comparison",
                    "support_ref": key,
                    "value_included": True,
                    "value_location": access._object_location(
                        "ligand_contact_comparison"
                    )
                    if column == "kind"
                    else access._location(
                        self.location("rows", key, "item", "site_class")
                        if column == "site_class"
                        else self.location("rows", key, column)
                    ),
                    "interpretation_location": interpretation_location,
                }
                for column in selection._fields
            },
            "value_included": True,
            "inspection_required": False,
        }


def defer_frame(frame):
    """Defer values and mandatory comparison context as one inspectable unit."""
    result = {
        key: deepcopy(value)
        for key, value in frame.items()
        if key not in ("label", "interpretation", "support", "cells")
    }
    result.update(
        cells={
            key: {k: deepcopy(v) for k, v in cell.items() if k != "value"}
            | {"value_included": False}
            for key, cell in frame["cells"].items()
        },
        value_included=False,
        inspection_required=True,
        value_location=frame["location"],
        reason="value_and_interpretation_exceed_response_budget",
    )
    return result


def _link_view(explorer, links, origin, title, *, source_location=None, rule=RULE):
    return {
        "rule": rule,
        "inputs": explorer.context["captures"],
        "focal": explorer.access._focal_key,
        "source_location": source_location,
        "links": links,
    }


class _Context:
    def __init__(self, access):
        self.access = access

    @property
    def context(self):
        return self.access.context

    def _location(self, *keys):
        return self.access._card_location(
            segments=[{"type": "Key", "value": key} for key in keys]
        )

    def _support(self, location):
        record, _ = self.access._resolve(location)
        refs = record.get("source_assertion_ids", [])
        proof = {
            "basis": "relationship_level",
            "location": location,
            "source_assertion_ids": deepcopy(refs),
            "statements": [_statement(self.access, ref) for ref in refs]
            if isinstance(refs, list) and all(isinstance(ref, str) for ref in refs)
            else [],
        }
        for key in ("derivation", "derivation_applications", "qualifier_conflicts"):
            if key in record:
                proof[key] = deepcopy(record[key])
        return [proof]


def restore_result(ref, wire):
    shell = _SiteResult(ref, wire, ())
    entries = tuple(
        _Entry(shell.location("rows", key), key, row)
        for key, row in sorted(
            wire["rows"].items(), key=lambda p: (p[1]["ligand_ref"], p[0])
        )
    )
    return _SiteResult(ref, wire, entries)


def expected_result(access):
    from .card_exploration_storage import _access

    original = _access(access._captures, access._inputs, {}, {}, access._focal_key)
    original._mode = "live"
    ref = _materialize(original)
    wire = original._objects[ref]
    wire["coverage"] = {
        "basis": "retained_contact_declarations",
        "scope": SCOPE,
        "source_request_classification": "not_evaluated_by_this_adapter",
    }
    for row in wire["rows"].values():
        row["interpretation"].update(
            comparison=deepcopy(row["item"]["comparison"]),
            coordinate_scope_rule="ligand_site_coordinate_scope@1",
            annotation_count_semantics="Retained source annotation contexts; not independently identified physical sites.",
        )
    return restore_result(ref, wire)


def expected_links(access, result, key):
    from .card_exploration_storage import _access

    original = _access(
        access._captures,
        access._inputs,
        {result.result_ref: result.wire},
        {},
        access._focal_key,
    )
    original._mode = "live"
    explorer = _Context(original)
    item = SimpleNamespace(
        _view=SimpleNamespace(explorer=explorer),
        _entry=SimpleNamespace(
            key=key,
            value=result.wire["rows"][key],
            location=result.location("rows", key),
        ),
        label=result.wire["rows"][key]["label"],
        payload_location=result.location("rows", key),
    )
    return links(item)


def descriptor():
    return {
        "key": TOPIC,
        "label": "Ligand contacts and annotated-site comparisons",
        "description": SCOPE,
        "adapter": ADAPTER,
        "scientific_adapter": True,
        "operations": ["select", "explain", "read", "page"],
        "columns": {key: {"type": "string"} for key in AGENT_COLUMNS},
        "default_fields": list(DEFAULT_FIELDS),
        "options": {},
        "projection": True,
        "machine_filter": True,
        "machine_order": True,
        "machine_membership": True,
        "selection_policy": SELECTION_POLICY,
        "mandatory_interpretation": ["scope", "comparison", "classification_rule"],
        "source_support": {
            "format": SUPPORT_FORMAT,
            "record_location": "Append Record(id) to source_store_location only for a present member.",
        },
        "save": True,
    }
