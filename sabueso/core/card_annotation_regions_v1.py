"""Frozen literal annotation membership and source-bound structural requests.

This rule prepares an explicit canonical-region question, not a residue mapping,
new SourceAssertion, model recommendation or coordinate-completeness finding.
Keep v1 admission stable for independent historical verification.
"""

from copy import deepcopy

from .card_access import _Entry
from .errors import ArgumentError
from .snapshot import canonical_json
from .source_assertion_store import assertion_value

RULE = "annotation_structure_request@1"
SUPPORT_RULE = "annotation_item_support@1"
NAVIGATION_RULE = "retained_context_links@3"
SCOPE = (
    "One original positional annotation per item, including unplaced records. "
    "Original axes and source support remain inspectable. Related experimental "
    "structures require exact source-supported canonical positions. Missing "
    "sequence revisions are explicit, not proof of revision agreement. A bond's "
    "two endpoints do not describe its intervening residues."
)
INTERVAL_FIELDS = frozenset(
    (
        "active_site",
        "binding_site",
        "family_site",
        "secondary_structure",
        "chain",
        "domains",
        "region",
        "motif",
        "natural_variant",
        "mutagenesis",
        "alternative_sequence",
        "sequence_conflict",
        "glycosylation",
        "lipidation",
        "modified_residue",
        "transmembrane",
        "topological_domain",
    )
)
NATIVE_TYPES = {
    "Active site": "active_site",
    "Binding site": "binding_site",
    "Disulfide bond": "disulfide_bond",
    "Natural variant": "natural_variant",
    "Mutagenesis": "mutagenesis",
    "Alternative sequence": "alternative_sequence",
    "Sequence conflict": "sequence_conflict",
    "Glycosylation": "glycosylation",
    "Lipidation": "lipidation",
    "Modified residue": "modified_residue",
    "Transmembrane": "transmembrane",
    "Topological domain": "topological_domain",
    "Domain": "domains",
    "Chain": "chain",
    "Motif": "motif",
    "Region": "region",
    "Helix": "secondary_structure",
    "Beta strand": "secondary_structure",
    "Turn": "secondary_structure",
}


def annotation_path(location):
    """Recognize the actual schema path, never an arbitrary location lookalike."""
    s = location.get("segments", [])
    if (
        location.get("kind") == "card"
        and len(s) == 5
        and [p.get("type") for p in s] == ["Key", "Key", "Key", "Key", "Index"]
        and [s[i].get("value") for i in (0, 1, 3)]
        == ["sections", "features_positional", "value"]
        and isinstance(s[2].get("value"), str)
        and type(s[4].get("value")) is int
        and s[4]["value"] >= 0
    ):
        return s[2]["value"], s[4]["value"]
    return None


def entries(explorer):
    found, gaps = [], []
    fields = explorer.access._focal.data.get("sections", {}).get("features_positional")
    if not isinstance(fields, dict):
        return (), [
            {
                "field": "features_positional",
                "state": "not_retained" if fields is None else "unrecognized_shape",
            }
        ]
    for key, node in sorted(fields.items()):
        root = explorer._location("sections", "features_positional", key)
        values = node.get("value") if isinstance(node, dict) else None
        if not isinstance(values, list) or not values:
            gaps.append(
                {
                    "field": f"features_positional.{key}",
                    "location": root,
                    "state": "retained_empty"
                    if values == []
                    else "not_retained"
                    if values is None
                    else "unrecognized_shape",
                }
            )
            continue
        for index, value in enumerate(values):
            location = {
                **root,
                "segments": [
                    *root["segments"],
                    {"type": "Key", "value": "value"},
                    {"type": "Index", "value": index},
                ],
            }
            if isinstance(value, dict):
                found.append(
                    _Entry(
                        location, f"features_positional.{key}[{index}]", value, index
                    )
                )
            else:
                gaps.append(
                    {
                        "field": f"features_positional.{key}[{index}]",
                        "location": location,
                        "state": "unrecognized_shape",
                    }
                )
    return tuple(found), gaps


def label(entry):
    from .card_protein_source_v1 import feature_label

    key, index = annotation_path(entry.location)
    description = entry.value.get("description")
    return f"{feature_label(key)} · annotation {index + 1}" + (
        f" · {description}" if isinstance(description, str) and description else ""
    )


def _equal(first, second):
    return canonical_json(first) == canonical_json(second)


def _matches(data, node, path, value, subject):
    refs = node.get("source_assertion_ids") if isinstance(node, dict) else None
    if not isinstance(refs, list) or not all(isinstance(ref, str) for ref in refs):
        return [], [], False
    store = {a["id"]: a for a in data["source_assertion_store"]}
    matched, missing = [], []
    for ref in dict.fromkeys(refs):
        a = store.get(ref)
        if a is None:
            missing.append(ref)
        elif a.get("subject_ref") == subject and a.get("field_path") == path:
            source = a.get("source")
            if (
                not isinstance(source, dict)
                or not isinstance(source.get("name"), str)
                or not source["name"]
                or not isinstance(source.get("record_id"), str)
                or not source["record_id"]
                or source["name"] == "UniProt"
                and subject != f"uniprot:{source['record_id']}"
            ):
                continue
            original = assertion_value(a)
            if (
                _equal(original, value)
                or isinstance(original, list)
                and any(_equal(row, value) for row in original)
            ):
                matched.append(ref)
    return matched, missing, True


def support(explorer, location):
    """Match the individual original value; other field members are not its support."""
    capture = explorer.access._focal
    if (
        location.get("card_ref") != capture.pin
        or location.get("snapshot_id") != capture.snapshot
    ):
        raise ArgumentError("Annotation support is limited to the focal capture.")
    key, _ = annotation_path(location)
    value, _ = explorer.access._resolve(location)
    parent = {**location, "segments": location["segments"][:3]}
    node, _ = explorer.access._resolve(parent)
    data = explorer.access._focal.data
    identifiers = data.get("sections", {}).get("identifiers")
    identifier = identifiers.get("uniprot") if isinstance(identifiers, dict) else None
    accession = identifier.get("value") if isinstance(identifier, dict) else None
    subject = f"uniprot:{accession}" if isinstance(accession, str) else None
    matched, missing, declared = _matches(
        data, node, f"features_positional.{key}", value, subject
    )
    return [
        {
            "basis": "original_annotation_item",
            "rule": SUPPORT_RULE,
            "location": deepcopy(location),
            "parent_field_location": parent,
            "source_assertion_ids": matched,
            "missing_field_source_assertion_ids": missing,
            "other_field_source_assertion_ids": [
                ref
                for ref in node.get("source_assertion_ids", [])
                if isinstance(ref, str) and ref not in matched and ref not in missing
            ]
            if declared
            else [],
            "reference_state": "declared" if declared else "unrecognized",
            "statements": [explorer._statement(ref) for ref in [*matched, *missing]],
        }
    ]


def context(explorer, location):
    """Bind a request to original typed nodes and actual source-supported values."""
    path = annotation_path(location)
    if path is None:
        return None
    key, _ = path
    value, _ = explorer.access._resolve(location)
    data = explorer.access._focal.data
    sections = data.get("sections", {})
    result = {
        "rule": RULE,
        "annotation_location": deepcopy(location),
        "state": "missing_prerequisite",
        "reason": None,
        "request": None,
        "input_locations": [deepcopy(location)],
        "source_assertion_ids": {},
        "sequence_revisions": {
            "annotation": [],
            "reference": [],
            "unstated_source_assertion_ids": {"annotation": [], "reference": []},
            "state": "not_stated",
        },
        "native_feature_inputs": [],
        "position_scope": None,
    }

    def stop(reason, state="missing_prerequisite"):
        return {**result, "state": state, "reason": reason}

    if explorer.profile != "protein":
        return stop(
            "This structural question requires a protein Card.", "not_applicable"
        )
    if not isinstance(value, dict):
        return stop("The original annotation shape is unrecognized.")
    if key not in INTERVAL_FIELDS and key != "disulfide_bond":
        return stop(
            "The position semantics of this annotation type are not supported.",
            "unsupported",
        )
    fields = {}
    for name, group, leaf in (
        ("identity", "identifiers", "uniprot"),
        ("sequence", "sequence", "primary"),
        ("length", "sequence", "length"),
    ):
        parent = sections.get(group)
        node = parent.get(leaf) if isinstance(parent, dict) else None
        fields[name] = node if isinstance(node, dict) else {}
        result["input_locations"].append(explorer._location("sections", group, leaf))
    accession = fields["identity"].get("value")
    sequence, length = fields["sequence"].get("value"), fields["length"].get("value")
    if (
        not isinstance(accession, str)
        or not accession
        or data.get("meta", {}).get("card_id") != f"sabueso:protein:uniprot:{accession}"
        or not isinstance(sequence, str)
        or not sequence
        or type(length) is not int
        or length != len(sequence)
    ):
        return stop(
            "Consistent captured canonical identity, sequence and length are required."
        )
    quality = data.get("quality")
    conflicts = quality.get("conflicts", []) if isinstance(quality, dict) else None
    if not isinstance(conflicts, list):
        return stop("The stored conflict declaration is unavailable or unrecognized.")
    relevant = {
        "identifiers.uniprot",
        "sequence.primary",
        "sequence.length",
        f"features_positional.{key}",
    }
    if any(
        isinstance(row, dict)
        and str(row.get("field")).removesuffix(".value") in relevant
        for row in conflicts
    ):
        return stop(
            "Stored identity, sequence or annotation conflicts require inspection."
        )
    subject = f"uniprot:{accession}"
    basis = support(explorer, location)[0]
    result["source_assertion_ids"]["annotation"] = basis["source_assertion_ids"]
    if (
        not basis["source_assertion_ids"]
        or basis["missing_field_source_assertion_ids"]
        or basis["reference_state"] != "declared"
    ):
        return stop(
            "Complete retained field references and exact subject-bound annotation support are required."
        )
    for name, field_path in (
        ("identity", "identifiers.uniprot"),
        ("sequence", "sequence.primary"),
        ("length", "sequence.length"),
    ):
        refs, missing, declared = _matches(
            data, fields[name], field_path, fields[name].get("value"), subject
        )
        result["source_assertion_ids"][name] = refs
        if not refs or missing or not declared:
            return stop(
                "Exact retained source support for canonical identity, sequence and length is required."
            )
    store = {row["id"]: row for row in data["source_assertion_store"]}
    loc = value.get("location")
    axis = (
        loc.get("sequence")
        if isinstance(loc, dict) and loc.get("kind") == "sequence"
        else None
    )
    if not isinstance(axis, dict):
        return stop("No explicit sequence location is retained.", "unsupported")
    for ref in result["source_assertion_ids"]["annotation"]:
        source = store[ref].get("source")
        if (
            not isinstance(source, dict)
            or source.get("name") != "UniProt"
            or source.get("record_id") != accession
        ):
            return stop(
                "This structural request supports native feature scope from the focal UniProt record only.",
                "unsupported",
            )
        metadata = store[ref].get("source_metadata")
        native = metadata.get("uniprot_feature") if isinstance(metadata, dict) else None
        if not isinstance(native, dict):
            return stop(
                "Original native UniProt feature scope was not retained; recorded positions remain inspectable. Refresh can record a new basis, not recover the old execution."
            )
        result["native_feature_inputs"].append(
            {"source_assertion_id": ref, "path": ["source_metadata", "uniprot_feature"]}
        )
        if NATIVE_TYPES.get(native.get("type")) != key:
            return stop(
                "The original native feature type differs from this annotation."
            )
        if native.get("molecule") is not None and native["molecule"] not in (
            accession,
            f"UniProt:{accession}",
        ):
            return stop(
                "The native feature declares another or unidentified molecule; no canonical mapping is inferred.",
                "unsupported",
            )
        original = native.get("location")
        if not isinstance(original, dict):
            return stop(
                "The original native feature has no identified location.", "unsupported"
            )
        if set(original) - {"start", "end"}:
            return stop(
                "Compound or unrecognized native location fields are not projected.",
                "unsupported",
            )
        for endpoint in ("start", "end"):
            position = original.get(endpoint)
            if position is not None and not isinstance(position, dict):
                return stop("The original native endpoint is malformed.")
            position = position or {}
            if not _equal(axis.get(endpoint), position.get("value")) or not _equal(
                axis.get(endpoint + "_modifier"), position.get("modifier")
            ):
                return stop(
                    "Recorded positions or modifiers differ from the retained native feature."
                )
    for role, group in (("annotation", "annotation"), ("reference", "sequence")):
        versions = []
        for ref in result["source_assertion_ids"][group]:
            row = store[ref]
            source = row.get("source")
            if (
                not isinstance(source, dict)
                or source.get("name") == "UniProt"
                and source.get("record_id") != accession
            ):
                return stop(
                    "The source record does not identify the focal sequence input."
                )
            metadata = row.get("source_metadata")
            if metadata is not None and not isinstance(metadata, dict):
                return stop("A retained sequence revision declaration is malformed.")
            metadata = metadata or {}
            version = (
                metadata.get("sequence_version")
                if isinstance(metadata, dict)
                and row.get("source", {}).get("name") == "UniProt"
                else None
            )
            if version is not None and (type(version) is not int or version < 1):
                return stop("A retained UniProt sequence revision is malformed.")
            if version is not None and version not in versions:
                versions.append(version)
            if version is None:
                result["sequence_revisions"]["unstated_source_assertion_ids"][
                    role
                ].append(ref)
        result["sequence_revisions"][role] = sorted(versions)
    versions = result["sequence_revisions"]
    if (
        any(len(versions[role]) > 1 for role in ("annotation", "reference"))
        or versions["annotation"]
        and versions["reference"]
        and versions["annotation"] != versions["reference"]
    ):
        versions["state"] = "conflicting"
        return stop(
            "The retained annotation and reference sequence revisions conflict."
        )
    if (
        versions["annotation"]
        and versions["reference"]
        and not any(versions["unstated_source_assertion_ids"].values())
    ):
        versions["state"] = "matching"
    elif versions["annotation"] or versions["reference"]:
        versions["state"] = "partially_stated"
    if axis.get("sequence_id") not in (f"UniProt:{accession}", subject):
        return stop(
            "The annotation does not declare the captured canonical sequence axis; no mapping is inferred.",
            "unsupported",
        )
    begin, end = axis.get("start"), axis.get("end")
    if (
        axis.get("indexing") != "1-based"
        or set(axis)
        - {"sequence_id", "start", "end", "indexing", "start_modifier", "end_modifier"}
        or any(
            axis.get(f"{part}_modifier") not in (None, "EXACT")
            for part in ("start", "end")
        )
        or any(type(n) is not int for n in (begin, end))
        or not 1 <= begin <= end <= length
    ):
        return stop(
            "Exact in-bounds 1-based positions without uncertain or compound locations are required.",
            "unsupported",
        )
    result["position_scope"] = (
        "declared_bond_endpoints"
        if key == "disulfide_bond"
        else "declared_inclusive_interval"
    )
    result["state"] = "ready"
    result["reason"] = (
        "Uses the annotation's declared canonical positions; sequence revision agreement is not established."
        if versions["state"] != "matching"
        else "Uses exact annotation positions on the source-supported canonical axis with matching stated sequence revisions."
    )
    result["request"] = {
        "question": "region_coverage",
        "options": {
            "sequence_ref": subject,
            "region": sorted({begin, end})
            if key == "disulfide_bond"
            else [[begin, end]],
            "include_fragments": False,
        },
    }
    return result


def navigation_support(explorer, location, binding):
    bases = support(explorer, location)
    refs = {ref for refs in binding["source_assertion_ids"].values() for ref in refs}
    bases[0]["derivation_input_statements"] = [
        explorer._statement(ref)
        for ref in sorted(refs)
        if ref not in bases[0]["source_assertion_ids"]
    ]
    return bases


def link(explorer, location):
    basis = context(explorer, location)
    if basis is None:
        return None
    return {
        "role": "question",
        "label": "Experimental structures at this annotation",
        "target_ref": "region_coverage",
        "rule": NAVIGATION_RULE,
        "support": navigation_support(explorer, location, basis),
        "candidates": [],
        "paths": [],
        "blocked_paths": [],
        "availability": "available" if basis["state"] == "ready" else basis["state"],
        "annotation_context": basis,
    }
