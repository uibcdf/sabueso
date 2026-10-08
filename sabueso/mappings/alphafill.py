"""Precomputed AlphaFill model/transplant statements, without observed binding claims."""

from __future__ import annotations

import re
from copy import deepcopy
from datetime import date

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.quantities import quantity_node
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

ACCESSION = re.compile(
    r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})\Z"
)


def accession(identifier):
    if not isinstance(identifier, str) or not ACCESSION.fullmatch(identifier.upper()):
        raise ConnectorError("AlphaFill metadata requires a base UniProt accession.")
    return identifier.upper()


def _integer(value, minimum=0):
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _text(value):
    return isinstance(value, str) and bool(value)


def validate_metadata(payload, identifier):
    """Validate the native AFDB subset; do not repair the provider's schema typos.

    The served schema has misplaced transplant properties and differs from native
    names such as transplant_atom_count and binding_site_rmsd. Validate native
    supported fields directly, keeping unknown context and null values unchanged.
    """
    identifier = accession(identifier)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("AlphaFill metadata is not finite JSON.") from error
    if not isinstance(payload, dict) or not re.fullmatch(
        rf"AF-{re.escape(identifier)}-F[1-9][0-9]*", str(payload.get("id", ""))
    ):
        raise ConnectorError(
            "AlphaFill model ID does not match the requested accession."
        )
    if payload.get("source", "AFDB") != "AFDB" or not all(
        _text(payload.get(k)) for k in ("alphafill_version", "date", "file")
    ):
        raise ConnectorError("AlphaFill input/run context is missing or unsupported.")
    try:
        if date.fromisoformat(payload["date"]).isoformat() != payload["date"]:
            raise ValueError("Non-ISO date")
    except ValueError as error:
        raise ConnectorError("AlphaFill run date is malformed.") from error
    if (
        "hits" not in payload
        or payload["hits"] is not None
        and not isinstance(payload["hits"], list)
    ):
        raise ConnectorError("AlphaFill native hits must be an array or explicit null.")
    placed = set()
    for hit in payload["hits"] or []:
        if (
            not isinstance(hit, dict)
            or not re.fullmatch(r"[1-9][A-Za-z0-9]{3}", str(hit.get("pdb_id", "")))
            or not _text(hit.get("pdb_asym_id"))
            or not _number(hit.get("global_rmsd"))
            or hit["global_rmsd"] < 0
            or not isinstance(hit.get("transplants"), list)
        ):
            raise ConnectorError("AlphaFill template/hit context is malformed.")
        alignment = hit.get("alignment")
        if (
            not isinstance(alignment, dict)
            or not _integer(alignment.get("af_start"))
            or not _integer(alignment.get("pdb_start"))
            or not _integer(alignment.get("length"), 1)
            or not _number(alignment.get("identity"))
            or not 0 <= alignment["identity"] <= 1
        ):
            raise ConnectorError("AlphaFill native alignment scope is malformed.")
        for transplant in hit["transplants"]:
            if not isinstance(transplant, dict) or not all(
                _text(transplant.get(k))
                for k in ("asym_id", "compound_id", "analogue_id")
            ):
                raise ConnectorError("AlphaFill transplant identity is malformed.")
            if transplant["asym_id"] in placed:
                raise ConnectorError("AlphaFill placed asym identity is repeated.")
            placed.add(transplant["asym_id"])
            for key in (
                "pdb_asym_id",
                "pdb_auth_asym_id",
                "pdb_auth_seq_id",
                "pdb_auth_ins_code",
            ):
                if (
                    key not in transplant
                    or transplant[key] is not None
                    and not isinstance(transplant[key], str)
                ):
                    raise ConnectorError(
                        "AlphaFill native donor numbering is malformed."
                    )
            if (
                "local_rmsd" not in transplant
                or transplant["local_rmsd"] is not None
                and (
                    not _number(transplant["local_rmsd"])
                    or transplant["local_rmsd"] < 0
                )
            ):
                raise ConnectorError(
                    "AlphaFill local RMSD must be non-negative or null."
                )
            clash = transplant.get("clash")
            if (
                not isinstance(clash, dict)
                or not _number(clash.get("score"))
                or clash["score"] < 0
                or not _integer(clash.get("clash_count"))
                or not _integer(clash.get("poly_atom_count"))
                or not isinstance(clash.get("distances"), list)
                or any(not isinstance(d, dict) for d in clash["distances"])
            ):
                raise ConnectorError("AlphaFill clash context is malformed.")
            atom_keys = {"transplant_atom_count", "ligand_atom_count"} & clash.keys()
            if not atom_keys or any(not _integer(clash[k]) for k in atom_keys):
                raise ConnectorError(
                    "AlphaFill native transplant atom count is malformed."
                )
            if (
                "pae" in transplant
                and transplant["pae"] is not None
                and not isinstance(transplant["pae"], dict)
            ):
                raise ConnectorError("AlphaFill PAE context is malformed.")
            validation = transplant.get("validation")
            if validation is not None:
                if not isinstance(validation, dict):
                    raise ConnectorError("AlphaFill validation context is malformed.")
                for key, value in validation.items():
                    if key.endswith("_rmsd") and (not _number(value) or value < 0):
                        raise ConnectorError(
                            "AlphaFill native validation RMSD is malformed."
                        )
                    if key.endswith("_atom_count") and not _integer(value):
                        raise ConnectorError(
                            "AlphaFill validation atom count is malformed."
                        )
    return payload


def _validated(envelope):
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "AlphaFill"
        or envelope.get("kind") != "metadata"
        or not isinstance(envelope.get("query"), dict)
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError(
            "AlphaFill mapping requires a complete native metadata envelope."
        )
    identifier = accession(envelope["query"].get("accession"))
    return identifier, validate_metadata(envelope.get("record"), identifier)


def _context(envelope, payload):
    metadata = {
        "native_run": {k: deepcopy(v) for k, v in payload.items() if k != "hits"},
        "response_hash": digest(canonical_json(payload)),
        "mapping_scope": {
            "interpretation": "source_calculated_transplant; not_observed_target_binding",
            "coordinates": "native_model_and_donor_numbering; no_UniProt_residue_projection",
            "revision": "record_revision_unknown; run_version_and_date_are_separate",
            "access": "metadata_only; no_coordinates_or_linked_sources_acquired",
            "compound_semantics": "native_compound_and_analogue_labels; no_chemical_equivalence_inferred",
        },
    }
    if "snapshot_receipt" in envelope:
        metadata["snapshot_receipt"] = deepcopy(envelope["snapshot_receipt"])
    return metadata


def map_model(envelope):
    """Describe the declared filled model; choose no current AlphaFold model or URL."""
    identifier, payload = _validated(envelope)
    assertion = make_source_assertion(
        "structures.predicted_models.alphafill",
        {
            "model_id": payload["id"],
            "model_ref": f"alphafill:{payload['id']}",
            "input_file": payload["file"],
            "run_version": payload["alphafill_version"],
            "run_date": payload["date"],
            "native_hits_state": "null" if payload["hits"] is None else "array",
        },
        "AlphaFill",
        payload["id"],
        envelope.get("retrieved_at"),
        subject_ref=f"uniprot:{identifier}",
    )
    assertion["source"]["version"] = None
    assertion["source_metadata"] = _context(envelope, payload)
    return [assertion]


def map_transplants(envelope):
    """Keep native compound/analogue labels distinct and physical metrics in angstroms."""
    identifier, payload = _validated(envelope)
    assertions = []
    context = _context(envelope, payload)
    for hit_index, hit in enumerate(payload["hits"] or []):
        for transplant_index, transplant in enumerate(hit["transplants"]):
            value = {
                "model_ref": f"alphafill:{payload['id']}",
                "protein_ref": f"uniprot:{identifier}",
                "placed_asym_id": transplant["asym_id"],
                "compound_id": transplant["compound_id"],
                "analogue_id": transplant["analogue_id"],
                "template_pdb_id": hit["pdb_id"],
                "template_protein_asym_id": hit["pdb_asym_id"],
                "donor_numbering": {
                    k: deepcopy(transplant[k])
                    for k in (
                        "pdb_asym_id",
                        "pdb_auth_asym_id",
                        "pdb_auth_seq_id",
                        "pdb_auth_ins_code",
                    )
                },
                "alignment": deepcopy(hit["alignment"]),
                "global_rmsd": quantity_node(hit["global_rmsd"], "angstrom"),
                "local_rmsd": None
                if transplant["local_rmsd"] is None
                else quantity_node(transplant["local_rmsd"], "angstrom"),
                "transplant_clash_score": quantity_node(
                    transplant["clash"]["score"], "angstrom"
                ),
            }
            assertion = make_source_assertion(
                "structures.predicted_ligand_context.alphafill",
                value,
                "AlphaFill",
                f"{payload['id']}:{transplant['asym_id']}",
                envelope.get("retrieved_at"),
                subject_ref=f"alphafill:{payload['id']}",
            )
            assertion["source"]["version"] = None
            metadata = deepcopy(context)
            metadata.update(
                native_hit_index=hit_index,
                native_transplant_index=transplant_index,
                native_template={
                    k: deepcopy(v) for k, v in hit.items() if k != "transplants"
                },
                native_transplant=deepcopy(transplant),
            )
            assertion["source_metadata"] = metadata
            assertions.append(assertion)
    return assertions
