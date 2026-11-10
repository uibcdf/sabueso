"""Retained protein relationships and explicitly supplied sequence comparisons.

Projection is not source validation or discovery. Source references keep their
recorded binding, and the native equal-length comparison establishes neither
residue correspondence nor entity identity.
"""

from copy import deepcopy
from dataclasses import dataclass

from .card_access import _Entry, _handle
from .card_protein_context_selection_v1 import COLUMNS, DEFAULT_FIELDS, FORMAT, item_ref
from .errors import ArgumentError
from .relationship_store import make_derivation
from .snapshot import canonical_json
from .source_assertion_store import assertion_value

ADAPTER = "protein_context_exploration@1"
SUPPORT_FORMAT = "protein_context_support@1"
PREDICATES = {
    "comparative_context": ("ortholog_of", "clustered_with"),
    "associations": (
        "associated_with",
        "participates_in",
        "interacts_with",
        "functionally_associated_with",
    ),
}
SCOPE = (
    "Captured protein relationship records with their recorded direction, source references, "
    "qualifiers, conflicts and derivations. Supplied comparison Cards are explicit inputs, "
    "not asserted relationships. No acquisition, identity merge, alignment, causal, "
    "pathogenicity, efficacy or interaction-mechanism inference. Source-reference binding "
    "does not independently validate a provider's mapping or scientific claim."
)
SAVE_REASON = "Independent original protein-context saved reading requires a clean producer capture and separate frozen reader."


def descriptor(topic):
    return {
        "key": topic,
        "label": "Related proteins and explicit comparisons"
        if topic == "comparative_context"
        else "Protein biological associations",
        "description": SCOPE,
        "adapter": ADAPTER,
        "scientific_adapter": True,
        "operations": ["select", "explain", "read", "page"],
        "columns": {
            c: {
                "type": "integer|null"
                if c in ("input_index", "difference_count")
                else "boolean|null"
                if c == "identical"
                else "string|null"
            }
            for c in COLUMNS
        },
        "default_fields": list(DEFAULT_FIELDS),
        "options": {"mode": "relationships"} if topic == "comparative_context" else {},
        "projection": True,
        "machine_filter": True,
        "machine_order": True,
        "machine_membership": True,
        "selection_policy": FORMAT,
        "source_support": {"format": SUPPORT_FORMAT},
        "mandatory_interpretation": [
            "rule",
            "scope",
            "row_grain",
            "identity",
            "coordinate_scope",
            "support_state",
        ],
        "save": False,
        "save_reason": SAVE_REASON,
    }


def options_for_context(topic, options=None):
    if topic not in PREDICATES or options is not None and not isinstance(options, dict):
        raise ArgumentError("Use a declared protein context topic and options mapping.")
    options = {} if options is None else options
    if topic == "associations":
        if options:
            raise ArgumentError("Protein associations take no scientific options.")
        return {}
    if set(options) - {"mode", "other_ref"} or options.get(
        "mode", "relationships"
    ) not in ("relationships", "sequence"):
        raise ArgumentError(
            "comparative_context mode requires relationships or sequence."
        )
    mode = options.get("mode", "relationships")
    if mode == "relationships":
        if "other_ref" in options:
            raise ArgumentError(
                "other_ref is only valid for an explicit sequence comparison."
            )
        return {"mode": mode}
    ref = options.get("other_ref")
    if not isinstance(ref, str) or not ref:
        raise ArgumentError(
            "Sequence comparison requires other_ref naming an exact supplied capture pin."
        )
    return {"mode": mode, "other_ref": ref}


def location(access, capture, *segments):
    owner = access._captures[capture]
    return {
        "format": "card_access_location@1",
        "kind": "card",
        "card_ref": owner.pin,
        "snapshot_id": owner.snapshot,
        "segments": list(segments),
    }


def record_location(access, capture, store, identifier):
    return location(
        access,
        capture,
        {"type": "Key", "value": store},
        {"type": "Record", "value": identifier},
    )


def anchor(capture):
    identifier = capture.data["meta"].get("card_id")
    return identifier.split(":", 2)[2] if identifier else None


def source_records(
    access, capture, identifiers, subject, field, *, value=None, exact=False
):
    store = {
        r["id"]: r for r in access._captures[capture].data["source_assertion_store"]
    }
    rows = []
    if not isinstance(identifiers, list):
        identifiers = [identifiers]
    for ref in identifiers:
        source = store.get(ref) if isinstance(ref, str) else None
        bound = (
            source is not None
            and source.get("subject_ref") == subject
            and source.get("field_path") == field
        )
        if bound and exact:
            bound = canonical_json(assertion_value(source)) == canonical_json(value)
        rows.append(
            {
                "id": ref if isinstance(ref, str) else None,
                "original_identifier": deepcopy(ref),
                "capture": capture,
                "state": "unrecognized_shape"
                if not isinstance(ref, str)
                else "retained_reference"
                if bound
                else "not_retained"
                if source is None
                else "binding_mismatch",
                "expected_subject_ref": subject,
                "expected_field_path": field,
                "value_binding": "exact_selected_field_value"
                if exact
                else "recorded_relationship_reference_only",
                "source": source.get("source", {}).get("name") if source else None,
                "location": record_location(
                    access, capture, "source_assertion_store", ref
                )
                if source
                else None,
            }
        )
    return rows


@dataclass(frozen=True)
class ProteinContextResult:
    result_ref: str
    wire: dict
    entries: tuple
    options: dict

    @property
    def native(self):
        return self.wire["native_payload"]

    @property
    def explanations(self):
        return self.wire["explanations"]

    def location(self, *keys):
        return {
            "format": "card_access_location@1",
            "kind": "result",
            "result_ref": self.result_ref,
            "segments": [{"type": "Key", "value": key} for key in keys],
        }

    def value(self, key, column):
        return self.wire["rows"][key][column]

    def cell_state(self, key, column):
        row = self.wire["rows"][key]
        applicable = {
            "input_index": "supplied_capture",
            "difference_count": "sequence_comparison",
            "identical": "sequence_comparison",
            "predicate": "relationship",
            "channel": "relationship",
            "source": "relationship",
        }
        if column in applicable and row["kind"] != applicable[column]:
            return "not_applicable"
        return row["cell_states"].get(
            column, "present" if row[column] is not None else "unknown"
        )

    def cell_reason(self, key, column):
        return (
            None
            if self.cell_state(key, column) == "present"
            else "The captured record does not state a value of the declared type; inspect the complete original."
        )

    def frame(self, access, selection, entry):
        row, support = self.wire["rows"][entry.key], self.wire["support"][entry.key]
        return {
            "adapter": ADAPTER,
            "item_ref": item_ref(self, entry),
            "kind": row["kind"],
            "label": row["label"],
            "subject_ref": row["subject_ref"],
            "state": row["state"],
            "location": access._location(entry.location),
            "payload_location": access._location(row["original_location"]),
            "support_location": access._location(self.location("support", entry.key)),
            "support": deepcopy(support),
            "interpretation": deepcopy(row["interpretation"]),
            "interpretation_location": access._location(
                self.location("rows", entry.key, "interpretation")
            ),
            "cells": {
                c: {
                    "value": deepcopy(row[c]),
                    "state": self.cell_state(entry.key, c),
                    "reason": self.cell_reason(entry.key, c),
                    "field": {"adapter": ADAPTER, "column": c},
                    "support_ref": entry.key,
                    "support_basis": support["basis"],
                    "value_included": True,
                    "value_location": access._location(
                        self.location("rows", entry.key, c)
                    ),
                }
                for c in selection._fields
            },
            "value_included": True,
            "inspection_required": False,
        }


def _row(kind, label, subject, target, basis, original, loc, support, **cells):
    row = dict.fromkeys(COLUMNS)
    row.update(
        kind=kind,
        label=label,
        subject_ref=subject,
        object_ref=target,
        basis=basis,
        state="retained",
        support_state=support["state"],
        item=deepcopy(original),
        original_location=loc,
        **cells,
    )
    row["cell_states"] = {}
    for c in COLUMNS:
        value = row[c]
        valid = value is None or (
            type(value) is int and value >= 0
            if c in ("input_index", "difference_count")
            else type(value) is bool
            if c == "identical"
            else isinstance(value, str)
        )
        if not valid:
            row[c] = None
            row["cell_states"][c] = "unrecognized_shape"
    row["interpretation"] = {
        "rule": "protein_context_projection@1",
        "scope": SCOPE,
        "row_grain": kind,
        "identity": "not_inferred; only original explicit identifiers are shown",
        "coordinate_scope": "No coordinate correspondence established; equal-length sequence comparison uses equal integer positions only.",
        "support_state": support["state"],
        "qualifier_conflicts": deepcopy(original.get("qualifier_conflicts", {})),
    }
    return row


class _SequenceInput:
    def __init__(self, captured):
        self.id, self.data = captured.data["meta"].get("card_id"), captured.data

    def get(self, path):
        node = self.data.get("sections", {})
        for key in path.split("."):
            node = node.get(key) if isinstance(node, dict) else None
        return node


def materialize(access, topic, options=None):
    options = options_for_context(topic, options)
    if access.mode != "live" or access.profile != "protein":
        raise ArgumentError(
            "Protein context materialization requires a LIVE captured protein."
        )
    target = options.get("other_ref")
    if target is not None and (
        target not in access._inputs[1:]
        or access._captures[target].data["meta"].get("entity_type") != "protein"
    ):
        raise ArgumentError(
            "other_ref must be the exact pin of an explicitly supplied protein Card."
        )
    key = canonical_json(
        {
            "adapter": ADAPTER,
            "focal": access._focal_key,
            "topic": topic,
            "options": options,
        }
    )
    if key in access._scientific_cache:
        return access._scientific_cache[key]
    rows, supports = {}, {}
    coverage = {
        "scope": "captured inputs only",
        "gaps": [],
        "source_queries": "not_performed_or_reinterpreted",
        "original_quality": deepcopy(access._focal.data.get("quality", {})),
        "inputs": list(access._inputs),
    }
    if target is None:
        for original in access._focal.data["relationship_store"]:
            predicate = original.get("predicate")
            if predicate not in PREDICATES[topic]:
                continue
            identifier = original["id"]
            row_key = "relationship:" + identifier
            records = source_records(
                access,
                access._focal_key,
                original.get("source_assertion_ids", []),
                original.get("subject_ref"),
                "relationships." + predicate,
            )
            derived = bool(
                original.get("derivation") or original.get("derivation_applications")
            )
            source_backed = bool(records)
            basis = (
                "recorded_source_and_derivation"
                if derived and source_backed
                else "recorded_derivation"
                if derived
                else "recorded_source_references"
                if source_backed
                else "missing_basis"
            )
            state = (
                "retained_references"
                if records and all(r["state"] == "retained_reference" for r in records)
                else "derivation_only"
                if derived and not records
                else "partial"
            )
            if original.get("qualifier_conflicts") or original.get(
                "subject_ref"
            ) != anchor(access._focal):
                state = "partial"
            loc = record_location(
                access, access._focal_key, "relationship_store", identifier
            )
            support = {
                "format": SUPPORT_FORMAT,
                "basis": basis,
                "state": state,
                "source_assertions": records,
                "relationship_location": loc,
                "derivation": deepcopy(original.get("derivation")),
                "derivation_applications": deepcopy(
                    original.get("derivation_applications", [])
                ),
                "expected_focal_subject": anchor(access._focal),
                "qualifier_conflicts": deepcopy(
                    original.get("qualifier_conflicts", {})
                ),
            }
            qualifiers = original.get("qualifiers", {})
            if not isinstance(qualifiers, dict):
                coverage["gaps"].append(
                    {"relationship_id": identifier, "state": "unrecognized_qualifiers"}
                )
                qualifiers = {}
            rows[row_key] = _row(
                "relationship",
                predicate + " → " + str(original.get("object_ref")),
                original.get("subject_ref"),
                original.get("object_ref"),
                basis,
                original,
                loc,
                support,
                predicate=predicate,
                channel=qualifiers.get("channel"),
                source="; ".join(
                    sorted(
                        {r["source"] for r in records if isinstance(r["source"], str)}
                    )
                )
                or None,
            )
            supports[row_key] = support
        if topic == "comparative_context":
            for index, capture in enumerate(access._inputs[1:], 1):
                if (
                    access._captures[capture].data["meta"].get("entity_type")
                    != "protein"
                ):
                    continue
                identifier = "input:" + str(index)
                loc = location(access, capture)
                support = {
                    "format": SUPPORT_FORMAT,
                    "basis": "explicit_supplied_input",
                    "state": "not_a_source_statement",
                    "source_assertions": [],
                    "input_index": index,
                    "input_location": loc,
                }
                rows[identifier] = _row(
                    "supplied_capture",
                    "Supplied protein · " + capture,
                    access._focal.pin,
                    capture,
                    "explicit_supplied_input",
                    {"input_index": index, "capture": capture},
                    loc,
                    support,
                    input_index=index,
                )
                supports[identifier] = support
    else:
        from .sequences import SEQUENCE, sequence_differences_view

        left, right = (
            _SequenceInput(access._focal),
            _SequenceInput(access._captures[target]),
        )
        nodes = [c.get(SEQUENCE) for c in (left, right)]
        malformed = any(
            node is not None
            and (
                not isinstance(node, dict)
                or node.get("value") is not None
                and not isinstance(node.get("value"), str)
            )
            for node in nodes
        )
        native = None if malformed else sequence_differences_view(left, right)
        if malformed:
            coverage["gaps"].append({"state": "unrecognized_sequence_shape"})
        records, inputs, input_bindings = [], [], []
        for capture, node in zip((access._focal_key, target), nodes):
            loc = location(
                access,
                capture,
                *[
                    {"type": "Key", "value": key}
                    for key in ("sections", "sequence", "primary")
                ],
            )
            inputs.append(
                {
                    "capture": capture,
                    "location": loc,
                    "state": "not_retained" if node is None else "retained",
                }
            )
            statements = (
                source_records(
                    access,
                    capture,
                    node.get("source_assertion_ids", []),
                    anchor(access._captures[capture]),
                    SEQUENCE,
                    value=node.get("value"),
                    exact=True,
                )
                if isinstance(node, dict)
                else []
            )
            records += statements
            input_bindings.append(
                bool(statements)
                and all(s["state"] == "retained_reference" for s in statements)
            )
        state = "retained_references" if all(input_bindings) else "partial"
        support = {
            "format": SUPPORT_FORMAT,
            "state": state,
            "basis": "explicit_captured_sequence_inputs",
            "source_assertions": records,
            "inputs": inputs,
        }
        original = {
            "native_result": native,
            "inputs": inputs,
            "rule": make_derivation(
                "captured_sequence_comparison@1", inputs=[access._focal_key, target]
            ),
        }
        rows["comparison"] = _row(
            "sequence_comparison",
            "Explicit equal-position sequence comparison",
            access._focal.pin,
            target,
            "equal_length_positions@1",
            original,
            None,
            support,
            difference_count=len(native["differences"])
            if native and "differences" in native
            else None,
            identical=native.get("identical") if native else None,
        )
        rows["comparison"]["state"] = (
            "available" if native and "differences" in native else "unavailable"
        )
        supports["comparison"] = support
    native_payload = {
        "rule": make_derivation(
            "protein_context_projection@1", inputs=list(access._inputs)
        ),
        "items": [deepcopy(r["item"]) for r in rows.values()],
    }
    ref = _handle(
        "XR_",
        {
            "adapter": ADAPTER,
            "focal": access._focal_key,
            "topic": topic,
            "options": options,
            "native": native_payload,
            "rows": rows,
            "support": supports,
            "coverage": coverage,
        },
    )
    for identifier, row in rows.items():
        if row["original_location"] is None:
            row["original_location"] = {
                "format": "card_access_location@1",
                "kind": "result",
                "result_ref": ref,
                "segments": [
                    {"type": "Key", "value": key}
                    for key in ("rows", identifier, "item")
                ],
            }
    wire = {
        "context": {
            **access.context,
            "adapter": ADAPTER,
            "topic": topic,
            "options": options,
            "used_captures": list(dict.fromkeys(access._inputs)),
        },
        "rows": rows,
        "support": supports,
        "explanations": {
            k: {
                "support": deepcopy(supports[k]),
                "interpretation": deepcopy(r["interpretation"]),
            }
            for k, r in rows.items()
        },
        "native_payload": native_payload,
        "schema": descriptor(topic),
        "coverage": coverage,
        "scope": SCOPE,
        "exclusions": [],
        "outcome": {
            "status": "partial"
            if coverage["gaps"]
            or any(
                r["state"] == "unavailable" or s["state"] == "partial"
                for r, s in zip(rows.values(), supports.values())
            )
            else "ok"
            if rows
            else "empty",
            "reason": "Only retained records and explicit inputs are projected. An empty projection does not establish source-stated absence.",
        },
    }
    shell = ProteinContextResult(ref, wire, (), options)
    result = ProteinContextResult(
        ref,
        wire,
        tuple(_Entry(shell.location("rows", k), k, r) for k, r in rows.items()),
        options,
    )
    access._objects[ref], access._scientific_cache[key] = wire, result
    for entry in result.entries:
        access._scientific_items[item_ref(result, entry)] = (result, entry.key)
    return result


def defer_frame(frame):
    result = {
        k: deepcopy(v)
        for k, v in frame.items()
        if k not in ("label", "interpretation", "support", "cells")
    }
    result.update(
        cells={
            k: {n: deepcopy(v) for n, v in cell.items() if n != "value"}
            | {"value_included": False}
            for k, cell in frame["cells"].items()
        },
        value_included=False,
        inspection_required=True,
        interpretation_included=False,
        support_included=False,
    )
    return result
