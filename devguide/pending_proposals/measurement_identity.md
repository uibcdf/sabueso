---
summary: How Sabueso recognises one measurement stated by several bioactivity sources, so that copies never count as independent confirmations.
issue: uibcdf/sabueso#66
status: open
opened: 2026-09-25
closed:
verification: measured
area: [bioactivities, identity, provenance, chembl, bindingdb, pubchem]
blocked_by: []
supersedes: []
---

# Identity of a measurement across bioactivity sources

## What

Every measurement on a card is a ChEMBL activity today, identified by `activity_id`.
Before BindingDB or PubChem BioAssay are added, Sabueso must recognise when two
sources state the same measurement. Otherwise one number from one paper, extracted or
re-deposited by three databases, reads as three confirmations.

## How / evidence (measured 2026-09-25)

**BindingDB** (REST `getLindsByUniprots`, no key). Each record carries a monomer id,
SMILES, affinity type, value in nM, PubMed id and DOI. It was compared with the
ChEMBL_37 fixtures by publication, type and value.

| Target | BindingDB records | Same paper, type and value in ChEMBL | Papers in BindingDB, also in ChEMBL |
| --- | --- | --- | --- |
| TcTIM (P52270, CHEMBL5834) | 17 | 17 | 3 of 3 |
| HsTIM (P60174, CHEMBL4880) | 23 | 18 | 6 of 7 |

The five HsTIM records that did not match show the hard cases:

- **Precision.** BindingDB states Kd 62 and 183 nM, where ChEMBL states 62.46 and
  182.66 nM from the same paper (PubMed 29928781). They are the same measurements,
  rounded.
- **Relation and format inside the value.** Values such as `>1.00e+5` carry the
  relation and use scientific notation.
- **Genuinely new.** Three records come from a paper (PubMed 23406473) that has no
  activity for this ChEMBL target. They may still be in ChEMBL under another target,
  so "absent from this target" is not "absent from ChEMBL".
- **ChEMBL's own duplicates.** In that same paper ChEMBL states each value twice, as
  Kd and as ED50. The type differs, so these are not grouped.

**PubChem BioAssay.** For HsTIM, all 11 assays linked to the protein were deposited
by ChEMBL (10) or BindingDB (1). Each states its origin, for example AID 214625 has
source ChEMBL and source id CHEMBL816360. For these targets PubChem adds copies with
declared provenance, and no new measurement.

## Why

- The views classify molecules and summarise evidence by counting measurements
  (`bioactivity_class@3`, `Card.ligands()`). Counting records instead would turn
  copies into corroboration.
- Each source keeps context the others lack: assay description, conditions, curation
  notes. Merging records would lose it, and a wrong merge could not be undone.

## Proposal

### 1. Two kinds of sameness, never confused

- **Provenance identity: a record says it is a copy.** A PubChem assay deposited by
  ChEMBL names the ChEMBL assay. A BindingDB record curated from ChEMBL would state
  that too, if the source says so. This is exact. It is recorded as a stated link
  (`redeposit_of`), supported by the copying source's own statement.
- **Statement identity: two sources read the same paper.** Candidates must share:
  - the publication (PubMed or DOI);
  - the target entity (UniProt anchor) and the molecule (InChIKey anchor);
  - the measurement type and the relation;
  - a value that agrees at the coarser of the two stated precisions (the rule already
    used for curated bioactivities, #44), in the normalized unit.

  Assay conditions are rarely comparable across sources, so this is a derived
  judgement (rule `measurement_identity@1`), never a stated fact.

### 2. Representation: keep the records, group the measurements

- Each source record stays a `has_bioactivity` relationship, with its verbatim
  context. Its identity qualifiers gain the source, so `activity_id` is no longer
  assumed to be ChEMBL's.
- A **measurement group** links the records judged to be one measurement, with its
  rule and basis. It is derived, like activity classes, and recomputed when sources
  change.
- When statement identity is ambiguous (one record, several candidates), nothing is
  grouped. The candidates are reported with the ambiguity; no choice is made silently.

### 3. Views count measurements

- `Card.bioactivities()` gives one measurement per group, listing its records and
  sources (`supported_by`). Classes, counts and "best pChEMBL" are computed per group.
- Agreement between sources for one measurement is reported. So is a disagreement
  when provenance says one record is a copy of another but the values differ: that is
  a transcription difference, flagged like `curated_difference`.
- Records from a publication that no other source holds are new measurements, marked
  with their single source.

### 4. Molecule identity

BindingDB records are anchored at the InChIKey through UniChem, where BindingDB is a
source, keyed by monomer id, as ChEMBL and CCD records are today. Sabueso never
derives identity from SMILES: that would mean computing chemistry, which is modelling
(`devguide/DECISIONS.md`, "Computable properties are recorded, not computed"). A
record UniChem does not anchor stays unanchored and is reported, as in ligand decks.

### 5. Which source first

- **BindingDB** first. It needs no key, and it adds measurements from papers ChEMBL
  lacks for a target, 3 of 23 for HsTIM.
- **PubChem BioAssay** later. Only assays of other depositors (screening centres,
  literature depositors that are not ChEMBL or BindingDB) add measurements. The rest
  are provenance copies, recorded as such.

## Alternatives

1. **Merge records into one relationship per measurement**, as `has_structure` merges
   support. It is simpler for views, but it loses per-source context, and a wrong match
   cannot be undone. Rejected for measurements. It suits structures because a
   structure's identity is stated, the PDB id, while a measurement's is judged.
2. **Count records and flag suspected duplicates.** It leaves the classification
   inflated by default. Rejected.
3. **Use only one bioactivity source.** It gives up measurements from papers ChEMBL
   lacks. Rejected, but it is the current state until this lands.

## Risks and future problems

- **Rounding can hide real differences.** Two measurements from one paper, for
  example on two constructs, can agree at a coarse precision. The publication, the
  type and the relation must match as well. Assay descriptions, where both sources give
  them, can split a group; that refinement would be `@2`.
- **Target assignment differs between sources.** ChEMBL can assign an activity by
  homology. BindingDB's target is the UniProt entry queried. Measurements assigned
  differently are grouped only when both state the same target entity.
- **Card size.** Every new source adds records (#19). The knowledge store (#27) shares
  identical rows, but it does not deduplicate different records of one measurement.

## Acceptance criteria

- On the TIM fixtures, the 17 TcTIM and 18 HsTIM BindingDB records that match ChEMBL
  form measurement groups with their ChEMBL records. Classes and counts equal those of
  ChEMBL alone.
- The three PubMed 23406473 records are new measurements with one source.
- Kd 62 and 62.46 nM, from the same paper, form one group, and ChEMBL's Kd and ED50
  duplicates do not.
- A PubChem assay deposited by ChEMBL is linked to its ChEMBL assay and never counted.

## Questions for the maintainer

1. Keep records and group measurements (proposed), or merge?
2. Is the coarser-precision rule acceptable for statement identity, with publication,
   type and relation required?
3. BindingDB first, PubChem BioAssay later and only for depositors that are not
   copies?

## Resolution

Pending.
