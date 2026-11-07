---
summary: Reversing repeated ligand occurrences changes a native false/null investigation flag.
issue: uibcdf/sabueso#192
status: open
opened: 2026-11-07
closed:
verification: reproduced
area: [ligands, source-context]
blocked_by: []
supersedes: []
---

# Order-dependent ligand investigation flags

Reported as [Sabueso #192](https://github.com/uibcdf/sabueso/issues/192), linked to
original work #25/#23 and B4/B5 molecule-target context #148. No aggregation
policy changed.

On 2026-11-07 a standalone public bug draft was prepared after checking the owning
issues; #25 is closed and no dedicated duplicate was found. Automatic review
initially rejected publication. The maintainer then explicitly authorized the
destination, action and exact `b5-ligand-flag-issue-draft-1.md` material. Issue #192
was created on 2026-11-07 and its returned body matches that authorized draft.
The new LIVE consumer discloses the original native
limitation and retains its occurrence context; it does not change the policy.

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
experimental independence from the aggregate. Follow up under #192, retaining its
original #25/#23 context. This LIVE increment keeps native code unchanged;
scientific rule/version and historical compatibility remain part of the fix review.
