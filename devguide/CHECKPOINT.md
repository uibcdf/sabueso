# Sabueso — Checkpoint

Last updated: **2026-10-26**, ligand-site comparison exploration following pause reconciliation
(#112). This is the resumption entry point. The complete preceding chronology is
[archived](archive/CHECKPOINT_before_pause_20261025.md); original scientific,
source and release receipts remain unchanged.

## Resume here

1. Read this checkpoint, [ROADMAP, Immediate resumption sequence](ROADMAP.md#immediate-resumption-sequence),
   then the [complete exploration inventory](pending_proposals/card_exploration_completion_0150.md).
   The original foundational and pilot-driven routes still apply together.
2. Confirm a clean `main` matching `origin/main` with `git status --short --branch`,
   `git fetch origin`, and `git rev-list --left-right --count HEAD...origin/main`.
   Do not overwrite another contributor's later work or apply an old stash.
3. Read the [pause receipt](evidence/pause_checkpoint_20261025.json) and its exact
   input/code/check scope. Final push CI/governance results are indexed by source
   SHA in [Actions](https://github.com/uibcdf/sabueso/actions) and the
   [owning coordination issue](https://github.com/uibcdf/sabueso/issues/112).
   Reproduce captures with the [recovery procedure](TESTS.md#recovering-deferred-ci);
   a historical receipt or skipped/cancelled run never qualifies a newer source.
4. Continue **#148's broad human/agent Card exploration**, starting with the
   remaining region/site/instance/aggregate/assembly transitions after the
   coordinate-admission correction. Use the existing named readers, original
   support, explicit axes/revisions and saved-reading contracts. Then follow
   the inventory's activity/assay/document/literature, clinical/classification,
   variant/comparison/association and combined human/agent acceptance order.
5. Keep scientific review separate: the [public worksheet](pending_proposals/scientific_review_packet_20261020.md)
   and [source drafts](pending_proposals/located_source_review.md) await actual
   scientist decisions. Authorized primary methods for the three identified
   assay articles remain needed. Agent preparation and metadata do not establish
   experimental comparability, efficacy or Nextia Evidence.

The maintainer confirmed that all ongoing implementations and fixes target
**0.15.0**. Complete the entire broad exploration design and validated human
experience before resuming release consolidation. Candidate selection, schema
freezing, staging and publication remain paused. There is no separate 0.14.1
backport workstream. Workload measurement belongs to that completion scope; it
does not replace the maintainer's newer exploration priority.

## Published and development state

| Scope | State |
| --- | --- |
| Published package | **0.14.0**, source/tag `78623d0`; its installed OS/Python matrix, public install and Zenodo archive retain their own [immutable receipt](../devtools/conda-build/receipts/sabueso_0.14.0_public_2026-10-09.json) |
| Published schema | **0.3.13** and earlier schemas/cards/shapes remain immutable |
| Development schema | **0.3.14**, unpublished, 1,938 recorded paths; coordinate/request scope, contact/model inputs, derivation applications and native feature identity follow [SCHEMA](SCHEMA.md) and migrations |
| Packet history | Default `packet_aspects@11` applies source-bound canonical ligand overlap; historical mappings keep their frozen projections, original support and semantics |
| Shared contracts | Sabueso records Knowledge/SourceAssertions; MOLI owns shared contracts, Nextia owns Evidence. Similarity is never identity; unknown/unqueried/failed scope remains explicit |
| Release target | 0.15.0, with the full exploration and human-acceptance gate in the [scope](pending_proposals/release_consolidation_0150.md). The [notes draft](../devtools/conda-build/release_notes_0.15.0.md) is incomplete preparation, not a candidate or release |

## Latest implementation and qualification

Upstream `680c6a1840783d4556f3f0d24fa407001f5e262c` includes the
[coordinate-admission correction #163](pending_bugs/ligand_overlap_coordinate_scope.md):
`ligand_site_coordinate_scope@1`, `annotated_site_overlap@3`, exact canonical
input support in full/index packets and a test boundary that preserves literal
source keys. Unsupported or conflicting coordinates stay uncomputed; partial
positives cannot turn unknown inputs into a negative result. The earlier
incomplete local run and cancelled CI are diagnostic history, not passing gates.

Its [CI](https://github.com/uibcdf/sabueso/actions/runs/40149749936) passes **15/15**
and [governance](https://github.com/uibcdf/sabueso/actions/runs/40149749833)
passes **1/1** on that exact SHA. Full receptor captures, member hashes and all
thirteen test summaries were checked during pause preparation: nine public
OS/Python lanes pass 5,626 cases each (ten local-only skips, 26 online deselections);
four installed public-Ackredit lanes pass 1,431 each. Coverage publication passes;
external coverage-service visibility is not independently qualified. These results
qualify that source, not the new combined-example closeout automatically.

The pause also reconciles the earlier local work with later upstream delivery:

- The [combined disease/clinical example](pending_proposals/clinical_reference_journey.md)
  writes `sabueso.disease_entities_example@6`: a separate pinned clinical card,
  one explicitly cited NCT, three explicit article metadata queries and original
  saved reading. Its original `@5` question is not broadened on reacquisition.
- The independent [clinical bibliography journey](pending_proposals/clinical_bibliography_journey.md)
  consumes an existing molecular bundle and retains a separate clinical workflow.
  It remains available alongside the combined producer; their local formats and
  original executions are distinct. Neither is a rich Card explorer clinical panel.
- The [2026-10-20 scientific preparation receipt](pending_proposals/scientific_review_preparation_20261020.json)
  and [combined-example receipt](pending_proposals/clinical_reference_journey_20261020.json)
  remain historical, with their exact source/environment and generated hashes.
  Later source changes invalidate reuse of their counts as current qualification.

Current integrated local gates and code/input fingerprints are recorded in the
[pause receipt](evidence/pause_checkpoint_20261025.json): **211 selected integration
cases pass in 329.76 seconds**, with twelve receptor workers and fatal runtime/
SQLite/unraisable guards. Ruff, fixture/dependency/governance checks, 402 local
Markdown links/anchors and warning-fatal Sphinx pass. That Diego receipt has all 37 local-only originals absent; it claims no new
local-original suite. This Liliana checkout has all 37 originals with matching
hashes on 2026-10-26; current gate results are recorded separately. The unskipped closeout
push receives its own exact-SHA CI and governance checks; the post-push result
belongs to that SHA in Actions and #112. Installed release-artifact qualification
and human usefulness remain separate from source CI.

The [first human ligand-site comparison pane](pending_proposals/card_ligand_site_comparisons.md)
now adds explicit readable comparisons and original annotation/contact/source,
structure-local component context and assembly-context links. It reuses native
science once per captured protein and keeps partial/uncomputed scope visible.
Specialized agent selection and historical saved comparison reading remain open;
the pane and its originating navigation explicitly refuse saving. No stored
schema or scientific rule changes. Selected qualification passes 732 integration cases, 208 presentation/quantity
cases and 100 final scope/context cases with twelve receptor workers. Full final
and remote qualification are recorded separately in the owning report and #148; broader completion and release remain paused.

## Open work and boundaries

| Owner | Remaining work |
| --- | --- |
| #148 | Broad scientific/nature panels, region/model-fragment/instance/aggregate/assembly transitions, shared saved navigation and compact agent parity; actual researcher walkthroughs and agreed workload budgets |
| #163 (closed) | Exact-source qualification/closure is complete at `680c6a1`; preserve canonical admission and original support while broader #148 work continues |
| #108 / #112 | Broader source/operation/bibliography coverage and coordination; both clinical examples are bounded demonstrations |
| #132 / #92 | Human dossier usefulness, located-statement review, authorized assay originals and source-specific protocol interpretation |
| MOLI / Nextia / MolSysSuite | Shared recording/consumer decisions, Evidence and modeling/correspondence remain with their owners; no shared contract or private pilot content is changed here |

The [completion inventory](pending_proposals/card_exploration_completion_0150.md),
[public API](PUBLIC_API.md), [schema](SCHEMA.md) and [tests](TESTS.md) own detailed
current contracts. Consult the [archived checkpoint](archive/CHECKPOINT_before_pause_20261025.md)
for preceding dated implementation/qualification history, not for next-step order.

## Inputs, environment and retained resources

Use Python 3.14 in `molsyssuite@uibcdf_3.14`, editable Sabueso and participating
local packages, and pytest through the receptor as [TESTS](TESTS.md) specifies.
Verify imports and editable metadata outside the checkout after synchronization.
The public input policy has 51 reviewed repository entries and 37 protected
local-only originals. Their availability is checkout-specific: a missing original
is not recovered by Git, and default repository-input tests cannot qualify it.
Never reconstruct it or infer source absence from that gap.

The pause receipt records current local availability and both test scopes. Earlier
local-original counts remain historical; newly absent inputs do not erase those
receipts. Public TcTIM/HsTIM/HK2 fixtures are the reproducible examples. Primary
article methods still require authorized originals; public metadata is insufficient.

Generated scientific bundles and full CI captures retained by this work have owner
**Sabueso #112** and the review trigger **resumption or 0.15.0 acceptance**. Their
locations/hashes are in the pause and dated receipts. `/tmp` paths are optional
local evidence, never the sole resumption mechanism: commands, source, fixtures,
GitHub run IDs and durable summaries remain available upstream. Disposable owned
scratch is removed after its final check; caller/private outputs and other work
are protected. No release, tag, schema freeze or new private/pilot data is created
by this closeout.
