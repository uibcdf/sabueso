---
summary: Mutable selected fields must not rewrite retained source assertions through shared object identity.
issue: uibcdf/sabueso#166
status: implemented_candidate_receiving
opened: 2026-11-06
verification: two public-input regressions fail before and pass after; neighboring receiving recorded separately
area: [knowledge-integrity, aggregation, source-support]
---

# Selected values and source records must be independent

This is a distinct follow-up to #166's qualified insertion/observation correction.
It does not invalidate or silently expand the earlier receipt.

The existing public ChEBI vincristine mapping exposes the problem on source
`5157fd1`: the selected `annotations.chemical_roles.value` shares its nested
objects with the retained SourceAssertion. Editing the selected first role's name
also changes `asserted_value`; editing the source changes the selection. Both
directions fail independent regression assertions before the correction.

`field_node()` previously retained the supplied value and assertion-ID list by
reference. The resolver returned a stored assertion's selected mutable value, so
the aggregation boundary reintroduced aliasing after `SourceAssertionStore.add`
had correctly detached its input. This is an observed in-memory ownership bug;
no corruption of an already saved pin has been established.

The field factory now deep-copies the selected value and support list. Raw Card
and source edits remain intentionally mutable and create new states, independently.
After a selected edit, the original statement stays original and the chemical
reader reports unsupported membership instead of accepting the edited source as
corroboration. Source-side edits likewise do not rewrite the selection.

No initial value, unit, scientific selection rule, schema or serialized shape is
changed. Existing original snapshots/readers keep their own scope. Receiving
includes source observations, aggregation/resolution, ChEBI mapping, physical
quantities and the new native classification. Broader affected Card/refresh/
historical checks and exact-source hosted qualification remain separately owned.

Owner: the #166 knowledge-integrity domain, coordinated through #148/#112. The
concrete update is prepared for the existing owning issue; actual delivery and
remaining qualification are recorded in the continuation receipt.
