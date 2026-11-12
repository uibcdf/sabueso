---
summary: Restore LIVE consumers after temporary historical-reader test guards.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-12
area: [testing, historical-reading, integration]
---

# Historical-reader guards survive through late imports

The complete local `f772e25` / SDK262 attempt exposes five failures in later
protein-context and sequence-change producer tests. Both raise the temporary
sequence-history guard, despite its pytest monkeypatch already being restored.
The source cohort separately stops at its 6 GiB scratch ceiling; its incomplete
stream is not a complete passing checkpoint.

A fresh-process reproduction confirms two retained aliases:
`card_sequence_change_exploration.materialize` and
`card_protein_context_access.make_derivation`. A consumer imported while its
provider is patched keeps that function when only the provider is restored.
Actual sequence-change and protein-association answers then fail with the guard.
This is test isolation, not an observed production scientific defect.

A bounded cold-import audit of eight historical helpers finds the same mechanism
in the molecule-activity and saved-literature helpers. The other five controls
show no retained aliases in that audit's eight inspected consumer families.
The three affected helpers now import consumers before patching providers and
explicitly guard/restore their LIVE aliases. Original assertions, independent
readers, source/client/network prohibitions and all frozen inputs remain fixed.

The fresh-child regression checks forbidden LIVE adapter/presentation calls
inside each of the three guards, exact alias restoration afterwards and actual
sequence, association, variant and knowledge-comparison questions. The original
red reproduction and both audit snapshots remain under
`recovered_work/checkpoint_recovery_20261106/b7-current-full-checkpoint-1/`.
The second audit records no retained aliases in its inspected families.

The [selected receipt](../evidence/history_guard_lifetime_checkpoint_20261112.json)
records 13 passing controls, including all three cold regressions and the original
five affected producer cases. Complete current source qualification remains
pending its fresh recovery. Keep
the original five failures and scratch stop, the corrected selected gate and
the eventual full checkpoint separate. #148 owns isolation and #112 coordinates
integration/CI; no new issue comment or hosted run is authorized by this fix.

## LIVE fixture and wider cold-consumer follow-up

The fresh clean `88b3fb2` attempt completes its 8,335 ordinary cases with 8,324
passes and eleven failures in the variant exploration module. The LIVE sequence
fixture patches the variant provider before its presentation module is imported;
that module retains the temporary function afterwards. There is no resource stop.

The wider audit covers twelve guards/fixtures and ten materializer families,
also checking all loaded core-module globals for leaked test functions. It finds
further aliases in saved-bioactivity and mixed bioactivity/literature guards,
including renamed imports inside the molecule adapter. The molecule history
guard additionally preloads/guards the bioactivity presentation consumer.
Affected helpers now import those consumers before installing temporary guards;
the LIVE sequence fixture explicitly restores its presentation alias too.

The [follow-up receipt](../evidence/guard_alias_followup_checkpoint_20261112.json)
records **116 cases passing together** with four workers on unchanged mapped
inputs, including both complete LIVE modules and all cold regressions. Fifteen
overlapping controls also pass with eighteen byte-identical copied modules,
external working/scratch directories and no data assets. The copied client is
removed after verification. No production code, existing scientific test
predicate, original input or frozen reader changes.

The new control initially expected only `AssertionError`; one existing guard
uses `pytest.fail.Exception`. Its corrected check accepts those two explicit
types, and the final unchanged-source selection passes completely. Preserve
that failed control, the original complete ordinary failure and passing gates
separately. Complete clean-source recovery and exact-head hosted gates remain
pending; raw evidence belongs to #148/#112 under
`recovered_work/checkpoint_recovery_20261106/b7-current-full-checkpoint-2/`.

## Original writer presentation under the stricter guard

The clean `4d170ce` / SDK264 attempt closes 1,553 native, 8,335 ordinary and
1,151 modern-history cases successfully. Its next complete 55-case molecule-file
cohort reports 44 failures and eleven passes, with one cause and no resource
stop. The stricter science guard also blocks the molecule/bioactivity `view`
functions used by the retained-result writer. That writer already replaces
materialization with exact original-cache lookups, but cannot reach them while
presentation itself is forbidden. This is a test-helper regression introduced
by the guard correction; no production scientific defect is observed.

Only `_retained_writer` in the original-file test module changes. It preserves
the three presentation entry points before installing the science guard and
restores them within its reenactment scope. Scientific providers, acquisition,
Card construction and unretained cache requests remain forbidden. Independent
receivers keep their separate strict LIVE-UI guard. The other 1,352 mapped source
inputs and every other top-level AST in the changed module remain unchanged;
the original positive/boundary assertions and frozen inputs are not edited.

The red/green synthetic helper probe, original complete failed stream and exact
correction map remain under
`recovered_work/checkpoint_recovery_20261106/b7-current-full-checkpoint-3/`.
The complete original writer and remaining history/copied receiving must pass
before this correction supplies a full local code checkpoint. Earlier passing
cohorts retain their actual input epoch; do not describe a composition across
this helper correction as one unchanged test-input execution.
