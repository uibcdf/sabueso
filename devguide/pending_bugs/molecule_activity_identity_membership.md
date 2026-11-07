---
summary: Keep native copy and parent context separate from explicit molecule identity membership.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-07
closed:
verification: reproduced
area: [exploration, molecule-identity, bioactivity]
blocked_by: []
supersedes: []
---

# Literal activity-record identity within native group context

The pre-capture audit of clean `69c0914` / SDK204 adds one explicitly synthetic
copied measurement to the complete public 493-record TcTIM input. Its literal
`has_bioactivity.object_ref` is `chembl:CHEMBL999999997`, while the focal BTS Card
only joins `chembl:CHEMBL1161789` and `pdb.ligand:BTS`. The copy points to the
original activity by source/id and retains the original parent-molecule context.
This is a synthetic scientific-scope control, not an observed provider error or
a real chemical identity assertion.

The native measurement group retains both source records under original @1 and
opt-in @2. The molecule-context wrapper initially counted two records and exposed
both through drill-down despite the missing copy-alias identity join. The expected
included set has one record; adding an explicit synthetic identity edge admits
the second. Native grouping and parent keys do not supply a chemical identity
join for the wrapper.

The first correction exposed a second scope problem: opening a group narrowed
the request to its native molecule key. That key can be a parent shared by two
literal source records, so the corrected target/group counts admitted two while
drill-down retained only one. Explicit source-record focus must also work when
the native key differs from the selected literal alias.

The maintained correction:

- Selects and counts actual relationship IDs whose literal objects belong to
  the selected explicit identities; no name, parent or copy inference joins them.
- Retains complete original native wires, source statements, groups and context.
  It names included versus context-only IDs and their distinct molecule refs.
- Preserves the originating alias scope through group drill-down and exposes one
  row per exact target/source relationship, retaining repeated native-view paths.
- Leaves broader or multi-alias native summary scalars in the original context;
  it computes no narrower class or quantity. Included record cells keep their
  original classes, values and units. Null states distinguish unsupported scalar
  scope from unstated source values.
- Refuses a foreign literal record focus before native evaluation. Original
  classification/grouping/target-scope policies and saved formats @1–@20 remain
  unchanged; no scientific default adoption is involved.

Evidence remains under `recovered_work/checkpoint_recovery_20261106/`:
`b5-molecule-activity-capture-preflight-3/` reproduces two versus one records;
`b5-molecule-identity-regression-red-1/` records six failures;
`b5-molecule-identity-regression-green-1/` records four passes/two failures;
`b5-molecule-identity-regression-green-2/` passes all six new controls. Their
receptor streams and during-gate source maps remain intact. Complete receiving
passes 51 owning, 291 shared, 383 native/profile and one copied outer case;
51 overlapping copied children add no distinct coverage. The
[selected receipt](../evidence/molecule_activity_identity_checkpoint_20261107.json)
binds the correction; final quality and clean-producer closeout precede capture.
No new genuine original or independent
saved reader has been created; a corrected clean producer must precede capture.

Owning issue delivery belongs to #148, with #112 checkpoint coordination. Retain
the evidence through the corrected producer/original-reader review. The separate
structural investigation flag defect remains #192.

A concrete ordinary technical update to #148 is prepared locally as
`b5-identity-issue148-draft-1.md`. Automatic approval review rejected publication
because the evidenced concrete approval covered only #192. Explicit permission
for this destination/material has been requested. No comment was posted and no
alternative publication route was used; retain the internal report for handoff
until that permission arrives.
