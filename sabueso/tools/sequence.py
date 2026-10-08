"""Explicit exact-sequence candidates, without resolving or merging protein identity."""

from __future__ import annotations

import hashlib
from copy import deepcopy

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import (
    ArgumentError,
    ConnectorError,
    NotArchivedError,
    OfflineError,
    RecordNotFoundError,
)
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_acquisition import capture_acquisitions
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.uniparc import AMINO_ACIDS, REFERENCE, map_sequence_records
from sabueso.tools.db import uniparc, uniprot

RULE = "exact_sequence_candidates@1"


def _normalize(text):
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    header = None
    if lines[0].startswith(">"):
        header = lines.pop(0)[1:].strip()
        if not header:
            raise ValueError("FASTA header is empty.")
    if any(line.startswith(">") for line in lines):
        raise ValueError("Supply exactly one FASTA record.")
    value = "".join("".join(lines).split())
    if not value.isascii():
        raise ValueError("Protein sequence letters must be ASCII.")
    value = value.upper()
    terminal_stop = value.endswith("*")
    if terminal_stop:
        value = value[:-1]
    if not value or set(value) - AMINO_ACIDS:
        raise ValueError(
            "Sequence is empty, gapped or outside the supported amino-acid alphabet."
        )
    return value, {
        "rule": "single_protein_sequence_normalization@1",
        "fasta_header": header,
        "removed_terminal_stop": terminal_stop,
        "raw_input_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }


def _entry(entry, accession):
    if not isinstance(entry, dict) or entry.get("primaryAccession") != accession:
        raise ConnectorError(
            "UniProt response accession does not match the queried reference."
        )
    if entry.get("entryType") == "Inactive":
        return None
    sequence = entry.get("sequence")
    if not isinstance(sequence, dict) or not isinstance(sequence.get("value"), str):
        raise ConnectorError("Current UniProt sequence is not stated.")
    value, length = sequence["value"], sequence.get("length")
    if (
        not value
        or set(value) - AMINO_ACIDS
        or isinstance(length, bool)
        or not isinstance(length, int)
        or length != len(value)
    ):
        raise ConnectorError("Current UniProt sequence/length is malformed.")
    actual_md5 = hashlib.md5(value.encode("ascii")).hexdigest().upper()  # nosec - native sequence identifier
    if sequence.get("md5") is not None and str(sequence["md5"]).upper() != actual_md5:
        raise ConnectorError("UniProt sequence checksum disagrees with its content.")
    return value


@arg_digest()
@capture_acquisitions
def find_protein_candidates(
    sequence_input,
    *,
    taxon_id=None,
    limit=100,
    uniparc_client=None,
    uniprot_client=None,
    skip_digestion=False,
):
    """Find current canonical UniProt candidates for one exact raw/FASTA sequence.

    The checksum is a search key; full archive and current entry sequences are
    compared. Returned native references, caps, failures and isoform/historical
    scope remain explicit. This function makes no card, identity link or choice.
    ``taxon_id`` is an exact NCBI taxonomy id, without descendant/name inference.
    """
    try:
        sequence, normalization = _normalize(sequence_input)
    except ValueError as error:
        raise ArgumentError(
            argument="sequence_input",
            value=sequence_input,
            caller=__name__ + ".find_protein_candidates",
            reason=str(error),
        ) from error
    checksum = hashlib.md5(sequence.encode("ascii")).hexdigest().upper()  # nosec - UniParc query, never a security seal
    out = {
        "rule": RULE,
        "status": "complete",
        "selection": "not_performed",
        "input": {
            "sequence": sequence,
            "md5": checksum,
            "sha256": hashlib.sha256(sequence.encode()).hexdigest(),
            "normalization": normalization,
        },
        "scope": {
            "taxon_id": taxon_id,
            "entry_limit": limit,
            "ordering": "native_returned_reference_order",
            "identity": "not_resolved",
            "references": "returned_UniParc_search_UniProtKB_reference_list",
            "entry_scope": "current_canonical_UniProtKB; isoform_sequences_not_queried",
        },
        "candidates": [],
        "candidate_status": "none_in_checked_scope",
        "verifications": [],
        "excluded": [],
        "source_assertions": [],
        "search": None,
    }
    try:
        search = uniparc.get_records(checksum, limit=limit, client=uniparc_client)
    except (ConnectorError, NotArchivedError, OfflineError) as error:
        partial = getattr(error, "received_subset", None)
        out["status"] = "partial" if partial and partial["results"] else "failed"
        out["search_error"] = {"type": type(error).__name__, "message": str(error)}
        if not partial or not partial["results"]:
            return out
        search = {
            "source": "UniParc",
            "kind": "checksum_search",
            "query": {"checksum": checksum, "limit": limit},
            "retrieved_at": partial["retrieved_at"],
            "version": partial["version"],
            "record": {
                "total": partial["total"],
                "results": partial["results"],
                "pages": partial["pages"],
            },
            "truncated": True,
        }
    out["search"] = deepcopy(search)
    if search["truncated"]:
        out["status"] = "partial"
    associations = map_sequence_records(search)
    out["source_assertions"].extend(associations)
    grouped = {}
    for assertion in associations:
        native = assertion["asserted_value"]
        if native["sequence"]["value"] != sequence:
            out["excluded"].append(
                {
                    "uniparc_ref": assertion["subject_ref"],
                    "reason": "full_archive_sequence_differs; checksum_is_only_a_search_key",
                }
            )
            continue
        for ref in native["uniprotkb_accessions"]:
            match = REFERENCE.fullmatch(ref)
            basis = {
                "native_reference": ref,
                "uniparc_ref": assertion["subject_ref"],
                "source_assertion_id": assertion["id"],
                "assertion_snapshot_id": digest(canonical_json(assertion)),
                "declared_sequence_revision": match["revision"][1:]
                if match["revision"]
                else None,
            }
            if match["isoform"]:
                out["excluded"].append(
                    {**basis, "reason": "isoform_sequence_not_queried"}
                )
                continue
            grouped.setdefault(match["accession"], []).append(basis)
    out["scope"]["canonical_references_stated"] = len(grouped)
    out["scope"]["canonical_reference_checks_attempted"] = min(limit, len(grouped))
    for index, (accession, basis) in enumerate(grouped.items()):
        verification = {"accession": accession, "basis": deepcopy(basis)}
        if index >= limit:
            verification.update(outcome="not_queried", reason="entry_limit")
            out["status"] = "partial"
            out["verifications"].append(verification)
            continue
        try:
            envelope = uniprot.get_entry(accession, client=uniprot_client)
            verification["record"] = deepcopy(envelope)
            current_sequence = _entry(envelope["record"], accession)
            if current_sequence is None:
                verification.update(outcome="excluded", reason="inactive_UniProt_entry")
            elif current_sequence != sequence:
                verification.update(
                    outcome="excluded", reason="current_UniProt_sequence_differs"
                )
            else:
                organism = envelope["record"].get("organism")
                observed_taxon = (
                    organism.get("taxonId") if isinstance(organism, dict) else None
                )
                if (
                    isinstance(observed_taxon, bool)
                    or not isinstance(observed_taxon, int)
                    or observed_taxon < 1
                ):
                    raise ConnectorError(
                        "Current UniProt taxon id is missing or malformed."
                    )
                if taxon_id is not None and taxon_id != observed_taxon:
                    verification.update(
                        outcome="excluded", reason="exact_taxon_differs"
                    )
                else:
                    support = make_source_assertion(
                        "sequence.primary",
                        current_sequence,
                        "UniProt",
                        accession,
                        envelope.get("retrieved_at"),
                        subject_ref=f"uniprot:{accession}",
                    )
                    support["source"]["version"] = envelope.get("version")
                    support["source_metadata"] = {
                        "entryAudit": deepcopy(envelope["record"].get("entryAudit")),
                        "sequence": deepcopy(envelope["record"]["sequence"]),
                        "organism": deepcopy(organism),
                    }
                    out["source_assertions"].append(support)
                    out["candidates"].append(
                        {
                            "entity_ref": f"sabueso:protein:uniprot:{accession}",
                            "accession": accession,
                            "taxon_id": observed_taxon,
                            "organism": deepcopy(organism),
                            "basis": deepcopy(basis),
                            "current_sequence_assertion_id": support["id"],
                            "current_sequence_assertion_snapshot_id": digest(
                                canonical_json(support)
                            ),
                            "match": "exact_archive_and_current_canonical_sequence; not_entity_equivalence",
                        }
                    )
                    verification["outcome"] = "exact_match"
        except (
            RecordNotFoundError,
            ConnectorError,
            NotArchivedError,
            OfflineError,
        ) as error:
            unavailable = getattr(error, "acquisition_trace", {})
            records = unavailable.get("records", [])
            outcome = (
                records[-1].get("outcome")
                if records
                else "failed_validation"
                if "record" in verification
                else "unobserved_failure"
            )
            verification.update(
                outcome=outcome,
                error={"type": type(error).__name__, "message": str(error)},
            )
            if outcome != "not_found":
                out["status"] = "partial"
        out["verifications"].append(verification)
    out["candidate_status"] = (
        "multiple"
        if len(out["candidates"]) > 1
        else "one"
        if out["candidates"]
        else "none_in_checked_scope"
    )
    return out
