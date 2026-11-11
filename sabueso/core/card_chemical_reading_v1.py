"""Current presentation of original molecular declarations, without new chemistry."""

from copy import deepcopy

from .card_exploration_profiles import CHEMISTRY, PROPERTIES
from .card_orientation_v1 import _field, _quality, _state, _support

RULE = "chemical_context_reading@1"
SCOPE = (
    "Original captured identity declarations and currently selected property fields. "
    "Source declarations, representations and methods do not establish missing "
    "stereochemical scope, parent identity, physical charge or experimental origin."
)
REPRESENTATIONS = (
    ("identifiers.smiles", "SMILES"),
    ("identifiers.smiles_connectivity", "Connectivity SMILES"),
    ("identifiers.inchi", "InChI"),
)
NATIVE_FIELDS = {
    "ChEMBL": (
        (("molecule_hierarchy", "parent_chembl_id"), "Parent record identifier", str),
        (
            ("molecule_hierarchy", "active_chembl_id"),
            "Hierarchy active-record identifier",
            str,
        ),
    ),
    "PDB CCD": (
        (("chem_comp", "name"), "Component name", str),
        (
            ("chem_comp", "pdbx_formal_charge"),
            "Formal charge number (native integer)",
            int,
        ),
        (("descriptors", "SMILES"), "CCD SMILES", str),
        (("descriptors", "SMILES_stereo"), "CCD SMILES_stereo", str),
    ),
}


def _nested(record, location, path, label, *, expected=None, copy_values=True):
    node = record
    segments = list(location["segments"])
    result = {
        "label": label,
        "state": "not_retained",
        "value": None,
        "location": None,
        "container_location": None,
    }
    for key in path:
        if not isinstance(node, dict):
            result.update(
                state="unrecognized_container",
                container_location={**location, "segments": segments},
            )
            return result
        if key not in node:
            return result
        node = node[key]
        segments = [*segments, {"type": "Key", "value": key}]
    state = _state(node)
    if expected is not None and node is not None and type(node) is not expected:
        state = "unrecognized_shape"
    result.update(
        state=state,
        value=deepcopy(node) if copy_values else node,
        location={**location, "segments": segments},
    )
    return result


def _metadata(explorer, support, *, copy_values, field_path):
    rows = []
    for source in support["sources"]:
        row = {"source": source, "state": source["state"], "fields": []}
        if source["location"] is not None:
            record, _ = explorer.access._resolve(source["location"])
            if not isinstance(record, dict) or record.get("field_path") != field_path:
                row["state"] = "field_scope_mismatch"
                rows.append(row)
                continue
            row["fields"] = [
                _nested(
                    record,
                    source["location"],
                    ("source_metadata", key),
                    label,
                    copy_values=copy_values,
                )
                for key, label in (
                    ("representation", "Source representation label"),
                    ("method", "Source method"),
                    ("determination", "Source determination declaration"),
                )
            ]
        rows.append(row)
    return rows


def _identity_context(view, limit, copy_values):
    explorer = view.explorer
    original = view._selection._entries
    candidates = original if limit is None else original[: len(CHEMISTRY) + limit]
    complete = len(candidates) == len(original)
    contexts = []
    for entry in candidates:
        relation = entry.value
        segments = entry.location.get("segments", [])
        if (
            segments[:1] != [{"type": "Key", "value": "relationship_store"}]
            or len(segments) != 2
            or segments[1].get("type") != "Record"
            or not isinstance(relation, dict)
            or relation.get("predicate") != "same_as"
        ):
            continue
        if limit is not None and len(contexts) >= limit:
            complete = False
            break
        support = _support(
            explorer, relation, source_limit=limit, copy_values=copy_values
        )
        rows = []
        for source in support["sources"]:
            row = {"source": source, "state": source["state"], "fields": []}
            if source["location"] is not None:
                record, _ = explorer.access._resolve(source["location"])
                value = (
                    record.get("asserted_value") if isinstance(record, dict) else None
                )
                if (
                    not isinstance(record, dict)
                    or record.get("field_path") != "relationships.same_as"
                    or record.get("subject_ref") != relation.get("subject_ref")
                    or not isinstance(value, dict)
                    or value.get("object_ref") != relation.get("object_ref")
                ):
                    row["state"] = "source_binding_mismatch"
                else:
                    name = (
                        (source["source"] or {}).get("name")
                        if isinstance(source["source"], dict)
                        else None
                    )
                    name = name if isinstance(name, str) else None
                    row["state"] = (
                        "retained"
                        if name in NATIVE_FIELDS
                        else "native_context_not_declared"
                    )
                    row["fields"] = [
                        _nested(
                            record,
                            source["location"],
                            ("asserted_value", *path),
                            label,
                            expected=expected,
                            copy_values=copy_values,
                        )
                        for path, label, expected in NATIVE_FIELDS.get(name, ())
                    ]
            rows.append(row)
        contexts.append(
            {
                "relationship_location": deepcopy(entry.location),
                "support": support,
                "records": rows,
            }
        )
    return contexts, complete


def reading(view, *, limit=None, copy_values=True):
    """Read original panel context; explicit complete properties are detached."""
    if (
        view.explorer.profile != "small_molecule"
        or view._field_panel not in ("chemistry", "properties")
        or view._context_only
        or view._selection._scientific is not None
    ):
        return None
    explorer = view.explorer
    context = {
        "rule": RULE,
        "scope": SCOPE,
        "panel": view._field_panel,
        "card_ref": explorer.context["card_ref"],
        "snapshot_id": explorer.context["snapshot_id"],
        "representations": [],
        "identity_context": [],
        "properties": [],
        "complete": True,
        "selected_items": len(view._selected),
        "captured_panel_items": len(view._selection._entries),
        "quality": {
            key: _quality(explorer, key) for key in ("conflicts", "alternatives")
        },
    }
    if view._field_panel == "chemistry":
        for path, label in REPRESENTATIONS:
            field = _field(
                explorer, path, label, source_limit=limit, copy_values=copy_values
            )
            field["metadata"] = _metadata(
                explorer, field["support"], copy_values=copy_values, field_path=path
            )
            context["representations"].append(field)
        context["identity_context"], context["complete"] = _identity_context(
            view, limit, copy_values
        )
    else:
        entries = view._selected
        selected = entries if limit is None else entries[:limit]
        context["complete"] = len(selected) == len(entries)
        for entry in selected:
            key = entry.key.rsplit(".", 1)[-1]
            support = _support(
                explorer, entry.value, source_limit=limit, copy_values=copy_values
            )
            context["properties"].append(
                {
                    "path": entry.key,
                    "label": PROPERTIES.get(key, key),
                    "field_location": deepcopy(entry.location),
                    "field_record": deepcopy(entry.value)
                    if copy_values
                    else entry.value,
                    "support": support,
                    "metadata": _metadata(
                        explorer, support, copy_values=copy_values, field_path=entry.key
                    ),
                }
            )
    return context


def opening(view, preview):
    """A bounded common text/HTML supplement over the original captured panel."""
    context = reading(view, limit=4, copy_values=False)
    if context is None:
        return []

    def stated(field):
        return (
            preview(field["value"])
            if field["state"] in ("retained", "retained_null", "retained_empty")
            else field["state"].replace("_", " ")
        )

    def source_label(source):
        if not isinstance(source, dict):
            return "Source not recognized"
        name = preview(source.get("name", "Source"))
        version = (
            preview(source["version"])
            if "version" in source
            else "version not retained"
        )
        return f"{name} [{version}]"

    lines = [
        "Chemical identity context · original capture; display filters select rows only."
        if context["panel"] == "chemistry"
        else "Property context · current selected fields and their original source declarations."
    ]
    if context["panel"] == "chemistry":
        seen = set()
        for field in context["representations"]:
            if field["value_location"] is not None:
                lines.append(f"{field['label']}: {preview(field['value'])}")
            for source in field["metadata"]:
                for row in source["fields"]:
                    if (
                        row["label"] == "Source representation label"
                        and row["state"] == "retained"
                    ):
                        lines.append(
                            f"{source_label(source['source']['source'])} · {field['label']} representation label: {stated(row)}"
                        )
        for relationship in context["identity_context"]:
            for record in relationship["records"]:
                source = record["source"]["source"]
                name = source_label(source)
                for field in record["fields"]:
                    if field["label"] in (
                        "Parent record identifier",
                        "Formal charge number (native integer)",
                    ):
                        seen.add(field["label"])
                        lines.append(f"{name} · {field['label']}: {stated(field)}")
            if not relationship["support"]["sources_complete"]:
                lines.append(
                    "Original identity support is incomplete or deferred; inspect chemical_reading."
                )
        for label in (
            "Parent record identifier",
            "Formal charge number (native integer)",
        ):
            if label not in seen:
                reason = (
                    "unknown in this captured context"
                    if context["complete"]
                    else "not evaluated in this bounded preview"
                )
                lines.append(f"{label}: {reason}")
        lines.append(
            "Stereochemical completeness and physical charge are not evaluated from representations."
        )
    else:
        for field in context["properties"]:
            for source in field["metadata"]:
                declarations = [
                    f"{row['label']}: {stated(row)}"
                    for row in source["fields"]
                    if row["label"] != "Source representation label"
                ]
                if declarations:
                    lines.append(
                        f"{field['label']} · {source_label(source['source']['source'])} · "
                        + "; ".join(declarations)
                    )
        lines.append(
            "Measured/calculated origin is stated only when retained in source metadata; each original field record keeps its value and unit together."
        )
    if not context["complete"]:
        lines.append(
            "Bounded context preview; chemical_reading exposes the complete retained panel context."
        )
    lines.append(
        "Original source records and exact value locations: chemical_reading and inspect(locator=...)."
    )
    return lines
