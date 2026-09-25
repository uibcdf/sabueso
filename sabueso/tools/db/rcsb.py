"""RCSB PDB structure access (entry, polymer entities, UniProt alignments, ligands).

The entry also brings what choosing a structure needs: the entities' mutations and
expression tags (``rcsb_polymer_entity_feature``), their canonical sequence and
expression host, the residues without coordinates per chain
(``rcsb_polymer_instance_feature``), R-free and R-work, and the deposit and release
dates. Instance features are fetched whole and filtered by the mapping, because
GraphQL cannot filter them by type.

Ligands come with the PDB "subject of investigation" flag and, per polymer chain, the
residues near each ligand instance (``rcsb_ligand_neighbors``, structure numbering).

``fetch_structure(pdb_id)`` returns ``(entry, retrieved_at)`` from one GraphQL request.
``OnlineRCSBClient`` queries data.rcsb.org; ``FixtureRCSBClient`` reads saved responses
from ``<directory>/rcsb/<PDB_ID>.json``. Both raise ``RecordNotFoundError`` when RCSB holds
no entry and ``ConnectorError`` when the source cannot answer.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.tools.db._record import online, source_record

RCSB_GRAPHQL = "https://data.rcsb.org/graphql"
STRUCTURE_QUERY = """query($id: String!) { entry(entry_id: $id) {
  rcsb_id
  exptl { method }
  rcsb_primary_citation {
    pdbx_database_id_PubMed pdbx_database_id_DOI title journal_abbrev year }
  rcsb_entry_info { resolution_combined polymer_entity_count_protein }
  rcsb_accession_info { deposit_date initial_release_date }
  refine { pdbx_refine_id ls_R_factor_R_free ls_R_factor_R_work }
  assemblies {
    rcsb_assembly_container_identifiers { assembly_id }
    pdbx_struct_assembly { oligomeric_details oligomeric_count details method_details }
    rcsb_struct_symmetry { kind type oligomeric_state stoichiometry }
  }
  polymer_entities {
    rcsb_id
    rcsb_polymer_entity { pdbx_description pdbx_mutation }
    entity_poly { rcsb_sample_sequence_length rcsb_mutation_count
      pdbx_seq_one_letter_code_can }
    rcsb_entity_host_organism { ncbi_scientific_name ncbi_taxonomy_id }
    rcsb_polymer_entity_feature { type name
      feature_positions { beg_seq_id end_seq_id } }
    rcsb_polymer_entity_container_identifiers { entity_id auth_asym_ids uniprot_ids }
    rcsb_polymer_entity_align { reference_database_name reference_database_accession
      aligned_regions { entity_beg_seq_id ref_beg_seq_id length } }
    polymer_entity_instances {
      rcsb_polymer_entity_instance_container_identifiers { asym_id auth_asym_id }
      rcsb_polymer_instance_feature { type feature_positions { beg_seq_id end_seq_id } }
      rcsb_ligand_neighbors {
        ligand_asym_id ligand_comp_id ligand_is_bound seq_id comp_id distance }
    }
  }
  nonpolymer_entities {
    rcsb_nonpolymer_entity_container_identifiers { nonpolymer_comp_id }
    rcsb_nonpolymer_entity { pdbx_description }
    nonpolymer_entity_instances {
      rcsb_nonpolymer_instance_validation_score {
        is_subject_of_investigation is_subject_of_investigation_provenance }
    }
  }
} }"""


class OnlineRCSBClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def fetch_structure(self, pdb_id: str) -> Tuple[Dict[str, Any], str]:
        body = json.dumps(
            {"query": STRUCTURE_QUERY, "variables": {"id": pdb_id.upper()}}
        ).encode("utf-8")
        request = Request(
            RCSB_GRAPHQL, data=body, headers={"Content-Type": "application/json"}
        )
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            with urlopen(request, timeout=self.timeout) as resp:  # nosec - trusted endpoint
                data = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            raise ConnectorError(f"RCSB request for {pdb_id} failed: {exc}") from exc
        if data.get("errors"):
            raise ConnectorError(f"RCSB request for {pdb_id} failed: {data['errors']}")
        entry = (data.get("data") or {}).get("entry")
        if entry is None:
            raise RecordNotFoundError(f"RCSB has no entry {pdb_id}")
        return entry, retrieved_at


class FixtureRCSBClient:
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def fetch_structure(self, pdb_id: str) -> Tuple[Dict[str, Any], str]:
        pdb_id = pdb_id.upper()
        if pdb_id in self.failing:
            raise ConnectorError(f"RCSB request for {pdb_id} failed (simulated)")
        path = self.directory / "rcsb" / f"{pdb_id}.json"
        if not path.is_file():
            raise RecordNotFoundError(f"RCSB has no entry {pdb_id}")
        return json.loads(path.read_text(encoding="utf-8")), self.retrieved_at


# --- Public source access (uibcdf/sabueso#49) -----------------------------------------


@arg_digest()
def get_entry(identifier: str, client: Any = None, skip_digestion: bool = False):
    """The RCSB PDB entry Sabueso maps (GraphQL: entities, UniProt alignments,
    assemblies, ligands and primary citation), in a provenance envelope. Not the
    coordinates: loading structures belongs to MolSysMT."""
    entry, retrieved_at = online(client, OnlineRCSBClient).fetch_structure(identifier)
    return source_record(
        "RCSB PDB", "entry", {"pdb_id": identifier.upper()}, retrieved_at, None, entry
    )
