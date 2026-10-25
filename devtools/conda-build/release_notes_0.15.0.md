# Sabueso 0.15.0 — Draft: knowledge integrity and inspectable scientific results

**Partial unpublished draft**, initially prepared 2026-10-20 under #112 and
reviewed for the 2026-10-25 pause. The target is 0.15.0, confirmed on 2026-10-24;
full Card exploration and actual human acceptance are prerequisites. Release
consolidation, candidate selection and publication remain paused. The current
[scope](../../devguide/pending_proposals/release_consolidation_0150.md) and
[completion inventory](../../devguide/pending_proposals/card_exploration_completion_0150.md)
override the earlier preparation order. `release_plan.toml` still describes published
0.14.0. No candidate artifact, new tag, schema freeze or release qualification
is established by this draft.

## Intended changes since 0.14.0

- Close SQLite connections owned by card/deck readers and writers; retain fatal
  Python 3.14 database/unraisable warning guards (#133).
- Keep absent dependent-source prerequisites unqueried before client construction,
  with unknown counts, original request options and actual source failures kept
  separate (#135/#141/#142/#143).
- Declare canonical ownership of shared UniProt/UniRef terms and reject ambiguous
  or inconsistent shared policy records (#136).
- Reject malformed OMA/UniRef/gnomAD/GTEx envelopes and unanswered required fields
  instead of presenting them as source absence (#137).
- Bound UniRef pagination by exact-URL cycle detection and a finite logical-page
  budget, independently of the successful explicit row ceiling (#140).
- Version tissue comparisons with explicit genomic scope and per-tissue resolved,
  missing and conflicting coverage. Preserve explicit legacy selectors (#138).
- Restore declared protein enrichment requests and recorded arguments during
  refresh; report historical missing parameters, conflicts and unsupported routes.
  Caller overrides remain explicit (#139).
- Version disease grouping/explanations and packet mapping with identifier-scoped
  identity coverage; preserve original grouping selectors and packet pins (#144).
- Extend bounded GTEx, UniRef, OMA and gnomAD acquisition observation; retain actual
  query/page/version bases, original responses, partial failures and bibliography
  gaps. Requested labels are not independently verified native revisions (#108).
- Add pinned comparative explanations, explicit-context execution observation,
  original result/workflow persistence, scoped resource/pext descriptions and
  compact comparative operation `@2` with historical `@1` compatibility (#91/#108).
- Add public structural/assay/located-literature dossier examples with exact support,
  original quantities, explicit unknowns and independent saved readers. Dossier
  `@2` exposes existing assay/target/document context; historical `@1` remains readable.
- Keep agent-prepared structural readings outside curated card knowledge until
  properly reviewed. Reject the unqualified initial located-review `@1` route
  (#92/#105/#132).
- Integrate a bounded clinical/reference journey in disease example `@6`: a
  separate pinned clinical card, one explicitly cited NCT study and three explicit
  article metadata queries, original bibliography and inert readers. Historical
  `@5` reacquisition keeps its original pre-clinical query scope (#108/#112).

## Intended schema and compatibility

Development card schema **0.3.14** remains unpublished. Its additive changes retain
requested genomic coordinate context on gnomAD variant assertions and optional
protein request/restoration quality records. Later work also retains scoped RCSB
contact inputs, original AlphaFold context, distinct derivation applications and
complete native UniProt positional feature/normalized context; follow the current
[schema record](../../devguide/SCHEMA.md). Earlier coordinate labels do not authenticate a native
assembly echo, freeze remote defaults or promise exact historical source replay.
Freeze this schema only through the accepted installed-candidate route.

Published 0.3.13 and earlier schemas/cards stay immutable. Historical reports keep
their original algorithms, pins and execution gaps. Runtime records remain separate
from scientific payloads. Required runtime floors remain those in `pyproject.toml`,
including Ackredit >=0.9.0; locally advanced editable providers do not replace
installed qualification against the public dependency closure.

## Explicit remaining scope

Human usefulness review, complete primary assay protocols, experimental
comparability and source-text acceptance remain open. Illustrative eligibility
does not establish project model selection, assay equivalence or selectivity.
Broader operation/bibliography coverage, non-protein packet queries, finer terms
filtering, larger workload budgets and peptide identity remain roadmap work.
The broad Card human/agent exploration implementation, source/coordinate integrity
corrections and versioned packet history are substantial additional development
scope since this initial draft. This list is incomplete until reconciled with
the completion inventory; it does not claim those rich panels are all delivered.
Shared MOLI/Recorda contracts and Nextia Evidence retain their owners; public
example readers do not close real consumer acceptance.

## Qualification still required

Select the final candidate and inspect its exact-SHA CI/governance. Build one
immutable staging artifact and qualify its installed public dependency closure,
historical readers and migrations on Linux/macOS arm64/Windows × Python 3.11–3.14.
Obtain final acceptance, promote the tested bytes, verify a clean public install
and identical-tag archival. Add actual receipts before changing this draft into
published release notes. See [the staged route](README.md) and
[the scope proposal](../../devguide/pending_proposals/release_consolidation_0150.md).
