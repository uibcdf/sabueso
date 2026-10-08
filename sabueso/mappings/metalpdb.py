"""Native MetalPDB site context and unit-qualified donor distances."""

from __future__ import annotations

import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.quantities import quantity_node
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

URL = "https://metalpdb.cerm.unifi.it/api?query=site:"
SITE_FIELDS = (
    "site",
    "pdb",
    "site_type",
    "organism",
    "molecule",
    "uniprot",
    "ec_number",
    "pfam",
    "cath",
    "scop",
    "is_representative",
)
METAL_FIELDS = (
    "symbol",
    "name",
    "atom_pdb_number",
    "residue_pdb_number",
    "pattern",
    "geometry",
    "coordination",
)
UNIT_BASIS = {
    "unit": "angstrom",
    "provider_field": "Donor Atom Distance",
    "provider_header": "Distance (Å)",
    "statement": "https://metalpdb.cerm.unifi.it/pdbSearchResult?id=12ca_2",
    "reviewed": "2026-10-07",
    "qualification_page_sha256": "9149d5e72a6b774f605a72fa951c33ac6d777d90b7b9a2fceb5460f36c2e1879",
    "qualification_table_sha256": "e389920434736f4ae6e813d94c71d12d4dd90692529890a0c641435d9b4fc283",
    "qualification": "native_coordination_sphere_header; three_API_donor_distances_match_display_rounding",
}


def site_id(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(
        r"[1-9][A-Za-z0-9]{3}_[1-9][0-9]*", identifier
    ):
        raise ConnectorError(
            "MetalPDB requires an explicit native site ID, such as 12ca_2."
        )
    return identifier[:4].lower() + identifier[4:]


def response_query(identifier):
    return {"site_id": site_id(identifier)}


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_sites(payload, identifier):
    """Validate every received native site before returning any assertion.

    Atom serials and residue integers retain native PDB labels, without inferring
    chain/model/assembly, insertion codes or a sequence correspondence. Coordination
    is a provider count; it is not recomputed from the received ligand list. Source
    distances use the independently qualified Coordination Sphere unit declaration.
    """
    identifier = site_id(identifier)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("MetalPDB site response is not finite JSON.") from error
    if not isinstance(payload, list):
        raise ConnectorError("MetalPDB requires the native site array.")
    for row in payload:
        if (
            not isinstance(row, dict)
            or row.get("site") != identifier
            or row.get("pdb") != identifier[:4]
            or not _text(row.get("site_type"))
            or not isinstance(row.get("is_representative"), bool)
        ):
            raise ConnectorError("MetalPDB native site/PDB identity or flags differ.")
        for key in (
            "organism",
            "molecule",
            "uniprot",
            "ec_number",
            "pfam",
            "cath",
            "scop",
        ):
            if key not in row or (row[key] is not None and not _text(row[key])):
                raise ConnectorError(
                    "MetalPDB native classification/reference string is malformed."
                )
        metals = row.get("metals")
        if not isinstance(metals, list) or not metals:
            raise ConnectorError("MetalPDB native metal array is missing or empty.")
        for metal in metals:
            if not isinstance(metal, dict):
                raise ConnectorError("MetalPDB native metal is malformed.")
            for key in ("symbol", "name"):
                if not _text(metal.get(key)):
                    raise ConnectorError("MetalPDB native metal label is malformed.")
            for key in ("geometry", "pattern"):
                if key not in metal or (
                    metal[key] is not None and not _text(metal[key])
                ):
                    raise ConnectorError(
                        "MetalPDB native geometry/pattern label is malformed."
                    )
            if (
                not _integer(metal.get("atom_pdb_number"))
                or metal["atom_pdb_number"] < 1
                or not _integer(metal.get("residue_pdb_number"))
                or not _integer(metal.get("coordination"))
                or metal["coordination"] < 0
            ):
                raise ConnectorError(
                    "MetalPDB native metal numbering/count is malformed."
                )
            ligands = metal.get("ligands")
            if not isinstance(ligands, list):
                raise ConnectorError("MetalPDB native ligand array is missing.")
            for ligand in ligands:
                if (
                    not isinstance(ligand, dict)
                    or not _text(ligand.get("chain"))
                    or not _text(ligand.get("residue"))
                    or not _integer(ligand.get("residue_pdb_number"))
                    or not isinstance(ligand.get("donors"), list)
                    or not ligand["donors"]
                ):
                    raise ConnectorError(
                        "MetalPDB native ligand/chain/donor context is malformed."
                    )
                for donor in ligand["donors"]:
                    if isinstance(donor, dict) and any(
                        k in donor
                        for k in ("unit", "units", "distance_unit", "distance_units")
                    ):
                        raise ConnectorError(
                            "MetalPDB unit-labelled donor shape needs separate qualification."
                        )
                    if (
                        not isinstance(donor, dict)
                        or not _text(donor.get("symbol"))
                        or not _text(donor.get("atom"))
                        or not _integer(donor.get("atom_pdb_number"))
                        or donor["atom_pdb_number"] < 1
                        or isinstance(donor.get("distance"), bool)
                        or not isinstance(donor.get("distance"), (int, float))
                        or donor["distance"] < 0
                    ):
                        raise ConnectorError(
                            "MetalPDB native donor numbering/distance is malformed."
                        )
    return payload


def map_sites(envelope):
    """Keep each site occurrence and its metal/ligand/donor parent context intact."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "MetalPDB"
        or envelope.get("kind") != "site"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"site_id"}
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError(
            "MetalPDB mapping requires a complete native site envelope."
        )
    identifier = site_id(envelope["query"]["site_id"])
    if envelope["query"] != response_query(identifier):
        raise ConnectorError(
            "MetalPDB mapping query must use the canonical native site ID."
        )
    rows = validate_sites(envelope.get("record"), identifier)
    response_hash = digest(canonical_json(rows))
    assertions = []
    for index, row in enumerate(rows):
        value = {k: deepcopy(row[k]) for k in SITE_FIELDS}
        value["metals"] = []
        for native_metal in row["metals"]:
            metal = {k: deepcopy(native_metal[k]) for k in METAL_FIELDS}
            metal["ligands"] = []
            for native_ligand in native_metal["ligands"]:
                ligand = {
                    k: deepcopy(native_ligand[k])
                    for k in ("chain", "residue", "residue_pdb_number")
                }
                ligand["donors"] = []
                for native_donor in native_ligand["donors"]:
                    donor = {
                        k: deepcopy(native_donor[k])
                        for k in ("symbol", "atom", "atom_pdb_number")
                    }
                    donor["distance"] = quantity_node(
                        native_donor["distance"], "angstrom"
                    )
                    ligand["donors"].append(donor)
                metal["ligands"].append(ligand)
            value["metals"].append(metal)
        assertion = make_source_assertion(
            "sites.metal_sites",
            value,
            "MetalPDB",
            f"{identifier}:{response_hash}:occurrence:{index + 1}",
            envelope.get("retrieved_at"),
            subject_ref=f"metalpdb:site:{identifier}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_site": deepcopy(row),
            "native_occurrence": index + 1,
            "response_hash": response_hash,
            "distance_unit_basis": deepcopy(UNIT_BASIS),
            "mapping_scope": {
                "identity": "native_metal_site_and_PDB_context; UniProt_is_a_pointer; no_protein_merge",
                "coordinates": "original_PDB_atom_and_residue_literals; metal_chain_model_assembly_insertions_and_sequence_revisions_unstated; no_projection",
                "geometry": "provider_geometry_pattern_and_coordination_only; no_essentiality_function_experimental_method_or_MOLI_Evidence",
                "coverage": "explicit_site_query_received_array; other_sites_and_native_database_total_unqueried",
                "access": "one_API_GET; no_assets_coordinates_sequence_classification_links_or_jobs_acquired",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
