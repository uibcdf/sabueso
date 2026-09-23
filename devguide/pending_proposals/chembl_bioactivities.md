---
summary: ChEMBL bioactivities as measured protein–molecule relationships with a derived, parameterized activity view.
issue: uibcdf/sabueso#23
status: partial
opened: 2026-09-23
closed:
verification: measured
area: [relationships, chembl, protein-card, derived-knowledge]
blocked_by: []
supersedes: []
---

# Summary

## What

The measured bioactivities that ChEMBL reports for a resolved protein become part of its ProteinCard.

**Relationships.** Each ChEMBL activity record becomes one `has_bioactivity` relationship from the protein (`uniprot:<accession>`) to the tested molecule (`chembl:<molecule_chembl_id>`).

**Qualifiers.** Each relationship carries:

- the measurement: standard type, relation, value, units, pChEMBL, activity and data-validity comments, potential-duplicate flag and action type;
- the assay: id, type, description, assay organism, target-assignment confidence and relationship type, and variant;
- the document: id, year and journal;
- the tested and parent molecule.

**Support.** Two ChEMBL SourceAssertions support each relationship, with the ChEMBL release in `source.version`:

- the activity record, verbatim (field path `relationships.has_bioactivity`);
- the assay record (field path `relationships.has_bioactivity.assay`). It is stated once per assay and shared by that assay's activities.

**Interpretation is derived, never asserted.** `Card.bioactivities()` groups the measurements by parent molecule. It classifies each measurement with the rule `bioactivity_class@1`, which has explicit, overridable thresholds, and returns that rule as a derivation record. Classification and scope:

- A single-point % inhibition reads as an IC50 bound at the test concentration.
- The test concentration is taken from the assay description, because ChEMBL gives it nowhere else.
- Negative and "Not Determined" results are kept.
- By default the view includes only assays assigned directly to the target (relationship type `D`). It lists every other measurement as excluded, with the reason.

**Enrichment.** `resolve_protein_card(..., chembl={...})` enables it. The target comes from the ChEMBL cross-reference of the UniProt entry. Every outcome is recorded in `quality.enrichments`: added, not_found, error, and truncation against `total_count`.

## How / evidence

Measured on ChEMBL_37 (released 2026-05-01), retrieved on 2026-09-23. The fixtures are in `temp_data/chembl/`.

**CHEMBL5834 (TcTIM, P52270)**
- 493 activities, 256 molecules, 13 assays and 5 documents. All assays are binding assays, with a direct assignment and confidence 9.
- 471 records are single-point % inhibition, and 185 of those are "Not Determined". The test concentration (50, 100, 200 or 400 µM) appears only in the assay description.
- One paper (CHEMBL1629474, 2010) provides 459 of the 493 records.
- Derived with the default thresholds:
  - measurements: 9 active, 32 weak, 202 inactive, 65 inconclusive and 185 not determined;
  - molecules: 8 active, 26 weak, 201 inactive and 21 inconclusive.
- The best potency is in the low µM range (pChEMBL ≤ 5.92).

**CHEMBL4880 (HsTIM, P60174)**
- 36 activities in 10 assays.
- All 8 Ki values come from assays assigned by homology (confidence 8, relationship `H`). They were measured on rabbit TIM (*Oryctolagus cuniculus*) or on TIM of unknown organism. They are not measurements of human TIM, and the default view excludes and reports them.
- Ten other measurements are "TPI (unknown origin)" assays that ChEMBL assigns directly to human TIM. They stay in the view and are flagged `assay_organism_unknown_origin`.
- Records flagged "Outside typical range": 8 in total, 4 of them among the included measurements.

**Selectivity.** 14 molecules were measured on both TIMs, which gives direct selectivity data. Example: CHEMBL567076 has IC50 6.5 µM on TcTIM (active) and IC50 > 1 mM on HsTIM (inactive).

**Card size.** The TcTIM card grows from about 37 KB to about 1.0 MB of compact JSON, roughly 2 KB per measurement: about 1.1 KB for the verbatim SourceAssertion and 0.9 KB for the relationship.

**Tests.** `tests/core/test_chembl_bioactivities_offline.py` covers these cases. The online counterpart is in `tests/core/test_online_protein_card.py`.

## Why

Known ligands and inhibitors, including the negative results, are part of the knowledge baseline of a target. They are the natural start of the MOLI vision of protein cards interacting with small-molecule decks (`devguide/SCIENTIFIC_POTENTIAL.md`).

Presenting the ChEMBL data naively would mislead:

- **Homology assignments** would present rabbit-TIM measurements as human-TIM data.
- **Single-point screens** at 400 µM would read as "inhibitors".
- **Source bias** would hide that one paper dominates a target's data.

## Decisions (MVP)

1. **Predicate `has_bioactivity`** (protein → molecule), added deliberately to the vocabulary. The direction follows the protein card (subject = card entity).
2. **One relationship per measurement.** `activity_id` is an identity qualifier. Repeated measurements of one molecule keep their own assay, document and support. Rejected alternative: one relationship per protein–molecule pair holding a list of measurements. The pair's qualifiers would be a list that grows and conflicts between sources, and support would no longer be per measurement.
3. **Object = tested molecule**, with the parent (salt-stripped) molecule as a qualifier. The view groups by parent.
4. **Activity classes are derived** in the view: active ≤ 10 µM < weak ≤ 100 µM < inactive, plus inconclusive, not_determined and unclassified. They are never stored. The thresholds are parameters and are recorded in the derivation.
5. **Single-point inhibition as an IC50 bound.** ≥ 50 % at c means IC50 ≤ c, and < 50 % means IC50 > c. This approximation assumes a standard dose response and is part of the rule.
6. **Direct target assignment only, by default.** Excluded measurements are reported, never silently dropped. `include_indirect=True` includes them.
7. **The molecule's strongest class wins** in the per-molecule summary. All class counts are kept, and `discordant` marks molecules that are both active or weak and inactive.

## Risks and future problems

- **Card size (uibcdf/sabueso#19).** About 2 KB per measurement.
  - A heavily studied target (tens of thousands of activities) would produce cards of tens of MB.
  - The default `limit` is 5000 and truncation is recorded. Truncation is by `activity_id` order (oldest first), which is itself a bias.
  - A real fix needs the storage re-evaluation of #19: externalized relationship or SourceAssertion stores, or a compact mode.
- **Cross-source duplicates.** BindingDB, PubChem BioAssay and ChEMBL overlap. Identity by `activity_id` is ChEMBL-specific. When a second bioactivity source is added, the identity of a measurement across sources has to be designed. It must not be assumed.
- **Test-concentration extraction** relies on free text ("at 100 uM"). It is a derived value and is recorded as coming from the "assay description text". Descriptions in other formats give "inconclusive", never a guess.
- **"Unknown origin" assays** are assigned by ChEMBL to the human target by convention. They are only flagged.
- **Targets beyond single proteins.** Only the targets that UniProt cross-references are used. Activities recorded against protein complexes or families that contain the protein are not included.
- **Classification thresholds** are generic. Target classes such as enzymes or GPCRs, and uses such as hit finding or probe quality, may need different values. That is why they are parameters.
- **Measurement types.** Types not listed as potency or single-point types (e.g. Km, Activity) are "unclassified". Adding one is a rule change and needs a new rule version.
- **Transient API responses.** One retrieval returned activity records without an assay id. The client tolerates that, and the view flags `missing_assay_metadata`.
- **Licence.** ChEMBL data is CC BY-SA 3.0. The attribution and share-alike obligations of the redistributed fixtures are tracked in uibcdf/sabueso#24.

## Acceptance criteria

- [x] Online and fixture clients: pagination, `total_count` and truncation, assay metadata and ChEMBL release.
- [x] Mapping to `has_bioactivity` relationships backed by activity and assay SourceAssertions.
- [x] `Card.bioactivities()`: derived classes with the rule and parameters, exclusions reported, source bias visible (`documents`).
- [x] `resolve_protein_card(..., chembl={...})` with recorded outcomes. A failure never blocks the card.
- [x] Offline tests on TcTIM and HsTIM, including the 14-molecule overlap. Online test.
- [ ] Small-molecule side: a Deck of the measured molecules (SmallMoleculeCards) and molecule-to-protein navigation. This is the `protein_card` ↔ `small_molecules_deck` interaction of the MOLI vision.
- [ ] A selectivity view between two protein cards, e.g. TcTIM against HsTIM.

## Resolution

Partial: the protein-side MVP was implemented on 2026-09-23. The remaining criteria stay open in uibcdf/sabueso#23.
