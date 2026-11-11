"""Curated orientation over original captured fields; no new scientific findings."""

from copy import deepcopy

RULE = "card_orientation@1"
SCOPE = (
    "Selected original orientation fields and their declared source references, "
    "not a completeness or independent support-validity assessment. Values, "
    "versions, missing inputs and stored quality declarations retain their "
    "original scope. No source acquisition or scientific interpretation is performed."
)
FIELDS = {
    "protein": (
        ("names.canonical_name", "Protein name"),
        ("annotations.organism", "Organism"),
        ("identifiers.uniprot", "UniProt accession"),
        ("sequence.length", "Sequence length"),
        ("annotations.function", "Function description"),
        ("annotations.catalytic_activity", "Catalytic activity"),
    ),
    "small_molecule": (
        ("names.canonical_name", "Molecule name"),
        ("identifiers.inchikey", "Standard InChIKey"),
        ("properties.physchem.formula", "Molecular formula"),
        ("identifiers.smiles", "SMILES"),
        ("identifiers.inchi", "InChI"),
    ),
    "disease": (
        ("names.canonical_name", "Disease term"),
        ("identifiers.mondo", "MONDO identifier"),
        ("annotations.definition", "Ontology definition"),
        ("names.synonyms", "Scoped synonyms"),
        ("annotations.term_status", "Retained term status"),
    ),
}


def _state(value):
    if value is None:
        return "retained_null"
    if isinstance(value, (str, list, dict)) and not len(value):
        return "retained_empty"
    return "retained"


def _support(explorer, field, *, source_limit, copy_values):
    declared = isinstance(field, dict) and "source_assertion_ids" in field
    refs = field.get("source_assertion_ids") if declared else None
    result = {
        "state": "not_retained",
        "references": deepcopy(refs) if copy_values else refs,
        "reference_count": len(refs) if isinstance(refs, list) else None,
        "sources": [],
        "sources_complete": False,
    }
    if not declared:
        return result
    if not isinstance(refs, list):
        result["state"] = "unrecognized_shape"
        return result
    if source_limit is not None and len(refs) > source_limit:
        # A bad tail member invalidates the whole selection. Do not validate or
        # attribute a prefix as though the complete declaration were recognized.
        result["state"] = "not_evaluated"
        return result
    if any(not isinstance(ref, str) for ref in refs):
        result["state"] = "unrecognized_shape"
        return result
    result["state"] = "retained" if refs else "retained_empty"
    result["sources_complete"] = True
    for ref in refs:
        statement = explorer._statement(ref)
        row = {**statement, "source": None}
        if statement["state"] == "present":
            record, _ = explorer.access._resolve(statement["location"])
            source = record.get("source") if isinstance(record, dict) else None
            row["source"] = deepcopy(source) if copy_values else source
        result["sources"].append(row)
    return result


def _field(explorer, path, label, *, source_limit, copy_values):
    keys = ["sections", *path.split(".")]
    node = explorer.access._focal.data
    field_location = value_location = container_location = None
    state = "not_retained"
    for index, key in enumerate(keys):
        if not isinstance(node, dict):
            state = "unrecognized_container"
            container_location = explorer._location(*keys[:index])
            break
        if key not in node:
            break
        node = node[key]
    else:
        field_location = explorer._location(*keys)
        state = "unrecognized_shape"
        if isinstance(node, dict) and "value" in node:
            value_location = explorer._location(*keys, "value")
            state = _state(node["value"])
    return {
        "path": path,
        "label": label,
        "state": state,
        "field_location": field_location,
        "value_location": value_location,
        "container_location": container_location,
        "value": (deepcopy(node["value"]) if copy_values else node["value"])
        if value_location is not None
        else None,
        "support": _support(
            explorer,
            node if field_location is not None else None,
            source_limit=source_limit,
            copy_values=copy_values,
        ),
    }


def _quality(explorer, key):
    data = explorer.access._focal.data
    quality = data.get("quality", {})
    if not isinstance(quality, dict):
        return {
            "state": "unrecognized_container",
            "count": None,
            "location": explorer._location("quality"),
        }
    if key not in quality:
        return {"state": "not_retained", "count": None, "location": None}
    value = quality[key]
    return {
        "state": _state(value)
        if value is None or isinstance(value, list)
        else "unrecognized_shape",
        "count": len(value) if isinstance(value, list) else None,
        "location": explorer._location("quality", key),
    }


def reading(view, *, source_limit=None, copy_values=True):
    """Read only actual supported overviews; complete properties remain detached."""
    if (
        view.title != "Card overview"
        or not view._route_catalog
        or view._question_catalog
        or view._context_only
        or view._selection._scientific is not None
        or view.explorer.profile not in FIELDS
    ):
        return None
    explorer = view.explorer
    return {
        "rule": RULE,
        "scope": SCOPE,
        "profile": explorer.profile,
        "card_ref": explorer.context["card_ref"],
        "snapshot_id": explorer.context["snapshot_id"],
        "fields": [
            _field(
                explorer,
                path,
                label,
                source_limit=source_limit,
                copy_values=copy_values,
            )
            for path, label in FIELDS[explorer.profile]
        ],
        "fields_complete": True,
        "full_content_location": explorer._location(),
        "quality": {
            key: _quality(explorer, key) for key in ("conflicts", "alternatives")
        },
    }


def _attribution(support, preview):
    if support["state"] == "not_evaluated":
        return f"{support['reference_count']} declared support references; attribution not evaluated in this bounded preview"
    if support["state"] == "not_retained":
        return "source attribution not retained"
    if support["state"] == "unrecognized_shape":
        return "source attribution unknown: unrecognized selection references"
    if support["state"] == "retained_empty":
        return "selection declares no support references"
    labels = []
    for row in support["sources"]:
        source = row["source"]
        if row["state"] != "present":
            labels.append("supporting record not retained")
        elif not isinstance(source, dict):
            labels.append("source descriptor not recognized")
        else:
            name = (
                preview(source["name"], 50)
                if "name" in source
                else "source name not retained"
            )
            version = (
                preview(source["version"], 50)
                if "version" in source
                else "version not retained"
            )
            labels.append(f"{name} [{version}]")
    return "; ".join(labels)


def opening(view, preview, field_text):
    """Bounded display without copying full field bodies or scanning long support."""
    context = reading(view, source_limit=4, copy_values=False)
    if context is None:
        return None
    fields = context["fields"]
    name = fields[0]
    lines = [preview(name["value"])] if name["value_location"] is not None else []
    lines.append(f"{context['profile']} · captured Card")
    for row in fields[1:]:
        if row["value_location"] is not None:
            text = field_text(row["path"], row["value"])
            lines.append(
                f"{row['label']}: {text} · {_attribution(row['support'], preview)}"
            )
        else:
            reason = (
                "not retained; no function is inferred from the name."
                if row["state"] == "not_retained"
                and row["path"]
                in ("annotations.function", "annotations.catalytic_activity")
                else "not retained in this capture."
                if row["state"] == "not_retained"
                else "unrecognized retained field or container; inspect the original content."
            )
            lines.append(f"{row['label']}: {reason}")
    if context["profile"] == "small_molecule":
        lines.append(
            "Explore source-stated chemical identity and retained properties. No chemical calculation or target-context acquisition is performed."
        )
    elif context["profile"] == "disease":
        lines.append(
            "Ontology terminology, not a diagnosis. Parent relationships and equivalent identifiers are separate routes; destination Cards are not opened here."
        )
    data = view.explorer.access._focal.data
    lines.append(
        f"Captured schema {preview(data.get('meta', {}).get('schema_version'))}; current sources have not been queried."
    )
    lines.append(
        "Start: items()[i].open() or explorer.questions(). All stored content: explorer.inspect()."
    )
    lines.append(
        f"{len(data.get('source_assertion_store', []))} retained source statements · {len(data.get('relationship_store', []))} retained relationships"
    )
    for key, declaration in context["quality"].items():
        if declaration["count"]:
            lines.append(
                f"Stored {key} are present ({declaration['count']} records). Inspect explorer.view('quality') for original declarations."
            )
        elif declaration["state"] in ("unrecognized_shape", "unrecognized_container"):
            lines.append(
                f"Stored {key} declaration has an unrecognized shape; inspect original quality records."
            )
        elif declaration["state"] == "retained_null":
            lines.append(f"Stored {key} declaration is null; its scope is unknown.")
    return lines
