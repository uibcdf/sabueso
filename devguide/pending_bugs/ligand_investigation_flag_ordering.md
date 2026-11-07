---
summary: Reversing repeated ligand occurrences changes a native false/null investigation flag.
issue: uibcdf/sabueso#25
status: open
opened: 2026-11-07
closed:
verification: reproduced
area: [ligands, source-context]
blocked_by: []
supersedes: []
---

# Order-dependent ligand investigation flags

Internal handoff for Sabueso #25/#23 and the B4/B5 molecule-target context work
under #148. No issue update has been published and no aggregation policy changed.

The native `ligands._structure_ligands()` helper groups source ligand occurrences
by component and structure using `previous_flag or current_flag`. For two
occurrences with the same component and structure, `[False, None]` produces
`None`, whereas `[None, False]` produces `False`. The result therefore depends on
input order. The positive controls `[False, True]` and `[True, False]` both produce
`True`.

The observation is reproduced with a minimal synthetic Card, no source clients
and the unchanged native helper. Evidence is retained at
`recovered_work/checkpoint_recovery_20261106/b5-ligand-flag-ordering-observation-1.json`.
Prevalence in public inputs and impact on the complete human/agent journey are
unmeasured. Original per-occurrence flags remain on the captured Card; this
observation concerns the grouped native output.

Before reusing that output in molecule-target browsing, add a permutation
regression and state the grouping policy explicitly, preserving original
occurrences and unknown/negative distinctions. Do not infer identity, efficacy or
experimental independence from the aggregate. Offer this observation as an update
to #25/#23 at the maintainer checkpoint; retain the handoff until publication is
authorized. The current shared-reading checkpoint keeps native code unchanged.
