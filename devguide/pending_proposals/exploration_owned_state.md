---
summary: Reduce redundant private copies without changing saved meaning or checks.
issue: uibcdf/sabueso#167
status: open
opened: 2026-11-04
verification: selected_local_qualified_exact_source_ci_pending
area: [persistence, performance, scientific-integrity, human-exploration]
---

# Owned exploration state and support

The [component workload study](component_navigation_workload.md) separates fast
interactive reading from complete-session saving and verification. Byte accounting
alone cannot attribute CPU. This continuation profiles the same three-position
synthetic task and removes two observed redundant copy boundaries. It changes no
logical format, native rule, scientific predicate, quantity codec or public API.
The complete broad experience and researcher/workload acceptance remain required;
0.15.0 consolidation stays paused.

## Separate profiles

On the `de10d00` / SDK `0.14.0+159.gde10d00` control, cProfile observes 27.714 s
inside fresh human saving: private restore/verification has 17.225 s cumulative,
preparation 7.551 s, and deep copies 15.557 s. The separate read profile observes
20.872 s: view verification has 12.079 s cumulative and deep copies 11.579 s.
Entries overlap and must not be added. Profiling overhead is substantial; these
numbers are not unprofiled latency or speedup measurements. Original current
science/navigation producers and acquisition remain forbidden during reading.

Cell serialization asks a public defensive support getter to copy data already
captured privately by the Cell. Restoration also deep-copies each view's stored
state even when its decoded bundle was just created locally and has no caller
that can mutate it. Public values/support still need defensive access; the
independent verifier still needs every original comparison.

## Bounded implementation

The private cell recorder keeps its existing independent value copy, including
quantity conversion, and reads the Cell's retained support through a fresh list
wrapper. Public `Cell.value`, `Cell.support` and `to_dict()` keep their defensive
semantics. Custom Cell implementations keep their original `to_dict()` boundary.
No caller gets the transient serialization/comparison record.

Only the local file decoder and newly prepared private serializer transfer bundle
ownership to restoration. The view receives a new top-level state wrapper while
reusing those owned nested values. Direct internal callers keep the default
defensive state-copy path. Ownership is a private boolean argument, never a
persisted flag or a user-controlled saved-file capability. Every manifest/hash,
original source/value/selection/navigation/quantity check still runs. Frozen
verifiers, native rules, source fixtures and Card/schema/migration stay unchanged.
This is ownership transfer of the same original data, not merging entities or
separate observations by equal bytes, and not a shared storage-format change.

## Unprofiled observations

The [machine-readable receipt](../evidence/exploration_owned_state_20261104.json)
records two fresh workers per version/operation in control/candidate/candidate/
control order. The qualified control function bodies are loaded only inside
disposable workers; the shared environment and original file are unchanged.
Actual loaded source hashes are recorded. Reads use the same trusted original;
fresh saves use independent sessions of the same declared task. Filesystem caches
and background load remain uncontrolled.

| Operation | Control wall seconds | Candidate wall seconds | Control mean | Candidate mean | Observed reduction |
| --- | --- | --- | ---: | ---: | ---: |
| Fresh human save | 12.198 /12.918 | 10.548 /10.482 | 12.558 | 10.515 | 16.3% |
| Original read/verify | 8.964 /8.968 | 7.755 /7.713 | 8.966 | 7.734 | 13.7% |

The plain original remains 42,434,469 bytes; no size reduction is claimed.
Independent sessions have random file-local lookup namespaces, so whole-file
hashes are not a cross-session identity test. Same-session control/reference
versus candidate checks establish exact bytes and digest across protein,
molecule quantities, disease and generic literal data. The original reader
checks every retained source/record/position and wire against its trusted digest.
All measured workers use zero owned swap and stay within the resource guard.

These are local observations from two samples/version on one synthetic task.
They do not establish a scaling law, a generic speedup or accepted latency/RAM
budgets. More complex histories, other natures and real researcher work remain
separate acceptance. No default receiving budget is raised or disabled.

## Qualification and ownership

Regression checks cover same-session exact bytes/digests, public nested value and
support isolation, registered quantities versus literal lookalikes, inert repeat
saving, caller-owned private restore state and resealed source-support changes.
The selected local gates pass **1,041 unique cases /32 files**, serial through
pytest-receptor, with zero owned swap and a sampled peak of 850,509,824 bytes.
All 78 protected original modules stay byte-identical. This is not a full-local
suite checkpoint. The new tests also enter the installed-consumer payload; copied generic receiving
needs no checkout fixture access. Four further fresh processes receive human
and accumulated agent originals from control/candidate producers with complete
original binding parity, without acquisition or current scientific production.
Select affected original-format, human/agent,
quantity, transport, large-original and persistence gates from `TESTS.md`.

Retain profiles, source/input hashes, comparisons and actual resource/test receipts
under `recovered_work/exploration_profile_167_20261104/`, owner #167/#148/#112,
reviewed at exact-source qualification or before 0.15.0. Remove completed owned
scratch and raw diagnostic exports after their final required use. No private
pilot content or new provider request is needed. Qualify the final committed
editable and unskipped exact-source CI/governance before calling that checkpoint
complete; an earlier source's passing CI does not qualify the changed runtime.
