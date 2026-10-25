---
summary: Integrate bounded clinical registry and explicit article metadata into the saved disease journey.
issue: uibcdf/sabueso#108
status: active
opened: 2026-10-20
verification: local_runtime_tested
area: [clinical, attribution, user-journeys]
related: [uibcdf/sabueso#112, uibcdf/sabueso#132]
---

# Saved clinical/reference journey

Pause reconciliation, 2026-10-25: this is the earlier combined disease producer,
now retained alongside the independent
[existing-molecular-input bibliography journey](clinical_bibliography_journey.md).
Their local formats and executions are distinct. The counts and environment in
the 2026-10-20 receipt below remain historical; the
[pause receipt](../evidence/pause_checkpoint_20261025.json) owns current integration
checks. Neither example implements the rich clinical explorer panel required by
the maintainer's complete #148 design.

The disease example now writes `sabueso.disease_entities_example@6`. It adds a
bounded clinical question through existing APIs, without changing the SDK, card
schema, published 0.14.0, source fixtures or shared MOLI contracts. The earlier
[registry checkpoint](clinical_registry_checkpoint.md) owns source-level delivery;
this slice integrates it into the saved user journey under #108/#112.

## Explicit public scope

- Retain the existing two separate disease questions, their MONDO identities,
  related-entity decks, original members and HsTIM context.
- Resolve a separate benznidazole card with `trials={"limit": 1}`. ChEMBL's
  indication records explicitly cite NCT00123916; intervention text is never an
  identity join. The deck member and clinical card are distinct pinned states.
- Request that NCT record's native references separately from its clinical fields.
- Explicitly request Europe PMC metadata for PMID 18585495, 26323937 and 19753491.
  These are three declared metadata operations, not automatic traversal by the
  registry client or substantive article readings.

The frozen public case retains four indication rows, one received study and
fifteen unfetched cited trials. The reference module has three PMID occurrences
and two see-also links. Complete returned article authors include the literal
BENEFIT Investigators collective author; missing issue metadata stays missing.
These are source records and fixture counts, not efficacy or approval findings.
The native `has_results` flag does not establish whether publications exist.

Study and reference fixtures have different data timestamps (2026-09-25 and
2026-10-05). Both remain original; this is not coherent current-source replay.
Europe PMC's service version is not an article revision. Article text, linked
websites and participant data remain unqueried. Access or metadata grants no new
article-text reuse permission. No literature curation or Nextia Evidence is made.

## Save, inspect and independently read

Run the [documented example](../../examples/user_journeys/README.md#diseases-and-related-entities)
from fresh output directories. Inspect `original.report.json` → `clinical` for
`clinical_registry_review@1`, its card pin, saved view, explicit source envelopes
and failure/access scope. Keep the complete bundle and `knowledge.db`.

Scientific values lead through original `investigated_for`/`tested_in`
relationships to their ChEMBL and registry SourceAssertions. Registry reference
envelopes and article metadata keep their own original acquisition traces and
portable attribution, rather than becoming new clinical card assertions. Workflow
credit is checked against the exact original source-operation union.

The reader verifies native clinical values, scope, source bodies, query/operation
bindings, saved card support and original workflow before exporting CSL-JSON and
BibTeX. It calls no clinical view, source getter, derivation or fresh credit
registration. Rehashed semantic changes are refused before export. Complete empty
queries, unavailable local inputs and connector failures retain different states.

Current reacquisition records new executions while leaving original files/pins
intact. Original `@1`–`@5` readers retain their declared gaps. An original `@5`
bundle keeps its pre-clinical scope and format on reacquisition; older originals
remain intact with their already-existing pre-clinical `@5` reacquisition route.
No old question silently acquires new NCT or PMID requests.

## Qualification and remaining work

The [local receipt](clinical_reference_journey_20261020.json) binds the changed
example/tests, public inputs, environment, independent execution and applicable
checks. It distinguishes the genuine preceding `@5` producer from the new `@6`
run. Existing public CI/staged workflows already copy and run this example and
test module unchanged; no workflow or dependency expansion is needed.

Twenty-one new regression cases cover saved clinical science and attribution,
rehashed semantic changes and separate registry/article failed, unavailable and
complete-empty states. All 234 selected cases pass in 186.66 seconds. The complete
repository-input offline suite passes 4,768 cases in 289.92 seconds, with ten
explicit local-only skips and nine expected fixture-failure/truncation warnings.
Both use twelve receptor workers and fatal SQLite/unraisable guards. Ruff format/
check, fixture delivery, dependency preflight, governance and warning-fatal Sphinx
pass. Local Markdown links and both independent execution receipts are checked.

All 37 protected originals are absent in this checkout; `--local-source-inputs`
stops before collection with exit 4. This is an unavailable input scope, not a
passing local-original suite or a replacement for its earlier historical receipt.

This is local editable-source acceptance. Hosted exact-SHA CI, installed public
dependency-floor receiving and staged release qualification remain separate.
Human dossier review and authorized primary assay methods remain open. Follow
the [current completion order](card_exploration_completion_0150.md) for broad
exploration, shared agent/saved behavior, human review and workload qualification.
The [0.15.0 release route](release_consolidation_0150.md) remains paused until that
acceptance. The scope does not close
complete clinical coverage, consumer scientific usefulness or shared recording.
