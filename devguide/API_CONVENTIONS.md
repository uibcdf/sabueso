# Sabueso — API Conventions

## Naming
- Use `snake_case` for fields in Python objects.
- Field path notation is **dot‑separated** and is now the frozen convention.

## Field Paths (Examples)
- `properties.physchem.molecular_weight`
- `annotations.catalytic_activity`
- `features_positional.binding_site`
- `sequence.length`

Canonical field path contract:
- `devguide/SCHEMA.md` (Field Path Contract)

## SourceAssertion IDs
- SourceAssertion IDs should be stable, unique, and deterministic if possible.
- Format: `SA_<source>_<record>_<hash>` (see `generate_source_assertion_id`).

## Inputs
- Accepted today (`sabueso.resolve`):
  - UniProt accessions;
  - `pdb:<id>`, `pubchem:<cid>`, `chembl:<id>`, `pdb.ligand:<code>`,
    `inchikey:<key>`;
  - bare ChEMBL ids and standard InChIKeys;
  - an `EntityQuery` with a name and an organism.
- Planned by the original design (`ROADMAP.md`): DrugBank ids, sequences (FASTA),
  SMILES and InChI, and structure files (PDB, MOL, SDF). Resolving these needs identity
  rules of its own.

Location contract:
- `devguide/SCHEMA.md` (Location Contract)

## API Style (Mixed)
- The public API is **mixed OO + functional**:
  - Card/Deck may expose ops as methods.
  - Tools are standalone functions grouped in modules.

## Repository Layout
See `CHECKPOINT.md` ("Package layout"). The rules that stay:
- `sabueso/mappings` holds source-to-canonical translation;
- `sabueso/tools/db` holds source access;
- `sabueso/_private` and `sabueso/utils` hold no public API.

## Errors
- Use explicit exception types for resolver errors, connector failures, and schema mismatches.
- Return partial cards only if SourceAssertions are complete for the fields present.

## Views (uibcdf/sabueso#47)
- A key whose value is a reference (`<namespace>:<id>`, or a card id) ends in `_ref` in
  every view: `molecule_ref`, `ligand_ref`, `structure_ref`, `partner_ref`,
  `publication_ref`, `self_ref`, `other_ref`. The guard is
  `tests/core/test_view_conventions_offline.py`.
- Stored data keeps its schema names (qualifiers such as `observed_in.structure`,
  enrichment records, deck meta). Renaming those is a schema change (#42).
- Molecule items carry `label` and `label_source`. The label is the name, else the
  ChEMBL id, else the PDB component code, else the InChIKey
  (`sabueso.core.labels.molecule_label`).

