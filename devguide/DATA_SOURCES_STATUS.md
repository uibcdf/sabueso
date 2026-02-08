# Data Sources Status (Implemented)

This document is a living checkpoint of the data sources (DBs) currently integrated in Sabueso. It summarizes the quality of each source integration, known issues, and operational notes (online/offline behavior).

## Legend
- **Status**: implemented / partial / paused
- **Access**: online API / dump (remote) / local file
- **Quality**: green (stable), yellow (works with caveats), red (broken)
- **Notes**: incidents, timeouts, missing fields, or skipped tests

---

## Protein / Structure / Chemistry

### UniProt
- **Status**: implemented
- **Access**: online API, local JSON
- **Quality**: green
- **Coverage**: identifiers, canonical name, organism, comments (function, catalytic activity, pathway, subunit, subcellular location, tissue specificity, PTM, polymorphism), positional features (binding/active sites, modified residues, disulfide bonds, glycosylation)
- **Notes**: stable online tests

### PDB (RCSB)
- **Status**: implemented
- **Access**: online API, local JSON
- **Quality**: green
- **Coverage**: entry title, experimental method, resolution, deposition/release dates, primary citation metadata
- **Notes**: stable online tests

### PubChem
- **Status**: implemented
- **Access**: online API, local JSON
- **Quality**: green
- **Coverage**: formula, MW, SMILES, InChI/InChIKey, logP, TPSA, HBD/HBA, rotatable bonds
- **Notes**: stable online tests

### ChEMBL
- **Status**: implemented
- **Access**: online API, local JSON
- **Quality**: green
- **Coverage**: identifiers, preferred name, molecule type, physchem (logP, HBD/HBA, TPSA, rotatable bonds), InChI/InChIKey, SMILES
- **Notes**: stable online tests

---

## Annotation / Interaction Sources

### Gene Ontology (GO)
- **Status**: implemented
- **Access**: online API, local JSON
- **Quality**: green
- **Coverage**: GO term id + label into `annotations.go_terms`
- **Notes**: stable online tests

### InterPro
- **Status**: implemented
- **Access**: online API (with reduced fields), local JSON
- **Quality**: yellow
- **Coverage**: domain accessions and names into `annotations.domains`
- **Notes**: online endpoint can be slow; test skips on timeout. Fetch attempts `fields=metadata` and falls back to full response if needed.

### STRING
- **Status**: implemented
- **Access**: online API, local JSON
- **Quality**: green
- **Coverage**: interaction partners into `interactions.binding_partners`
- **Notes**: stable online tests

### BioGRID
- **Status**: implemented
- **Access**: online API (requires key), local JSON
- **Quality**: yellow
- **Coverage**: interaction partners into `interactions.binding_partners`
- **Notes**: online test skips without `BIOGRID_ACCESS_KEY`

---

## Domain Classification Sources (Dump-backed)

### CATH
- **Status**: implemented
- **Access**: online API (domain_summary), local JSON
- **Quality**: green
- **Coverage**: domains into `annotations.domains` (id + name)
- **Notes**: uses `domain_summary` endpoint (not `domain`); test uses a known good domain id (`1cukA01`)

### SCOPe
- **Status**: implemented
- **Access**: remote dump (default Zenodo) or local file
- **Quality**: yellow
- **Coverage**: domains into `annotations.domains` (sunid + name)
- **Notes**: online API not reliable; fetch uses dump. Supports `SCOPE_DUMP_URL` or `SCOPE_DUMP_PATH`.
- **Dump**: `https://zenodo.org/records/5829561/files/dir.des.scope.2.08-stable.txt?download=1`

### TED
- **Status**: implemented
- **Access**: remote dump (default Zenodo) or local file
- **Quality**: yellow
- **Coverage**: domains into `annotations.domains` (TED entry id)
- **Notes**: no stable public API; fetch uses dump. Supports `TED_DUMP_URL` or `TED_DUMP_PATH`.
- **Dump**: `https://zenodo.org/records/13908086/files/novel_folds_set.domain_summary.tsv.gz?download=1`

---

## PTM Source

### PhosphoSitePlus (PSP)
- **Status**: implemented (offline only)
- **Access**: local JSON
- **Quality**: yellow
- **Coverage**: PTM entries mapped to `features_positional.modified_residue`
- **Notes**: no public API; online test is skipped.

---

## Summary of Open Incidents
- **InterPro**: slow endpoint; online test may timeout (skips). Consider caching or a smaller endpoint.
- **SCOPe/TED**: rely on dumps (no stable API confirmed). Monitor for official API availability.
- **BioGRID**: online test requires API key.

## Operational Notes
- SCOPe/TED dumps can be large; set `SCOPE_DUMP_PATH` / `TED_DUMP_PATH` to avoid re-downloading.
