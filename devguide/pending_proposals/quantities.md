---
summary: Physical quantities in Sabueso — inventory, negotiated units, and alignment with PyUnitWizard's QuantityRecord before schema 0.3.0.
issue: uibcdf/sabueso#32
status: partial
opened: 2026-09-24
closed:
verification: measured
area: [schema, units, persistence, interoperability]
blocked_by: []
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

## Implemented (2026-09-24, schema 0.3.0)

- Quantity nodes in section fields, `resolution`, `min_distance` and
  `measurement.normalized`. The explicit ChEMBL unit vocabulary (`CHEMBL_UNITS`) is in
  place, and nothing is guessed.
- Card-level seal (`quantities`) written by `Card.to_dict()` and verified by
  `Card.from_dict()`. Every public loader now returns a verified `Card` or `Deck`.
- `Card.quantity(path)`. The structures view returns `resolution` as a quantity.
- Dependency on `pyunitwizard>=0.27.0` in pyproject, the recipe and the conda
  environments; `schemas/card_schema_0.3.0.yaml`.
- Tests (`tests/core/test_quantities_offline.py`):
  - units on nodes;
  - the explicit vocabulary;
  - columns in the seal;
  - six kinds of tampering refused;
  - independence from the session policy;
  - a canary through every read path;
  - a static guard against `get_value(` without `to_unit`.

Also implemented:

- Bioactivity classification (`bioactivity_class@2`) reads the normalized nanomolar node.
  `UNITS_TO_UM` is gone. Records without the node go through the same explicit ChEMBL
  vocabulary.
- Thresholds (`active_max`, `weak_max`, `single_point_min`) are quantities in any form,
  including strings such as `"20 uM"`. A bare number is refused, and the thresholds are
  recorded as `{value, unit}` nodes.
- The single-point test concentration is returned as a quantity.
- Converted values are rounded to 12 significant digits (`quantities.converted`). pint
  converts through SI base units, so 20 µM became 19999.999999999996 nM, and a
  measurement exactly on a threshold was classified differently depending on the unit
  the threshold was written in. The test
  `test_the_same_threshold_in_another_unit_classifies_identically` caught it.

Remaining:

- the cross-source 3-or-6-orders-of-magnitude check;
- the pChEMBL consistency check.

## Decisions on the open questions (Diego, 2026-09-24)

1. **Normalized bioactivities are homogeneous.** Concentrations are normalized to
   **nanomolar**, and percentages stay a separate quantity in `percent`. The source's value
   and unit are kept verbatim. Units that cannot be normalized get no normalized node,
   and nothing is guessed. The tagged layout is not needed.
2. **pChEMBL is kept as ChEMBL states it** (it carries their curation), as a named,
   dimensionless kind. A consistency check against the normalized concentration is a
   derived check, never a replacement.
3. **Accessors**: `card.quantity(path)` for scalars, and array quantities for columns, in
   the session's default form.

## Storage design for schema 0.3.0 (released dependency: PyUnitWizard 0.27.0)

- **Quantity nodes** are `{"value": x, "unit": "<canonical name>"}` wherever a quantity is
  stored:
  - section fields (the two molecular weights, TPSA), which keep `source_assertion_ids`;
  - `has_structure` qualifier `resolution` (was `resolution_angstrom`);
  - contact `min_distance` (was `min_distance_angstrom`);
  - bioactivity `measurement.normalized`.

  Missing values (for example the resolution of an NMR structure) are `null`, not
  nodes.
- **One seal per card.** `to_dict()` writes `quantities`, a PyUnitWizard
  `QuantityRecordBundle` whose entries are **columns**. Each column holds every value of
  one quantity path in one unit (key `"<path template>|<unit>"`), in deterministic
  traversal order. Relationships are visited in id order, and lists keep their order.
  A card has about a dozen entries, at about 8 B per value. A bundle entry per scalar
  would cost about 166 B, and a card can hold thousands of contact distances.
- **On load**, PyUnitWizard verifies the bundle, and Sabueso checks that every node
  equals its column. This is cross-checked redundancy, never a fallback. An edit made
  outside the codec, whether to a node or to the bundle, is refused.
