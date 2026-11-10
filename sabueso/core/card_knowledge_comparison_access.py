"""Shared LIVE projection of explicit typed knowledge comparisons (#148/#59)."""

from copy import deepcopy

from . import card_knowledge_diff_v2 as native
from .card_access import _Entry, _handle
from .card_knowledge_comparison_dispatch import ADAPTER
from .card_knowledge_diff_v2 import RULE
from .card_protein_context_access import (
    ProteinContextResult,
    anchor,
    location,
    record_location,
)
from .card_protein_context_selection_v1 import COLUMNS, item_ref
from .errors import ArgumentError
from .relationship_store import make_derivation
from .snapshot import canonical_json

PROJECTION = "protein_knowledge_projection@1"


def options_for_comparison(options):
    if not isinstance(options, dict) or set(options) - {
        "mode",
        "other_ref",
        "residue_map",
    }:
        raise ArgumentError(
            "Knowledge comparison accepts mode, exact other_ref and an optional residue_map."
        )
    if (
        options.get("mode") != "knowledge"
        or not isinstance(options.get("other_ref"), str)
        or not options["other_ref"]
    ):
        raise ArgumentError(
            "Knowledge comparison requires mode knowledge and an exact supplied other_ref."
        )
    mapping = options.get("residue_map")
    if isinstance(mapping, dict):
        pairs = list(mapping.items())
    elif isinstance(mapping, list):
        pairs = mapping
    elif mapping is None:
        pairs = None
    else:
        raise ArgumentError("residue_map requires positive integer pairs or a mapping.")
    if pairs is not None and (
        any(
            not isinstance(p, (list, tuple))
            or len(p) != 2
            or any(type(x) is not int or x < 1 for x in p)
            for p in pairs
        )
        or len({p[0] for p in pairs}) != len(pairs)
        or len({p[1] for p in pairs}) != len(pairs)
    ):
        raise ArgumentError(
            "residue_map must be one-to-one, without repeated endpoints or boolean positions."
        )
    return {
        "mode": "knowledge",
        "other_ref": options["other_ref"],
        "residue_map": None if pairs is None else [list(p) for p in sorted(pairs)],
    }


class _Store:
    def __init__(self, rows):
        self.rows = rows
        self.by_id = {r["id"]: r for r in rows}

    def get(self, identifier):
        return self.by_id.get(identifier)

    def to_list(self):
        return self.rows

    def find_by_field(self, path):
        return [r for r in self.rows if r.get("field_path") == path]


class CapturedKnowledge:
    """Read a detached capture without reconstructing a Card or acquiring anything."""

    def __init__(self, capture):
        self.capture = capture
        self.id = capture.data["meta"]["card_id"]
        self.meta = capture.data["meta"]
        self.quality = capture.data.get("quality", {})
        self.sections = capture.data["sections"]
        self.source_assertion_store = _Store(capture.data["source_assertion_store"])
        self.relationship_store = _Store(capture.data["relationship_store"])

    def get(self, path):
        value = self.sections
        for key in path.split("."):
            value = value.get(key) if isinstance(value, dict) else None
        return value

    def list_fields(self):
        paths = []

        def walk(value, prefix=""):
            if isinstance(value, dict):
                for key, child in value.items():
                    path = prefix + "." + key if prefix else key
                    paths.append(path)
                    walk(child, path)

        walk(self.sections)
        return paths

    def pinned_ref(self):
        return self.capture.pin

    def knowledge_state(self):
        from .knowledge_state import knowledge_state

        return knowledge_state(self)


class KnowledgeResult(ProteinContextResult):
    def cell_state(self, key, column):
        if column in ("input_index", "difference_count", "identical", "channel"):
            return "not_applicable"
        if (
            column == "predicate"
            and self.wire["rows"][key]["kind"] != "knowledge_relationships"
        ):
            return "not_applicable"
        return "present" if self.value(key, column) is not None else "unknown"

    def frame(self, access, selection, entry):
        frame = super().frame(access, selection, entry)
        frame["adapter"] = ADAPTER
        for cell in frame["cells"].values():
            cell["field"]["adapter"] = ADAPTER
        return frame


def materialize(access, options):
    options = options_for_comparison(options)
    target = options["other_ref"]
    if (
        access.mode != "live"
        or access.profile != "protein"
        or target not in access._inputs[1:]
        or access._captures[target].data["meta"].get("entity_type") != "protein"
    ):
        raise ArgumentError(
            "Knowledge comparison requires an exact explicitly supplied protein capture."
        )
    key = canonical_json(
        {"adapter": ADAPTER, "focal": access._focal_key, "options": options}
    )
    if key in access._scientific_cache:
        return access._scientific_cache[key]
    mapping = options["residue_map"]
    native_result = native.compare(
        CapturedKnowledge(access._focal),
        CapturedKnowledge(access._captures[target]),
        None if mapping is None else dict(mapping),
    )
    ref = _handle(
        "XR_", {"adapter": ADAPTER, "options": options, "native": native_result}
    )
    rows, supports, explanations = {}, {}, {}
    source_tables = {
        pin: {r["id"]: r for r in access._captures[pin].data["source_assertion_store"]}
        for pin in (access._focal_key, target)
    }

    def loc(*keys):
        return {
            "format": "card_access_location@1",
            "kind": "result",
            "result_ref": ref,
            "segments": [{"type": "Key", "value": k} for k in keys],
        }

    def add(kind, name, value, state, native_path, source=None, predicate=None):
        row_key = _handle("K_", {"kind": kind, "native_path": list(native_path)})
        inputs = [
            {"role": role, "capture": pin, "location": location(access, pin)}
            for role, pin in (("self", access._focal_key), ("other", target))
        ]
        statements = []
        if kind == "knowledge_field":
            for input_ in inputs:
                support = value["support"][input_["role"]]
                for binding in support["bindings"]:
                    identifier = binding["id"]
                    original = source_tables[input_["capture"]][identifier]
                    statements.append(
                        {
                            "id": identifier,
                            "capture": input_["capture"],
                            "state": binding["state"],
                            "source": original["source"].get("name"),
                            "location": record_location(
                                access,
                                input_["capture"],
                                "source_assertion_store",
                                identifier,
                            ),
                        }
                    )
                for alternative in support["other_field_assertions"]:
                    identifier = alternative["id"]
                    statements.append(
                        {
                            "id": identifier,
                            "capture": input_["capture"],
                            "state": "retained_other_field_assertion",
                            "source": alternative["source"].get("name"),
                            "location": record_location(
                                access,
                                input_["capture"],
                                "source_assertion_store",
                                identifier,
                            ),
                        }
                    )
                for identifier in support["missing_source_assertion_ids"]:
                    statements.append(
                        {
                            "id": identifier,
                            "capture": input_["capture"],
                            "state": "not_retained",
                            "source": None,
                            "location": None,
                        }
                    )
        elif kind == "knowledge_relationships":
            for input_ in inputs:
                for record in value[input_["role"] + "_records"]:
                    for identifier in record.get("source_assertion_ids", []):
                        source_record = source_tables[input_["capture"]].get(identifier)
                        statements.append(
                            {
                                "id": identifier,
                                "capture": input_["capture"],
                                "state": "retained_reference"
                                if source_record
                                else "not_retained",
                                "source": source_record["source"].get("name")
                                if source_record
                                else None,
                                "location": record_location(
                                    access,
                                    input_["capture"],
                                    "source_assertion_store",
                                    identifier,
                                )
                                if source_record
                                else None,
                            }
                        )
        support_state = (
            "retained_references"
            if statements
            and all(
                s["state"] in ("retained_reference", "retained_other_field_assertion")
                for s in statements
            )
            else "caller_supplied"
            if kind == "supplied_residue_map"
            else "partial"
        )
        if kind == "knowledge_field" and any(
            side["state"] != "retained_references" for side in value["support"].values()
        ):
            support_state = "partial"
        if kind == "supplied_residue_map" and value["pairs"] is None:
            support_state = "not_supplied"
        support = {
            "format": "protein_knowledge_support@1",
            "state": support_state,
            "basis": "original_native_input_scope; no item-level attribution or source claim validation inferred",
            "inputs": inputs,
            "source_assertions": statements,
            "native_support": deepcopy(value.get("support", {})),
            "residue_map": deepcopy(native_result["residue_map"]),
        }
        row = dict.fromkeys(COLUMNS)
        row.update(
            label=name,
            kind=kind,
            predicate=predicate,
            subject_ref=anchor(access._focal),
            object_ref=anchor(access._captures[target]),
            basis=RULE,
            state=state,
            support_state=support_state,
            source=source,
            item=deepcopy(value),
            original_location=loc("native_payload", *native_path),
            cell_states={},
        )
        row["interpretation"] = {
            "rule": PROJECTION,
            "native_rule": RULE,
            "row_grain": kind,
            "scope": native_result["scope"],
            "identity": "not_inferred",
            "coordinate_scope": deepcopy(native_result["residue_map"]),
            "support_state": support_state,
        }
        rows[row_key], supports[row_key] = row, support
        explanations[row_key] = {
            "input_scope": support,
            "interpretation": row["interpretation"],
            "original_native": deepcopy(value),
        }
        return row_key

    add(
        "supplied_residue_map",
        "Supplied residue map",
        native_result["residue_map"],
        native_result["residue_map"]["basis"],
        ("residue_map",),
    )
    for path, value in native_result["fields"].items():
        add("knowledge_field", path, value, value["status"], ("fields", path))
    for predicate, value in native_result["relationships"].items():
        state = (
            "shared_and_distinct_refs"
            if value["both"] and (value["only_self"] or value["only_other"])
            else "same_object_refs"
            if value["both"]
            else "distinct_object_refs"
        )
        add(
            "knowledge_relationships",
            predicate,
            value,
            state,
            ("relationships", predicate),
            predicate=predicate,
        )
    for index, value in enumerate(native_result["knowledge_states"]):
        row_key = add(
            "knowledge_state",
            value["area"] + " · " + value["source"],
            value,
            "different_recorded_states",
            ("knowledge_states", index),
            source=value["source"],
        )
        # State rows are list entries, never dictionary keys.
        rows[row_key]["original_location"]["segments"][-1] = {
            "type": "Index",
            "value": index,
        }
    wire = {
        "context": {
            "adapter": ADAPTER,
            "card_ref": access._focal.pin,
            "snapshot_id": access._focal.snapshot,
            "inputs": list(access._inputs),
            "options": options,
            "profile": "protein",
            "mode": "live",
        },
        "schema": {
            "kind": ADAPTER,
            "label": "Knowledge comparison of supplied protein captures",
        },
        "rows": rows,
        "support": supports,
        "explanations": explanations,
        "native_payload": native_result,
        "rule": make_derivation(
            PROJECTION,
            inputs=[access._focal.pin, target],
            parameters={
                "native_rule": RULE,
                "row_grains": [
                    "knowledge_field",
                    "knowledge_relationships",
                    "knowledge_state",
                    "supplied_residue_map",
                ],
            },
        ),
        "outcome": {
            "status": "partial"
            if any(r["state"] in ("partial", "not_compared") for r in rows.values())
            else "ok",
            "reason": "Only captured knowledge and an explicit optional map are compared; no alignment, acquisition or identity merge.",
        },
    }
    shell = KnowledgeResult(ref, wire, (), options)
    result = KnowledgeResult(
        ref,
        wire,
        tuple(_Entry(shell.location("rows", k), k, v) for k, v in rows.items()),
        options,
    )
    access._objects[ref], access._scientific_cache[key] = wire, result
    for entry in result.entries:
        access._scientific_items[item_ref(result, entry)] = result, entry.key
    return result
