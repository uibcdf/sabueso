"""Source-calculated EPPIC interface and assembly interpretations."""

from __future__ import annotations

import math
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.quantities import quantity_node
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion


def pdb_id(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(
        r"[1-9][A-Za-z0-9]{3}", identifier
    ):
        raise ConnectorError("EPPIC requires one four-character public PDB ID.")
    return identifier.lower()


def _integer(value, minimum=0):
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and (not isinstance(value, float) or math.isfinite(value))
    )


def validate_component(payload, identifier, component):
    """Validate the supported native subset without inventing missing annotations."""
    identifier = pdb_id(identifier)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("EPPIC response is not finite JSON.") from error
    if component == "entry":
        if (
            not isinstance(payload, dict)
            or any(payload.get(k) != identifier for k in ("entryId", "pdbCode"))
            or not isinstance(payload.get("runParameters"), dict)
        ):
            raise ConnectorError(
                "EPPIC native entry identity/run context differs or is missing."
            )
        if not isinstance(payload.get("exhaustiveAssemblyEnumeration"), bool):
            raise ConnectorError("EPPIC assembly enumeration scope is missing.")
        return payload
    if component not in {"interfaces", "assemblies"} or not isinstance(payload, list):
        raise ConnectorError("EPPIC native annotation collection is malformed.")
    seen = set()
    for row in payload:
        if not isinstance(row, dict):
            raise ConnectorError("EPPIC annotation is not an object.")
        key = "interfaceId" if component == "interfaces" else "id"
        identity = row.get(key)
        if (
            not _integer(identity, 1 if component == "interfaces" else 0)
            or identity in seen
        ):
            raise ConnectorError("EPPIC annotation identity is invalid or repeated.")
        seen.add(identity)
        if component == "interfaces":
            if row.get("pdbCode") != identifier or not _integer(
                row.get("clusterId"), 1
            ):
                raise ConnectorError("EPPIC interface parent/cluster identity differs.")
            if any(
                not isinstance(row.get(k), str) or not row[k]
                for k in ("chain1", "chain2", "operator", "operatorType")
            ):
                raise ConnectorError("EPPIC chain/operator context is missing.")
            if not _number(row.get("area")) or row["area"] < 0:
                raise ConnectorError("EPPIC native interface area is invalid.")
            if any(not isinstance(row.get(k), bool) for k in ("infinite", "isologous")):
                raise ConnectorError("EPPIC interface topology flags are malformed.")
            scores = row.get("interfaceScores")
        else:
            if any(
                not isinstance(row.get(k), bool)
                for k in ("unitCellAssembly", "topologicallyValid")
            ):
                raise ConnectorError("EPPIC assembly topology flags are malformed.")
            contents = row.get("assemblyContents")
            if "assemblyContents" not in row or (
                contents is None
                and not row["unitCellAssembly"]
                or contents is not None
                and (
                    not isinstance(contents, list)
                    or any(not isinstance(c, dict) for c in contents)
                )
            ):
                raise ConnectorError("EPPIC assembly composition is malformed.")
            clusters = row.get("interfaceClusters")
            if not isinstance(clusters, list) or any(
                not isinstance(c, dict)
                or c.get("pdbCode") != identifier
                or not _integer(c.get("clusterId"), 1)
                for c in clusters
            ):
                raise ConnectorError("EPPIC assembly cluster parent identity differs.")
            scores = row.get("assemblyScores")
        if not isinstance(scores, list):
            raise ConnectorError("EPPIC method scores must be explicitly listed.")
        methods = set()
        for score in scores:
            if (
                not isinstance(score, dict)
                or not isinstance(score.get("method"), str)
                or not score["method"]
                or score["method"] in methods
            ):
                raise ConnectorError("EPPIC score method is missing or repeated.")
            methods.add(score["method"])
            if component == "interfaces" and (
                not _integer(score.get("interfaceId"), 1)
                or score["interfaceId"] != identity
            ):
                raise ConnectorError("EPPIC score belongs to another interface.")
            for k in ("score", "confidence"):
                if not _number(score.get(k)):
                    raise ConnectorError("EPPIC method score/confidence is malformed.")
            if (
                not isinstance(score.get("callName"), str)
                or not score["callName"]
                or score.get("callReason") is not None
                and not isinstance(score["callReason"], str)
            ):
                raise ConnectorError("EPPIC native method interpretation is malformed.")
    return payload


def _validated(envelope):
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "EPPIC"
        or envelope.get("kind") != "annotations"
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError("EPPIC mapping requires its annotation bundle envelope.")
    identifier = pdb_id(envelope["query"].get("pdb_id"))
    record, metadata = envelope.get("record"), envelope.get("component_metadata")
    if (
        envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(record, dict)
        or set(record) != {"entry", "interfaces", "assemblies"}
        or not isinstance(metadata, dict)
        or set(metadata) != set(record)
    ):
        raise ConnectorError("EPPIC bundle components/revision/scope are unsupported.")
    for component in record:
        validate_component(record[component], identifier, component)
        if (
            not isinstance(metadata[component], dict)
            or metadata[component].get("version") is not None
            or metadata[component].get("response_hash")
            != digest(canonical_json(record[component]))
        ):
            raise ConnectorError("EPPIC component revision metadata is unsupported.")
    available = {r["clusterId"] for r in record["interfaces"]}
    if any(
        c["clusterId"] not in available
        for a in record["assemblies"]
        for c in a["interfaceClusters"]
    ):
        raise ConnectorError(
            "EPPIC assembly refers to an unreceived interface cluster."
        )
    return identifier, record, metadata


def _map(envelope, component):
    identifier, record, metadata = _validated(envelope)
    assertions = []
    for row in record[component]:
        if component == "interfaces":
            identity = row["interfaceId"]
            value = {
                k: deepcopy(row[k])
                for k in (
                    "interfaceId",
                    "clusterId",
                    "chain1",
                    "chain2",
                    "operator",
                    "operatorType",
                    "infinite",
                    "isologous",
                    "interfaceScores",
                )
            }
            value["area"] = quantity_node(row["area"], "angstrom ** 2")
        else:
            identity = row["id"]
            value = {
                k: deepcopy(row[k])
                for k in (
                    "id",
                    "unitCellAssembly",
                    "topologicallyValid",
                    "assemblyScores",
                    "assemblyContents",
                )
            }
            value["interface_cluster_ids"] = [
                c["clusterId"] for c in row["interfaceClusters"]
            ]
        value["pdb_id"] = identifier.upper()
        assertion = make_source_assertion(
            "structures." + component + ".eppic",
            value,
            "EPPIC",
            f"{identifier}:{component}:{identity}",
            metadata[component].get("retrieved_at"),
            subject_ref="pdb:" + identifier.upper(),
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_annotation": deepcopy(row),
            "native_entry": deepcopy(record["entry"]),
            "native_component_hash": digest(canonical_json(record[component])),
            "component_metadata": deepcopy(metadata),
            "scope": "source_calculated_interpretations; no_experimental_confirmation_or_automatic_selection",
            "numbering": "native_EPPIC_ids_and_chain_operators; not_wwPDB_assembly_ids_or_UniProt_positions",
            "score_semantics": "native_method_specific_scores_and_sentinels; no_probability_conversion",
        }
        assertions.append(assertion)
    return assertions


def map_interfaces(envelope):
    """Read native method calls with explicitly dimensioned interface areas."""
    return _map(envelope, "interfaces")


def map_assemblies(envelope):
    """Read EPPIC assembly interpretations, including unit-cell and alternative calls."""
    return _map(envelope, "assemblies")


def interface_id(value):
    if not _integer(value, 1):
        raise ConnectorError(
            "EPPIC requires one explicitly selected positive interface ID."
        )
    return value


def validate_residues(payload):
    """Validate the native residue table without projecting its serial numbering.

    Both sides can contain the same serial. Native -1/zero serials, unknown region
    codes, null residue labels, entropy sentinels and quoted NaN fractions survive.
    These are per-side calculated records, including rows with zero buried area;
    the collection is not a declaration that every row belongs to a contact patch.
    """
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("EPPIC residue response is not finite JSON.") from error
    if not isinstance(payload, list):
        raise ConnectorError("EPPIC native residue table must be an explicit array.")
    required = {
        "side",
        "asa",
        "bsa",
        "burialFraction",
        "region",
        "residueNumber",
        "residueType",
        "entropyScore",
    }
    for row in payload:
        if not isinstance(row, dict) or not required <= set(row):
            raise ConnectorError("EPPIC native residue fields are missing.")
        if not isinstance(row["side"], bool) or any(
            not isinstance(row[k], int) or isinstance(row[k], bool)
            for k in ("residueNumber", "region")
        ):
            raise ConnectorError("EPPIC residue side/serial/region is malformed.")
        if row["residueType"] is not None and (
            not isinstance(row["residueType"], str) or not row["residueType"]
        ):
            raise ConnectorError("EPPIC native residue type is malformed.")
        if any(not _number(row[k]) or row[k] < 0 for k in ("asa", "bsa")):
            raise ConnectorError("EPPIC native residue surface areas are malformed.")
        fraction = row["burialFraction"]
        if fraction != "NaN" and (not _number(fraction) or not 0 <= fraction <= 1):
            raise ConnectorError("EPPIC native burial fraction is malformed.")
        if not _number(row["entropyScore"]):
            raise ConnectorError("EPPIC native residue entropy is malformed.")
    return payload


def _validated_residues(envelope):
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "EPPIC"
        or envelope.get("kind") != "interface_residues"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError(
            "EPPIC residue mapping requires its bound native envelope."
        )
    identifier = pdb_id(envelope["query"].get("pdb_id"))
    selected = interface_id(envelope["query"].get("interface_id"))
    record, metadata = envelope.get("record"), envelope.get("component_metadata")
    if (
        not isinstance(record, dict)
        or set(record) != {"interfaces", "residues"}
        or not isinstance(metadata, dict)
        or set(metadata) != set(record)
    ):
        raise ConnectorError("EPPIC residue context/components are incomplete.")
    validate_component(record["interfaces"], identifier, "interfaces")
    validate_residues(record["residues"])
    context = next(
        (r for r in record["interfaces"] if r["interfaceId"] == selected), None
    )
    if context is None:
        raise ConnectorError(
            "EPPIC requested interface is not in the received native context."
        )
    for name in record:
        if (
            not isinstance(metadata[name], dict)
            or metadata[name].get("version") is not None
            or metadata[name].get("response_hash")
            != digest(canonical_json(record[name]))
        ):
            raise ConnectorError("EPPIC residue component revision/hash differs.")
    return identifier, context, record, metadata


def map_interface_residues(envelope):
    """Read every native side/serial occurrence with dimensioned ASA/BSA.

    side=false refers to native chain1, side=true to chain2. Equal chain names and
    residue serials remain distinct sides of the selected interface/operator.
    No source sequence, author/insertion, label or canonical numbering is inferred.
    A NaN fraction is not zero; region/entropy remain the provider's native values.
    """
    identifier, context, record, metadata = _validated_residues(envelope)
    assertions = []
    for index, row in enumerate(record["residues"]):
        row_hash = digest(canonical_json(row))
        value = {
            "pdb_id": identifier.upper(),
            "interface_id": context["interfaceId"],
            "side": row["side"],
            "native_chain": context["chain2" if row["side"] else "chain1"],
            "native_residue_number": row["residueNumber"],
            "residue_type": row["residueType"],
            "accessible_surface_area": quantity_node(row["asa"], "angstrom ** 2"),
            "buried_surface_area": quantity_node(row["bsa"], "angstrom ** 2"),
            "burial_fraction": row["burialFraction"],
            "region": row["region"],
            "entropy_score": row["entropyScore"],
        }
        assertion = make_source_assertion(
            "structures.interface_residues.eppic",
            value,
            "EPPIC",
            f"{identifier}:interfaceResidues:{context['interfaceId']}:row:{index}:{row_hash}",
            metadata["residues"].get("retrieved_at"),
            subject_ref="pdb:" + identifier.upper(),
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_residue": deepcopy(row),
            "native_row_index": index,
            "native_residue_hash": row_hash,
            "native_interface": deepcopy(context),
            "component_metadata": deepcopy(metadata),
            "scope": "one_selected_interface; all_returned_side_rows_including_zero_BSA; no_client_cap",
            "numbering": "native_EPPIC_residue_serial; SEQRES_and_no_SEQRES_basis_not_identified_in_response; no_UniProt_author_or_label_projection",
            "classification": "native_region_and_entropy_only; no_contact_membership_or_experimental_class_inferred",
            "revision": "record_sequence_and_calculation_revisions_not_stated; separate_context_and_residue_times_are_not_atomic",
        }
        assertions.append(assertion)
    return assertions
