---
summary: Normalize and method-qualify physicochemical properties across sources.
issue: uibcdf/sabueso#10
status: resolved
opened: 2026-09-23
closed: 2026-09-23
verification: reproduced
area: [mappings, resolver, small-molecules]
blocked_by: []
supersedes: []
---

# Cross-source physicochemical properties

## What

When two sources describe the **same** molecule, the resolver reports conflicts that are
not disagreements about one quantity. Some come from values that were never normalized,
others from different calculation methods, representations or definitions being stored
in one field.

## How / evidence

Reproduced on `main` on 2026-09-23 by merging ChEMBL `CHEMBL90555` with PubChem CID 5978.
Both are vincristine, with InChIKey `OGWKCGZFUXNPDA-XQKSVPLYSA-N`. The run used the
default selection rules and the fixtures `temp_data/CHEMBL90555.json` and
`temp_data/5978.json`.

| field | ChEMBL | PubChem | cause |
|---|---|---|---|
| `properties.physchem.logp` | `'3.52'` (ALogP, string) | `2.8` (XLogP3) | different methods; string not normalized |
| `properties.physchem.tpsa` | `'171.17'` (string) | `171` | string not normalized; precision |
| `properties.physchem.molecular_weight` | `'824.97'` (`mw_freebase`, string) | `825.0` | string not normalized; rounding; free-base vs full-weight semantics |
| `properties.physchem.rotatable_bonds` | `8` | `10` | different definitions |
| `identifiers.smiles` | isomeric | connectivity | different representations |

ChEMBL serializes `alogp`, `psa`, `mw_freebase` and `full_mwt` as strings. `hbd`, `hba`,
`rtb` and `aromatic_rings` are integers.

## Boundary

Recomputing one canonical value with a chemistry toolkit is not a fix for these
conflicts. Computing properties is modelling, which belongs to MolSysSuite, so Sabueso
only records what sources state (`devguide/DECISIONS.md`, "Computable properties are
recorded, not computed"; uibcdf/sabueso#25). The fix stays here: qualify each value by
its method, and keep real disagreements visible.

## Why

False conflicts hide real ones and degrade the resolved values. The fix concerns how
Sabueso represents and resolves SourceAssertions, which is local to Sabueso.

## Alternatives

1. **Normalize ChEMBL numeric strings** through `normalized_value`, as done for PubChem in
   #9.
2. **Qualify method-dependent properties**, either:
   - by recording the method in `source_metadata` and letting the resolver compare only
     like with like, or
   - by splitting the field paths (e.g. `logp.alogp`, `logp.xlogp3`).
3. **Explicit numeric tolerance** in the selection rules for rounded quantities.
4. **Separate isomeric from connectivity SMILES**, or record the representation.
5. **Define `molecular_weight`:** free base or parent vs full salt form.

## Acceptance criteria

- The vincristine merge produces no conflicts caused by type, rounding, method or
  representation differences.
- Real disagreements are still reported.
- The chosen field-path and tolerance rules are documented in `FIELD_PATHS.md`,
  `SELECTION_RULES_EXAMPLES.md` and the schema.
- Offline tests cover the vincristine merge.

## Resolution

Resolved on 2026-09-23. The vincristine merge (ChEMBL CHEMBL90555 + PubChem 5978, both
anchored at `OGWKCGZFUXNPDA-XQKSVPLYSA-N` since #25) produces no conflicts. Every earlier
conflict now has an explicit reason:

| field | outcome |
|---|---|
| `molecular_weight` | agree at the stated precision (`824.97` vs `"825.0"`); both sources support the value |
| `tpsa` | agree at the stated precision (`171.17` vs `171`); both sources support it |
| `logp` | alternatives by method (ALogP 3.52, XLogP3 2.8), not a conflict |
| `rotatable_bonds` | alternatives by method (`chembl:rtb` 8, `pubchem:RotatableBondCount` 10) |
| `smiles` | split: `identifiers.smiles` (isomeric) and `identifiers.smiles_connectivity`; SMILES are compared only within one source |

Choices against the alternatives above:
1. **Numeric strings** are normalized (`normalized_value`) in the ChEMBL mapping, which is
   now table-driven. PubChem numbers are normalized too.
2. **Method-dependent properties** keep their field path. The method goes in
   `source_metadata.method`, and the resolver compares only within one method
   (`compare_within`). Split field paths were rejected: they multiply paths per method and
   hide that the values describe one property.
3. **Tolerance** is not a free parameter. It is the coarser precision the sources stated
   (`numeric_agreement: "stated_precision"`).
4. **SMILES** are split by representation. SMILES from different sources are never
   compared: equal molecules give different strings in different toolkits, and the
   InChIKey anchor carries identity.
5. **Molecular weight** is that of the anchored structure: ChEMBL `full_mwt`, not
   `mw_freebase`, which is the parent's weight.

Found and fixed on the way:
- **Last value wins.** Without selection rules, the aggregator kept the last source's
  value while citing every source's assertion. Every field is now resolved, with the
  packaged rules by default, and the card records the rules used.
- **List fields.** Itemised list fields (one assertion per item) are a union, not
  competing values.
- **PubChem SMILES.** PubChem's isomeric SMILES (`("SMILES", "Absolute")`, `SMILES`) was
  never mapped: the card only got the connectivity SMILES. The online client requested
  `CanonicalSMILES`, which in PubChem terms has no stereochemistry.
- **Quality schema.** The formal schema described `quality.conflicts` as a source-stated
  field, so any card with a legitimate conflict failed validation. `quality` is now
  declared as records (`devguide/SCHEMA.md`, "Quality records").
- **Selection rules.** The default `priority_sources` listed removed sources (InterPro,
  CATH, SCOPe, TED). The rules are now version 0.2.0.
- **Retrieval times.** Resolving every field exposed that `most_recent` compared
  timezone-aware stamps (online clients) with plain dates (fixtures) and failed. Naive
  times are now read as UTC.

Tests: `tests/core/test_physchem_resolution_offline.py`.

Not in scope, tracked elsewhere: typed quantities with units (PyUnitWizard, #31). Units
stay in `source_metadata.unit` and field names until then.
