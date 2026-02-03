# Sabueso — Architecture

## Conceptual Architecture
1) **Input Layer**
   - Accepts identifiers and descriptors: database IDs, sequences (FASTA), SMILES, InChI, names, and structure files (PDB/MOL/SDF).

2) **Resolver**
   - Classifies entity type (protein, peptide, small molecule).
   - Normalizes identifiers and resolves ambiguity.

3) **Database Modules (tools.db.\*)**
   - Per‑database modules (UniProt, PDB, ChEMBL, PubChem, eMolecules, ChemSpider, DrugBank).
   - Provide public functions for querying and extracting source data.
   - Internally, these functions return raw source data + source metadata.

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

## ProteinCard Extensions
- `disease` section for disease associations.
- `ligands` section with a `role` attribute (e.g., inhibitor, activator, substrate).
- An operation to extract a **Deck of inhibitor cards** from a ProteinCard.

## Core Objects
- **Card** and **Deck** are the core domain objects.
- Users can operate on a single Card or a Deck of cards.

## Ops vs Tools
- **Ops**: internal operations attached to Card/Deck with consistent semantics (compare, filter, sort, expand, extract, etc.).
- **Tools**: public, heterogeneous functions that take Card/Deck as inputs and can return any output type.

## Tools Modules (Public API)
- `tools.db.*`: per‑database modules with public functions for querying and extracting data.
- `tools.card.*`: tools that operate on a single Card.
- `tools.deck.*`: tools that operate on a Deck.

Tools are **ad‑hoc by design**; there is no enforced common interface or protocol.

## Mappings Layer
Mappings are the explicit translation rules from **source fields** to **canonical card fields**.
They should live outside database modules to keep transformations consistent and maintainable.

## Design Principles
- **Uniform Evidence Mechanism**: every field uses the same provenance model.
- **Nested Sections**: cards are hierarchical and ordered, not flat.
- **All Values Preserved**: selection never discards evidence.
- **Auditable Decisions**: selection rules and conflicts are explicit.
