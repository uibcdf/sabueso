Selection Rules (Canonical Resolver Policy)
==========================================

This page lists the **current selection rules** used by the Resolver (version 0.1.0).
These rules are intended to be transparent for **users**, **developers**, and future
agents/AI integrations.

General Policy
--------------
- **Any discrepancy** (multiple distinct values for the same field) is **always reported**.
- The Resolver **selects a canonical value** but keeps all evidence in the EvidenceStore.
- Selection behavior is controlled by `selection_rules` (versioned, x.y.z).

Field Rules (Examples)
----------------------

1) ProteinCard — Domains (`annotations.domains`)

- Priority sources: InterPro → CATH → SCOPe → TED
- Allow multiple values

2) ProteinCard — Catalytic Activity (`annotations.catalytic_activity`)

- Priority source: UniProt
- Single value

3) SmallMoleculeCard — Molecular Weight (`properties.physchem.molecular_weight`)

- Strategy: most_recent
- Single value

4) SmallMoleculeCard — SMILES (`identifiers.smiles`)

- Priority sources: ChEMBL → PubChem
- Single value

5) ProteinCard — Binding Sites (`features_positional.binding_site`)

- Allow multiple values

Machine-Readable Rules
----------------------

The canonical, machine-readable rules live at:

- ``docs/selection_rules.json``

This file is intended for programmatic consumption by tools, agents, and future AI systems.
