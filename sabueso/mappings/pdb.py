"""PDB (RCSB) → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from .base import get_in
from sabueso.core.source_assertion_store import make_source_assertion


def map_structure(pdb_entry: Dict[str, Any], pdb_id: str, retrieved_at: str) -> Dict[str, Any]:
    """
    Map minimal PDB entry fields into canonical card fields.

    Expected (if present):
      - entry.struct.title
      - entry.rcsb_entry_info.experimental_method
      - entry.rcsb_entry_info.resolution_combined
    """
    fields: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

    title = get_in(pdb_entry, ['entry', 'struct', 'title'])
    if not title:
        title = get_in(pdb_entry, ['struct', 'title'])
    if title:
        fp = 'structure.entry_metadata.title'
        fields[fp] = title
        assertion = make_source_assertion(fp, title, 'RCSB PDB', pdb_id, retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    method = get_in(pdb_entry, ['entry', 'rcsb_entry_info', 'experimental_method'])
    if not method:
        method = get_in(pdb_entry, ['entry', 'exptl', 0, 'method'])
    if not method:
        method = get_in(pdb_entry, ['exptl', 0, 'method'])
    if method:
        fp = 'structure.entry_metadata.experimental_method'
        fields[fp] = method
        assertion = make_source_assertion(fp, method, 'RCSB PDB', pdb_id, retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    res = get_in(pdb_entry, ['entry', 'rcsb_entry_info', 'resolution_combined'])
    if res is None:
        res = get_in(pdb_entry, ['entry', 'refine', 0, 'ls_dres_high'])
    if res is None:
        res = get_in(pdb_entry, ['refine', 0, 'ls_dres_high'])
    if res:
        fp = 'structure.entry_metadata.resolution'
        fields[fp] = res
        assertion = make_source_assertion(fp, res, 'RCSB PDB', pdb_id, retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    # dates
    deposit = get_in(pdb_entry, ['rcsb_accession_info', 'deposit_date'])
    if deposit:
        fp = 'structure.entry_metadata.deposition_date'
        fields[fp] = deposit
        assertion = make_source_assertion(fp, deposit, 'RCSB PDB', pdb_id, retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    release = get_in(pdb_entry, ['rcsb_accession_info', 'initial_release_date'])
    if release:
        fp = 'structure.entry_metadata.release_date'
        fields[fp] = release
        assertion = make_source_assertion(fp, release, 'RCSB PDB', pdb_id, retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    # primary citation
    citation = get_in(pdb_entry, ['rcsb_primary_citation'])
    if citation:
        doi = citation.get('pdbx_database_id_doi')
        if doi:
            fp = 'structure.entry_metadata.primary_citation.doi'
            fields[fp] = doi
            assertion = make_source_assertion(fp, doi, 'RCSB PDB', pdb_id, retrieved_at)
            source_assertions.append(assertion)
            field_source_assertions[fp] = [assertion['id']]

        pmid = citation.get('pdbx_database_id_pub_med')
        if pmid:
            fp = 'structure.entry_metadata.primary_citation.pmid'
            fields[fp] = pmid
            assertion = make_source_assertion(fp, pmid, 'RCSB PDB', pdb_id, retrieved_at)
            source_assertions.append(assertion)
            field_source_assertions[fp] = [assertion['id']]

        title = citation.get('title')
        if title:
            fp = 'structure.entry_metadata.primary_citation.title'
            fields[fp] = title
            assertion = make_source_assertion(fp, title, 'RCSB PDB', pdb_id, retrieved_at)
            source_assertions.append(assertion)
            field_source_assertions[fp] = [assertion['id']]

    return {'fields': fields, 'source_assertions': source_assertions, 'field_source_assertions': field_source_assertions}
