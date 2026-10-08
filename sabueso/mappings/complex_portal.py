"""Native Complex Portal context and participant occurrences, without binary expansion."""

from __future__ import annotations

import re
from copy import deepcopy
from datetime import date

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

COMPLEX = re.compile(r"CPX-[1-9][0-9]*\Z")
ACCESSION = re.compile(r"EBI-[1-9][0-9]*\Z")
MI = re.compile(r"MI:[0-9]{4}\Z")
TEXT_ARRAYS = (
    "synonyms",
    "functions",
    "properties",
    "ligands",
    "complexAssemblies",
    "diseases",
    "agonists",
    "antagonists",
    "comments",
    "releaseDates",
)


def complex_id(identifier):
    if not isinstance(identifier, str) or not COMPLEX.fullmatch(identifier.upper()):
        raise ConnectorError(
            "Complex Portal requires an explicit unversioned CPX accession."
        )
    return identifier.upper()


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _optional_text(value):
    return value is None or isinstance(value, str)


def _xref(rows):
    if not isinstance(rows, list):
        raise ConnectorError("Complex Portal native cross-references are missing.")
    for row in rows:
        if (
            not isinstance(row, dict)
            or not _text(row.get("database"))
            or not _text(row.get("identifier"))
            or not _optional_text(row.get("qualifier"))
            or any(
                row.get(k) is not None
                and (not isinstance(row[k], str) or not MI.fullmatch(row[k]))
                for k in ("dbMI", "qualifierMI")
            )
        ):
            raise ConnectorError("Complex Portal native cross-reference is malformed.")


def _features(rows):
    if not isinstance(rows, list):
        raise ConnectorError("Complex Portal native feature array is missing.")
    for row in rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("featureAc"), str)
            or not ACCESSION.fullmatch(row["featureAc"])
            or not _optional_text(row.get("participantId"))
            or not isinstance(row.get("ranges"), list)
            or any(not _text(v) for v in row["ranges"])
            or not isinstance(row.get("linkedFeatures"), list)
            or any(
                not isinstance(v, str) or not ACCESSION.fullmatch(v)
                for v in row["linkedFeatures"]
            )
            or any(
                row.get(k) is not None
                and (not isinstance(row[k], str) or not MI.fullmatch(row[k]))
                for k in ("featureTypeMI", "featureRoleMI")
            )
        ):
            raise ConnectorError(
                "Complex Portal native feature identity/range/reference is malformed."
            )
        _xref(row.get("crossReferences"))
        # Some native references name features absent from this response. Do not
        # repair the graph, infer endpoints, or turn unknown ranges into coordinates.


def validate_complex(payload, identifier):
    """Validate the complete qualified JSON response before selecting any participant.

    Participant references, stoichiometry literals, ECO/MI terms, feature ranges
    and release dates stay native. Species describes the complex, not necessarily
    every component. Neither a prediction flag nor ECO code creates MOLI Evidence.
    """
    identifier = complex_id(identifier)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("Complex Portal response is not finite JSON.") from error
    if (
        not isinstance(payload, dict)
        or payload.get("complexAc") != identifier
        or not isinstance(payload.get("ac"), str)
        or not ACCESSION.fullmatch(payload["ac"])
        or not _text(payload.get("name"))
        or not _text(payload.get("species"))
    ):
        raise ConnectorError(
            "Complex Portal native primary identity/context differs from the query."
        )
    for key in TEXT_ARRAYS:
        if not isinstance(payload.get(key), list) or any(
            not isinstance(v, str) for v in payload[key]
        ):
            raise ConnectorError(
                "Complex Portal native annotation array is missing or malformed."
            )
    for value in payload["releaseDates"]:
        try:
            if date.fromisoformat(value).isoformat() != value:
                raise ValueError("Noncanonical date")
        except (ValueError, TypeError) as error:
            raise ConnectorError(
                "Complex Portal native release date is malformed."
            ) from error
    if (
        "predictedComplex" not in payload
        or payload["predictedComplex"] is not None
        and not isinstance(payload["predictedComplex"], bool)
    ):
        raise ConnectorError(
            "Complex Portal native prediction flag is missing or malformed."
        )
    if "evidenceType" not in payload:
        raise ConnectorError("Complex Portal native ECO context is missing.")
    evidence = payload["evidenceType"]
    if evidence is not None:
        if (
            not isinstance(evidence, dict)
            or not isinstance(evidence.get("identifier"), str)
            or not re.fullmatch(r"ECO:[0-9]{7}", evidence["identifier"])
            or not _optional_text(evidence.get("description"))
        ):
            raise ConnectorError("Complex Portal native ECO context is malformed.")
        score = evidence.get("confidenceScore")
        if score is not None and (
            not isinstance(score, int) or isinstance(score, bool) or not 1 <= score <= 5
        ):
            raise ConnectorError(
                "Complex Portal native confidence stars are malformed."
            )
    _xref(payload.get("crossReferences"))
    primary = [
        r
        for r in payload["crossReferences"]
        if r.get("dbMI") == "MI:2279" and r.get("qualifierMI") == "MI:2282"
    ]
    if not primary or any(r["identifier"] != identifier for r in primary):
        raise ConnectorError(
            "Complex Portal native primary cross-reference differs or is unstated."
        )
    participants = payload.get("participants")
    if not isinstance(participants, list) or not participants:
        raise ConnectorError(
            "Complex Portal native participant array is missing or empty."
        )
    for row in participants:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("interactorAC"), str)
            or not ACCESSION.fullmatch(row["interactorAC"])
            or not _text(row.get("identifier"))
            or "stochiometry" not in row
            or not _optional_text(row["stochiometry"])
            or any(
                not _optional_text(row.get(k))
                for k in (
                    "name",
                    "description",
                    "identifierLink",
                    "bioRole",
                    "interactorType",
                )
            )
            or any(
                row.get(k) is not None
                and (not isinstance(row[k], str) or not MI.fullmatch(row[k]))
                for k in ("bioRoleMI", "interactorTypeMI")
            )
        ):
            raise ConnectorError(
                "Complex Portal native participant identity/type/stoichiometry is malformed."
            )
        _features(row.get("linkedFeatures"))
        _features(row.get("otherFeatures"))
    return payload


def _validated(envelope):
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "Complex Portal"
        or envelope.get("kind") != "complex"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"complex_id"}
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError(
            "Complex Portal mapping requires a complete native complex envelope."
        )
    identifier = complex_id(envelope["query"]["complex_id"])
    payload = validate_complex(envelope.get("record"), identifier)
    return identifier, payload, digest(canonical_json(payload))


def _assertion(envelope, identifier, payload, response_hash, field, value, locator):
    assertion = make_source_assertion(
        field,
        value,
        "Complex Portal",
        f"{identifier}:{locator}:{response_hash}",
        envelope.get("retrieved_at"),
        subject_ref=f"complexportal:{identifier}",
    )
    assertion["source"]["version"] = None
    assertion["source_metadata"] = {
        "native_complex_context": deepcopy(
            {k: v for k, v in payload.items() if k != "participants"}
        ),
        "response_hash": response_hash,
        "mapping_scope": {
            "identity": "native_complex_and_participant_references; no_entity_merge_or_alias_following",
            "interpretation": "native_prediction_flag_ECO_and_stars; no_experimental_class_or_probability_inference",
            "membership": "native_participant_occurrences; no_binary_expansion_or_stoichiometric_count_inference",
            "features": "native_ranges_and_links; no_sequence_numbering_projection_or_graph_closure_claim",
            "revisions": "complex_and_participant_sequence_revisions_not_stated; release_dates_separate",
            "coverage": "one_selected_complex; received_occurrences_not_database_or_topology_completeness",
        },
    }
    if "snapshot_receipt" in envelope:
        assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
            envelope["snapshot_receipt"]
        )
    return assertion


def map_complex(envelope):
    """Keep one full complex declaration, including its complete native participant array."""
    identifier, payload, response_hash = _validated(envelope)
    return [
        _assertion(
            envelope,
            identifier,
            payload,
            response_hash,
            "interactions.complex_context.complex_portal",
            deepcopy(payload),
            "context",
        )
    ]


def map_participants(envelope):
    """Keep independent native member occurrences; equal references never collapse."""
    identifier, payload, response_hash = _validated(envelope)
    out = []
    for index, participant in enumerate(payload["participants"]):
        assertion = _assertion(
            envelope,
            identifier,
            payload,
            response_hash,
            "interactions.complex_memberships.complex_portal",
            {"complex_id": identifier, "native_participant": deepcopy(participant)},
            f"participant:{index}:{participant['interactorAC']}",
        )
        assertion["source_metadata"]["native_participant_index"] = index
        out.append(assertion)
    return out
