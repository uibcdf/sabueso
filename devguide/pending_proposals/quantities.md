---
summary: Physical quantities in Sabueso — inventory, negotiated units, and alignment with PyUnitWizard's QuantityRecord before schema 0.3.0.
issue: uibcdf/sabueso#32
status: open
opened: 2026-09-24
closed:
verification: measured
area: [schema, units, persistence, interoperability]
blocked_by: [uibcdf/pyunitwizard#82]
supersedes: []
---

# Physical quantities in Sabueso

## What

Decisions (Diego, 2026-09-24; recorded on uibcdf/sabueso#32):

1. When Sabueso is asked for information that is a quantity, it **returns a quantity**
   (PyUnitWizard), not a bare number.
2. Canonical unit strings are ones PyUnitWizard parses and that round-trip, in the
   unambiguous long form (`"nanomolar"`, never `nM`/`nm`).
3. The priority is that no MOLI tool can read 3 nM as 3 pM. Serialization follows the
   platform design owned by PyUnitWizard: **`QuantityRecord`**, an inert native form with
   negotiated containers, an integrity digest, a reader handshake and no defaults
   (uibcdf/pyunitwizard#82; design record and alternatives review in #83; routing in
   uibcdf/moli#13 and uibcdf/molsyssuite#46; contract in uibcdf/moli#12).

This document covers the Sabueso side only. Questions about the format itself go to
uibcdf/pyunitwizard#83, not here.

## Inventory (code on `main`, 2026-09-24)

| Path | Where it is stored | Unit today | How the unit is expressed | Negotiated unit | Kind |
|---|---|---|---|---|---|
| `properties.physchem.molecular_weight` (small molecule) | card field | Da | `source_metadata.unit` (ChEMBL, PubChem) | `dalton` | molar mass / mass |
| `sequence.molecular_weight` (protein) | card field | Da | `source_metadata.unit` (UniProt) | `dalton` | mass |
| `properties.physchem.tpsa` | card field | Å² | **nowhere** | `angstrom ** 2` | area |
| `relationships.has_structure` qualifier `resolution_angstrom` | relationship qualifier | Å | **field name** | `angstrom` | length (resolution) |
| `has_structure` assertion `resolution_combined` | SourceAssertion `asserted_value` | Å | implicit (RCSB) | stays verbatim | — |
| ligand contacts `min_distance_angstrom` | structure mapping | Å | **field name** | `angstrom` | length (distance) |
| bioactivity `value` + `units` | `has_bioactivity` assertion | per measurement (nM, µM, %…) | **verbatim source string** | tagged layout or normalized nM; see open question 2 | concentration, or a percentage |
| bioactivity `pchembl` | `has_bioactivity` assertion | −log₁₀(M) | implicit | not a unit: a named **kind** with its definition | pChEMBL (logarithmic) |
| `test_concentration_uM` | derived view (not stored) | µM | **field name** | returned as a quantity | concentration |
| thresholds `active_max_uM`, `weak_max_uM` | parameters and derivations | µM | **field name** | accepted as quantities | concentration |
| `single_point_min_percent` | parameter | % | field name | `percent` | dimensionless ratio |
| `properties.physchem.logp` | card field | — | — | dimensionless | log partition coefficient (logarithmic) |
| `properties.physchem.isoelectric_point` | schema only (no mapping yet) | pH | — | dimensionless | pH (logarithmic) |
| `hbd`, `hba`, `rotatable_bonds`, `aromatic_rings`, `ro5_violations`, `sequence.length` | card fields | counts | — | not quantities: integer counts | count |
| feature positions, ranges | card fields | residue indices | — | not quantities | — |

Facts that bound the migration:

- **SourceAssertion ids** hash `(source, record_id, field_path, asserted_value)`. Keeping
  `asserted_value` verbatim keeps every id.
- **Relationship ids** hash only *identity* qualifiers (`IDENTITY_QUALIFIERS`). Reshaping
  `resolution_angstrom` changes no `REL_` id.
- **ChEMBL already flags unit errors.** `data_validity_comment` includes *Potential
  transcription error* (values differing by exactly 3 or 6 orders of magnitude) and *Non
  standard unit for type*. Sabueso keeps the field and turns it into a bioactivity flag.
- **UDUNITS does not know `nM`, `Da`, `dalton` or `M`** (checked with cf-units 3.3.1).
  Source strings always go through an explicit vocabulary.

## How (proposed)

1. **Schema 0.3.0, before release 0.1.0.** There are no published cards yet, so migrating
   costs only fixtures and tests. Quantity fields take the `QuantityRecord` **descriptor
   shape**: canonical `unit`, `si` (factor, offset, exponents), `ucum` and optional
   `kind`. At card level they use the **bundle** layout, a single seal for many scalars.
   Unit-in-name fields move to neutral names (`resolution`, `min_distance`) carrying a
   descriptor. TPSA gains its unit.
2. **The digest is added when `QuantityRecord` ships in PyUnitWizard.** The shape is the
   same, so the change is additive: a new field, not a reshape. Sabueso does **not**
   implement a private codec, because two implementations of one contract diverge (the
   lesson of ArgDigest's passport, uibcdf/pyunitwizard#83).
3. **Accessors return quantities.** Examples: `card.quantity(path)`, and bioactivity views
   returning array quantities per column rather than lists of scalars. PyUnitWizard is
   imported lazily on first use, so `import sabueso` does not pay the 0.3–0.5 s pint
   registry build.
4. **Conversions are explicit.** `UNITS_TO_UM` and the test-concentration parser convert
   with PyUnitWizard and an explicit `to_unit`. Sabueso never sets a PyUnitWizard policy
   (uibcdf/moli#11).
5. **Source vocabularies.** A Sabueso table maps each source's unit strings (ChEMBL
   `standard_units`, and later others) to canonical names. An unknown string is recorded
   as unconvertible, never guessed.
6. **Domain check.** A cross-source check flags equivalent measurements that differ by
   exactly 3 or 6 orders of magnitude, in the same way as ChEMBL's transcription-error
   flag. This covers the one error class no format can detect: a source that is wrong and
   consistent.

## Checkpoints and tests

- A conformance test runs card building and reading under a non-default PyUnitWizard
  session policy (Å, ns). It must give the same stored numbers.
- A static guard forbids `get_value(` without `to_unit` in Sabueso's boundary modules.
- A canary test writes a card with 3 nM and asserts that every reader path returns 3 nM.
- A migration test takes every 0.2.0 fixture to 0.3.0 and checks that the ids are
  unchanged.

## Possible future problems

- **Divergence from the final `QuantityRecord` specification.** Step 1 uses the draft
  descriptor shape (`qrec/0.2`). If PyUnitWizard changes it, Sabueso migrates again.
  Mitigation: adopt only the descriptor keys that the draft marks stable, and track #82.
- **A runtime dependency and its cost.** Returning quantities makes PyUnitWizard, and
  therefore pint, a runtime dependency. The first quantity costs 0.3–0.5 s. Lazy import
  keeps it off `import sabueso`, but the first call pays it.
- **Floating-point noise.** Conversions add noise (`5 pM → 4.9999999999999996e-06 µM`).
  Converted values must never feed ids, hashes or stated-precision comparisons.
  `asserted_value` stays verbatim.
- **Tolerance of SI factors.** Unit definitions differ between libraries by up to ~7e-7
  (UDUNITS `u` against pint's dalton), which is close to the 1e-6 tolerance. Any tolerance
  change must be justified with measurements.
- **Logarithmic kinds** (pChEMBL, logP, pH) are not units. Until PyUnitWizard defines
  named kinds (#83, open question 3), Sabueso keeps them dimensionless and names them
  explicitly.
- **Heterogeneous bioactivity units.** Whether normalized values should be homogeneous
  (for example nM, with the source unit kept verbatim) or use the tagged layout is open
  question 2 below. The tagged layout is implemented in PyUnitWizard only when a consumer
  needs it.

## Open questions

1. Accessor API names and return forms: the session's default form, or pint only?
2. Normalized bioactivities: homogeneous (for example nM) plus the verbatim source unit,
   or the tagged layout? Percent-inhibition values cannot share a unit with potencies.
3. Whether `pchembl` should be recomputed from the normalized concentration or kept as
   ChEMBL states it (ChEMBL's value carries its own curation).
