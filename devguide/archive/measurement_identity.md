---
summary: How Sabueso recognises one measurement stated by several bioactivity sources, so that copies never count as independent confirmations.
issue: uibcdf/sabueso#66
status: resolved
opened: 2026-09-25
closed: 2026-09-25
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

## Decisions (maintainer, 2026-09-25)

1. **Records are never lost.** Each source record stays a relationship; measurements
   are derived groups over them.
2. **Identity in layers.** Declared provenance comes first, and is exact. Independent
   readings of one paper are grouped on publication, molecule, type, relation and
   value at the coarser stated precision. Several candidates, or near matches, are
   reported for a reader and never grouped.
3. **Copies are pointers, not noise.** A copy whose original is on the card is grouped
   with it. A copy whose original is missing leads to the original: fetch it, or keep
   the copy with its declared origin. It can reveal measurements a target-based query
   missed, or a different target assignment. So PubChem BioAssay copies will be used,
   not only other depositors' assays.

## Implementation (2026-09-25)

- `sabueso/core/measurements.py` (rule `measurement_identity@1`): provenance
  (`copy_of`), statement identity, ambiguity, and a **review** list. The review list
  holds pairs with the same paper, type and exact value but different molecules
  (`molecule_differs`, `stereo_differs` when only the stereochemistry differs, or
  `molecule_unresolved`). Censored values are not reviewed.
- `Card.bioactivities()` counts measurements, not records: `measurement_count`,
  `record_count`, `sources`, a `group` per record, and a group whose sources classify
  it differently is `inconclusive`. A BindingDB molecule joins the ChEMBL entry of the
  same entity.
- BindingDB enrichment (`bindingdb={}`). Monomers are anchored through UniChem. When
  BindingDB is asked for, ChEMBL molecules are anchored at the InChIKey ChEMBL states
  for them.

Measured on the TIM fixtures, with molecule identity required:

| Target | BindingDB | Grouped with ChEMBL | New (paper ChEMBL lacks) | Reported for review |
| --- | --- | --- | --- | --- |
| TcTIM | 17 | 16 | — | 1 pair with molecule_differs: IC50 13000 nM, PubMed 35189560, BindingDB IAFAANQPDPWPHK against ChEMBL XMRUGIFDPFFCIV (and two further pairs) |
| HsTIM | 23 | 13 | 3 (PubMed 23406473) | 5 molecule_unresolved (monomers UniChem does not hold yet); 1 stereo_differs (REDPJRNIRCVACW, SQYZTQLGSA against UGMRNKNYSA) |

The first measurement estimated 17/17 and 18/23 matches from paper, type and value
alone. Requiring the molecule's identity shows that some of them are not the same
molecule by the sources' own identity statements. These are curation discrepancies
worth reading, and grouping them would have hidden them.

PubChem BioAssay (#68, same day):
- **Copies are grouped by provenance.** Each assay's depositor and depositor assay id
  become `copy_of`; within the named assay, the molecule and the type select the
  original.
- **A copy whose compound PubChem standardised differently** (stereochemistry or salt
  lost) is grouped when only one record of the assay shares its connectivity, and is
  flagged `stereo_differs`.
- **Copies never vote** for a group's class, because PubChem's table drops the relation.
- **Pointers are followed.** ChEMBL assays a copy names but the card lacks are fetched
  from ChEMBL. That includes assays on the card when the target query was truncated.
- **Unresolved copies** say why: `original_not_on_card` or `molecule_not_found_in_assay`.

| Target | Records (ChEMBL, BindingDB, PubChem) | Measurements |
| --- | --- | --- |
| TcTIM | 1002 | 505 |
| HsTIM | 88 | 49 |

With ChEMBL limited to 25 activities, TcTIM's PubChem copies led to the 468 missing
ones, and the card equals the complete one. Still open: BindingDB's per-record origin,
which only its bulk download states (recorded in RISKS).
## Resolution

Resolved: the common part and BindingDB (#66), and PubChem BioAssay with copies as pointers (#68).
