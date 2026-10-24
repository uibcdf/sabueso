---
summary: Preserve independent derivation applications and their original output context.
issue: uibcdf/sabueso#156
status: open
opened: 2026-10-24
closed:
verification: tested
area: [knowledge-integrity, relationships, schema, human-exploration]
blocked_by: []
supersedes: []
---

# Distinct relationship derivation applications

The #148 contact prerequisite exposed a core merge defect: differing incoming
derivations disappeared while their sources and qualifier alternatives survived.
Equal rule/parameters/engine records instead unioned independent input sets,
losing the original execution-to-output association. These are Sabueso defects,
not demonstrated source/provider defects or a shared MOLI contract change.

## Stored contract

New relationships constructed with a derivation carry optional
`derivation_applications` in unpublished schema 0.3.14. Each entry keeps:

- `binding: original_output`, the exact derivation (rule, inputs, parameters and
  Sabueso version), original qualifiers and original direct source references;
- optional original qualifier conflicts when a legacy context is captured;
- full output context without claiming every qualifier was derived. A rule's
  parameters may limit scope, as RCSB contacts do with `qualifier_paths`.

Merging preserves every distinct application and the first singular `derivation`
for compatibility. The singular record is not certification of all selected or
alternative values. Exact canonical JSON duplicates deduplicate in deterministic
order. Input-list order, JSON types, scope/output, parameters, rule and engine
differences remain distinct. No union of input sets creates a new execution.
Selected qualifier ordering remains first-seen; all alternatives, including those
from incoming premerged records, survive. Caller records remain detached.

Legacy unique records load unchanged. When merged, their singular derivation and
observed qualifiers/conflicts/support become `binding: recorded_context`. This is
explicitly not recovered original output membership: prior applications may
already have been combined or lost. Migration never reconstructs them and this
addition is explicit-only in `SCHEMA_CHANGES`, without claiming an automatic
refresh can recover historical executions. A fresh refresh produces new bases.
Published schemas/cards, snapshots, source assertions and saved capsules stay fixed.

## Receiving and integrity

Human literal/relationship inspection retains all applications in support, with
raw access to the complete original application context. New saved views retain
those exact records; independent readers use original saved data without Card
reconstruction or current scientific rules. Existing saved views remain original.
This provides traceable support, not the full future derived comparison interface.

Packet terms retain every application's inputs and relationship dependencies in
both full and index support requirements. Packet facts, mapping `@8`, historic
`@6`/`@7` adapters, envelopes and acquisition scope remain unchanged. This corrects
support for new stored relationships rather than changing scientific fact rules.

Output-context physical quantities retain their original units in separate
PyUnitWizard seal columns under `relationships.<predicate>.derivation_applications`.
Both `qualifiers` and legacy `qualifier_conflicts` application contexts are sealed,
as are the merged relationship alternatives when the new application contract is
present. Original legacy seals keep their original column inventory; their
unsealed conflict-quantity limit is separately tracked in [#157](https://github.com/uibcdf/sabueso/issues/157).
External original pins still detect content changes; the reproduced gap concerns
raw Card loading, not a bypass of verified pinned storage. Editing an
application quantity without changing the original seal is refused on load.

## Qualification and remaining work

The final selected scope passes **133 cases / 40.13 seconds**, with pytest-receptor,
twelve workers and fatal RuntimeWarning/SQLite/unraisable guards. One expected
fixture truncation warning is retained. This includes 21 new application cases,
original independent reading, quantities, real public mention intake, old/new
packet scope and shape/schema policy. A preceding 169-case integration scope
passed before the final merged-alternative quantity guard; its count does not
qualify that later change. The full local-original checkpoint passes **6,941 cases / 764.78 seconds**, with
pytest-receptor/twelve workers, thirteen expected fixture warnings and fatal
SQLite/unraisable guards. Runtime/tests/shape are unchanged since that run began;
the schema explanatory note was clarified without changing its parsed structure.
Exact-head CI/governance remains pending under #156; no release qualification is
claimed. Ruff format/lint, 359 Markdown targets/anchors, nine changed Python files
parsed under 3.11, shape/schema alignment (1,794 paths), source registry, fixture
delivery (51 reviewed / 37 protected), dependency routing, local governance and
warning-fatal Sphinx pass. The three public Card walkthroughs and an independent
reader outside the checkout pass with fixture reads and Card reconstruction
forbidden. This is technical acceptance, not measured researcher usefulness. Source hashes, exact gate
results, saved examples, environment and remote receipts belong to
`recovered_work/derivation_applications_20261024/`, owner #156, review at the next
exploration checkpoint or release. Disposable owned scratch is removed after use.

Canonical UTF-8 mapping-result outputs for public 1SUX / 1HTI / 2OMA grow by
6,027 / 3,824 / 9,689 bytes from application metadata at the same SDK. This bounded
source-output observation is not total Card/save/session/RSS/token or general
performance qualification. Whole-output context has a storage cost; do not remove
its original value binding to optimize a preview.

AlphaFold original sequence/MD5/isoform input binding remains the next prerequisite.
The broad annotation/region/aggregate/assembly and nature-profile routes, agent
conformance and measured researcher usefulness remain open before 0.15.0.
Release consolidation remains paused. No new source queries or private pilot reads
are required for this correction.
