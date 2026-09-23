# Sabueso — Selection Rules (Field Examples)

Field-level examples of `selection_rules`, as in the packaged defaults
(`sabueso/resolver/selection_rules.json`, version `0.2.0`). Versioning follows x.y.z.

## How a field is resolved

- **Every field is resolved from its SourceAssertions.** When no rules are given, the
  packaged defaults apply, and the card records the rules it was resolved with
  (`card.selection_rules`). A field stated by several sources never takes the last one
  merged while citing them all (uibcdf/sabueso#10).
- **Itemised fields are a union.** When each assertion states one item of a list (a
  subcellular location, a binding site, a reaction), the items do not compete: the field is
  their union, each item traced to its assertion.
- **Only comparable values are compared.** `compare_within` and `numeric_agreement`
  (below) say which assertions measure the same thing. Disagreements among comparable
  assertions go to `quality.conflicts`. Values that are not comparable (another method,
  representation or source) go to `quality.alternatives`, visible and never hidden.
- **Support is every agreeing assertion.** The selected value cites all the assertions
  that state it within its comparable partition, from every source that agrees, and none
  from another method.

## 1) Molecular weight and TPSA — agreement at the stated precision

```json
"properties.physchem.molecular_weight": {
  "strategy": "priority_sources",
  "numeric_agreement": "stated_precision"
}
```

Two numbers agree when they are equal at the coarser precision their sources wrote:
ChEMBL `"824.97"` and PubChem `"825.0"` agree at one decimal; `"171.17"` and `171` at zero;
`"824.4"` and `825` do not. The precision is read from the asserted value, never assumed.
ChEMBL's molecular weight is `full_mwt`, the weight of the structure the record
describes; `mw_freebase` is the parent's, another structure with its own card.

## 2) logP and rotatable bonds — compared only within one method

```json
"properties.physchem.logp": {
  "strategy": "priority_sources",
  "compare_within": ["source_metadata.method"]
}
```

ChEMBL's ALogP (3.52) and PubChem's XLogP3 (2.8) for vincristine are two quantities, not a
disagreement. Mappings record the method in `source_metadata.method`: `ALogP`, `XLogP3`,
`chembl:rtb`, `pubchem:RotatableBondCount` (sources define rotatable bonds differently).
Two XLogP3 values that differ are still a conflict. Sabueso never recomputes a property
to reconcile sources (`devguide/DECISIONS.md`).

## 3) SMILES — never compared across sources

```json
"identifiers.smiles": {
  "strategy": "priority_sources",
  "compare_within": ["source.name"]
}
```

`identifiers.smiles` is isomeric (stereochemistry kept where the source defines it) and
`identifiers.smiles_connectivity` has connectivity only. Two isomeric SMILES of one
molecule from two toolkits are different strings: comparing them would need a
canonicalisation, which is a calculation. The molecule's identity is its standard InChIKey
(uibcdf/sabueso#25), so SMILES are only compared within one source. PubChem names them
`SMILES` (formerly `IsomericSMILES`) and `ConnectivitySMILES` (formerly
`CanonicalSMILES`, which never carried stereochemistry).

## 4) Source priority

```json
"priority_sources": ["UniProt", "ChEMBL", "PubChem", "PDB CCD", "InterPro"]
```

Priority chooses which comparable value is shown when sources agree or disagree. It does
not decide identity, and it does not hide the other values.

## Notes

- These rules are a baseline. A project may pass its own; the card records which rules
  resolved it.
- `allow_multiple` applies to fields whose assertions each state a whole list. Itemised
  fields are always a union.
