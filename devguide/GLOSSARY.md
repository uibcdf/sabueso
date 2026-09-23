# Sabueso — Glossary

- **Card**: A structured, nested object representing a molecular system with resolved values linked to the SourceAssertions that support them.
- **SourceAssertion**: A record of what an external source asserts about an entity or property (value, field, source record, retrieval), stored in `source_assertion_store`.
- **SourceAssertionStore**: Map of all SourceAssertions of a card, indexed by `source_assertion_id`.
- **Evidence** *(not a Sabueso concept)*: in MolSysSuite, project-contextual scientific information in a Nextia DiscoveryProject that supports, contradicts or informs a Question or Hypothesis. It may cite SourceAssertions as its basis.
- **Provenance**: Cross-cutting information about origin, lineage, transformations and production context of any object; a SourceAssertion has provenance but is not provenance.
- **Field Path**: Canonical string identifying a field (e.g., `properties.physchem.molecular_weight`).
- **Selection Rule**: A rule that picks a canonical value among multiple SourceAssertions for a field.
- **Conflict**: Disagreement among SourceAssertions for the same field.
- **Deck**: A collection of Cards with operations for filtering, sorting, comparing, and expansion.
- **Clinical Layer**: Dedicated section with pharmacology, ADMET, clinical trials, pharmacovigilance, etc.
- **Database Module (tools.db)**: A per‑database module that exposes public functions for fetching and extracting data.
- **Resolver**: Component that classifies inputs and normalizes identifiers.
- **Ligand Role**: The functional role assigned to a ligand (e.g., inhibitor, activator, substrate).
- **Ambiguous Input**: Input that maps to multiple plausible entities; should return a Deck.
- **Mappings**: Translation rules that map source fields to canonical card fields.
