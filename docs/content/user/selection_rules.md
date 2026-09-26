# Selection Rules

How Sabueso chooses the value it shows for a field when several sources state it. The
packaged rules are version 0.2.0.

## General policy

- **Every field is resolved from its SourceAssertions**, and none is ever discarded.
  The card records the rules it was resolved with (`card.selection_rules`); a project
  may pass its own.
- **Itemised fields are a union.** When each assertion states one item of a list (a
  subcellular location, a binding site, a reaction), the items do not compete: the field
  is their union, each item traced to its assertion.
- **Only comparable values are compared.** Disagreements among comparable assertions go
  to `quality.conflicts`. Values that are not comparable (another method, representation
  or source) go to `quality.alternatives`, visible and never hidden.
- **Support is every agreeing assertion**: the selected value cites all the assertions
  that state it, from every source that agrees.
- **Priority** (`priority_sources`: UniProt, ChEMBL, PubChem, PDB CCD, InterPro) chooses
  which comparable value is shown. It never decides identity and never hides the others.

## Representative field rules

- **Molecular weight and TPSA** — `numeric_agreement: stated_precision`: two numbers
  agree when they are equal at the coarser precision their sources wrote (ChEMBL
  `"824.97"` and PubChem `"825.0"` agree at one decimal).
- **logP and rotatable bonds** — `compare_within: source_metadata.method`: ChEMBL's ALogP
  and PubChem's XLogP3 are two quantities, not a disagreement. Sabueso never recomputes a
  property to reconcile sources.
- **SMILES** — `compare_within: source.name`: SMILES from two toolkits are different
  strings for one molecule, so they are compared only within one source. A molecule's
  identity is its standard InChIKey.
- **Catalytic activity** — by source priority; **binding sites** and **domains** —
  lists (`allow_multiple`).

The rationale and more examples are in the developer guide
(`devguide/SELECTION_RULES_EXAMPLES.md`).

## Machine-readable rules

The rules are published for tools and agents at `docs/content/user/selection_rules.json`,
identical to the packaged `sabueso/resolver/selection_rules.json` (a test keeps them
equal).
