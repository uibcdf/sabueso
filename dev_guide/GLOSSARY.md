# Sabueso — Glossary

- **Card**: A structured, nested object representing a molecular system with selected values and explicit evidence links.
- **Evidence Object**: A record of a single value from a source, stored in `evidence_store`.
- **Evidence Store**: Global map of all evidence objects, indexed by `evidence_id`.
- **Field Path**: Canonical string identifying a field (e.g., `properties.physchem.molecular_weight`).
- **Selection Rule**: A rule that picks a canonical value among multiple evidences for a field.
- **Conflict**: Disagreement among evidence objects for the same field.
- **Clinical Layer**: Dedicated section with pharmacology, ADMET, clinical trials, pharmacovigilance, etc.
- **Connector**: Source‑specific adapter that fetches and normalizes data from one database.
- **Resolver**: Component that classifies inputs and normalizes identifiers.

