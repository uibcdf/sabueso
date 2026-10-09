# Sabueso — Checkpoint

Current state and resumption guidance. Historical receipts belong to the
[archive](archive/README.md); development order belongs to [ROADMAP.md](ROADMAP.md).
Last updated: 2026-10-08, consolidation after completed local-work recovery (#112).

## Resume here

The maintainer authorized the consolidation order in the
[global audit](pending_proposals/post_recovery_global_audit.md): fixture delivery,
guide structure, explicit source maturity, bounded scientific journeys and parallel
consumer coordination. Keep the approved foundational and pilot-driven routes.

| Work | Current state | Next acceptance |
| --- | --- | --- |
| Fixture delivery | 49 repository inputs; 37 protected local originals; public absence suite passes with originals restored and verified | Requalification of local delivery only with applicable declarations; retain both test scopes |
| Guide | Six complete entry-document snapshots archived; common guidance separated from provider details; warning-failing Sphinx passes | Keep current guidance true alongside the next implementation |
| Source maturity | Generated native/mapping/enricher/input scope; 83 `in_use`, 37 deferred, 11 evaluating; 24 declared enricher instances | Integration by scientific question; portfolio-wide live health and consumer acceptance remain unassessed |
| Scientific journeys | Protein example `@2` retains active-site residue/composition support; independent legacy reader and reacquisition pass | Next bounded clinical bibliography/query/explanation work; complete derived-operation observation remains open |
| Consumers | Bounded private revalidation passes 14 original cells, saved reading and replay; taxonomy observation/fixture-state follow-up passes local and exact-SHA CI; ready MOLI correction in PR #65; Nextia #1 retains Evidence ownership | Extend declared consumer scope #132; broader #108/owner acceptance and SQLite lifetime #133 stay open |

The accumulated recovery/consolidation code checkpoint is published as
`dc4642414c46744f39d85cb666094b0d52dd705a`, with
[15/15 exact-SHA CI jobs](https://github.com/uibcdf/sabueso/actions/runs/37838441204)
and [passing governance](https://github.com/uibcdf/sabueso/actions/runs/37838441190),
inspected with gh-run-receptor. The
[publication receipt](pending_proposals/post_recovery_public_checkpoint.md)
and [machine-readable record](pending_proposals/post_recovery_public_checkpoint.json)
retain both input scopes and the portability corrections. No new release is claimed.
Current scoped acceptance and measurements are in the
[consolidation report](pending_proposals/post_recovery_consolidation.md).
The [bounded consumer report](pending_proposals/private_consumer_revalidation.md)
records live versus replayed inputs, persisted support, measured costs and the
taxonomy observation follow-up and corrected memory measurement. Overall private workflow acceptance stays
open; no installed artifact or scientific Evidence is qualified by this exercise.
The follow-up code `a05e0a3132a43bf3a7bd53b94217db9690f39693` is published with
[15/15 exact-SHA CI jobs](https://github.com/uibcdf/sabueso/actions/runs/37847914597)
and [passing governance](https://github.com/uibcdf/sabueso/actions/runs/37847914659),
inspected with gh-run-receptor. The [sanitized receipt](pending_proposals/taxonomy_followup_checkpoint.json)
retains local and remote scopes, measured cost correction and remaining limits.

## Release and schema

**Published release: 0.13.0**, qualified source/tag
`7e78d078111ac8dd51e08746c3818108ebd825a4`, released 2026-10-05 (#121).
The promoted `sabueso-0.13.0-py_0.tar.bz2` has SHA-256
`1e8f80375cbc08c04df452dbbb55084dc4ff41c6242fbb07e3479f0cd4c7361c`.
All 12 installed Linux/macOS-arm64/Windows × Python 3.11–3.14 lanes passed
613 receiving cases and the public workflow; clean public installation and
identical-tag Zenodo archival were verified. Complete
[publication receipt](../devtools/conda-build/receipts/sabueso_0.13.0_public_2026-10-05.json).

Published schema **0.3.12** and its shapes/frozen cards remain immutable.
Schema **0.3.13** is frozen from the clean installed preliminary Conda writer
for the staged **0.14.0** candidate (#134); stable publication is pending. The
[release notes](../devtools/conda-build/release_notes_0.14.0.md) define its scope
and limits. Every further shape change follows [SCHEMA.md](SCHEMA.md), migrations
and recorded-shape gates, preserving the frozen shape.
Earlier release receipts remain in `../devtools/conda-build/receipts/`.

## Capabilities delivered in 0.13.0

Source-supported identity, conflict-preserving cards/decks, versioned derived views,
quantities, curation and pinned persistence form the established knowledge model.
0.13.0 adds broader required acquisition observation, original literal extraction
and explicit article bibliography, pinned derived explanations, integrity/count
corrections and a persisted application producer/reader/reuse exercise.
See [the public API](PUBLIC_API.md),
[release notes](../devtools/conda-build/release_notes_0.13.0.md) and
[design/implementation matrix](pending_proposals/design_implementation_review.md).

## Current development

The previously pushed post-release code checkpoint (`413cdf6`, followed by
`74c8c3d34299a59784b29937361be03da2c29640`) has
[15/15 exact-head CI jobs](https://github.com/uibcdf/sabueso/actions/runs/37438528677)
and [passing governance](https://github.com/uibcdf/sabueso/actions/runs/37438528644).
It implements the three independent SDK journeys, molecular knowledge-state
correction, exact disease membership/build support and conservative admission,
additional source observations, ChEMBL indication references and explicit
ClinicalTrials.gov/Europe PMC observation/bibliography (#122–#128).
Public-package delivery of those fixes remains open.

The published development checkpoint adds bounded native-source readers/mappings, supplied original
snapshots, canonical residue/source-sequence knowledge and composition, isoform/
exact-sequence candidates, notebook reports and additional UniProt/PubChem/ChEBI
annotations. Source-specific subjects and revisions remain explicit. New native
access is not automatic card integration. Details:
[development API](PUBLIC_API.md#development-recovery-after-0130),
[native-access reference](sources/NATIVE_ACCESS_REFERENCE.md), and
[recovery closure](archive/local_work_2026-07/closure.json).

**Public test systems:** TcTIM/HsTIM and [HK2/P52789](HK2_TEST_SYSTEM.md).
HK2 rebuilds 239 SourceAssertions from its unchanged public UniProt fixture,
original acquisition 2026-09-23. It is UniProt-only; further native source inputs
are needed before claiming a multi-source HK2 card.

The 87 historical originals were reviewed and verified; the maintainer-authorized
stash deletion completed 2026-10-08. The stash list is empty. Historical cards,
notebooks and ligand hints are not current fixtures or confirmed knowledge.
Complete evidence stays in the [recovery archive](archive/local_work_2026-07/README.md).

## Package layout

- `core/`: cards/decks, assertions/relationships, selection, quantities, derived
  views, curation/extraction, packets, snapshots, stores and migration.
- `resolver/`: entity/field resolution and packaged selection/source metadata.
- `tools/db/`, `mappings/`, `enrichers/`: native access, transformation and declared
  card contributions, respectively; shared services remain in `tools/db/`.
- `tools/card/`, `tools/deck/` and other public tools: construction, storage,
  queries/navigation, source snapshots and notebook reports.
- `_private/`: ArgDigest argument digesters and SMonitor diagnostics.
- `schemas/`, `temp_data/`, `tests/`: schemas/shapes, declared fixtures/frozen cards,
  and scoped verification. Local-only originals are protected from Git delivery.
- `examples/`, `docs/`, `devguide/`: scientific SDK journeys, user documentation
  and maintained implementation/design guidance.
- `tools/`, `devtools/`: repository gates, build/release and governance tooling.

Core, resolver, native/public tools, mappings, enrichers and argument digesters
above are relative to `sabueso/`; schemas, fixtures, tests and documentation are
repository directories. See [ARCHITECTURE.md](ARCHITECTURE.md) for semantic ownership.

## Quality baseline

Use editable Python **3.14.7** in **`molsyssuite@uibcdf_3.14`**, verified outside the
checkout. Sabueso's runtime requirements are satisfied in the shared development
environment; separately recorded Amber/preparation dependency conflicts remain
outside Sabueso's source behavior. Do not repair unrelated packages by changing
shared versions without their owner-local compatibility evidence.

Pre-consolidation full local checkpoint: **5,554 passed / 173.00 s**, ten expected
fixture warnings; architectural audit selected gate: **395 passed / 128.46 s**.
Those precede the explicit public/local input split and subsequent implementation.
Earlier consolidation gates and scope are recorded in the consolidation report.
Public input qualification passed **4,021 tests / 130.19 s**, ten explicit native
skips and ten expected warnings, with protected originals physically absent.
Full verified local-original qualification passed **5,574 tests / 164.11 s**,
ten expected warnings and no skips. Both scopes include all three independent
scientific journeys; complete receipts are in that report.
Final public checkpoint `dc46424` passes **5,576 local-original tests / 175.56 s**,
ten source-fixture warnings and no skips. Its nine remote repository-input lanes
each pass **4,023 tests**, ten native skips and 26 online deselections; four
installed public Ackredit receiving lanes each pass 965 cases. Git checkout-byte,
UTF-8 metadata and bounded pytest case-name regressions protect Windows validation;
notebook schema validation declares its `nbformat` test dependency. Linux Python
3.14.8 additionally reports 66 unclosed SQLite connection warnings tracked in
[#133](https://github.com/uibcdf/sabueso/issues/133). See the publication receipt
for exact-SHA/platform results, warning scopes and qualification limits.
Local pytest uses **pytest-receptor and 12 workers**; exact remote CI inspection uses
gh-run-receptor when a code checkpoint is pushed. See [TESTS.md](TESTS.md).
The final taxonomy-operation/fixture-state follow-up passes **173 selected tests / 23.43 s** and
**5,592 full local-original tests / 196.16 s**, ten expected fixture warnings,
using the same environment/receptor/12 workers. Its nine remote repository-input
lanes each pass **4,039 tests**, ten native skips and 26 online deselections;
four installed public Ackredit 0.9.0 receiving lanes each pass **981 cases** and
the public workflow. Eight repository lanes report six expected fixture warnings;
Linux Python 3.14 reports those six plus **67 unclosed SQLite warnings** (#133).
The receiving lanes report two expected fixture warnings each. This qualifies the
exact follow-up code, not a new Sabueso release or overall private-pilot acceptance.

## Open work

Follow the [immediate resumption sequence](ROADMAP.md#immediate-resumption-sequence).
The recovered checkpoint's CI is qualified. Bounded private MOLI consumer
revalidation under [#132](https://github.com/uibcdf/sabueso/issues/132) now passes
14 original cells, exact saved-state reading and original-answer replay.
The exercised NCBI Taxonomy acquisition-operation gap under
[#108](https://github.com/uibcdf/sabueso/issues/108) is implemented and rechecked
in live/replayed private scope, with original scientific content retained.
Its exact-SHA CI is qualified; extend the existing consumer routes with declared
source scope before broadening sources or APIs. The previously reported 942 MiB
counter predates SDK imports; matched Linux sampling shows 132/129 MiB live/replay
with profiler overhead, rather than a new 942 MiB SDK allocation.
Keep their checkout read-only and their content/results private. Broad profiles,
full packet acquisition, unavailable historical pins and overall acceptance remain
unqualified; see the [bounded report](pending_proposals/private_consumer_revalidation.md).
Independent SDK acceptance remains useful while consumer-owned work proceeds.
Queries/non-protein packets (#71), derived explanations (#91), complete observed
pipeline/bibliography (#108), finer use-term filtering (#29), peptide identity
and selected source integration remain bounded open work. Seven deferred recovered
providers have [explicit reactivation conditions](pending_proposals/historical_provider_reactivation.md).
Release qualification follows [the staged route](../devtools/conda-build/README.md).

## Release qualification

Published receipts prove only their exact source and artifact. The recovered code
checkpoint and taxonomy follow-up are qualified at `dc46424` and `a05e0a3`;
subsequent code revisions need their own
applicable gates and exact-SHA CI. Staged installed-package/platform gates remain
required before release.
Older diagnostic wheels, local native inputs and historical pilot execution are
not qualification of a new release or private-consumer acceptance. See
[the audit](pending_proposals/post_recovery_global_audit.md).
