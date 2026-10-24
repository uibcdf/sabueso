"""Bounded wording of original protein declarations; no computed science."""

from itertools import islice


def feature(value):
    from .card_exploration_render import preview

    if not isinstance(value, dict):
        return preview(value)
    description = value.get("description")
    location = value.get("location")
    if not isinstance(location, dict) or location.get("kind") != "sequence":
        return (
            preview(description) + " · " if description else ""
        ) + "original location not an identified sequence location; inspect full record"
    axis = location.get("sequence")
    if not isinstance(axis, dict):
        return "sequence location shape unrecognized; inspect full record"

    def span(row):
        if not isinstance(row, dict):
            return preview(row)
        return "–".join(
            (preview(row[endpoint]) if endpoint in row else "?")
            + (
                f" [{preview(row[endpoint + '_modifier'])}]"
                if row.get(endpoint + "_modifier") is not None
                else ""
            )
            for endpoint in ("start", "end")
        )

    fragments = axis.get("fragments")
    positions = (
        ", ".join(span(row) for row in fragments[:3])
        + (f" … ({len(fragments)} fragments)" if len(fragments) > 3 else "")
        if isinstance(fragments, list)
        else span(axis)
    )
    parts = [preview(description)] if description else []
    parts.extend(
        [
            preview(axis["sequence_id"])
            if axis.get("sequence_id") is not None
            else "sequence axis not stated",
            positions,
            preview(axis["indexing"])
            if axis.get("indexing") is not None
            else "indexing not stated",
        ]
    )
    if value.get("element") is not None:
        parts.append("element: " + preview(value["element"]))
    return " · ".join(parts)


def relationship(topic, row):
    from .card_exploration_render import preview
    from .card_protein_source_v1 import MODEL_FIELDS

    q = row.get("qualifiers")
    if not isinstance(q, dict):
        return "source qualifier shape unrecognized; inspect original relationship"
    if topic == "predicted_structures":

        def metric(key):
            value = q.get(key)
            if value is None:
                return "unknown"
            if key == "range" and isinstance(value, list):
                return "–".join(preview(v, 40) for v in value[:2]) + (
                    " (unexpected range shape; inspect original)"
                    if len(value) != 2
                    else ""
                )
            if key == "plddt_fractions" and isinstance(value, dict):
                return ", ".join(
                    f"{preview(k, 30)}={preview(v, 30)}"
                    for k, v in islice(value.items(), 4)
                ) + (f" … ({len(value)} bands)" if len(value) > 4 else "")
            return preview(value)

        rendered = " · ".join(
            f"{label}: {metric(key)}" for key, label in MODEL_FIELDS.items()
        )
        context = q.get("sequence_context")
        if isinstance(context, dict):
            identity_state = context.get("identity_state")
            identity = {
                "focal_entry": "the declared focal accession",
                "source_stated_isoform": "an isoform stated by UniProt",
                "different_accession_unclassified": "a different accession; isoform relationship not established",
                "model_accession_not_stated": "model accession not stated",
                "invalid_model_accession": "model accession has an unrecognized shape",
            }.get(
                identity_state if isinstance(identity_state, str) else None,
                "identity context unrecognized",
            )
            rendered += (
                f" · Recorded mapping context: {identity}"
                f" · Original context rule: {preview(context.get('rule'))}"
                f" · Coverage of original reference input: {preview(context.get('coverage')) if context.get('coverage') is not None else 'not computed'}"
                " · Full original inputs and uncertainty: open the relationship and its support"
            )
            reasons = context.get("reasons")
            if isinstance(reasons, list) and reasons:
                labels = {
                    "source_stated_isoform": "the model refers to a source-stated isoform",
                    "different_accession_unclassified": "a different accession does not establish an isoform",
                    "model_accession_not_stated": "the model accession was not stated",
                    "invalid_model_accession": "the model accession has an unrecognized shape",
                    "focal_source_support_not_supplied": "original reference source support was not supplied",
                    "focal_checksum_not_retained": "the original reference checksum is not retained",
                    "invalid_focal_checksum": "the reference checksum does not satisfy the MD5 contract",
                    "conflicting_focal_checksums": "the original inputs retain different reference checksums",
                    "focal_checksum_argument_missing_or_invalid": "the checksum argument was missing or invalid",
                    "supplied_checksum_differs_from_original_support": "the supplied checksum differs from its source support",
                    "model_checksum_not_stated": "the model checksum was not stated",
                    "invalid_model_checksum": "the model checksum does not satisfy the MD5 contract",
                    "whole_focal_sequence_scope_not_established": "a whole-reference sequence comparison is not established",
                    "whole_sequence_checksums_differ": "the checksums differ; cause and age are unknown",
                }
                rendered += (
                    " · Why coverage may be unavailable: "
                    + "; ".join(
                        labels.get(reason, preview(reason))
                        if isinstance(reason, str)
                        else preview(reason)
                        for reason in islice(reasons, 3)
                    )
                    + (
                        f" … ({len(reasons)} recorded reasons)"
                        if len(reasons) > 3
                        else ""
                    )
                )
        if row.get("qualifier_conflicts"):
            rendered += " · Alternative model values are retained; inspect qualifier conflicts before interpreting this recorded context"
        return rendered
    residues = q.get("residues")
    positions = (
        ", ".join(
            f"{preview(r.get('start'))}–{preview(r.get('end'))}"
            if isinstance(r, dict)
            else preview(r)
            for r in residues[:3]
        )
        + (f" … ({len(residues)} residue records)" if len(residues) > 3 else "")
        if isinstance(residues, list)
        else "residue declarations not retained or unrecognized"
    )
    return " · ".join(
        [
            "numbering: "
            + (
                preview(q["numbering"]) if q.get("numbering") is not None else "unknown"
            ),
            "retained residue spans: "
            + (positions if positions else "[] (retained empty list)"),
            "Original per-residue observed_in and stated structure references remain in open().native_payload.",
        ]
    )
