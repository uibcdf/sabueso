# Sabueso — Card Schema Notes

## Schema Location
The frozen draft schema lives at:
- `schemas/card_schema.yaml`

This is a **conceptual** schema meant to be refined into formal validation later.

## Nested Structure
Cards are **nested** to preserve hierarchy and order. Each card type (protein, peptide, small molecule) inherits from a shared base.

## Field Path Contract (Approved)
Canonical field paths use **dot‑separated notation**.

Examples:
- `names.canonical_name`
- `properties.physchem.molecular_weight`
- `uniprot_comments.catalytic_activity`
- `features_positional.binding_site`

Identifier paths are **direct**:
- `identifiers.uniprot`
- `identifiers.pdb`
- `identifiers.chembl`
- `identifiers.pubchem`
(No `secondary_ids` level.)

## Uniform Evidence Mechanism (Critical)
All fields in all cards follow the same evidence protocol:

1) **Card fields store the selected value only**
   - Each field has `value` and `evidence_ids`.
   - This keeps the card readable and deterministic.

2) **All values from all sources live in `evidence_store`**
   - Each evidence object includes:
     - `field` (canonical field path)
     - `value`
     - `normalized_value`
     - `sources`
     - `source_records`
     - `retrieved_at`
     - optional timestamps (published/updated)
     - `confidence`

3) **Selection rules are explicit**
   - `selection_rules` is a map keyed by field path.
   - Rules do not delete evidence.

4) **Conflicts are explicit**
   - `quality.conflicts` lists fields with multiple disagreeing evidences.

This mechanism is **homogeneous** across all fields and all card types. It is a core design decision.

## Evidence Object Contract (Approved)
Every evidence object stored in `evidence_store` must include:

**Required**
- `evidence_id: string`
- `field: string` (canonical field path)
- `value: any`
- `source: { type: string, name: string, record_id: string }`
- `retrieved_at: date`

**Recommended**
- `normalized_value: any`
- `source_meta: dict`
- `timestamps: { published_at?: date, updated_at?: date }`
- `confidence: float`
- `notes: string`

The `source.type` must distinguish at least: `database`, `article`, `dataset`, and `llm` when applicable.

## Evidence Creation Rules (Approved)
- Each mapped field value must generate **at least one** evidence object.
- Evidence IDs should be **deterministic** from `(source, record_id, field, value)`.
- Evidence creation happens **before** any selection rules are applied.

## Positional Features (Proteins/Peptides)
The schema includes positional features observed directly in UniProt JSON examples:
- Active site, Binding site, Disulfide bond, Glycosylation, Lipidation, Modified residue, Mutagenesis, Natural variant, Region, Motif, Topological domain, Transmembrane, etc.

These are stored as lists of objects with `location`, `description`, and `evidence_ids`.

For the exact, verified enumerations, see:
- `devguide/UNIPROT_ENUMS.md`

## Location Model (Sequence + Structure)
Positional features must support **both**:
- **Sequence‑based locations** (start/end indices, sequence ID, 1‑based indexing)
- **Structure‑based locations** (PDB ID, chain ID, residue numbers, optional atom IDs)

This is required for TopoMT integration and visualization.

Real‑ID validation examples:
- `devguide/LOCATION_EXAMPLES.md`

## Location Contract (Approved)
`location` is a typed container that supports multiple contexts:\n\n```\nlocation:\n  kind: \"sequence\" | \"structure\" | \"atom\" | \"substructure\"\n  sequence?: { sequence_id, start, end, indexing, residue_ids? }\n  structure?: { pdb_id, chain_id, residue_id?, residue_number?, atom_ids? }\n  atom?: { atom_ids, atom_id_type }\n  substructure?: { smiles?, smarts?, atom_ids? }\n```\n\nThe exact atom/residue identifier type must always be specified when relevant (e.g., PDB residue IDs, RDKit atom indices).

## Disease Section (ProteinCard)
Protein cards include a `disease` section with disease associations and evidence links.

## Ligands with Roles (ProteinCard)
Protein cards include a `ligands` section. Each ligand has a `role` attribute
(e.g., inhibitor, activator, substrate) and evidence links.

## Clinical Layer (Small Molecules)
The schema includes a dedicated `clinical` section for:
- pharmacology, ADMET, clinical trials, pharmacovigilance,
- indications, contraindications, interactions.

This is intentionally separated from the core physchem and bioactivity data.
