# Sabueso — API Conventions

## Naming
- Use `snake_case` for fields in Python objects.
- Field path notation is **dot‑separated** and is now the frozen convention.

## Field Paths (Provisional Examples)
- `properties.physchem.molecular_weight`
- `annotations.catalytic_activity`
- `features_positional.binding_site`
- `structure.entry_metadata.experimental_method`

Canonical field path contract:
- `devguide/SCHEMA.md` (Field Path Contract)

## Evidence IDs
- Evidence IDs should be stable, unique, and deterministic if possible.
- Format example: `E_<source>_<record>_<hash>`

## Inputs (Accepted)
- Database IDs (UniProt, PDB, ChEMBL, PubChem, DrugBank, etc.)
- Sequences (FASTA)
- SMILES / InChI / InChIKey
- Common names and synonyms
- Structure files (PDB, MOL, SDF)

Location contract:
- `devguide/SCHEMA.md` (Location Contract)

## API Style (Mixed)
- The public API is **mixed OO + functional**:
  - Card/Deck may expose ops as methods.
  - Tools are standalone functions grouped in modules.

## Repository Layout (Phase 0)
- `sabueso/core`: Card, Deck, EvidenceStore
- `sabueso/resolver`: input resolution
- `sabueso/tools`: db/card/deck tools
- `sabueso/ops`: internal operations
- `sabueso/mappings`: source → canonical field mappings
- `sabueso/utils`: internal utilities only (no public API)
- `docs`: Sphinx documentation
- `tests`: unit/contract/snapshot tests

## Errors
- Use explicit exception types for resolver errors, connector failures, and schema mismatches.
- Return partial cards only if evidence is complete for the fields present.
