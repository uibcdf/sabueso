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
- **Quality**: green for the listed coverage. Offline tests on five fixtures, including HsTIM (P60174) and TcTIM (P52270), compare mapped counts against the raw records (uibcdf/sabueso#13).
- **Coverage**:
  - identifiers, canonical name, organism;
  - free-text comments: function, pathway, subunit, tissue specificity, PTM, polymorphism;
  - catalytic activity as `{reaction, ec_number, rhea_id, molecule?}`;
  - subcellular location as `{location, topology?, orientation?, molecule?}`;
  - sequence: primary, length, molecular weight in Da, CRC64/MD5 checksums;
  - positional features: binding and active sites, modified residues, disulfide bonds, glycosylation;
  - PDB cross-references as `has_structure` relationships (method, resolution, chains, UniProt-numbered ranges, coverage), shown through `Card.structures()`;
  - GO cross-references as `annotated_with` relationships (aspect, term, GO code, assigned by; ECO in `source_metadata`);
  - InterPro, Pfam, Gene3D (CATH), SUPFAM, PANTHER, PROSITE and CDD cross-references as `classified_in` relationships;
  - curated INTERACTION comments (IntAct binary interactions) as `interacts_with` relationships;
  - UniProt evidence qualifiers kept per SourceAssertion as `source_metadata.eco`.
- **Known limits**:
  - other comment types (interaction, alternative products, similarity, …) and feature types are not mapped;
  - isoform restrictions (`molecule`) are recorded for catalytic activity and subcellular location, but not for free-text comments;
  - identical repeated values in one record share one SourceAssertion id.
  - INTERACTION comments are UniProt's curated subset of binary interactions: 3 for human TIM, while its IntAct cross-reference reports 75. Full interaction data would need IntAct, STRING or BioGRID directly.
- **Notes**: stable online tests

### RCSB PDB — polymer-entity mapping (GraphQL)
- **Status**: implemented (uibcdf/sabueso#6, step 4b)
- **Access**: online GraphQL (`OnlineRCSBClient`), saved entries (`FixtureRCSBClient`, `temp_data/rcsb/`)
- **Quality**: green for the listed coverage, verified on 1HTI, 1KLG and 1TCD
- **Coverage**:
  - `has_structure` relationships per UniProt accession aligned to polymer entities: chains, UniProt-numbered ranges, method, resolution;
  - polymer entities, the other entities present, and bound ligands;
  - structure facts keep `pdb:<id>` as SourceAssertion subject;
  - `EntityResolver` resolves `pdb:<id>` to the structure record and its proteins.
- **Notes**: one request per entry. Ligand lists include every non-polymer entity (buffers and solvents too); no curation yet.

### PDB (RCSB) — entry metadata cards (removed)
- **Status**: removed 2026-09-23 (uibcdf/sabueso#21)
- **Notes**:
  - `create_structure_card_*` and `mappings/pdb.py::map_structure` built one card per PDB entry, typed as a protein, with scalar `structure.entry_metadata.*` fields. That was a structure card in all but name, contrary to the decision "no StructureCard" (#6, #20).
  - Structures are now `has_structure` relationships (see *RCSB PDB — polymer-entity mapping* above and the UniProt coverage).
  - Entry title, dates and primary citation are not mapped at the moment. They can return as structure-subject SourceAssertions shown in `Card.structures()` when a real need appears.
  - `tools/db/pdb.py::fetch_pdb_json` (raw REST entry) remains.

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
