# Sabueso — Card Schema Notes

## Schema Location
The frozen draft schema lives at:
- `schemas/card_schema.yaml`

This is a **conceptual** schema meant to be refined into formal validation later.

## Nested Structure
Cards are **nested** to preserve hierarchy and order. Each card type (protein, peptide, small molecule) inherits from a shared base.

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

## Positional Features (Proteins/Peptides)
The schema includes positional features observed directly in UniProt JSON examples:
- Active site, Binding site, Disulfide bond, Glycosylation, Lipidation, Modified residue, Mutagenesis, Natural variant, Region, Motif, Topological domain, Transmembrane, etc.

These are stored as lists of objects with `location`, `description`, and `evidence_ids`.

For the exact, verified enumerations, see:
- `dev_guide/UNIPROT_ENUMS.md`

## Location Model (Sequence + Structure)
Positional features must support **both**:
- **Sequence‑based locations** (start/end indices, sequence ID, 1‑based indexing)
- **Structure‑based locations** (PDB ID, chain ID, residue numbers, optional atom IDs)

This is required for TopoMT integration and visualization.

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
