"""Independent native ChannelsDB annotations on an explicitly queried PDB entry."""

from __future__ import annotations

import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

URL = "https://channelsdb2.biodata.ceitec.cz/api/annotations/pdb/"
CHANNELS_URL = "https://channelsdb2.biodata.ceitec.cz/api/channels/pdb/"
GROUPS = ("ChannelsDB", "UniProt")
CHANNEL_GROUPS = tuple(
    f"{scope}_{method}"
    for scope in (
        "CSATunnels",
        "ReviewedChannels",
        "CofactorTunnels",
        "TransmembranePores",
        "ProcognateTunnels",
        "AlphaFillTunnels",
    )
    for method in ("MOLE", "Caver")
)


def pdb_id(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(
        r"[1-9][A-Za-z0-9]{3}", identifier
    ):
        raise ConnectorError("ChannelsDB requires one explicit four-character PDB ID.")
    return identifier.lower()


def validate_annotations(payload):
    """Validate the whole native DTO without assigning residue axes or support."""
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("ChannelsDB annotations are not finite JSON.") from error
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("EntryAnnotations"), list)
        or not isinstance(payload.get("ResidueAnnotations"), dict)
    ):
        raise ConnectorError("ChannelsDB requires its native annotations object.")
    for row in payload["EntryAnnotations"]:
        if not isinstance(row, dict) or any(
            not isinstance(row.get(k), str) for k in ("UniProtId", "Function", "Name")
        ):
            raise ConnectorError("ChannelsDB entry annotation literals are malformed.")
        if not row["UniProtId"] or not isinstance(row.get("Catalytics"), list):
            raise ConnectorError("ChannelsDB entry pointer/reactions are malformed.")
        if any(not isinstance(v, str) for v in row["Catalytics"]):
            raise ConnectorError("ChannelsDB native reaction literal is malformed.")
    residues = payload["ResidueAnnotations"]
    if set(residues) != set(GROUPS):
        raise ConnectorError("ChannelsDB residue annotation groups are unsupported.")
    for group in GROUPS:
        if not isinstance(residues[group], list):
            raise ConnectorError("ChannelsDB residue annotation array is malformed.")
        for row in residues[group]:
            if not isinstance(row, dict) or any(
                not isinstance(row.get(k), str)
                for k in ("Id", "Chain", "Reference", "ReferenceType", "Text")
            ):
                raise ConnectorError(
                    "ChannelsDB residue annotation literals are malformed."
                )
            if not row["Id"] or not row["Chain"]:
                raise ConnectorError(
                    "ChannelsDB native residue/chain pointer is empty."
                )
    return payload


def annotation_count(payload):
    return len(payload["EntryAnnotations"]) + sum(
        len(payload["ResidueAnnotations"][g]) for g in GROUPS
    )


def validate_channels(payload):
    """Qualify native membership/annotation tables, leaving geometry uninterpreted.

    OpenAPI documents the twelve required category arrays but does not describe
    their item schema. This bounded item contract follows the original DTO. Opaque
    residue tokens and FlowIndices are not decoded, zipped or repaired; native
    MOLE/CAVER representations differ. All known tables are checked before output.
    """
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("ChannelsDB channel data are not finite JSON.") from error
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("Annotations"), list)
        or not isinstance(payload.get("Channels"), dict)
        or set(payload["Channels"]) != set(CHANNEL_GROUPS)
    ):
        raise ConnectorError("ChannelsDB requires all twelve native channel groups.")
    for row in payload["Annotations"]:
        if (
            not isinstance(row, dict)
            or any(
                not isinstance(row.get(k), str)
                for k in ("Id", "Name", "Description", "Reference", "ReferenceType")
            )
            or not row["Id"]
        ):
            raise ConnectorError(
                "ChannelsDB channel annotation literals are malformed."
            )
    for rows in payload["Channels"].values():
        if not isinstance(rows, list):
            raise ConnectorError("ChannelsDB channel category is not an array.")
        for row in rows:
            if (
                not isinstance(row, dict)
                or not isinstance(row.get("Type"), str)
                or not isinstance(row.get("Id"), (str, int))
                or isinstance(row["Id"], bool)
                or row["Id"] == ""
                or not isinstance(row.get("Cavity"), (str, int))
                or isinstance(row["Cavity"], bool)
                or not isinstance(row.get("Auto"), (str, bool))
                or not isinstance(row.get("Layers"), dict)
            ):
                raise ConnectorError("ChannelsDB native channel header is malformed.")
            layers = row["Layers"]
            for name in ("ResidueFlow", "HetResidues"):
                if not _tokens(layers.get(name)):
                    raise ConnectorError(
                        "ChannelsDB channel membership tokens are missing/malformed."
                    )
            if not isinstance(layers.get("LayersInfo"), list):
                raise ConnectorError("ChannelsDB native layers are missing.")
            for layer in layers["LayersInfo"]:
                if (
                    not isinstance(layer, dict)
                    or not _tokens(layer.get("Residues"))
                    or not _tokens(layer.get("FlowIndices"))
                ):
                    raise ConnectorError(
                        "ChannelsDB native layer membership is malformed."
                    )
    return payload


def _tokens(values):
    return isinstance(values, list) and all(
        isinstance(v, str) and bool(v) for v in values
    )


def channel_counts(payload):
    return {
        "Annotations": len(payload["Annotations"]),
        **{g: len(rows) for g, rows in payload["Channels"].items()},
    }


def _channels_envelope(envelope):
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "ChannelsDB"
        or envelope.get("kind") != "pdb_channels"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"pdb_id"}
    ):
        raise ConnectorError(
            "ChannelsDB requires a complete native PDB channels envelope."
        )
    identifier = pdb_id(envelope["query"]["pdb_id"])
    if identifier != envelope["query"]["pdb_id"]:
        raise ConnectorError("ChannelsDB channel envelope requires an exact PDB query.")
    return identifier, validate_channels(envelope.get("record"))


def _channel_assertion(
    envelope, identifier, payload, response_hash, group, index, field, value
):
    assertion = make_source_assertion(
        field,
        value,
        "ChannelsDB",
        f"{identifier}:{response_hash}:{group}:{index}",
        envelope.get("retrieved_at"),
        subject_ref=f"channelsdb:channel_occurrence:{identifier}:{group}:{index}",
    )
    assertion["source"]["version"] = None
    assertion["source_metadata"] = {
        "query": deepcopy(envelope["query"]),
        "native_group": group,
        "native_row_index": index,
        "received_counts": channel_counts(payload),
        "response_hash": response_hash,
        "response_hash_basis": "canonical_decoded_native_JSON",
        "parser": "channelsdb_tunnel_membership_json@1",
        "identity_basis": "source_native_parent_and_occurrence; URL_or_caller_PDB_context_not_echoed",
        "mapping_scope": {
            "membership": "original_opaque_tokens_and_independent_arrays; no_token_decoding_index_resolution_or_set_repair",
            "heterogens": "native_HetResidues_label_only; no_chemical_or_amino_acid_classification",
            "identity": "no_Id_based_annotation_join_or_cross_category_channel_cavity_chain_protein_merge",
            "axis": "residue_numbering_chain_model_assembly_sequence_and_revisions_unqualified; no_canonical_placement",
            "interpretation": "native_categories_Type_and_Auto_literals; no_experimental_method_or_MOLI_Evidence_class",
            "geometry": "full_original_DTO_retained; Profile_geometry_and_physicochemical_properties_uninterpreted_and_unmapped",
            "coverage": "all_received_membership_and_annotation_tables; no_native_total_or_database_completeness_claim",
            "access": "existing_PDB_channel_DTO_only; separate_assembly_annotations_coordinates_AlphaFill_and_jobs_unqueried",
        },
    }
    if "snapshot_receipt" in envelope:
        assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
            envelope["snapshot_receipt"]
        )
    if "download_sha256" in envelope:
        assertion["source_metadata"]["download_sha256"] = envelope["download_sha256"]
    return assertion


def map_channel_memberships(envelope):
    """Record native channel membership, preserving every layer/token occurrence.

    Source declarations are channel-local context, not structure-to-sequence
    placement or a detected cavity. ResidueFlow, HetResidues, layer Residues and
    FlowIndices remain independent literal arrays even when they differ.
    Geometry and physical properties stay only in the unchanged original DTO.
    """
    identifier, payload = _channels_envelope(envelope)
    response_hash = digest(canonical_json(payload))
    assertions = []
    for group, rows in payload["Channels"].items():
        for index, row in enumerate(rows):
            layers = row["Layers"]
            value = {
                "native_header": {
                    k: deepcopy(row[k]) for k in ("Id", "Type", "Cavity", "Auto")
                },
                "native_residue_flow": deepcopy(layers["ResidueFlow"]),
                "native_het_residues": deepcopy(layers["HetResidues"]),
                "native_layers": [
                    {
                        "native_layer_index": i,
                        "native_residues": deepcopy(layer["Residues"]),
                        "native_flow_indices": deepcopy(layer["FlowIndices"]),
                    }
                    for i, layer in enumerate(layers["LayersInfo"])
                ],
            }
            assertions.append(
                _channel_assertion(
                    envelope,
                    identifier,
                    payload,
                    response_hash,
                    group,
                    index,
                    "structure.channelsdb_tunnel_membership",
                    value,
                )
            )
    return assertions


def map_channel_annotations(envelope):
    """Retain native channel comments/references without joining equal channel IDs."""
    identifier, payload = _channels_envelope(envelope)
    response_hash = digest(canonical_json(payload))
    return [
        _channel_assertion(
            envelope,
            identifier,
            payload,
            response_hash,
            "Annotations",
            index,
            "structure.channelsdb_channel_annotations",
            deepcopy(row),
        )
        for index, row in enumerate(payload["Annotations"])
    ]


def map_annotations(envelope):
    """Retain all native occurrences, preserving source groups and literal pointers.

    Residue IDs have no qualified author/label/sequence/model/assembly axis. They
    remain unplaced literals; equal numbers, chains or UniProt pointers do not
    merge identity or join tunnel rows. HTML entities in source text stay literal.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "ChannelsDB"
        or envelope.get("kind") != "pdb_annotations"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"pdb_id"}
    ):
        raise ConnectorError(
            "ChannelsDB mapping requires a native PDB annotations envelope."
        )
    identifier = pdb_id(envelope["query"]["pdb_id"])
    if identifier != envelope["query"]["pdb_id"]:
        raise ConnectorError("ChannelsDB envelope requires the canonical PDB query.")
    record = validate_annotations(envelope.get("record"))
    response_hash = digest(canonical_json(record))
    assertions = []
    groups = [("EntryAnnotations", record["EntryAnnotations"])] + [
        (g, record["ResidueAnnotations"][g]) for g in GROUPS
    ]
    for group, rows in groups:
        for index, row in enumerate(rows):
            field = (
                "structure.channelsdb_entry_annotations"
                if group == "EntryAnnotations"
                else "structure.channelsdb_residue_annotations"
            )
            assertion = make_source_assertion(
                field,
                deepcopy(row),
                "ChannelsDB",
                f"{identifier}:{response_hash}:{group}:{index}",
                envelope.get("retrieved_at"),
                subject_ref=f"pdb:{identifier}",
            )
            assertion["source"]["version"] = None
            assertion["source_metadata"] = {
                "native_group": group,
                "native_row_index": index,
                "response_hash": response_hash,
                "query": deepcopy(envelope["query"]),
                "received_counts": {g: len(r) for g, r in groups},
                "mapping_scope": {
                    "identity": "queried_PDB_context; UniProt_pointer_does_not_merge_entities",
                    "residues": "literal_Id_and_Chain; numbering_model_assembly_sequence_axis_unqualified; no_canonical_placement",
                    "support": "native_group_and_reference_literals; no_method_or_MOLI_Evidence_inferred",
                    "geometry": "separate_channels_and_assembly_routes_not_acquired_or_joined",
                    "revision": "record_input_sequence_and_annotation_revisions_not_stated; API_version_is_separate",
                    "coverage": "full_received_annotations_DTO_only; no_native_total_or_database_completeness_claim",
                    "terms": "data_grant_NOT_STATED; software_article_and_input_rights_remain_separate",
                },
            }
            if "snapshot_receipt" in envelope:
                assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                    envelope["snapshot_receipt"]
                )
            assertions.append(assertion)
    return assertions
