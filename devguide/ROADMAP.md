# Sabueso — Roadmap

## Phase 0 — Foundations
- Freeze conceptual schema (done in `schemas/card_schema.yaml`).
- Define minimal repository structure (core, resolver, tools, ops, mappings).
- Write developer guidance and decisions (this folder).

## Phase 1 — Core Connectors
- Implement connectors for:
  - UniProt
  - PDB (RCSB)
  - ChEMBL
  - PubChem
- Define connector outputs + raw evidence objects.

## Phase 2 — Aggregation & Evidence Store
- Implement aggregator to map source fields to canonical field paths.
- Implement `evidence_store` population.
- Implement uniform conflict detection.

## Phase 3 — Selection Rules
- Implement selection engine with configurable rules per field path.
- Keep selection rules separate from evidence store.

## Phase 4 — Small Molecule Enrichment
- Add eMolecules, ChemSpider, DrugBank.
- Expand physchem and bioactivity fields.
- Add clinical layer data.

## Phase 5 — Developer Experience
- CLI or SDK entry points.
- Sphinx documentation.
- pytest coverage with contract tests and snapshots.
