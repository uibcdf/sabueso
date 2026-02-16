# Selection Rules (Canonical Resolver Policy)

This page describes the current selection behavior used by the Resolver
(version 0.1.0).

## General Policy

- Any discrepancy (multiple distinct values for the same field) is always reported.
- Resolver selects canonical values while preserving full evidence traceability.
- Selection behavior is controlled by versioned `selection_rules`.

## Representative Field Rules

1. Protein domains (`annotations.domains`)

- Priority sources: InterPro -> CATH -> SCOPe -> TED
- `allow_multiple = true`

2. Catalytic activity (`annotations.catalytic_activity`)

- Priority source: UniProt
- `allow_multiple = false`

3. Molecular weight (`properties.physchem.molecular_weight`)

- Strategy: `most_recent`
- `allow_multiple = false`

4. SMILES (`identifiers.smiles`)

- Priority sources: ChEMBL -> PubChem
- `allow_multiple = false`

5. Binding sites (`features_positional.binding_site`)

- `allow_multiple = true`

## Machine-Readable Rules

Canonical machine-readable rules are published at:

- `docs/content/user/selection_rules.json`
- `sabueso/resolver/selection_rules.json`

These files are intended for programmatic use by tools, agents, and automation.
