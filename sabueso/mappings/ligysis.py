"""Source-calculated LIGYSIS site summaries from literal public result-page data."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from html.parser import HTMLParser

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.quantities import quantity_node
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.tools.source_snapshot import _json

ACCESSION = re.compile(
    r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})\Z"
)
VARIABLES = (
    "proteinId",
    "segmentId",
    "chartData",
    "seg_ress_dict",
    "segmentReps",
    "segStats",
)
SCORES = ("RSA", "DS", "MES", "FS")


def accession(identifier):
    if not isinstance(identifier, str) or not ACCESSION.fullmatch(identifier.upper()):
        raise ConnectorError("LIGYSIS requires a base UniProt accession.")
    return identifier.upper()


def segment_id(segment):
    if not isinstance(segment, int) or isinstance(segment, bool) or segment < 1:
        raise ConnectorError(
            "LIGYSIS requires an explicitly selected positive segment."
        )
    return segment


def structure_id(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(
        r"[1-9][A-Za-z0-9]{3}", identifier
    ):
        raise ConnectorError(
            "LIGYSIS requires an explicitly selected four-character PDB ID."
        )
    return identifier.lower()


def validate_structure_mapping(payload, pdb_id):
    """Validate all four native tables before selection, retaining independent parents.

    Only directed residue dictionaries echo the structure. Protein/segment query
    context is bound by the caller/transport, not echoed or independently confirmed.
    Chain-to-accession declarations never fill missing parents or repair directions.
    """
    pdb_id = structure_id(pdb_id)
    if not isinstance(payload, dict) or not {
        "pdb2up",
        "up2pdb",
        "chain2acc",
        "chains",
    } <= set(payload):
        raise ConnectorError("LIGYSIS structure mapping tables are missing.")
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("LIGYSIS structure mapping is not finite JSON.") from error
    for direction in ("pdb2up", "up2pdb"):
        structures = payload[direction]
        if (
            not isinstance(structures, dict)
            or set(structures) != {pdb_id}
            or not isinstance(structures[pdb_id], dict)
        ):
            raise ConnectorError("LIGYSIS mapping structure differs from the query.")
        for chain, pairs in structures[pdb_id].items():
            if (
                not isinstance(chain, str)
                or not chain
                or not isinstance(pairs, dict)
                or any(
                    not isinstance(key, str)
                    or not re.fullmatch(r"-?[0-9]+", key)
                    or not isinstance(value, int)
                    or isinstance(value, bool)
                    for key, value in pairs.items()
                )
            ):
                raise ConnectorError(
                    "LIGYSIS mapping chain/residue labels are malformed."
                )
    for table in ("chain2acc", "chains"):
        values = payload[table]
        if not isinstance(values, dict) or any(
            not isinstance(key, str)
            or not key
            or not isinstance(value, str)
            or not value
            for key, value in values.items()
        ):
            raise ConnectorError("LIGYSIS chain declaration is malformed.")
    for reference in payload["chain2acc"].values():
        base, separator, isoform = reference.partition("-")
        if (
            not ACCESSION.fullmatch(base)
            or separator
            and not re.fullmatch(r"[1-9][0-9]*", isoform)
        ):
            raise ConnectorError("LIGYSIS native chain accession is unsupported.")
    return payload


def map_structure_mapping(envelope):
    """Retain directed residues, declared chain accessions and remapping separately.

    Source-native chain declarations supply an explicit identity basis, without
    merging chains or joining this response to a different unversioned result page.
    Residue numbering/insertion, chain2acc namespace and scientific revisions stay
    unknown. No inverse reconstruction or current canonical placement occurs.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "LIGYSIS"
        or envelope.get("kind") != "structure_mapping"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"accession", "segment", "pdb_id"}
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError(
            "LIGYSIS requires a complete native structure-mapping envelope."
        )
    query = envelope["query"]
    identifier, segment, pdb_id = (
        accession(query["accession"]),
        segment_id(query["segment"]),
        structure_id(query["pdb_id"]),
    )
    if query != {"accession": identifier, "segment": segment, "pdb_id": pdb_id}:
        raise ConnectorError("LIGYSIS structure-mapping query is not exact.")
    payload = validate_structure_mapping(envelope.get("record"), pdb_id)
    response_hash = digest(canonical_json(payload))
    rows = []
    for direction in ("pdb2up", "up2pdb"):
        for chain, pairs in payload[direction][pdb_id].items():
            rows.append(
                (
                    direction,
                    chain,
                    {
                        "native_direction": direction,
                        "native_structure_key": pdb_id,
                        "native_chain_key": chain,
                        "native_pairs": deepcopy(pairs),
                    },
                )
            )
    for chain, reference in payload["chain2acc"].items():
        rows.append(
            (
                "chain2acc",
                chain,
                {"native_chain_key": chain, "native_accession": reference},
            )
        )
    for chain, original in payload["chains"].items():
        rows.append(
            (
                "chains",
                chain,
                {"native_chain_key": chain, "native_original_chain_key": original},
            )
        )
    assertions = []
    for index, (table, chain, value) in enumerate(rows):
        assertion = make_source_assertion(
            "annotations.ligysis_structure_mapping",
            value,
            "LIGYSIS",
            f"{identifier}:{segment}:{pdb_id}:{response_hash}:table:{table}:row:{index}",
            envelope.get("retrieved_at"),
            subject_ref=f"ligysis:structure_mapping:{identifier}:{segment}:{pdb_id}:{table}:{index}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "query": deepcopy(query),
            "native_table": table,
            "native_row_index": index,
            "response_sha256": response_hash,
            "response_hash_basis": "canonical_decoded_native_json",
            "parser": "ligysis_structure_mapping_json@1",
            "native_table_order": list(payload),
            "identity_basis": "native_chain2acc_declaration"
            if table == "chain2acc"
            else "native_table_declaration",
            "query_binding": {
                "structure": "native_directed_dictionary_parent",
                "protein_segment": "caller_transport_context_only; not_echoed_or_validated_by_response",
            },
            "identity_context": {
                "chain_namespace": None,
                "structure_numbering_scheme": None,
                "insertion_codes": "not_stated",
                "source_sequence_revision": None,
                "structure_revision": None,
                "mapping_revision": None,
            },
            "mapping_scope": {
                "coverage": "all_four_received_tables_for_one_explicit_structure",
                "identity": "separate_native_declarations; no_cross_table_or_old_page_join_or_chain_merge",
                "interpretation": "no_inverse_reconstruction_conflict_repair_or_current_canonical_placement",
                "support": "one_response; not_independent_confirmation",
                "access": "mapping_only; coordinates_other_structures_and_jobs_unqueried",
            },
        }
        if table in ("pdb2up", "up2pdb"):
            assertion["source_metadata"].update(
                native_pair_order=list(value["native_pairs"]),
                received_pair_count=len(value["native_pairs"]),
            )
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions


class _Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.blocks = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "script" and not dict(attrs).get("src"):
            self.current = []

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.current is not None:
            self.blocks.append("".join(self.current))
            self.current = None


def _literals(document, names):
    """Read unique whole-line JSON declarations, without evaluating JavaScript."""
    if not isinstance(document, str) or not document:
        raise ConnectorError("LIGYSIS result page is missing.")
    parser = _Scripts()
    try:
        parser.feed(document)
        parser.close()
        if parser.current is not None:
            raise ValueError("Unclosed inline script")
        scripts = "\n".join(parser.blocks)
        out = {}
        for name in names:
            matches = re.findall(
                r"(?m)^\s*(?:const|let)\s+"
                + re.escape(name)
                + r"\s*=\s*([^\r\n]+)\s*$",
                scripts,
            )
            if len(matches) != 1:
                raise ValueError(f"Missing/repeated native declaration: {name}")
            out[name] = _json(matches[0].strip().removesuffix(";"))
    except (ValueError, UnicodeError) as error:
        raise ConnectorError(
            f"LIGYSIS result literals are unreadable: {error}"
        ) from error
    return out


def parse_result(document, identifier, segment):
    """Read six JSON literals without evaluating JavaScript or loading page assets.

    This is a deliberately bounded result-page format. Duplicate declarations,
    expressions, changed layout and missing identity/counts fail closed. The full
    original page remains the source record; parsed literals are a representation.
    """
    identifier, segment = accession(identifier), segment_id(segment)
    out = _literals(document, VARIABLES)
    if out["proteinId"] != identifier or out["segmentId"] != str(segment):
        raise ConnectorError("LIGYSIS result identity differs from the query.")
    bounds = out["segmentReps"]
    stats = out["segStats"]
    if (
        not isinstance(bounds, dict)
        or not isinstance(bounds.get(str(segment)), dict)
        or not isinstance(stats, dict)
        or not isinstance(stats.get(identifier), dict)
        or not isinstance(stats[identifier].get(str(segment)), dict)
    ):
        raise ConnectorError("LIGYSIS segment bounds/counts are unstated.")
    bounds, stats = bounds[str(segment)], stats[identifier][str(segment)]
    begin, end = bounds.get("start"), bounds.get("end")
    if (
        any(not isinstance(n, int) or isinstance(n, bool) for n in (begin, end))
        or not 1 <= begin <= end
    ):
        raise ConnectorError("LIGYSIS source segment boundaries are malformed.")
    if any(
        not isinstance(stats.get(k), int) or isinstance(stats[k], bool) or stats[k] < 0
        for k in ("bss", "ligs", "strucs")
    ):
        raise ConnectorError("LIGYSIS segment counts are malformed.")
    table, residues = out["chartData"], out["seg_ress_dict"]
    if (
        not isinstance(table, dict)
        or not isinstance(residues, dict)
        or not all(k in table for k in ("ID", "Size", "Cluster", *SCORES))
    ):
        raise ConnectorError("LIGYSIS native site table/residue membership is missing.")
    size = stats["bss"]
    if any(
        not isinstance(values, list) or len(values) != size for values in table.values()
    ):
        raise ConnectorError("LIGYSIS site columns differ from the stated count.")
    ids = table["ID"]
    if (
        any(not isinstance(n, int) or isinstance(n, bool) or n < 0 for n in ids)
        or len(set(ids)) != size
    ):
        raise ConnectorError("LIGYSIS site identities are invalid or repeated.")
    if set(residues) != {str(n) for n in ids} | {"ALL_BINDING"}:
        raise ConnectorError("LIGYSIS site/residue parents differ.")
    for row_index, site_id in enumerate(ids):
        numbers = residues[str(site_id)]
        count, cluster = table["Size"][row_index], table["Cluster"][row_index]
        if (
            not isinstance(count, int)
            or isinstance(count, bool)
            or count < 0
            or not isinstance(cluster, int)
            or isinstance(cluster, bool)
            or not 1 <= cluster <= 4
        ):
            raise ConnectorError("LIGYSIS native site size/cluster is malformed.")
        if (
            not isinstance(numbers, list)
            or len(numbers) != count
            or any(
                not isinstance(n, int) or isinstance(n, bool) or not begin <= n <= end
                for n in numbers
            )
            or len(set(numbers)) != len(numbers)
        ):
            raise ConnectorError(
                "LIGYSIS residue membership differs from site size/bounds."
            )
        for key in SCORES:
            value = table[key][row_index]
            if value == "NaN":
                continue
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value < 0
                or key == "RSA"
                and value > 100
                or key == "FS"
                and value > 1
            ):
                raise ConnectorError("LIGYSIS native score is malformed.")
    all_binding = residues["ALL_BINDING"]
    if (
        not isinstance(all_binding, list)
        or any(not isinstance(n, int) or isinstance(n, bool) for n in all_binding)
        or len(set(all_binding)) != len(all_binding)
        or set(all_binding) != {n for site in ids for n in residues[str(site)]}
    ):
        raise ConnectorError("LIGYSIS combined membership differs from its sites.")
    return out


def parse_displayed_residues(document, identifier, segment):
    """Validate the initial residue table; its selected site is not stated here.

    The native ``cc`` column order and ``newChartData`` arrays describe only the
    initial displayed panel. Membership is checked against the received segment's
    declared binding residues without inferring a site by equal residue sets.
    Repeated positions and unknown declared columns retain their occurrences.
    """
    native = parse_result(document, identifier, segment)
    detail = _literals(document, ("cc", "newChartData"))
    columns, table = detail["cc"], detail["newChartData"]
    required = {"UPResNum", "MSACol", "DS", "MES", "p", "AA", "RSA", "SS"}
    if (
        not isinstance(columns, list)
        or any(not isinstance(key, str) or not key for key in columns)
        or len(set(columns)) != len(columns)
        or not required <= set(columns)
        or not isinstance(table, dict)
        or set(table) != set(columns)
        or any(not isinstance(values, list) for values in table.values())
    ):
        raise ConnectorError("LIGYSIS displayed residue columns are unsupported.")
    count = len(table["UPResNum"])
    if any(len(values) != count for values in table.values()):
        raise ConnectorError("LIGYSIS displayed residue column lengths differ.")
    rows = [{key: deepcopy(table[key][i]) for key in columns} for i in range(count)]
    binding = set(native["seg_ress_dict"]["ALL_BINDING"])
    for row in rows:
        position, alignment = row["UPResNum"], row["MSACol"]
        if (
            not isinstance(position, int)
            or isinstance(position, bool)
            or position not in binding
            or not isinstance(alignment, int)
            or isinstance(alignment, bool)
            or alignment < 0
            or not isinstance(row["AA"], str)
            or len(row["AA"]) != 1
            or not isinstance(row["SS"], str)
        ):
            raise ConnectorError(
                "LIGYSIS displayed residue numbering/labels are malformed."
            )
        for key in ("DS", "MES", "p", "RSA"):
            value = row[key]
            if value == "NaN":
                continue
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value < 0
                or key == "p"
                and value > 1
                or key == "RSA"
                and value > 100
            ):
                raise ConnectorError("LIGYSIS displayed residue score is malformed.")
    return {"columns": columns, "rows": rows}


def _page_query(envelope):
    """Require the explicit qualified result-page scope before detail mapping."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "LIGYSIS"
        or envelope.get("kind") != "result_page"
        or not isinstance(envelope.get("query"), dict)
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError("LIGYSIS detail requires a native result-page envelope.")
    identifier = accession(envelope["query"].get("accession"))
    segment = segment_id(envelope["query"].get("segment"))
    if envelope["query"] != {"accession": identifier, "segment": segment}:
        raise ConnectorError("LIGYSIS detail query scope is unsupported.")
    return identifier, segment


def parse_residue_correspondences(document, identifier, segment):
    """Validate native directed dictionaries without assigning a protein to chains.

    Native structure/chain labels and signed integer-shaped residue keys remain
    literal. Neither direction supplies chain-to-accession identity, insertion
    codes, numbering namespaces or scientific revisions. Missing opposite parents
    and contradictory/non-bijective directions remain separate declarations.
    """
    parse_result(document, identifier, segment)
    tables = _literals(document, ("Pdb2UpDict", "Up2PdbDict"))
    for structures in tables.values():
        if not isinstance(structures, dict):
            raise ConnectorError(
                "LIGYSIS residue correspondence dictionary is missing."
            )
        for structure, chains in structures.items():
            if not re.fullmatch(r"[1-9][A-Za-z0-9]{3}", structure) or not isinstance(
                chains, dict
            ):
                raise ConnectorError(
                    "LIGYSIS correspondence structure parent is malformed."
                )
            for chain, pairs in chains.items():
                if not chain or not isinstance(pairs, dict):
                    raise ConnectorError(
                        "LIGYSIS correspondence chain parent is malformed."
                    )
                if any(
                    not re.fullmatch(r"-?[0-9]+", key)
                    or not isinstance(value, int)
                    or isinstance(value, bool)
                    for key, value in pairs.items()
                ):
                    raise ConnectorError(
                        "LIGYSIS native correspondence labels are malformed."
                    )
    return tables


def map_residue_correspondences(envelope):
    """Record each received directed structure/chain dictionary independently.

    The page query is context, not chain-to-protein identity. Both directions
    belong to the same source response and do not constitute independent
    confirmation. No inversion, chain pairing, residue placement or repair occurs.
    """
    identifier, segment = _page_query(envelope)
    document = envelope.get("record")
    tables = parse_residue_correspondences(document, identifier, segment)
    response_hash = hashlib.sha256(document.encode("utf-8")).hexdigest()
    assertions = []
    for direction, structures in tables.items():
        for structure_index, (structure, chains) in enumerate(structures.items()):
            for chain_index, (chain, pairs) in enumerate(chains.items()):
                assertion = make_source_assertion(
                    "annotations.ligysis_residue_correspondences",
                    {
                        "native_direction": direction,
                        "native_structure_key": structure,
                        "native_chain_key": chain,
                        "native_pairs": deepcopy(pairs),
                    },
                    "LIGYSIS",
                    f"{identifier}:{segment}:{direction}:{response_hash}:structure:{structure_index}:chain:{chain_index}",
                    envelope.get("retrieved_at"),
                    subject_ref=f"ligysis:correspondence_table:{identifier}:{segment}:{direction}:{structure_index}:{chain_index}",
                )
                assertion["source"]["version"] = None
                assertion["source_metadata"] = {
                    "query": deepcopy(envelope["query"]),
                    "native_structure_index": structure_index,
                    "native_chain_index": chain_index,
                    "native_pair_order": list(pairs),
                    "received_pair_count": len(pairs),
                    "received_direction_structure_count": len(structures),
                    "response_sha256": response_hash,
                    "parser": "ligysis_residue_correspondence_literals@1",
                    "identity_context": {
                        "protein_accession": None,
                        "chain_to_accession_basis": "not_stated_by_received_correspondence_literals",
                        "chain_namespace": None,
                        "structure_numbering_scheme": None,
                        "insertion_codes": "not_stated",
                        "source_sequence_revision": None,
                        "structure_revision": None,
                        "mapping_revision": None,
                    },
                    "mapping_scope": {
                        "coverage": "all_received_directed_dictionaries; other_result_structures_unqueried",
                        "interpretation": "native_key_value_declarations_only; no_inverse_reconstruction_or_conflict_repair",
                        "identity": "page_query_context_only; no_chain_protein_merge_or_current_canonical_axis",
                        "support": "both_directions_from_same_page; not_independent_confirmation",
                        "access": "received_page_only; chain_accession_maps_coordinates_and_jobs_unqueried",
                    },
                }
                if "snapshot_receipt" in envelope:
                    assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                        envelope["snapshot_receipt"]
                    )
                assertions.append(assertion)
    return assertions


def map_displayed_residues(envelope):
    """Retain initial-panel residue declarations without canonical placement.

    Amino-acid/secondary-structure labels, alignment columns and scores belong to
    the provider's unversioned coordinate context. No site is identified by
    similarity, p-value classification assigned or complete-segment coverage claimed.
    """
    identifier, segment = _page_query(envelope)
    document = envelope.get("record")
    parsed = parse_displayed_residues(document, identifier, segment)
    response_hash = hashlib.sha256(document.encode("utf-8")).hexdigest()
    assertions = []
    for index, row in enumerate(parsed["rows"]):
        assertion = make_source_assertion(
            "annotations.ligysis_residue_records",
            {
                "native_fields": deepcopy(row),
                "relative_solvent_accessibility": None
                if row["RSA"] == "NaN"
                else quantity_node(row["RSA"], "percent"),
            },
            "LIGYSIS",
            f"{identifier}:{segment}:displayed_residues:{response_hash}:row:{index}",
            envelope.get("retrieved_at"),
            subject_ref=f"ligysis:displayed_residue_table:{identifier}:{segment}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "query": deepcopy(envelope["query"]),
            "native_column_order": deepcopy(parsed["columns"]),
            "native_row_index": index,
            "received_row_count": len(parsed["rows"]),
            "response_sha256": response_hash,
            "parser": "ligysis_displayed_residue_literals@1",
            "displayed_site_id": None,
            "mapping_scope": {
                "coverage": "initial_displayed_residue_table_only; other_site_tables_unqueried",
                "identity": "native_page_accession_segment; selected_site_not_stated_in_table_literals",
                "coordinates": "provider_UPResNum_and_MSACol_only; sequence_alignment_and_result_revisions_unknown",
                "interpretation": "native_AA_SS_and_score_literals; no_current_sequence_placement_or_significance_class",
                "access": "received_page_only; no_scripts_assets_coordinates_or_jobs_acquired",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions


def map_sites(envelope):
    """Keep provider scores/clusters and original residue numbers, without remapping."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "LIGYSIS"
        or envelope.get("kind") != "result_page"
        or not isinstance(envelope.get("query"), dict)
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError("LIGYSIS mapping requires a native result-page envelope.")
    identifier = accession(envelope["query"].get("accession"))
    segment = segment_id(envelope["query"].get("segment"))
    document = envelope.get("record")
    literals = parse_result(document, identifier, segment)
    table = literals["chartData"]
    assertions = []
    for row_index, site_id in enumerate(table["ID"]):
        row = {k: deepcopy(v[row_index]) for k, v in table.items()}
        value = {
            "site_id": site_id,
            "segment": segment,
            "site_size": row["Size"],
            "source_cluster": row["Cluster"],
            "source_scores": {k: row[k] for k in ("DS", "MES", "FS")},
            "relative_solvent_accessibility": None
            if row["RSA"] == "NaN"
            else quantity_node(row["RSA"], "percent"),
            "source_residue_numbers": deepcopy(literals["seg_ress_dict"][str(site_id)]),
            "numbering_context": {
                "provider_reference": "UniProt",
                "sequence_revision": None,
                "segment_bounds": deepcopy(literals["segmentReps"][str(segment)]),
            },
        }
        assertion = make_source_assertion(
            "sites.binding_sites.ligysis",
            value,
            "LIGYSIS",
            f"{identifier}:{segment}:{site_id}",
            envelope.get("retrieved_at"),
            subject_ref=f"uniprot:{identifier}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_site_row": row,
            "native_segment_stats": deepcopy(
                literals["segStats"][identifier][str(segment)]
            ),
            "response_sha256": hashlib.sha256(document.encode("utf-8")).hexdigest(),
            "parser": "ligysis_result_literals@1",
            "mapping_scope": {
                "interpretation": "provider_calculated_site_scores_and_cluster; no_function_or_binding_inference",
                "coordinates": "provider_numbering_only; source_sequence_and_revision_not_supplied",
                "coverage": "explicit_selected_segment; other_segments_and_individual_ligands_unqueried",
                "access": "result_page_only; no_scripts_executed_or_assets_coordinates_jobs_acquired",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
