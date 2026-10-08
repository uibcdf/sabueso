---
summary: Assess architectural alignment and consolidate the locally recovered knowledge capabilities.
issue: uibcdf/sabueso#112
status: open
opened: 2026-10-08
closed:
verification: checked
area: [architecture, source-access, documentation, integration, delivery]
blocked_by: []
supersedes: []
---

# Global audit after local-work recovery

## What

The recovery has produced useful knowledge capabilities and has preserved Sabueso's
architectural purpose in the inspected implementation. It has also expanded source
access faster than integrated scientific journeys and accumulated considerable
documentation and delivery work. Consolidation is needed before further provider
breadth becomes the default development activity.

This is a completed assessment with an open consolidation proposal under #112.
The maintainer-authorized implementation and current acceptance receipts are in
the [consolidation report](post_recovery_consolidation.md); measurements below
describe the pre-consolidation audit state.
It does not declare every new provider integrated, consumer acceptance complete,
or the uncommitted working tree qualified for public delivery. It supplements the
[design/implementation review](design_implementation_review.md) and preserves the
maintainer-approved [development order](../ROADMAP.md#next-roadmap-after-0130).

## How / evidence

### Purpose and development direction

The inspected MOLI architecture defines Sabueso as the Knowledge component:

`Source → SourceAssertion → normalization/resolution → knowledge → Card / Deck / relationships`

Sabueso preserves source support, identity, original and normalized values,
revisions, acquisition method, conflicts and unknowns. Nextia owns project-contextual
Evidence and Discovery; Praxis owns methodology; MolSysSuite owns modeling and
scientific calculations. Acquiring source-reported geometry or predictions does
not authorize Sabueso to calculate them or turn them into confirmed findings.
Knowledge, runtime provenance and bibliography retain distinct meanings.

References reviewed in the sibling MOLI checkout were
`architecture_1.0/SABUESO.md`, `SCIENTIFIC_WORKFLOW.md`, `CONTEXT_ASSEMBLY.md`,
`LEARNING_LOOP.md`, the conceptual SourceAssertion schema and the pending knowledge
reference contract. The local `MOLI_GUIDE.md` matches the canonical checkout copy;
the read-only MOLI repository-governance check passed.

Sabueso's `VISION.md`, `ARCHITECTURE.md`, `USE_CASES.md`, `ROADMAP.md`, source
architecture and independent-user acceptance report preserve both development
routes: foundations and scientifically useful pilot-driven slices. The approved
order after 0.13.0 is independent protein/comparator, molecule/activity and
disease/entity journeys; bounded queries, explanations, traceability and use-term
filtering; scoped peptide identity; parallel consumer contracts. Provider count is
not an acceptance criterion for those routes.

Private pilot guidance was reviewed read-only, including its execution phases,
roadmap and operational requirements. Its generalizable requirement is that a
scientist can execute, inspect, save and reproduce a useful slice through public
Python/Jupyter APIs before an agent orchestrates it. Repeated infrastructure in
notebooks belongs in the appropriate component. A scientific negative or
inconclusive outcome is distinct from a platform failure. No private hypotheses,
strategies, campaigns, regions or results are reproduced here.

Eight current consumer notebooks were inspected statically (45 code cells, all
parseable), without execution. They use Sabueso cards/decks, queries, retrieval
archives and persistent knowledge stores. Static inspection establishes their
intended consumption pattern; it does not qualify them against the recovered
working tree. Earlier public-version pilot validation is a separate receipt.

### Measured expansion

Measurements compare the current working tree with committed base
`68dac8f8bfc35944f5b6dd59aca8cb2a2819388d`. They describe accumulated local changes,
not public-release capabilities or a scientific completeness score.

| Measure | Committed base | Current local tree | Meaning |
| --- | ---: | ---: | --- |
| Registry resources marked `in_use` | 39 | 83 | Direct readers or source cross-references, according to the registry definition |
| Deferred resources | 28 | 37 | Useful scopes with explicit conditions for reopening |
| Evaluating resources | 16 | 11 | Remaining evaluations; independent of deferred access requirements |
| Declared enricher instances | 24 | 24 | Card-contribution declarations; 22 distinct registry resources |
| New `in_use` resources with a declared enricher | — | 0 of 44 | Native access does not establish automatic card contribution |
| New runtime Python files | — | 122 | 20,088 lines, including clients, mappings, argument validation and views |
| New top-level source `get_*` functions | — | 49 | All 49 carry ArgDigest decorators in the AST inspection |
| `CHECKPOINT.md` lines | 861 | 1,424 | Current resume guidance contains substantial chronological history |
| `ROADMAP.md` lines | 648 | 1,115 | Priorities compete with repeated recovery receipts |
| `PUBLIC_API.md` lines | 452 | 1,016 | Development-source inventories now dominate the entry document |
| `SOURCE_ACCESS.md` lines | 529 | 1,203 | Common contracts and provider-specific qualification are interleaved |

The full fixture directory occupies 67,217,050 bytes. That is fixture storage,
not a measured runtime memory cost or a predicted card size. Whole-export parsing,
original-response support and repeated snapshot retention warrant measurement on
actual journeys before changing cache or storage architecture.

### Useful gains and preserved boundaries

- Native readers and mappings preserve original records and source-specific scope;
  supplied-file binding, original-byte hashes, declared times and replay provide
  a reusable acquisition route. Generic file parsing is separate from provider
  validation and from card admission.
- Existing UniProt, PubChem and ChEBI knowledge mappings gained bounded useful
  fields. Residue readers and explicitly selected residue-set composition expose
  knowledge with named rules and full support, without deriving cavity membership,
  structural alignment or geometry. AAindex, isoform and source-sequence scopes
  remain explicit; identical sequence content is not merged identity.
- Current notebook reports and saved readers expose source support and unknown
  scope. Public HK2/P52789 adds a reproducible, current-source test system alongside
  TcTIM/HsTIM. Its 239-assertion card is UniProt-only; historical HK2 cards and ligand
  lists remain unqualified historical artifacts/query hints.
- The existing independent protein, molecule/target and disease/entity examples
  exercise producer, inert saved reader and reacquisition processes. Original
  support, quantities, report rules and pins survive later acquisitions.
- The recovery did not reinstate the historical alternative Evidence model,
  turn project conclusions into SourceAssertions, or modify frozen published
  schema/card versions. Current additive work remains in unpublished schema 0.3.13.

Inspection covered all new runtime Python files syntactically and representative
acquisition, mapping, derived-view, schema and persistence implementations in
depth. It is not a line-by-line correctness proof of every provider or an online
availability audit. Small repeated parser predicates exist; the inspected
duplication does not justify a broad shared-parser rewrite.

### Findings and ownership

| Priority / finding | Concrete evidence and consequence | Owner and proposed action |
| --- | --- | --- |
| Before public delivery: fixture publication remains unqualified for some scopes | `temp_data/NOTICE.md` and registry terms explicitly mark original TTD, Pharos, ECOD, MetalPDB, ProBiS and other responses local/unreleased or sharing unknown; MEROPS qualification is explicitly unshared. Untracked fixture files could be included in a public commit. Wheels omit `temp_data`, but the Git repository also redistributes data. | #95 / source owners: review the exact file set before a public checkpoint. Qualify redistribution with applicable declarations, or keep affected originals local and design a reproducible test-input route consistent with their terms. Public access, article licences and MIT code do not supply missing data grants. |
| Before further breadth: source adoption and usable knowledge have different maturity | All 44 new `in_use` resources lack declared card enrichers. Many are intentionally standalone native subjects; protein, EC, cell-model, regulatory-page and source-defined structural subjects cannot be merged merely for uniformity. | #83/#86/#112: expose access, mapping, card/view integration, saved journey, live health, terms and consumer acceptance separately. Select integration by a concrete scientific question; leave justified standalone scopes explicit. |
| Current documentation needs consolidation | The checkpoint says history does not belong there, yet includes 35 follow-ups and obsolete statements that the stash is intact or has remaining candidates. Similar receipt repetition obscures the roadmap and test guide. | #112: move chronological recovery detail to the existing archive; keep a short current checkpoint, one approved roadmap and a behavior-based gate index. Preserve historical receipts and links. |
| Source and API status statements drifted | ASD is `deferred` in the registry but described as `evaluating` in two maintained guides. Six unreleased source bullets preceded the published-0.13.0 API introduction, obscuring qualification boundaries. | #112/#83: correct those bounded status/layout inconsistencies during this audit; broader restructuring remains open. |
| Cross-component acceptance and reference documentation need coordination | MOLI #3 and its contract report still describe #79 as pending. #79 is closed; MOLI's own issue comments already record its fix and clean public installation in 0.5.0. Current local negative tests cover tampered item reads. Shared grammar, retention and real consumer interpretation remain undecided. | MOLI #3 and Sabueso #53; packet #71/MOLI #22; attribution #108/MOLI #36: refresh owner-maintained summaries and run bounded consumer acceptance. Existing local integrity is not a new blocker and is not shared-contract acceptance. |
| Recovery delivery is still local | The stash is empty, but the accumulated implementation remains uncommitted/unpushed. Full offline validation is a local code receipt. Published 0.13.0 and its earlier remote checkpoints are different artifacts. | Sabueso maintainers: after the file/terms review, create reviewable code checkpoints, select applicable gates and verify CI by exact SHA through gh-run-receptor. Qualify staged/installed artifacts separately before any release claim. |
| Scale and user documentation remain partially qualified | Full exports validate before selection; retained original support may have meaningful cost. New source-level regressions do not by themselves demonstrate a convenient complete user workflow or current service availability. | #98/#100/#112 and existing query/explanation issues: measure time, memory and stored support on bounded examples; execute the current public user journeys and refresh tutorials. Retain unknown/unasked/failed scope and units. |

The status of a standalone reader is not a defect merely because it is absent from
the enricher registry. Its subject, intended use and maturity need to be apparent
to users. There is no recommendation to attach all new sources to every protein
card or query all providers by default.

### Verification receipts

The preceding full code checkpoint is **5,554 offline tests passed in 173.00 s**,
with ten expected fixture warnings, pytest-receptor, 12 workers and editable
Python 3.14.7 in `molsyssuite@uibcdf_3.14`. Runtime, test, fixture and schema files
were checked against the saved checkpoint hashes before this audit's documentation
changes; no intervening changes were found in that set. Published frozen cards and
schema remain unchanged.

The audit's independent gate passed **395 tests in 128.46 s**, through
pytest-receptor with **12 workers** in the same editable Python 3.14.7 environment.
It covers argument contracts,
SourceAssertions/acquisition, enricher wiring, the registry, pinned storage and
packets, all three user journeys, terms, residue views, HK2 and supplied/native
snapshots. The selected files were:

```text
tests/core/test_argument_contracts_offline.py
tests/core/test_source_assertions_offline.py
tests/core/test_source_acquisition_offline.py
tests/core/test_enrichers_offline.py
tests/core/test_source_registry_offline.py
tests/core/test_knowledge_store_offline.py
tests/core/test_knowledge_packets_offline.py
tests/core/test_user_journeys_offline.py
tests/core/test_molecule_target_journey_offline.py
tests/core/test_disease_entities_journey_offline.py
tests/core/test_terms_offline.py
tests/core/test_packet_terms_offline.py
tests/core/test_residue_knowledge_offline.py
tests/core/test_residue_composition_offline.py
tests/core/test_hk2_test_system_offline.py
tests/tools/test_source_snapshot_offline.py
tests/tools/test_bound_native_snapshots_offline.py
```

Invocation: `python -m pytest -n 12 -m 'not online' --receptor=llm`, with those
paths as individual arguments. The checkpoint-hash comparison verified 290
runtime/test/schema/fixture files from the saved changed-file manifest; none
changed. Documentation and fixture notices are outside that code comparison.

Governance, canonical-guide equivalence and `tools/source_registry.py --check`
pass. AST checks and read-only notebook inspection
are described above. This audit does not establish live provider health, new
private-consumer execution, Windows/macOS qualification or remote CI for the local
recovery. The prior Sphinx gate passed with warnings treated as errors; an extra
nitpicky run reported unresolved cross-references and was not a passing nitpicky
qualification.

## Why

The recovery has increased the range and fidelity of source knowledge available
to Sabueso. The remaining risk is development direction and delivery clarity:
another connector is easier to count than a supported scientific journey.
Without consolidation, a growing catalogue and passing source tests can obscure
missing integrated behavior, consumer contracts and data-publication conditions.

The architectural direction remains sound. Gains become a coherent product when
scientists can use supported APIs to answer bounded questions, inspect alternatives
and missing knowledge, save exact support and reuse it independently, while other
MOLI components retain their own scientific responsibilities.

## Alternatives

- Continue adding providers: defer as the default activity until a scientific
  need identifies the next source and its end-to-end acceptance.
- Automatically enrich every card from every new source: reject; it would conflate
  subjects, increase acquisition/storage cost and weaken scope reporting.
- Rewrite the knowledge model or share all native parsers: unsupported by this
  audit. Preserve accepted contracts and source-specific validation; extract
  shared implementation only when repeated semantics are demonstrated.
- Delete recovered capabilities to reduce size: unnecessary. Retain useful,
  bounded, tested APIs and make their maturity and maintenance ownership clear.
- Complete all of Sabueso before advancing consumers: reject. Continue bounded
  independent SDK slices and parallel owner-local integration acceptance.

## Acceptance criteria

Consolidation should proceed in bounded, reviewable slices:

1. Review the exact publication file set and resolve or explicitly isolate the
   local-only fixture scopes under #95 before publishing the recovery.
2. Make the current checkpoint concise, move follow-up history into the archive,
   and keep the approved roadmap and test gates easy to find. Separate published
   API guarantees from unreleased development surfaces.
3. Add a maintained capability/maturity view using registry/enricher declarations
   where possible. `in_use` continues to mean actual access, not full integration,
   live availability or release qualification. Avoid a second hand-maintained
   source registry.
4. Choose a small subset of recovered capabilities for the approved scientific
   journeys. Where card enrichment is justified, use declared enrichers and test
   knowledge state, migration and packet wiring; otherwise demonstrate explicit
   standalone use with preserved subject and support.
5. Re-run independent producer/reader/reacquisition acceptance on the resulting
   checkpoints, including absence, failure, conflict, foreign sequence axes,
   physical quantities and original pinned support. Keep HK2's limited scope clear.
6. Measure bounded parsing/support/storage costs before deciding optimizations;
   retain original response identity and complete assertion support.
7. Refresh shared-contract evidence with the owning issues and perform concrete
   consumer acceptance without copying confidential pilot content. Keep remaining
   Nextia/Recorda/modeling work with its owners.
8. Qualify each public code checkpoint by exact SHA, then follow the established
   staged installed-package route when a substantial release is appropriate.

## Resolution

The architectural assessment is complete. Consolidation and public delivery remain
open; this report does not replace the approved roadmap or close its owning issues.

Findings and acceptance are recorded in
[Sabueso #112](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6063719176).
The access/publication-scope finding is cross-linked in
[Sabueso #95](https://github.com/uibcdf/sabueso/issues/95#issuecomment-6063731678);
the stale reference-contract evidence is reported to its owner in
[MOLI #3](https://github.com/uibcdf/moli/issues/3#issuecomment-6063730466).
