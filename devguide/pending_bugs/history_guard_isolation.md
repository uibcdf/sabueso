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
