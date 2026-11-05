"""Original AlphaFold ModelCIF metadata declarations, apart from API models.

Only the optional input parser needs Gemmi. Declaration projection and original
binding use retained literal metadata and never interpret coordinates, compare
sequences or infer an isoform. Keep this named policy stable for saved inputs.
"""

import importlib
import math
import re
from copy import deepcopy

from depdigest import dep_digest

from sabueso.core.errors import ConnectorError
from sabueso.core.relationship_store import make_derivation, make_relationship
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

FORMAT = "alphafold_modelcif_metadata@1"
RULE = "alphafold_modelcif_declaration@1"
SOURCE = "AlphaFold DB"
KIND = "modelcif_prediction"
QUALIFIER_PATHS = [
    "native_modelcif",
    "range",
    "tool",
    "mean_plddt",
    "model_version",
    "created",
    "isoform",
    "sequence_matches",
]


@dep_digest("gemmi")
def _gemmi():
    return importlib.import_module("gemmi")


def extract_metadata(text):
    """Validate one whole CIF document; retain every non-atom-site column token."""
    if not isinstance(text, str) or not text:
        raise ConnectorError("AlphaFold ModelCIF requires nonempty original text.")
    gemmi = _gemmi()
    try:
        document = gemmi.cif.read_string(text)
        document.check_for_duplicates()
        document.check_for_missing_values()
        block = document.sole_block()
        columns, pairs, loops, excluded = {}, [], [], []
        for item in block:
            if item.frame is not None:
                raise ValueError("Save frames are outside this single-model contract.")
            if item.pair is not None:
                tag, token = item.pair
                if tag.lower().startswith(("_atom_site.", "_atom_site_anisotrop.")):
                    excluded.append({"tags": [tag], "rows": 1})
                else:
                    pairs.append(tag)
                    columns[tag] = [token]
            elif item.loop is not None:
                tags = list(item.loop.tags)
                if not tags or len(item.loop.values) % len(tags):
                    raise ValueError("A complete native loop is required.")
                omitted = [
                    tag
                    for tag in tags
                    if tag.lower().startswith(("_atom_site.", "_atom_site_anisotrop."))
                ]
                if omitted:
                    if len(omitted) != len(tags):
                        raise ValueError(
                            "Coordinate and metadata columns cannot share a loop."
                        )
                    excluded.append(
                        {"tags": tags, "rows": len(item.loop.values) // len(tags)}
                    )
                else:
                    loops.append(tags)
                    for i, tag in enumerate(tags):
                        columns[tag] = list(item.loop.values[i :: len(tags)])
        record = {
            "block_name": block.name,
            "columns": columns,
            "pairs": pairs,
            "loops": loops,
        }
        validate_record(record)
        return record, excluded
    except (ValueError, RuntimeError, IndexError) as error:
        raise ConnectorError(
            f"Invalid or unsupported AlphaFold ModelCIF: {error}"
        ) from error


def validate_record(record):
    """Closed literal representation; no dependency or source-file access."""
    if not isinstance(record, dict) or set(record) != {
        "block_name",
        "columns",
        "pairs",
        "loops",
    }:
        raise ConnectorError("Unsupported AlphaFold ModelCIF metadata representation.")
    columns, pairs, loops = record["columns"], record["pairs"], record["loops"]
    if (
        not isinstance(record["block_name"], str)
        or not record["block_name"]
        or not isinstance(columns, dict)
        or not isinstance(pairs, list)
        or not isinstance(loops, list)
    ):
        raise ConnectorError("Invalid AlphaFold ModelCIF block/columns.")
    if any(
        not isinstance(tag, str)
        or not tag.startswith("_")
        or not isinstance(values, list)
        or not values
        or any(not isinstance(v, str) or not v for v in values)
        for tag, values in columns.items()
    ):
        raise ConnectorError("Invalid or empty native metadata column.")
    if len({tag.lower() for tag in columns}) != len(columns):
        raise ConnectorError("Repeated case-insensitive native metadata tag.")
    if any(
        tag.lower().startswith(("_atom_site.", "_atom_site_anisotrop."))
        for tag in columns
    ):
        raise ConnectorError("Coordinate columns cannot enter Card metadata.")
    if any(
        not isinstance(tag, str) or tag not in columns or len(columns[tag]) != 1
        for tag in pairs
    ):
        raise ConnectorError("Invalid native scalar membership.")
    names = list(pairs)
    for tags in loops:
        if (
            not isinstance(tags, list)
            or not tags
            or any(not isinstance(tag, str) or tag not in columns for tag in tags)
            or len({len(columns[tag]) for tag in tags}) != 1
        ):
            raise ConnectorError("Invalid native loop membership/width.")
        names.extend(tags)
    if len(names) != len(set(names)) or set(names) != set(columns):
        raise ConnectorError("Native column membership is incomplete or repeated.")


def _plain(token):
    """Single-line declaration scalars only; sequence/text columns remain literal."""
    if token is None or token in ("?", "."):
        return None
    if token.startswith(("'", '"')) and token[-1:] == token[:1]:
        return token[1:-1]
    if token.startswith(";") or any(c in token for c in "\r\n"):
        raise ConnectorError(
            "Multiline identity/number declarations are outside this native contract."
        )
    return token


def _rows(record, category):
    columns = {
        tag.lower()[len(category) :]: values
        for tag, values in record["columns"].items()
        if tag.lower().startswith(category)
    }
    if not columns:
        return []
    if len({len(values) for values in columns.values()}) != 1:
        raise ConnectorError("Native category columns have incompatible row counts.")
    if len(next(iter(columns.values()))) > 1:
        groups = [
            tags
            for tags in record["loops"]
            if any(tag.lower().startswith(category) for tag in tags)
        ]
        category_tags = {
            tag for tag in record["columns"] if tag.lower().startswith(category)
        }
        if len(groups) != 1 or not category_tags.issubset(groups[0]):
            raise ConnectorError(
                "Native category rows must share one original loop; independent loops are never joined by ordinal."
            )
    return [
        {key: values[i] for key, values in columns.items()}
        for i in range(len(next(iter(columns.values()))))
    ]


def _integer(token):
    value = _plain(token)
    if value is None:
        return None
    if not re.fullmatch(r"[1-9][0-9]*", value):
        raise ConnectorError(
            "A stated native sequence bound must be a positive integer."
        )
    return int(value)


def declaration(record, accession):
    """Project explicit source declarations, never canonical correspondence."""
    validate_record(record)
    if not isinstance(accession, str) or not accession:
        raise ConnectorError("An explicit reference accession is required.")
    databases = [
        r
        for r in _rows(record, "_database_2.")
        if _plain(r.get("database_id")) == "AlphaFoldDB"
    ]
    if len(databases) != 1:
        raise ConnectorError("One explicit AlphaFoldDB model identity is required.")
    model = _plain(databases[0].get("database_code"))
    if not isinstance(model, str) or not re.fullmatch(
        r"AF-[A-Za-z0-9][A-Za-z0-9_-]*", model
    ):
        raise ConnectorError("Invalid or unstated native AlphaFold model identifier.")
    entities = _rows(record, "_entity_poly.")
    models = _rows(record, "_ma_model_list.")
    if (
        len(entities) != 1
        or len(models) != 1
        or _plain(entities[0].get("type")) != "polypeptide(L)"
    ):
        raise ConnectorError(
            "This native contract requires one polypeptide target and one model; no alternative is selected."
        )
    entity = _plain(entities[0].get("entity_id"))
    model_id = _plain(models[0].get("model_id"))
    chains = _rows(record, "_struct_asym.")
    if (
        not entity
        or not model_id
        or len(chains) != 1
        or not _plain(chains[0].get("id"))
        or _plain(chains[0].get("entity_id")) != entity
    ):
        raise ConnectorError(
            "One source-bound target chain is required; no assembly is inferred."
        )
    refs = _rows(record, "_ma_target_ref_db_details.")
    if not refs or any(_plain(r.get("target_entity_id")) != entity for r in refs):
        raise ConnectorError(
            "All reference rows must explicitly name the retained target entity."
        )
    uniprot = [r for r in refs if _plain(r.get("db_name")) == "UNP"]
    if not any(_plain(r.get("db_accession")) == accession for r in uniprot):
        raise ConnectorError(
            "The native model does not explicitly declare the requested UniProt accession; no identity is inferred from its name or sequence."
        )
    structs = _rows(record, "_struct_ref.")
    struct_ids = [_plain(r.get("id")) for r in structs]
    if (
        not structs
        or any(not ref for ref in struct_ids)
        or len(set(struct_ids)) != len(struct_ids)
        or any(_plain(r.get("entity_id")) != entity for r in structs)
    ):
        raise ConnectorError(
            "Native structural reference rows require unique IDs and the original target entity."
        )
    alignments = _rows(record, "_struct_ref_seq.")
    if not alignments or any(
        _plain(r.get("ref_id")) not in struct_ids for r in alignments
    ):
        raise ConnectorError(
            "Every native alignment must bind an original reference row."
        )
    for row in refs:
        for key in ("seq_db_align_begin", "seq_db_align_end"):
            _integer(row.get(key))
    for row in alignments:
        for key in ("db_align_beg", "db_align_end", "seq_align_beg", "seq_align_end"):
            _integer(row.get(key))
    reasons, span, model_span = [], [None, None], [None, None]
    crc64 = sequence_date = isoform = None
    if len(refs) == len(uniprot) == len(structs) == len(alignments) == 1:
        ref, struct, alignment = refs[0], structs[0], alignments[0]
        a, z = (
            _integer(ref.get("seq_db_align_begin")),
            _integer(ref.get("seq_db_align_end")),
        )
        start, end = (
            _integer(alignment.get("seq_align_beg")),
            _integer(alignment.get("seq_align_end")),
        )
        if not (
            a is not None
            and z is not None
            and a <= z
            and start is not None
            and end is not None
            and start <= end
            and _plain(struct.get("db_name")) == "UNP"
            and _plain(struct.get("pdbx_db_accession")) == accession
            and _plain(alignment.get("pdbx_db_accession")) == accession
            and [
                _integer(alignment.get("db_align_beg")),
                _integer(alignment.get("db_align_end")),
            ]
            == [a, z]
            and _plain(alignment.get("pdbx_strand_id")) == _plain(chains[0].get("id"))
        ):
            reasons.append("incomplete_or_inconsistent_native_reference_declarations")
        else:
            span, model_span = [a, z], [start, end]
        crc64 = _plain(ref.get("seq_db_sequence_checksum"))
        if crc64 is not None and not re.fullmatch(r"[0-9a-fA-F]{16}", crc64):
            reasons.append("invalid_stated_reference_crc64")
        sequence_date = _plain(ref.get("seq_db_sequence_version_date"))
        isoform = ref.get("seq_db_isoform")
    else:
        reasons.append("multiple_native_reference_rows_unselected")
    tool_rows = [
        r for r in _rows(record, "_software.") if _plain(r.get("name")) == "AlphaFold"
    ]
    tool = None
    if len(tool_rows) == 1:
        tool = " ".join(
            v
            for v in (
                _plain(tool_rows[0].get("name")),
                _plain(tool_rows[0].get("version")),
            )
            if v
        )
    elif tool_rows:
        reasons.append("multiple_native_software_rows_unselected")
    metric_rows = [
        r
        for r in _rows(record, "_ma_qa_metric.")
        if _plain(r.get("type")) == "pLDDT" and _plain(r.get("mode")) == "global"
    ]
    globals_ = _rows(record, "_ma_qa_metric_global.")
    metrics = [
        r
        for r in globals_
        if len(metric_rows) == 1
        and _plain(r.get("metric_id")) == _plain(metric_rows[0].get("id"))
        and _plain(r.get("model_id")) == model_id
    ]
    mean = None
    if len(metrics) == 1 and _plain(metrics[0].get("metric_value")) is not None:
        try:
            value = float(_plain(metrics[0]["metric_value"]))
        except ValueError:
            value = float("nan")
        if math.isfinite(value) and 0 <= value <= 100:
            mean = value
        else:
            reasons.append("invalid_native_global_plddt")
    elif len(metrics) > 1 or len(metric_rows) > 1:
        reasons.append("multiple_native_global_plddt_rows_unselected")
    return {
        "rule": RULE,
        "input_contract": FORMAT,
        "model_id": model,
        "reference_accession": accession,
        "identity_basis": "explicit_native_UNP_reference_row",
        "target_entity_id": entity,
        "reference_row_count": len(refs),
        "alignment_row_count": len(alignments),
        "state": "source_declared" if not reasons else "unresolved_native_declarations",
        "reference_range": span,
        "model_sequence_range": model_span,
        "reference_crc64": crc64,
        "checksum_scope": "reference_database_sequence; not_model_MD5",
        "reference_sequence_version_date": sequence_date,
        "isoform_source_token": isoform,
        "canonical_correspondence": "not_evaluated",
        "coordinate_or_assembly_mapping": "not_evaluated",
        "tool": tool,
        "mean_plddt": mean,
        "model_version": None,
        "reasons": reasons,
    }


def validate_response(response, accession):
    """Validate the explicit native envelope without importing a file parser."""
    if (
        not isinstance(response, dict)
        or response.get("source") != SOURCE
        or response.get("kind") != KIND
        or response.get("query") != {"accession": accession}
        or response.get("version") is not None
        or response.get("native_format") != FORMAT
    ):
        raise ConnectorError(
            "Native AlphaFold metadata response differs from its source/query contract."
        )
    projected = declaration(response.get("record"), accession)
    extraction = response.get("native_extraction")
    if (
        not isinstance(extraction, dict)
        or extraction.get("format") != FORMAT
        or extraction.get("metadata_sha256")
        != digest(canonical_json(response["record"]))
    ):
        raise ConnectorError(
            "Native metadata differs from its recorded extraction identity."
        )
    return projected


def _qualifiers(projected):
    return {
        "native_modelcif": projected,
        "range": projected["reference_range"],
        "tool": projected["tool"],
        "mean_plddt": projected["mean_plddt"],
        "model_version": None,
        "created": None,
        "isoform": None,
        "sequence_matches": None,
    }


def map_modelcif_predictions(response, accession, retrieved_at):
    """One native declaration with literal support; no synthetic API record."""
    projected = validate_response(response, accession)
    object_ref = "alphafold:" + projected["model_id"]
    assertion = make_source_assertion(
        "relationships.has_predicted_structure",
        {"object_ref": object_ref, "modelcif_metadata": deepcopy(response["record"])},
        SOURCE,
        projected["model_id"],
        retrieved_at,
        subject_ref=f"uniprot:{accession}",
    )
    assertion["source_metadata"] = {
        "input_contract": FORMAT,
        "native_extraction": deepcopy(response["native_extraction"]),
        "snapshot_receipt": deepcopy(response.get("snapshot_receipt")),
    }
    relationship = make_relationship(
        f"uniprot:{accession}",
        "has_predicted_structure",
        object_ref,
        qualifiers=_qualifiers(projected),
        source_assertion_ids=[assertion["id"]],
        derivation=make_derivation(
            RULE,
            inputs=[assertion["id"]],
            parameters={
                "qualifier_paths": QUALIFIER_PATHS,
                "focal_accession": accession,
                "model_input_path": ["asserted_value", "modelcif_metadata"],
            },
        ),
    )
    return {
        "fields": {},
        "source_assertions": [assertion],
        "field_source_assertions": {},
        "relationships": [relationship],
    }


def bound_declaration(card, relationship):
    """Require the exact original native source and recorded declaration output."""
    if not isinstance(relationship, dict):
        return None
    q = relationship.get("qualifiers") or {}
    if (
        not isinstance(q, dict)
        or not isinstance(q.get("native_modelcif"), dict)
        or q["native_modelcif"].get("rule") != RULE
        or q.get("sequence_context") is not None
    ):
        return None
    if not isinstance(relationship.get("qualifier_conflicts", {}), dict):
        return None
    if any(
        path in (relationship.get("qualifier_conflicts") or {})
        for path in QUALIFIER_PATHS
    ):
        return None
    applications = relationship.get("derivation_applications") or []
    if not isinstance(applications, list):
        return None
    for application in applications:
        if not isinstance(application, dict):
            continue
        if application.get("binding") != "original_output":
            continue
        derivation = application.get("derivation") or {}
        if not isinstance(derivation, dict):
            continue
        params = derivation.get("parameters") or {}
        if (
            not isinstance(params, dict)
            or derivation.get("rule") != RULE
            or params.get("qualifier_paths") != QUALIFIER_PATHS
        ):
            continue
        accession = params.get("focal_accession")
        if relationship.get("subject_ref") != f"uniprot:{accession}":
            continue
        for ref in relationship.get("source_assertion_ids") or []:
            assertion = card.source_assertion_store.get(ref) or {}
            original = assertion.get("asserted_value") or {}
            if not isinstance(original, dict):
                continue
            if (
                assertion.get("field_path") != "relationships.has_predicted_structure"
                or assertion.get("subject_ref") != relationship["subject_ref"]
                or (assertion.get("source") or {}).get("name") != SOURCE
                or original.get("object_ref") != relationship["object_ref"]
                or derivation.get("inputs") != [ref]
            ):
                continue
            try:
                replay = declaration(original["modelcif_metadata"], accession)
            except (ConnectorError, KeyError, TypeError, ValueError):
                continue
            expected = _qualifiers(replay)
            output = application.get("qualifiers")
            if not isinstance(output, dict):
                continue
            if (
                (assertion.get("source") or {}).get("record_id") == replay["model_id"]
                and relationship["object_ref"] == "alphafold:" + replay["model_id"]
                and canonical_json({k: q.get(k) for k in QUALIFIER_PATHS})
                == canonical_json(expected)
                == canonical_json({k: output.get(k) for k in QUALIFIER_PATHS})
            ):
                return deepcopy(replay)
    return None
