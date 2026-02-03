# Sabueso — API Conventions

## Naming
- Use `snake_case` for fields in Python objects.
- Field path notation is **open**. Dot‑separated paths are the current working assumption, but the final convention is not frozen yet.

## Field Paths (Provisional Examples)
- `properties.physchem.molecular_weight`
- `uniprot_comments.catalytic_activity`
- `features_positional.binding_site`

## Evidence IDs
- Evidence IDs should be stable, unique, and deterministic if possible.
- Format example: `E_<source>_<record>_<hash>`

## Inputs (Accepted)
- Database IDs (UniProt, PDB, ChEMBL, PubChem, DrugBank, etc.)
- Sequences (FASTA)
- SMILES / InChI / InChIKey
- Common names and synonyms
- Structure files (PDB, MOL, SDF)

## API Style (Mixed)
- The public API is **mixed OO + functional**:
  - Card/Deck may expose ops as methods.
  - Tools are standalone functions grouped in modules.

## Errors
- Use explicit exception types for resolver errors, connector failures, and schema mismatches.
- Return partial cards only if evidence is complete for the fields present.
