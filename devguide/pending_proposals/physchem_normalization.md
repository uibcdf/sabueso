---
summary: Normalize and method-qualify physicochemical properties across sources.
issue: uibcdf/sabueso#10
status: open
opened: 2026-09-23
closed:
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

Pending.
