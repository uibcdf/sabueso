> **Archived (2026-09-26).** The original roadmap (phases 0–5) of 2026-01. It is not
> dropped: `devguide/ROADMAP.md` integrates it with the pilot-driven route and tracks the
> status of each of its items.

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
- Define connector outputs + SourceAssertions.

## Phase 2 — Aggregation & SourceAssertion Store
- Implement aggregator to map source fields to canonical field paths.
- Implement `source_assertion_store` population.
- Implement uniform conflict detection.

## Phase 3 — Selection Rules
- Implement selection engine with configurable rules per field path.
- Keep selection rules separate from the SourceAssertion store.

## Phase 4 — Small Molecule Enrichment
- Add eMolecules, ChemSpider, DrugBank.
- Expand physchem and bioactivity fields.
- Add clinical layer data.

## Phase 5 — Developer Experience
- CLI or SDK entry points.
- Sphinx documentation.
- pytest coverage with contract tests and snapshots.
