"""Frozen source_active_site_selection@1 over original retained inputs (#172).

This is the original residue_annotations@1 predicate followed by the examples'
complete active-site filter. It verifies the fixed dossier @1/@2/@3 criterion;
it does not reconstruct an invocation or add a rule to an old report. Expected
positions are private verifier inputs, never replacement scientific output.
Do not import current residue readers, support/normalization helpers or defaults.
"""

from .errors import SchemaError

RULE = "source_active_site_selection@1"
ANNOTATION_RULE = "residue_annotations@1"
FIELD = "features_positional.active_site"


def _value(assertion):
    return (
        assertion["normalized_value"]
        if "normalized_value" in assertion
        else assertion.get("asserted_value")
    )


def _fields(sections, prefix=""):
    # Preserve literal dotted-key traversal as well as ordinary nested fields.
    for key, node in sections.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(node, dict):
            if "value" in node and "source_assertion_ids" in node:
                yield path, node
            else:
                yield from _fields(node, path)


def _support(card, node, item, subject):
    supported, incomplete = [], False
    for identifier in node.get("source_assertion_ids") or []:
        assertion = card.source_assertion_store.get(identifier)
        if assertion is None or assertion.get("subject_ref") != subject:
            incomplete = True
        elif assertion.get("field_path") == FIELD:
            value = _value(assertion)
            if value == item or isinstance(value, list) and item in value:
                supported.append(assertion)
    return supported if supported and not incomplete else []


def _v1_positions(card):
    """Ascending unique positions selected by the original fixed criterion.

    Nonmapped, unsupported or absent annotations select no positions. That is
    never a finding that the source has no active sites or structures cover them:
    the dossier's original empty-selection check remains unknown. Compound/fuzzy
    locations retain their original unsupported interpretation, without backfill.
    """
    sequence_node = card.get("sequence.primary") or {}
    sequence = sequence_node.get("value")
    accession = (card.get("identifiers.uniprot") or {}).get("value")
    if (
        card.meta.get("entity_type") != "protein"
        or not isinstance(sequence, str)
        or not sequence
        or not isinstance(accession, str)
        or not accession
    ):
        raise SchemaError(
            "Original active-site selection needs a canonical protein sequence and UniProt identity."
        )
    subject, axis = f"uniprot:{accession}", f"UniProt:{accession}"
    sequence_versions = {
        assertion.get("source_metadata", {}).get("sequence_version")
        for identifier in sequence_node.get("source_assertion_ids") or []
        if (assertion := card.source_assertion_store.get(identifier)) is not None
        and assertion.get("subject_ref") == subject
        and assertion.get("source", {}).get("name") == "UniProt"
        and assertion.get("field_path") == "sequence.primary"
        and _value(assertion) == sequence
        and assertion.get("source_metadata", {}).get("sequence_version") is not None
    }
    spans = []
    for path, node in _fields(card.sections):
        if path != FIELD:
            continue
        for item in node.get("value") or []:
            if not isinstance(item, dict):
                continue
            location = item.get("location") or {}
            coordinates = location.get("sequence") or {}
            if location.get("kind") != "sequence":
                continue
            stated = coordinates.get("sequence_id")
            if (
                not isinstance(stated, str)
                or not stated
                or stated.casefold() != axis.casefold()
            ):
                continue
            sources = _support(card, node, item, subject)
            versions = {
                source.get("source_metadata", {}).get("sequence_version")
                for source in sources
                if source.get("source", {}).get("name") == "UniProt"
                and source.get("source_metadata", {}).get("sequence_version")
                is not None
            }
            if versions and sequence_versions and versions != sequence_versions:
                continue
            begin, end = coordinates.get("start"), coordinates.get("end")
            if (
                not sources
                or coordinates.get("indexing") != "1-based"
                or any(
                    coordinates.get(f"{endpoint}_modifier") not in (None, "EXACT")
                    for endpoint in ("start", "end")
                )
                or any(
                    isinstance(n, bool) or not isinstance(n, int) for n in (begin, end)
                )
                or not 1 <= begin <= end <= len(sequence)
            ):
                continue
            spans.append((begin, end))
    # Equivalent to filtering every original residue row, without constructing
    # rows for the rest of the sequence or copying every annotation per position.
    merged = []
    for begin, end in sorted(spans):
        if merged and begin <= merged[-1][1] + 1:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([begin, end])
    return [position for begin, end in merged for position in range(begin, end + 1)]
