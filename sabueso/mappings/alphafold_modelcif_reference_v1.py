"""Source-bound native sequence-interval correspondence, without atom mapping.

This rule decodes retained sequence tokens only. Gemmi is neither imported nor
used to reconstruct a document. Original declarations and source assertions stay
unchanged; calculated checksums and comparisons belong to this derived finding.
"""

import hashlib
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError
from sabueso.core.relationship_store import (
    RelationshipStore,
    make_derivation,
    make_relationship,
)
from sabueso.core.snapshot import canonical_json, digest

from .alphafold_modelcif_v1 import (
    FORMAT,
    _integer,
    _plain,
    _rows,
    bound_declaration,
    declaration,
    map_modelcif_predictions,
)

RULE = "alphafold_modelcif_reference_context@1"
KEY = "native_reference_context"
FIELDS = ("sequence.primary", "sequence.length", "sequence.checksums")
QUALIFIER_PATHS = [KEY]
AMINO_ACIDS = dict(
    zip(
        "ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL".split(),
        "ARNDCQEGHILKMFPSTWYV",
    )
)


def crc64(sequence):
    """CRC-64/ISO: reflected 0xD800000000000000, initial/final zero."""
    value = 0
    for byte in sequence.encode("ascii"):
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0xD800000000000000 if value & 1 else 0)
    return f"{value:016X}"


def original_inputs(assertions, accession):
    """All supplied original focal database statements; no selected-field fallback."""
    rows = []
    for row in assertions or []:
        if not isinstance(row, dict):
            continue
        source, acquisition = row.get("source"), row.get("acquisition")
        if not isinstance(source, dict) or not isinstance(acquisition, dict):
            continue
        if (
            isinstance(row.get("id"), str)
            and row.get("subject_ref") == f"uniprot:{accession}"
            and row.get("field_path") in FIELDS
            and source.get("name") == "UniProt"
            and source.get("record_id") == accession
            and source.get("type") == "database"
            and acquisition.get("method") == "database"
        ):
            if not any(canonical_json(row) == canonical_json(old) for old in rows):
                rows.append(row)
    return sorted(rows, key=lambda row: (row["id"], canonical_json(row)))


def _sequence_token(token):
    """Decode CIF1 sequence quoting and ASCII layout; never repair chemistry."""
    if not isinstance(token, str) or not token or token in ("?", "."):
        return None
    if token.startswith(";"):
        if token.endswith("\r\n;"):
            token = token[1:-3]
        elif token.endswith(("\n;", "\r;")):
            token = token[1:-2]
        else:
            return None
    elif token.startswith(("'", '"')):
        if token[-1:] != token[:1] or len(token) < 2:
            return None
        token = token[1:-1]
    elif any(char in token for char in " \t\r\n"):
        return None
    token = token.translate(str.maketrans("", "", " \t\r\n"))
    return token if token and set(token) <= set(AMINO_ACIDS.values()) else None


def _native_sequence(record, projected):
    (entity,) = _rows(record, "_entity_poly.")
    sequence = _sequence_token(entity.get("pdbx_seq_one_letter_code_can"))
    if (
        sequence is None
        or _sequence_token(entity.get("pdbx_seq_one_letter_code")) != sequence
    ):
        return None
    if any(_plain(entity.get(key)) != "no" for key in ("nstd_linkage", "nstd_monomer")):
        return None
    rows = _rows(record, "_entity_poly_seq.")
    if len(rows) != len(sequence):
        return None
    positions = {}
    for row in rows:
        number = _integer(row.get("num"))
        code = AMINO_ACIDS.get(_plain(row.get("mon_id")))
        if (
            number is None
            or number in positions
            or code is None
            or _plain(row.get("entity_id")) != projected["target_entity_id"]
            or _plain(row.get("hetero")) != "n"
        ):
            return None
        positions[number] = code
    if set(positions) != set(range(1, len(sequence) + 1)):
        return None
    if "".join(positions[i] for i in range(1, len(sequence) + 1)) != sequence:
        return None
    return sequence


def _hex(value, size):
    return (
        value.upper()
        if isinstance(value, str) and re.fullmatch(f"[0-9a-fA-F]{{{size}}}", value)
        else None
    )


def interpret(record, accession, assertions=None):
    """Compare original explicit reference intervals, not identities by similarity."""
    rows = original_inputs(assertions, accession)
    result = {
        "rule": RULE,
        "input_contract": FORMAT,
        "input_binding": "source_assertions"
        if assertions is not None
        else "not_supplied",
        "reference_accession": accession,
        "model_id": None,
        "identity_basis": "explicit_native_UNP_reference_row; never_sequence_similarity",
        "state": "missing_prerequisite",
        "reasons": [],
        "eligible_for_reference_interval": False,
        "focal_input_assertion_ids": sorted({row["id"] for row in rows}),
        "reference": {
            "entry_version": None,
            "sequence_version": None,
            "length": None,
            "computed_md5": None,
            "computed_crc64": None,
            "stated_md5": None,
            "stated_crc64": None,
            "checksum_integrity": None,
            "sequence_date": None,
        },
        "comparison": {
            "reference_interval": [None, None],
            "entity_sequence_interval": [None, None],
            "entity_sequence_length": None,
            "model_scope": None,
            "native_reference_crc64": None,
            "reference_crc64_equal": None,
            "native_reference_sequence_date": None,
            "reference_date_equal": None,
            "interval_sequence_equal": None,
            "additional_reference_sequence_scope": None,
        },
        "sequence_date_scope": "native_date_retained; original_UniProt_sequence_date_not_retained",
        "coordinate_or_assembly_mapping": "not_evaluated",
        "experimental_equivalence": "not_evaluated",
        "isoform_membership": "not_established_by_sequence_comparison",
    }

    def stop(state, reason):
        return {**result, "state": state, "reasons": [reason]}

    try:
        projected = declaration(record, accession)
    except (ConnectorError, TypeError, ValueError):
        return stop("unsupported", "invalid_or_unsupported_native_declarations")
    comparison, reference = result["comparison"], result["reference"]
    result["model_id"] = projected["model_id"]
    comparison.update(
        reference_interval=deepcopy(projected["reference_range"]),
        entity_sequence_interval=deepcopy(projected["model_sequence_range"]),
        native_reference_crc64=projected["reference_crc64"],
        native_reference_sequence_date=projected["reference_sequence_version_date"],
    )
    if projected["isoform_source_token"] not in (None, "?", "."):
        return stop(
            "unsupported", "native_isoform_declaration_requires_separate_reference"
        )
    groups = {
        path: [row for row in rows if row["field_path"] == path] for path in FIELDS
    }
    if any(not group for group in groups.values()):
        return stop(
            "missing_prerequisite",
            "original_focal_sequence_length_or_checksums_not_retained",
        )
    if any(len(group) != 1 for group in groups.values()):
        return stop("ambiguous", "multiple_original_focal_inputs_unselected")
    if any(
        row.get("source_metadata") is not None
        and not isinstance(row["source_metadata"], dict)
        for row in rows
    ):
        return stop("unsupported", "invalid_original_focal_revision_metadata")
    versions = [
        (
            row["source"].get("version"),
            row["source_metadata"].get("sequence_version")
            if isinstance(row.get("source_metadata"), dict)
            else None,
        )
        for row in rows
    ]
    if any(
        entry is None or sequence_version is None
        for entry, sequence_version in versions
    ):
        return stop(
            "missing_prerequisite", "original_focal_revision_context_not_retained"
        )
    if any(
        not isinstance(entry, str)
        or not entry
        or type(sequence_version) is not int
        or sequence_version <= 0
        for entry, sequence_version in versions
    ):
        return stop("unsupported", "invalid_original_focal_revision_metadata")
    if len(set(versions)) != 1:
        return stop("ambiguous", "original_focal_revision_contexts_differ")
    reference["entry_version"], reference["sequence_version"] = versions[0]
    sequence = groups["sequence.primary"][0].get("asserted_value")
    length = groups["sequence.length"][0].get("asserted_value")
    checksums = groups["sequence.checksums"][0].get("asserted_value")
    if (
        not isinstance(sequence, str)
        or not sequence
        or not set(sequence) <= set(AMINO_ACIDS.values())
        or type(length) is not int
        or length != len(sequence)
    ):
        return stop("unsupported", "invalid_or_ambiguous_original_focal_sequence")
    reference["length"] = length
    if not isinstance(checksums, dict):
        return stop("unsupported", "invalid_original_focal_checksums")
    reference.update(
        stated_md5=deepcopy(checksums.get("md5")),
        stated_crc64=deepcopy(checksums.get("crc64")),
        computed_md5=hashlib.md5(
            sequence.encode("ascii"), usedforsecurity=False
        ).hexdigest(),
        computed_crc64=crc64(sequence),
    )
    if (
        _hex(checksums.get("md5"), 32) is None
        or _hex(checksums.get("crc64"), 16) is None
    ):
        return stop(
            "missing_prerequisite"
            if any(checksums.get(key) is None for key in ("md5", "crc64"))
            else "unsupported",
            "original_focal_md5_or_crc64_missing_or_invalid",
        )
    reference["checksum_integrity"] = (
        _hex(checksums["md5"], 32) == reference["computed_md5"].upper()
        and _hex(checksums["crc64"], 16) == reference["computed_crc64"]
    )
    if not reference["checksum_integrity"]:
        return stop(
            "unsupported", "original_focal_sequence_differs_from_its_stated_checksums"
        )
    native_crc = _hex(projected["reference_crc64"], 16)
    if native_crc is not None:
        comparison["reference_crc64_equal"] = native_crc == reference["computed_crc64"]
    begin, end = projected["reference_range"]
    if not (type(begin) is int and type(end) is int and 1 <= begin <= end <= length):
        return stop(
            "unsupported",
            "native_reference_interval_incomplete_conflicting_or_outside_focal_sequence",
        )
    # Additional original STRUCT_REF declarations cannot silently disagree with
    # the primary reference/alignment. Its sequence can state the full database
    # sequence or the already explicit interval; neither establishes atom mapping.
    (struct,) = _rows(record, "_struct_ref.")
    if struct.get("pdbx_db_isoform") not in (None, "?", "."):
        return stop(
            "unsupported",
            "additional_native_reference_isoform_requires_separate_reference",
        )
    try:
        stated_begin = _integer(struct.get("pdbx_align_begin"))
    except ConnectorError:
        return stop("unsupported", "invalid_additional_native_reference_start")
    if stated_begin is not None and stated_begin != begin:
        return stop("unsupported", "additional_native_reference_start_differs")
    token = struct.get("pdbx_seq_one_letter_code")
    if token not in (None, "?", "."):
        stated_sequence = _sequence_token(token)
        if stated_sequence == sequence:
            comparison["additional_reference_sequence_scope"] = "whole_reference"
        elif stated_sequence == sequence[begin - 1 : end]:
            comparison["additional_reference_sequence_scope"] = (
                "explicit_reference_interval"
            )
        else:
            return stop(
                "unsupported",
                "additional_native_reference_sequence_differs_or_is_ambiguous",
            )
    else:
        comparison["additional_reference_sequence_scope"] = "not_stated"
    try:
        model_sequence = _native_sequence(record, projected)
    except (ConnectorError, TypeError, ValueError):
        model_sequence = None
    if model_sequence is None:
        return stop(
            "unsupported", "native_sequence_tokens_or_entity_positions_not_unambiguous"
        )
    comparison["entity_sequence_length"] = len(model_sequence)
    if (
        projected["model_sequence_range"] != [1, len(model_sequence)]
        or len(model_sequence) != end - begin + 1
    ):
        return stop(
            "unsupported",
            "native_alignment_does_not_declare_the_complete_entity_interval",
        )
    comparison["model_scope"] = (
        "whole_reference" if [begin, end] == [1, length] else "proper_fragment"
    )
    comparison["interval_sequence_equal"] = model_sequence == sequence[begin - 1 : end]
    if native_crc is None:
        return stop(
            "missing_prerequisite"
            if projected["reference_crc64"] is None
            else "unsupported",
            "native_reference_crc64_missing_or_invalid",
        )
    if not comparison["reference_crc64_equal"]:
        return stop(
            "mismatch", "native_reference_crc64_differs; cause_or_age_not_inferred"
        )
    if not comparison["interval_sequence_equal"]:
        return stop(
            "mismatch",
            "native_entity_sequence_differs_from_the_explicit_reference_interval",
        )
    return {
        **result,
        "state": "comparable_interval",
        "eligible_for_reference_interval": True,
    }


def map_modelcif_reference_context(
    response, accession, retrieved_at, *, input_assertions=None
):
    """Add a separately bound finding; keep the original declaration rule intact."""
    mapping = map_modelcif_predictions(response, accession, retrieved_at)
    (original,) = mapping["relationships"]
    (source,) = mapping["source_assertions"]
    finding = interpret(response["record"], accession, input_assertions)
    refs = finding["focal_input_assertion_ids"]
    derived = make_relationship(
        original["subject_ref"],
        original["predicate"],
        original["object_ref"],
        qualifiers={KEY: finding},
        source_assertion_ids=[source["id"]],
        derivation=make_derivation(
            RULE,
            inputs=[source["id"], *refs],
            parameters={
                "qualifier_paths": QUALIFIER_PATHS,
                "focal_accession": accession,
                "focal_input_assertion_ids": refs,
                "input_binding": finding["input_binding"],
                "model_input_path": ["asserted_value", "modelcif_metadata"],
            },
        ),
    )
    mapping["relationships"] = RelationshipStore([original, derived]).to_list()
    return mapping


def bound_context(card, relationship):
    """Replay the recorded context from original sources, never current fields."""
    if bound_declaration(card, relationship) is None:
        return None
    qualifiers = relationship.get("qualifiers") or {}
    expected = qualifiers.get(KEY)
    if (
        not isinstance(expected, dict)
        or expected.get("rule") != RULE
        or KEY in (relationship.get("qualifier_conflicts") or {})
    ):
        return None
    applications = [
        a
        for a in relationship.get("derivation_applications") or []
        if isinstance(a, dict)
        and isinstance(a.get("derivation"), dict)
        and a["derivation"].get("rule") == RULE
    ]
    model_refs = relationship.get("source_assertion_ids")
    if (
        len(applications) != 1
        or not isinstance(model_refs, list)
        or len(model_refs) != 1
    ):
        return None
    application = applications[0]
    derivation = application["derivation"]
    parameters = derivation.get("parameters")
    if application.get("binding") != "original_output" or not isinstance(
        parameters, dict
    ):
        return None
    if (
        parameters.get("qualifier_paths") != QUALIFIER_PATHS
        or parameters.get("model_input_path") != ["asserted_value", "modelcif_metadata"]
        or parameters.get("input_binding") not in ("source_assertions", "not_supplied")
    ):
        return None
    accession = parameters.get("focal_accession")
    refs = parameters.get("focal_input_assertion_ids")
    if (
        relationship.get("subject_ref") != f"uniprot:{accession}"
        or not isinstance(refs, list)
        or any(not isinstance(ref, str) for ref in refs + model_refs)
        or refs != sorted(set(refs))
    ):
        return None
    rows = [card.source_assertion_store.get(ref) for ref in refs]
    if any(row is None for row in rows) or {
        r["id"] for r in original_inputs(rows, accession)
    } != set(refs):
        return None
    (model_ref,) = model_refs
    source = card.source_assertion_store.get(model_ref) or {}
    value = source.get("asserted_value") or {}
    if (
        not isinstance(value, dict)
        or "modelcif_metadata" not in value
        or derivation.get("inputs") != [model_ref, *refs]
        or application.get("source_assertion_ids") != [model_ref]
    ):
        return None
    metadata = source.get("source_metadata")
    extraction = (
        metadata.get("native_extraction") if isinstance(metadata, dict) else None
    )
    if (
        not isinstance(extraction, dict)
        or metadata.get("input_contract") != FORMAT
        or extraction.get("format") != FORMAT
        or extraction.get("metadata_sha256")
        != digest(canonical_json(value["modelcif_metadata"]))
    ):
        return None
    supplied = rows if parameters["input_binding"] == "source_assertions" else None
    replay = interpret(value["modelcif_metadata"], accession, supplied)
    recorded = application.get("qualifiers")
    if (
        isinstance(recorded, dict)
        and KEY in recorded
        and canonical_json(replay)
        == canonical_json(expected)
        == canonical_json(recorded[KEY])
    ):
        return deepcopy(replay)
    return None
