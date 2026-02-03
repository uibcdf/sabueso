# Sabueso — Glossary

- **Card**: A structured, nested object representing a molecular system with selected values and explicit evidence links.
- **Evidence Object**: A record of a single value from a source, stored in `evidence_store`.
- **Evidence Store**: Global map of all evidence objects, indexed by `evidence_id`.
- **Field Path**: Canonical string identifying a field (e.g., `properties.physchem.molecular_weight`).
- **Selection Rule**: A rule that picks a canonical value among multiple evidences for a field.
- **Conflict**: Disagreement among evidence objects for the same field.
- **Deck**: A collection of Cards with operations for filtering, sorting, comparing, and expansion.
- **Clinical Layer**: Dedicated section with pharmacology, ADMET, clinical trials, pharmacovigilance, etc.
- **Database Module (tools.db)**: A per‑database module that exposes public functions for fetching and extracting data.
- **Resolver**: Component that classifies inputs and normalizes identifiers.
- **Ligand Role**: The functional role assigned to a ligand (e.g., inhibitor, activator, substrate).
- **Ambiguous Input**: Input that maps to multiple plausible entities; should return a Deck.
- **Mappings**: Translation rules that map source fields to canonical card fields.
