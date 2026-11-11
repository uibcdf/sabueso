# Sabueso 0.15.0 — Draft: knowledge integrity and inspectable scientific results

Development implementation: opt-in `bioactivity_target_scope@2` prevents declared copies
from bypassing their retained original's target assignment in activity/ligand
answers, explanations and tables. It keeps excluded records and support visible,
with `outside_scope` for a retained excluded activity. Original @1/defaults and
packet meanings stay unchanged. Scientific/default review is explicitly pending;
this is not a released or scientifically accepted correction yet.

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

- Add nature-specific Card exploration for protein, small-molecule and disease
  captures: readable questions, original fields and source versions, complete
  value/support inspection, contextual source/back navigation and typed compact
  agent access. Unknowns, alternatives and retained conflicts remain explicit.
  The participant tasks, blank worksheet and offline public input preparer are
  ready for recruitment; actual independent researcher acceptance is pending.

- Present original molecular representations, native parent/formal-charge
  declarations and selected property records with their units. Method attribution
  follows the exact source field; measured/calculated origin is declared or stays
  unknown. RCSB CCD intake now requests its native integer formal-charge field.

- Extend structural exploration with source annotations and explicit regional
  questions, original chain gaps/author numbering, native AlphaFold whole/fragment
  scope, ligand/contact records and separate assembly declarations. The bounded
  positive/uncertain MolSysMT control keeps geometry separate from source
  knowledge; declaration counts alone do not establish physical membership.

- Add original activity/assay/publication routes, shared literature, molecule
  target context, clinical indication/citation/registry views and retained disease
  associations. Source roles, exact identity bases, units, qualifiers, query gaps
  and unsupported causal/efficacy interpretations retain their original scope.

- Add variant/isoform/tissue and sequence-change exploration, retained protein
  cluster/orthology and biological associations, and explicit supplied-context
  sequence/knowledge comparisons. Named correspondence rules and missing maps
  remain visible; similarity and equal integer positions do not merge entities.

- Preserve delivered profiles through independent original saved readers and
  finite agent requests, including actual access origins in @35/@36. Current
  human-root saving now retains already executed supported scientific projections/queries and native empty outcomes;
  source-destination replay returns through the original navigation trail.
  Earlier meanings and original files stay fixed, and unexecuted operations remain
  `not_saved`. Source-bound technical receipts do not replace candidate gates.

- Record default overview and chemical-preview policies separately from science.
  Historical text/HTML remains stable when reopened and saved again; explicit
  detached current readings remain available on original captures. Unknown
  recorded policies are refused rather than silently upgraded.

- Share complete original source support across generic related links instead of
  copying every statement into every source row (#167). Exact source opening,
  complete field explanations and agent inspection remain available. Independent
  exploration format @11 preserves the new membership binding alongside original
  formats @1–@10. The full public titin panel now completes under its original
  bounded resource control; broader workload/researcher acceptance remains pending.

- Add opt-in measurement correspondence @2 to direct activity/ligand answers,
  explanations and tables. Declared copies retain unique original selectors;
  numeric matches stay possible correspondence with explicit context and unknown
  independence. Counts are not independent-experiment counts, and copy-only groups
  have no original class vote. Original @1/defaults and packet meanings remain
  unchanged. Scientific/default and consumer acceptance are pending (#186/#148).
  A bounded explanation prerequisite reads actual pinned glossary identity entries
  without changing glossary interpretation, source data or Card pins (#182).

- Use conservative activity class @4 for new activity and ligand views: classify
  only intervals wholly within one configured band, and retain single-point
  inhibition without unsupported potency/dose inference. Readable explanations
  preserve original support; explicit @3 retains historical interpretation.
  New packet mapping @15 changes activity interpretation while inheriting @14's
  other scopes; original stored packets remain inert. Scientific/researcher and
  exact-candidate acceptance remain separate and pending (#184/#185/#148).

- Add explicit gzip/Zstandard transport for saved human/agent exploration, keeping
  plain JSON defaults and original scientific formats/readers. Strict content-based
  single-frame reading, visible encoded/decoded/window ceilings and positive/None
  overrides preserve complete history/support/quantities and atomic output. Separate
  transport sizes/hashes remain distinct from the trusted scientific bundle digest.
  Source-bound runtime/installed and workload qualification remain required (#178/#167).

- Prioritize questions and destinations in bounded navigation previews, with
  original item indices, explicit shown/total counts and complete public filters
  (#148). New saved explorations retain their named presentation policy; older
  files preserve their original preview. Scientific rules and complete retained
  membership remain unchanged.

- Retain original RCSB assembly generators/operator descriptors and expose
  `Card.assembly_generation()` under named generation `@4` (#173). Exact native
  key binding distinguishes polymer instances, ligand-neighbor references and
  missing/ambiguous inputs, retaining every original projection and source link.
  Compact component/operation declaration plans keep exact count factors;
  optional tuple/occurrence expansion preserves repeats and per-tuple binding.
  Preflight source/operator/component work and all requested count/text costs
  before expansion or capture, with visible refusal and positive/None overrides.
  Earlier `@1`–`@3` remain selectable and unchanged. No physical copy, geometry or
  assembly-contact inference follows. A shared live human/agent assembly view now
  adds readable declarations/detail, original input/source navigation and compact
  typed selection with mandatory scope/support. Original scientific saved reading
  now preserves findings, requests and navigation under explicit exploration @5,
  with independent frozen input/presentation predicates and unchanged older readers.
  Shared explanation request admission (#176) rejects inconsistent literal reads.
  Exact inventory/relationship/qualifier items now offer a lazy assembly question,
  sharing the captured result with agents. Exploration @6 preserves this question's
  exact request and navigation; old files gain no links or unvisited answers.
  Full component/physical-occurrence and operation-aware contact closure stay pending.

- Separate exact experimental declaration admission (#169) from original
  coordinate/reference support (#170). Preserve unplaced declarations and unknown
  comparisons with their exact original source scope; use state/inventory @3,
  explanation @4 and packet @14 while preserving earlier named saved readers and
  packet projections. Read #170 for source-bound correction qualification;
  broad researcher acceptance and release qualification remain separate gates.
  Scientific dossier @3 adopts the coordinate scope with frozen independent
  verification and preserves original @1/@2 report semantics.

- Preserve exact structural relationships in inventory explanations, source/group
  support and fragment exclusions. Report PDB-only ambiguity with every original
  candidate; offer an exact `relationship_id` selector and retain frozen @1 saved
  reading under the new named explanation @2 (#168/#148). Repeated machine saves
  reuse their original transport root without deleting scientific history (#167).
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
