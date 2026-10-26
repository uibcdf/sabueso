# Frozen original comparison predicates for exploration history @1 (#148).
# Keep these semantics; future scientific changes require a new historical rule.
"""Source-bound canonical coordinate admission for ligand-site comparisons.

No alignment, identity inference, source acquisition or atom projection occurs.
Unknown coordinate scope is a retained uncomputed input, never a negative result.
"""

from copy import deepcopy

from .snapshot import canonical_json


def assertion_value(assertion):
    # Original SourceAssertion projection; normalized values remain explicit.
    return (
        assertion["normalized_value"]
        if "normalized_value" in assertion
        else assertion.get("asserted_value")
    )


RULE = "ligand_site_coordinate_scope@1"


def equal(a, b):
    return canonical_json(a) == canonical_json(b)


def matching(card, node, path, value, subject):
    refs = node.get("source_assertion_ids") if isinstance(node, dict) else None
    if not isinstance(refs, list) or any(not isinstance(r, str) for r in refs):
        return [], ["unrecognized_source_references"]
    sources, problems = [], []
    for ref in dict.fromkeys(refs):
        source = card.source_assertion_store.get(ref)
        if source is None:
            problems.append("missing_source_assertion")
        elif not isinstance(source.get("source"), dict) or any(
            not isinstance(source["source"].get(k), str) or not source["source"][k]
            for k in ("name", "record_id")
        ):
            problems.append("unrecognized_source_identity")
        elif source.get("subject_ref") != subject or source.get("field_path") != path:
            problems.append("incompatible_source_assertion")
        elif equal(assertion_value(source), value) or (
            isinstance(assertion_value(source), list)
            and any(equal(v, value) for v in assertion_value(source))
        ):
            sources.append(source)
    return sources, problems


def _conflict(card, paths):
    if not isinstance(card.quality, dict):
        return True
    rows = card.quality.get("conflicts", [])
    return not isinstance(rows, list) or any(
        isinstance(row, dict) and str(row.get("field")).removesuffix(".value") in paths
        for row in rows
    )


def _versions(sources):
    stated, unknown = set(), []
    for source in sources:
        metadata = source.get("source_metadata")
        if metadata is not None and not isinstance(metadata, dict):
            return None, unknown
        version = (
            (metadata or {}).get("sequence_version")
            if source.get("source", {}).get("name") == "UniProt"
            else None
        )
        if version is None:
            unknown.append(source["id"])
        elif type(version) is not int or version < 1:
            return None, unknown
        else:
            stated.add(version)
    return sorted(stated), unknown


def reference(card):
    result = {
        "rule": RULE,
        "status": "not_computed",
        "reason": None,
        "sequence_ref": None,
        "length": None,
        "source_assertion_ids": {},
        "sequence_versions": [],
        "unstated_sequence_version_ids": [],
    }
    fields = {
        path: card.get(path) or {}
        for path in ("identifiers.uniprot", "sequence.primary", "sequence.length")
    }
    fields = {
        path: node if isinstance(node, dict) else {} for path, node in fields.items()
    }
    # Retain the declared inputs independently of admission, using the existing
    # packet terms reference shape. A grouped per-field map alone is not a link.
    result["inputs"] = sorted(
        {
            ref
            for node in fields.values()
            if isinstance(node.get("source_assertion_ids"), list)
            for ref in node["source_assertion_ids"]
            if isinstance(ref, str)
        }
    )
    accession = fields["identifiers.uniprot"].get("value")
    sequence = fields["sequence.primary"].get("value")
    length = fields["sequence.length"].get("value")
    if (
        card.meta.get("entity_type") != "protein"
        or not isinstance(accession, str)
        or not accession
        or card.id != f"sabueso:protein:uniprot:{accession}"
        or not isinstance(sequence, str)
        or not sequence
        or type(length) is not int
        or length != len(sequence)
    ):
        return {**result, "reason": "canonical_identity_sequence_or_length_unavailable"}
    subject = f"uniprot:{accession}"
    result.update(sequence_ref=subject, length=length)
    if _conflict(card, set(fields)):
        return {**result, "reason": "conflicting_canonical_inputs"}
    for path, node in fields.items():
        sources, problems = matching(card, node, path, node.get("value"), subject)
        result["source_assertion_ids"][path] = [s["id"] for s in sources]
        if (
            problems
            or not sources
            or any(
                s.get("source", {}).get("name") != "UniProt"
                or s["source"].get("record_id") != accession
                for s in sources
            )
        ):
            return {**result, "reason": "canonical_source_support_unavailable"}
        if any(
            not equal(source.get("asserted_value"), node.get("value"))
            for source in sources
        ):
            return {**result, "reason": "native_canonical_value_differs"}
        if any(
            not equal(
                assertion_value(card.source_assertion_store.get(ref)), node.get("value")
            )
            for ref in node["source_assertion_ids"]
        ):
            return {**result, "reason": "conflicting_canonical_source_values"}
        if path == "sequence.primary":
            versions, unknown = _versions(sources)
            result.update(
                sequence_versions=versions, unstated_sequence_version_ids=unknown
            )
            if versions is None or len(versions) > 1:
                return {**result, "reason": "invalid_or_conflicting_canonical_revision"}
    return {**result, "status": "comparable"}


def _spans(spans, length):
    if not isinstance(spans, list) or not spans:
        return None
    positions = set()
    for span in spans:
        if not isinstance(span, dict):
            return None
        if set(span) - {
            "start",
            "end",
            "start_modifier",
            "end_modifier",
            "residue",
            "residues",
            "observed_in",
        }:
            return None
        begin, end = span.get("start"), span.get("end")
        if (
            type(begin) is not int
            or type(end) is not int
            or not 1 <= begin <= end <= length
            or any(
                span.get(k + "_modifier") not in (None, "EXACT")
                for k in ("start", "end")
            )
        ):
            return None
        positions.update(range(begin, end + 1))
    return sorted(positions)


def annotation(card, canonical, kind, field, index, value, sources, problems):
    result = {
        "rule": RULE,
        "status": "not_computed",
        "reason": None,
        "sequence_ref": canonical["sequence_ref"],
        "positions": None,
        "field_path": field,
        "index": index,
        "source_assertion_ids": [s["id"] for s in sources],
        "reference_source_assertion_ids": deepcopy(canonical["source_assertion_ids"]),
        "sequence_revisions": {
            "state": "not_stated",
            "annotation": [],
            "reference": canonical["sequence_versions"],
            "unstated_source_assertion_ids": [],
        },
    }

    def stop(reason):
        return {**result, "reason": reason}

    if canonical["status"] != "comparable":
        return stop(canonical["reason"])
    if not isinstance(value, dict):
        return stop("unrecognized_annotation")
    if _conflict(card, {field}):
        return stop("conflicting_annotation_inputs")
    if problems or not sources:
        return stop(
            problems[0] if problems else "annotation_source_support_unavailable"
        )
    location = value.get("location")
    axis = (
        location.get("sequence")
        if isinstance(location, dict) and location.get("kind") == "sequence"
        else None
    )
    accession = canonical["sequence_ref"].split(":", 1)[1]
    if not isinstance(axis, dict) or axis.get("sequence_id") not in (
        canonical["sequence_ref"],
        f"UniProt:{accession}",
    ):
        return stop("annotation_axis_not_canonical")
    if set(location) - {"kind", "sequence"}:
        return stop("annotation_coordinate_shape_unsupported")
    if axis.get("indexing") != "1-based":
        return stop("annotation_indexing_unsupported")
    if "fragments" in axis:
        if kind != "family_site" or set(axis) - {
            "sequence_id",
            "indexing",
            "fragments",
        }:
            return stop("annotation_compound_scope_unsupported")
        spans = axis["fragments"]
    else:
        if set(axis) - {
            "sequence_id",
            "indexing",
            "start",
            "end",
            "start_modifier",
            "end_modifier",
        }:
            return stop("annotation_coordinate_shape_unsupported")
        spans = [
            {
                key: axis[key]
                for key in ("start", "end", "start_modifier", "end_modifier")
                if key in axis
            }
        ]
    positions = _spans(spans, canonical["length"])
    if positions is None:
        return stop("annotation_positions_uncertain_or_invalid")
    for source in sources:
        provider = source.get("source", {})
        if provider.get("name") == "UniProt":
            metadata = source.get("source_metadata")
            native = (
                metadata.get("uniprot_feature") if isinstance(metadata, dict) else None
            )
            if not isinstance(native, dict):
                return stop("native_annotation_scope_not_retained")
            if provider.get("record_id") != accession or native.get("type") != {
                "active_site": "Active site",
                "binding_site": "Binding site",
            }.get(kind):
                return stop("native_annotation_identity_or_type_differs")
            if native.get("molecule") not in (None, accession, f"UniProt:{accession}"):
                return stop("native_annotation_molecule_not_canonical")
            if value.get("molecule") != native.get("molecule"):
                return stop("native_annotation_molecule_differs")
            original = native.get("location")
            if not isinstance(original, dict) or set(original) - {"start", "end"}:
                return stop("native_annotation_compound_scope_unsupported")
            for endpoint in ("start", "end"):
                point = original.get(endpoint)
                if (
                    not isinstance(point, dict)
                    or not equal(axis.get(endpoint), point.get("value"))
                    or not equal(
                        axis.get(endpoint + "_modifier"), point.get("modifier")
                    )
                ):
                    return stop("native_annotation_positions_differ")
        elif provider.get("name") == "InterPro":
            if (
                provider.get("record_id") != accession
                or kind != "family_site"
                or not equal(source.get("asserted_value"), value)
            ):
                return stop("family_annotation_source_scope_differs")
        elif not equal(source.get("asserted_value"), value):
            return stop("annotation_native_normalization_unsupported")
    versions, unknown = _versions(sources)
    revision = result["sequence_revisions"]
    revision.update(annotation=versions, unstated_source_assertion_ids=unknown)
    if (
        versions is None
        or len(versions) > 1
        or versions
        and canonical["sequence_versions"]
        and versions != canonical["sequence_versions"]
    ):
        revision["state"] = "conflicting_or_invalid"
        return stop("annotation_sequence_revision_differs")
    revision["state"] = (
        "matching"
        if versions
        and canonical["sequence_versions"]
        and not unknown
        and not canonical["unstated_sequence_version_ids"]
        else "partially_stated"
        if versions or canonical["sequence_versions"]
        else "not_stated"
    )
    return {**result, "status": "comparable", "positions": positions}


def contact(card, canonical, relationship):
    q = relationship.get("qualifiers")
    result = {
        "rule": RULE,
        "status": "not_computed",
        "reason": None,
        "basis": "captured_relationship_qualifiers",
        "relationship_id": relationship["id"],
        "sequence_ref": canonical["sequence_ref"],
        "positions": None,
        "source_assertion_ids": deepcopy(relationship.get("source_assertion_ids", [])),
        "sequence_revision": "not_stated",
    }

    def stop(reason):
        return {**result, "reason": reason}

    if canonical["status"] != "comparable":
        return stop(canonical["reason"])
    if relationship.get("subject_ref") != canonical["sequence_ref"]:
        return stop("contact_subject_not_canonical")
    if not isinstance(q, dict) or q.get("numbering") != "uniprot":
        return stop("contact_numbering_not_comparable")
    if q.get("indexing", "1-based") != "1-based":
        return stop("contact_indexing_unsupported")
    accession = canonical["sequence_ref"].split(":", 1)[1]
    if any(
        key in q and q[key] not in (canonical["sequence_ref"], f"UniProt:{accession}")
        for key in ("sequence_id", "sequence_ref")
    ):
        return stop("contact_axis_not_canonical")
    if any(key in q for key in ("location", "fragments")):
        return stop("contact_coordinate_shape_unsupported")
    positions = _spans(q.get("residues"), canonical["length"])
    if positions is None:
        return stop("contact_positions_unstated_or_invalid")
    refs = result["source_assertion_ids"]
    if (
        not isinstance(refs, list)
        or not refs
        or any(not isinstance(r, str) for r in refs)
    ):
        return stop("contact_source_support_unavailable")
    for ref in dict.fromkeys(refs):
        source = card.source_assertion_store.get(ref)
        if (
            not source
            or source.get("subject_ref") != canonical["sequence_ref"]
            or source.get("field_path") != "relationships.has_ligand_site"
        ):
            return stop("contact_source_support_incompatible")
        provider = source.get("source")
        if not isinstance(provider, dict) or any(
            not isinstance(provider.get(key), str) or not provider[key]
            for key in ("name", "record_id")
        ):
            return stop("contact_source_identity_unrecognized")
        raw = source.get("asserted_value")
        if (
            isinstance(raw, dict)
            and equal(raw.get("qualifiers"), q)
            and raw.get("object_ref") == relationship["object_ref"]
        ):
            continue
        if (
            source.get("source", {}).get("name") != "PDBe-KB"
            or not isinstance(raw, dict)
            or raw.get("object_ref") != relationship["object_ref"]
        ):
            return stop("contact_native_binding_unsupported")
        if provider["record_id"] != canonical["sequence_ref"].split(":", 1)[1]:
            return stop("contact_native_record_identity_differs")
        ligand = raw.get("ligand")
        if (
            not isinstance(ligand, dict)
            or f"pdb.ligand:{ligand.get('accession')}" != relationship["object_ref"]
        ):
            return stop("contact_native_ligand_identity_differs")
        native = ligand.get("residues") if isinstance(ligand, dict) else None
        if (
            not isinstance(native, list)
            or not native
            or any(
                not isinstance(r, dict)
                or str(r.get("indexType", "")).upper() != "UNIPROT"
                for r in native
            )
        ):
            return stop("contact_native_numbering_not_comparable")
        if any(
            type(r.get(key)) is not int
            for r in native
            for key in ("startIndex", "endIndex")
        ):
            return stop("contact_native_endpoints_not_stated_exactly")
        expected = [
            {
                "start": r.get("startIndex"),
                "end": r.get("endIndex"),
            }
            for r in native
        ]
        if _spans(expected, canonical["length"]) != positions:
            return stop("contact_native_positions_differ")
    return {**result, "status": "comparable", "positions": positions}
