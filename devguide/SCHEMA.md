# Sabueso — Card Schema Notes

## Schema Location
The frozen draft schema lives at:
- `schemas/card_schema.yaml`
The formal schema (versioned) lives at:
- `schemas/card_schema_0.2.0.yaml`

This is a **conceptual** schema meant to be refined into formal validation later.

## Nested Structure
Cards are **nested** to preserve hierarchy and order. Each card type (protein, peptide, small molecule) inherits from a shared base.

## Field Path Contract (Approved)
Canonical field paths use **dot‑separated notation**.

Examples:
- `names.canonical_name`
- `properties.physchem.molecular_weight`
- `annotations.catalytic_activity`
- `features_positional.binding_site`
- `structure.entry_metadata.experimental_method`

Identifier paths are **direct**:
- `identifiers.uniprot`
- `identifiers.pdb`
- `identifiers.chembl`
- `identifiers.pubchem`
(No `secondary_ids` level.)

## SourceAssertion Mechanism (Critical)
**A SourceAssertion records what an external source asserts about an entity or property.**
All fields in all cards are resolved from SourceAssertions through the same protocol:

1) **Card fields store the resolved value only**
   - Each field has `value` and `source_assertion_ids`.
   - `source_assertion_ids` lists the assertions that support the resolved value.
   - This keeps the card readable and deterministic.

2) **All assertions from all sources live in `source_assertion_store`**
   - One SourceAssertion per value asserted by one source record (see the contract
     below). Alternative and contradictory assertions are kept.
   - The store is serialized with the card.

3) **Selection rules are explicit**
   - `selection_rules` is a map keyed by field path.
   - Rules never delete SourceAssertions.

4) **Conflicts are explicit**
   - `quality.conflicts` lists fields whose SourceAssertions disagree, with the
     competing values and their `source_assertion_ids`.

This mechanism is **homogeneous** across all fields and all card types. It is a core design decision.

### What a SourceAssertion is not
MolSysSuite Architecture 1.0 distinguishes `SourceAssertion ≠ Evidence ≠ Provenance`:
- **Evidence** belongs to Nextia: project-contextual scientific information that
  supports, contradicts or informs a Question or Hypothesis. Sabueso never produces it; a
  DiscoveryProject may cite SourceAssertions as the basis of its own Evidence.
- **Provenance** is cross-cutting: origin, lineage, transformations and production
  context of any object. A SourceAssertion *has* provenance (source, record, version,
  retrieval, mapping); it is not provenance itself.
- Qualifiers a source attaches to its own statements (UniProt ECO codes, cited PubMed
  IDs, ChEMBL assay descriptors) are stored in `source_meta` under their source-native
  names; Sabueso defines no generic `evidence` field.

## SourceAssertion Contract (Approved)
Every SourceAssertion stored in `source_assertion_store` must include:

**Required**
- `source_assertion_id: string`
- `field: string` (canonical field path)
- `value: any`
- `source: { type: string, name: string, record_id: string, version?: string }`
- `retrieved_at: date`

**Recommended**
- `normalized_value: any` (when Sabueso normalization changes the asserted value)
- `source_meta: dict` (source-native qualifiers)
- `timestamps: { published_at?: date, updated_at?: date }`
- `confidence: float` (only when reported by the source)
- `notes: string`

The `source.type` must distinguish at least: `database`, `article`, `dataset`, and `llm` when applicable.

## SourceAssertion Creation Rules (Approved)
- Each mapped field value must generate **at least one** SourceAssertion.
- SourceAssertion IDs are **deterministic** from `(source, record_id, field, value)`
  (`generate_source_assertion_id`, prefix `SA_`).
- Mappings create SourceAssertions with `make_source_assertion`, **before** any
  selection rules are applied.

## Positional Features (Proteins/Peptides)
The schema includes positional features observed directly in UniProt JSON examples:
- Active site, Binding site, Disulfide bond, Glycosylation, Lipidation, Modified residue, Mutagenesis, Natural variant, Region, Motif, Topological domain, Transmembrane, etc.

These are stored as lists of objects with `location`, `description`, and `source_assertion_ids`.

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
Protein cards include a `disease` section with disease associations linked to their SourceAssertions.

## Ligands with Roles (ProteinCard)
Protein cards include a `ligands` section. Each ligand has a `role` attribute
(e.g., inhibitor, activator, substrate) and SourceAssertion links.

## Clinical Layer (Small Molecules)
The schema includes a dedicated `clinical` section for:
- pharmacology, ADMET, clinical trials, pharmacovigilance,
- indications, contraindications, interactions.

This is intentionally separated from the core physchem and bioactivity data.
