# Sabueso — Architecture

## Conceptual Architecture
1) **Input Layer**
   - Accepts identifiers and descriptors: database IDs, sequences (FASTA), SMILES, InChI, names, and structure files (PDB/MOL/SDF).

2) **Resolver**
   - Classifies entity type (protein, peptide, small molecule).
   - Normalizes identifiers and resolves ambiguity.

3) **Connectors**
   - Source‑specific adapters (UniProt, PDB, ChEMBL, PubChem, eMolecules, ChemSpider, DrugBank).
   - Each connector produces raw source data + source metadata.

4) **Aggregator**
   - Merges results, deduplicates, and aligns to canonical field paths.
   - Preserves all values via evidence objects.

5) **Selection Layer**
   - Chooses a canonical value per field based on configurable rules.
   - Keeps the full evidence history independent of selection.

6) **Card Builder**
   - Builds the final structured card with nested sections.
   - All fields point to evidence IDs.

7) **Cache / Store (optional)**
   - Local storage for previously generated cards.
   - Does not replace online queries; it is a convenience layer.

## Clinical Layer
Sabueso supports a **clinical layer** for drug‑design workflows. Clinical data (pharmacology, ADMET, clinical trials, pharmacovigilance, indications, contraindications, interactions) is included as a separate section to avoid mixing it with core physicochemical and biological data.

## Design Principles
- **Uniform Evidence Mechanism**: every field uses the same provenance model.
- **Nested Sections**: cards are hierarchical and ordered, not flat.
- **All Values Preserved**: selection never discards evidence.
- **Auditable Decisions**: selection rules and conflicts are explicit.

