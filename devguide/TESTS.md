# Sabueso — Tests and Quality Gates

Select verification by changed behavior and state its scope. Detailed provider
cases are in [the native test reference](sources/NATIVE_TEST_REFERENCE.md); dated
receipts remain [archived](archive/consolidation_2026-10-08/TESTS.md). A passing
source test does not complete a scientific journey, consumer contract or release.

## Running the tests

Use Python 3.14 in the existing editable `molsyssuite@uibcdf_3.14` environment.
Install Sabueso and participating installable workspace packages from their local
checkouts with `python -m pip install --no-deps --editable .`. Verify editable
metadata and import paths outside the checkout. Keep installed-artifact
qualification separate from workspace development.

Compare the imported SDK and distribution versions inside the checkout as well:
an old generated `*.egg-info` there can shadow a correctly installed editable
`dist-info` outside it. Review its ownership and quarantine or refresh that
generated metadata before qualifying producer labels; do not rewrite old saved
labels silently. The #148 scientific-capsule receipt records this concrete repair.

Public/repository-input offline suite:

```bash
python -m pytest -n 12 -m "not online" --receptor=llm
```

Full local suite including verified unshared native originals:

```bash
python -m pytest -n 12 -m "not online" --receptor=llm --local-source-inputs
```

The default excludes 25 native-only modules before import and explicitly skips
ten mixed native cases. Synthetic binding/malformed-input and public sequence-axis
tests remain active. The local option verifies original digests and includes that
coverage; unavailable or changed originals fail before collection. See the exact
[fixture delivery scope](sources/FIXTURE_DELIVERY.md). Test counts must identify
which command ran. Historical 5,554-case receipts precede this separation.

For a smaller changed scope, append its individual test paths. A private pilot
execution, an online test and a public fixture replay are different acceptance
routes. Run online tests only for an authorized concrete source/use scope; a
fixture does not establish current live availability.

## Test kinds

- Unit/contract tests verify errors, identities, assertion support, quantities and
  transformations, including deliberately synthetic parser inputs.
- Native response tests preserve qualified original wire/file content and scopes.
- Integration tests combine resolution, cards/decks, packets, persistence and
  original runtime/bibliography sidecars.
- Independent-user tests exercise separate producer, inert reader and reacquisition
  processes outside the checkout with exact original support.
  Use a native `tempfile.TemporaryDirectory` for a subprocess working directory
  outside the checkout across supported OSes.
- Installed-artifact tests establish the behavior and complete dependency closure
  of the exact built/published package, independent of workspace imports.

## Behavior-based gate selection

| Changed behavior | Select these test files / gates |
| --- | --- |
| Original regional chain reading | `test_card_regional_reading_offline.py`, human/nature/structural/source/context/annotation/model, compact cell/selection/access and saved-science/exploration cases; complete versus gapped versus uncomputed original regions, exact chain/relationship locations, duplicate PDB labels, quantity-preserving inspection, no machine-frame growth, detached captured state, bounded escaped previews and independent inert current/genuine old reading. Presentation does not change native rules, schema or stored wires (#148/#173) |
| Original active-site selection binding | `test_dossier_selection_offline.py`, dossier/comparison journeys, residue knowledge/composition and original coordinate cases; frozen exact source item/subject/axis/support/revisions, normalized precedence, compound/fuzzy/missing states, ascending unique union and strict reported positions/axes/numbering/correspondence, coherent region/subset substitutions with original-stage isolation, unchanged Cards/runtime and genuine pre-fix reading; forbid current selectors/support helpers and new queries/credit (#172) |
| Region receiving workload budgets | `test_region_request_budget_offline.py`, argument contracts, native structures/inventory/explanation, public Card tables, human/agent protein/structural questions and saved exploration/history cases; exact interval unions, raw complexity, per-Card aggregate counts, pre-expansion refusal, explicit raised/unlimited budgets, scientific bounds under override, preserved cached selection identity and source/Card inputs, original saved reading without current engines. Use tiny test budgets and a forbidden expander, never host-memory exhaustion (#171) |
| Experimental coordinate/reference admission | `test_experimental_coordinates_offline.py`, `test_scientific_dossier_journey_offline.py`, native structures/inventory/explanation, human/agent/region/source/saved routes, packet full/index/terms/history and argument/quantity gates; exact original canonical support, source/object binding, retained alignment/feature projection, malformed/ambiguous/bounded axes, partial declarations, unknown versus negative completeness, source inspection, independent inert @4 reading, resealed coordinate substitutions and unchanged genuine @3 fixture. Full local-original checkpoint and unskipped exact-SHA CI/governance qualify #170/#148 |
| Experimental declaration admission | `test_experimental_structure_admission_offline.py`, native structures/inventory/explanation, Card human/agent/region/source/saved cases, packets full/index/terms/history and argument/quantity gates; exact declared subject, missing/foreign/alias/conflicting identity, duplicate Card ids, malformed unplaced qualifiers, separate fragments, exact originals and typed source locations, inert new reading, genuine old @2 capsule and resealed scope/support changes. Full local-original code checkpoint and unskipped exact-SHA CI/governance qualify the native correction (#169/#148) |
| Exact structural explanation scope | `test_structure_relationship_scope_offline.py`, direct/Deck inventory explanations, human/agent structures/support/navigation, all saved formats, argument and quantity gates; duplicate labels/states, coarse grouping and explicit maps, cross-Card ids/pins, admitted/fragment/unknown scope, strict selectors before work, exact independent original reading, resealed field/group/exclusion/rule substitution and genuine @1 compatibility. Include a full local-original code checkpoint and unskipped exact-SHA CI/governance (#168/#148). Repeated literal/scientific machine saves preserve roots/bytes (#167) |
| Original structure context | `test_card_structure_context_offline.py`, all Card access/navigation/source/structural/saved/argument/quantity cases and native explanation gates; exact experimental/literal declaration fields, repeated literal PDB labels, captured input/support, separate supplied revisions, missing/null/empty/malformed scope, no rereading science, independent inert @1/@2 reading, fresh semantic field/origin substitutions and genuine old codec without backfill. Duplicate-reference experimental explanations now have the separate #168 qualification (#148) |
| Ligand instance to original parent | `test_card_ligand_parent_navigation_offline.py`, original instance/quaternary/source/model/annotation routes and all Card access/navigation/saved/argument/quantity cases; exact typed parent and occurrence, repeated labels, source/foreign/conflicting/empty scope, separate supplied Cards/revisions, compact literal access, inert independent reading, freshly identified semantic substitutions, swapped related-operation origin, repeat-save stability and genuine old producer without backfill (#148) |
| Persistence copy cost and storage accounting | `test_card_saved_exploration_offline.py`, original scientific/site/quaternary saved readers, all Card access/exploration/navigation/quantity and argument cases; unchanged supplied wire, defensive outputs, original formats and resealed tampering. `test_exploration_storage_observation_offline.py` checks UTF-8 byte accounting, exact typed repetition, duplicate/nonfinite refusal and untouched inputs. Public profiled costs remain observations without speed assertions (#167) |
| Source observation collisions | `test_source_observations_offline.py`, source assertions, aggregation/resolution, refresh/migration/knowledge store, curation/acquisition and derived input support; both merge orders, atomic conflict refusal, typed duplicates and extraction restoration, compatible metadata completion, all annotation alias/date receipts, scoped native comment identity, live/frozen coverage parity, caller isolation and separate original/refreshed pins. Select broader/full offline and exact-source CI for this core insertion change (#166) |
| Whole-model reference navigation | `test_card_model_regions_offline.py`, all Card access/exploration/navigation/history cases, original AlphaFold context/predicted views, structures, native/packet/table/argument/quantity cases; public positive/shared result, fragments/foreign identities/checksums/references/alternatives/history gaps, detached captures, independent inert process, @1/@2/@3 original navigation and genuine @4 producer, exact original region/source/origin and resealed substitution refusal (#148) |
| Original quaternary scientific reading | `test_card_saved_quaternary_offline.py`, live quaternary tests, all Card access/exploration/navigation/history and native oligomer/explanation/packet/table/argument/quantity cases; genuine original live capsules, frozen predicates, explicit @4/mixed adapters, exact original requests/order/units/source closure, independent inert subprocess, coherent result reidentification and resealed policy/schema/type/membership/origin refusal, empty/missing contexts and bounded repeat saving (#148) |
| Live quaternary human/agent interpretation | `test_card_quaternary_interpretation_offline.py`, all Card access/exploration/navigation/history cases, native oligomer/explanations/packet/table/baseline, quantity and argument contracts; one capture/evaluation in either order, all declarations/pairs, exact source membership and destinations, typed selection, partial/uncertain/foreign/missing inputs, bounded atomic deferral, unchanged original capsules/source reading, original scientific saving and unretained saved `not_saved`. Also `tests/tools/test_installed_receiving_scope_offline.py` for declared installed receiving helpers (#148/#165) |
| Quaternary interpretation admission | `test_quaternary_interpretation_scope_offline.py`, explicit historical oligomer/explanation cases, flat tables, public knowledge baseline, disease-identity packets, packet full/index/terms/history, source/assertion/quantity and Card exploration cases; public current positives, foreign/source/uncertain/conflicting inputs, all declarations/pairs, unknown counts versus zero, original source display, exact field scope, genuine original @1/@2 capsule and unchanged older packet projections (#165) |
| Original quaternary source exploration | `test_card_quaternary_source_offline.py`, all Card exploration/access/context/saved/argument/quantity cases and native oligomer/explanation cases; exact public membership, original source/structure destinations, missing/empty/foreign scope, duplicate structure-local IDs, bounded escaped previews, independent saved reading, old capsules and rehashed origin/scope/membership changes (#148) |
| Individual annotation structural navigation / saved operation origin | `test_card_annotation_regions_offline.py`, human/nature/source/structure/access/agent/context/saved/quantity/argument and migration cases; exact item support, original typed indices/axes/native inputs, explicit canonical region sharing, disulfide endpoints, conflicts/unknowns, native revisions, independent inert reading, unmaterialized `not_saved`, genuine @1/@2 history and internally resealed related-operation swap rejection (#148/#161) |
| Native UniProt feature scope and identity | `test_uniprot_feature_scope_offline.py`, `test_uniprot_feature_molecule_identity_offline.py`, domain/additional/mapping/acquisition/residue/migration/refresh/schema cases; every mapped type, full native asserted value versus normalized annotation, distinct molecule/citation/compound/unprojected contexts, exact native duplicates, stable order/retrieval IDs, original support and independent inert saved reading, unknown endpoints, malformed shapes, historical gaps without backfill and refreshed original-pin preservation. Shape coverage includes explicitly synthetic optional molecule labels in all 17 mapped fields (#160/#162) |
| Original saved comparisons | `test_card_saved_sites_offline.py`, native scope/explanations and all Card access/human/context/agent/saved/quantity cases; frozen native conformance, explicit @3 and genuine @1/@2, mixed adapters, exact requests, independent reader with current engines/catalogs/network forbidden, source/related-operation origins, typed/coherently rehashed changes and bounded repeat saving (#148) |
| Compact ligand-site delivery | `test_card_ligand_site_delivery_offline.py`, owning selection/comparison and shared Card access/history/quantity gates; public byte reduction, complete 8 KiB pages, exact reconstruction of every original support location, missing membership, capture/mutation isolation and no repeated science (#148) |
| Compact ligand-site selection | `test_card_ligand_site_access_offline.py`, human comparisons, Card access/selection/context/saved-history/argument/quantity and native scope/explanation cases; one captured evaluation in either entry order, shared result/item identity, exact textual filters/membership/order, display exclusions, mandatory comparison/source closure, bounded atomic deferral, cursor isolation, native outcomes, exact original saved requests and explicit unretained `not_saved` behavior (#148) |
| Human ligand-site comparisons | `test_card_ligand_site_comparisons_offline.py`, Card nature/source/access/structure/context/saved/quantity/argument cases and native ligand explanations; native conformance, one captured calculation, exact original support/annotation/contact links, partial/foreign/uncertain axes, source-declared component context with duplicate indices and foreign-subject refusal, preserved distance units, separate assembly context, bounded literal agent reading, verified saved scientific/origin closure and inert old saved `not_saved` behavior (#148) |
| Ligand overlap coordinate admission | `test_ligand_overlap_scope_offline.py`, native ligand sites/explanation/deck, annotation source identity, packet full/index/history/terms, oligomer and public HK2/exploration cases; exact focal identity/sequence/support, foreign/unknown/fuzzy/compound axes, strict endpoints, original PDBe-KB object binding, native-vs-normalized override, conflicting/unstated revisions, partial positives and no false negatives. Freeze @10 exactly and preserve older readers; qualify @11 with local originals, full offline and exact-SHA CI/governance (#163) |
| AlphaFold original model context | `test_alphafold_context_offline.py`, predicted structures/acquisition, model source panels, navigation/saved readers, packet terms/index/history, migration/refresh/schema and quantities; original checksum/length/isoform support, foreign/unstated identity, invalid/conflicting MD5, fragments, original-input replay, direct input links, unchanged old projection and inert saved reading. Shape/schema and exact-head CI/governance qualify the optional stored context, packet @9 and navigation @2 (#148) |
| Relationship derivation applications | `test_derivation_applications_offline.py`, relationships, extraction/structure mentions, RCSB lineage, quantities, packet terms, Card access/exploration/saved and migration/schema cases; distinct input sets/rules/parameters/engine/output scopes, exact deduplication, premerged conflicts, caller isolation, sealed original-output quantities, unchanged legacy loading/migration and independent inert saved reading. Shape/schema and exact-SHA CI/governance qualify the additive unpublished keys (#156) |
| RCSB contact identity/lineage | `test_rcsb_contact_lineage_offline.py`, owning ligand sites/explanation/deck, RCSB acquisition/structure/inventory, migration/refresh and exploration/saved cases; original-input replay, unidentified instances, equal labels across contexts, ambiguous axes, conflicting flags, quantities, inert history and explicit migration gaps. Run shape/schema gates and exact-SHA CI/governance for the stored optional lineage (#148) |
| Protein source-context exploration | `test_card_protein_source_offline.py`, `test_card_ligand_instances_offline.py`, human/nature/access/structure/context/saved/argument/quantity/entities cases; original fields/units/axes and instance indices, structure/component/instance selection, bounded wording, exact subjects, malformed declarations, source-backed navigation, inert saved requests/membership and no duplicate scientific calculations (#148) |
| Readable structural support | `test_card_structural_support_offline.py`, human/access/structural/context/saved/argument/quantity cases; direct original source records, missing support, named original rules/options, literal lookalikes, bounded escaped wording, historical saved membership, independent inert reading and rejection of incomplete source membership (#148) |
| First-version human walkthrough / closeout documentation | Execute `examples/user_journeys/card_exploration.py produce` over the three public fixtures and `read` in a separate process without fixture access; initial protein/nature/context/saved and human/structural tests; Markdown/snippet syntax, example lint and Sphinx checks. Technical script success is not uncoached usability (#148) |
| Caller-owned diagnostic policy | `test_diagnostic_policy_receiving_offline.py`, SMonitor integration, argument contracts, bioactivity and quantity cases; fresh import/reload/emission, pre-collection diagnostic refusal, native errors, retained Card outcomes and filtered/failed catalog delivery (#150) |
| Structural cell support and delivery | `test_card_cell_support_offline.py`, structural agent selection plus human/access/saved/argument, native structural/state/explanation, quantity and diagnostic cases; exact cell identity/value/support paths, missing assertion members, atomic typed deferral for large values/qualifiers/membership, next-page delivery and original frozen producer reading (#148) |
| Public arguments/diagnostics | `tests/core/test_argument_contracts_offline.py`; owning API cases; SMonitor/diagnostic cases |
| Human source/ontology wording | `test_card_human_labels_offline.py`, `test_card_method_preview_offline.py`, human/access/context/saved/argument and native structural/coverage/quantity cases; original source roles, whole-declaration reference guards, unknown versus empty selection, missing/partial method support, methods/units, synonym scope, recorded derivation, literal lookalikes, bounded escaped previews, earlier saved label filters and independent inert reading (#148) |
| Structural agent selection | `test_card_agent_selection_offline.py` plus human/access/argument, saved exploration, native structural/state/explanation, quantity and diagnostic cases; typed filters, exact membership, missing-last deterministic order, bounded pages/cursors, original support, historical policy checks and exact saved variants (#148) |
| Portable scientific exploration | `test_card_saved_science_offline.py` plus literal/human/access/argument, native structural/state/explanation, quantity and diagnostic cases; historical bytes, original decisions/support, independent readers with current rules/catalogs/columns forbidden, exact requests/focal captures, quantities/filter predicates, region prerequisites and coherent rehash/rebinding refusal (#148) |
| Portable literal/field exploration | `test_card_saved_exploration_offline.py`, human/access/argument and native structural/coverage/quantity cases; independent inert process, unchanged snapshots, source/unit/request/membership closure, missing/ambiguous destinations, history preservation, fresh cursors, atomic failures and rehashed tampering (#148) |
| Captured contextual navigation | `test_card_context_navigation_offline.py`, human/access/argument and native structural/coverage cases; exact return/profile transitions, original source and endpoint links, missing/ambiguous context, supported identity graphs, duplicate/revision/pin handling, mutation/cycle/cache isolation and bounded escaped display (#148) |
| Initial nature profiles and coverage | `test_card_nature_exploration_offline.py`, human/access/argument, native knowledge-state/explanation and quantity cases; exact source/quantity/method support, hierarchy/identity separation, typed literal keys, unrecognized shapes, original state/count parity, lazy capture/explanation cache, no new attribution and bounded escaped previews (#148) |
| Human protein journey | `test_card_protein_exploration_offline.py`, human/access/argument and native structural cases; supported field values, original assertions/back navigation, explicit canonical region/identity guards, shared cache, preserved unknowns and bounded escaped previews (#148) |
| Shared structural exploration | `test_card_structures_exploration_offline.py`, original structures/inventory/explanation/knowledge-state and human/access/argument cases; exact existing outputs, original support/rules/exclusions, scope gaps, shared cache, typed units, projected byte limits, complete deferral and navigation (#148) |
| Human literal Card exploration | `test_card_exploration_offline.py`, literal access and argument contracts; shared one-time capture, full typed locations, complete item sequences, original support/conflicts, navigation/selection identities, Unicode search, bounded escaped rendering and preserved quantity units (#148) |
| Bounded literal Card access | `test_card_access_offline.py`, argument, quantity, knowledge-store and Card schema/policy cases; exact reconstruction and snapshot locations, fixed byte/record limits, foreign/retry cursors, Unicode/large-key deferral, quantity codec/seal, no scientific/source calls and atomic export (#148) |
| Source/assertion identity and acquisition | `test_source_assertions_offline.py`, `test_source_acquisition_offline.py`, `test_source_access_offline.py`; owning source/mapping cases |
| gnomAD operation observation / prerequisites | `test_gnomad_acquisition_offline.py`, source/acquisition/refresh and comparative journeys; actual GraphQL aliases/revisions/count bases, unavailable fixtures, partial failure, exact pins, inert readers and no source client without gene identity (#108/#141) |
| Open Targets upstream prerequisite | `test_disease_source_acquisition_offline.py`, disease associations, enrichers, knowledge-state and refresh cases; forbidden constructors/calls, no operation/resource credit, actual native non-binding outcomes, exact valid-gene science and historical pinned refresh (#142) |
| Source-local upstream prerequisites | `test_source_prerequisites_offline.py`, owning DISEASES/ClinVar/SKEMPI/SAbDab/disease-card, enrichers, knowledge-state and refresh cases; forbidden clients, unknown counts, actual empty/missing/failing outcomes, retained source credit and original/corrected pins (#143) |
| Derived disease identity coverage | `test_disease_identity_coverage_offline.py`, disease-card/explanation/journey, packet and packet-terms cases; exact identifier diagnostics, blocked/failed/unknown/mixed scope, MedGen UID prerequisites, historical @1/@2 rules and @6 packets, inert readers and original pins (#144) |
| Comparative native response contracts | `test_comparative_response_contracts_offline.py`, OMA/UniRef/gnomAD/GTEx cases; malformed and unanswered envelopes stay connector failures, while explicit empty/null answers preserve absence (#137) |
| Comparative genomic scope | `test_scoped_tissue_usage_offline.py`, gnomAD and migration cases; wrong/missing assemblies and chromosomes, transcript versions, union coverage, overlapping conflicts, nullable tissue values, explicit legacy behavior and both independent report formats (#138) |
| Comparative explanations | `test_comparative_explanation_offline.py`, `test_comparative_support_journey_offline.py`; exact sequence/tissue pins, selected/alternative support, actual genomic intersections, term joins, incomplete/foreign scope, historical rules and inert independent readers (#91/#138) |
| Comparative execution observation | `test_comparative_operations_offline.py`, comparative/explanation/scoped-tissue, attribution and packet cases; exact ordinary-view science, explicit-context execution, reused input support, historical rules, genuine provider absence/failure, changed/misbound pins and independent inert saved bibliography (#108) |
| Persisted comparative journey | `test_comparative_support_journey_offline.py`, comparative operation/explanation/scoped-tissue, attribution and packet cases; `@3` result/support/credit bindings, workflow union, partial support, immutable original exports, distinct reacquired executions, historical `@1`/`@2` compatibility and refusal of rehashed/misbound sidecars (#108/#112) |
| Comparative bibliography | `test_comparative_bibliography_offline.py`, comparative/journey, gnomAD/GTEx/source acquisition, attribution and packet cases; complete verified collective-author exports, pext-only real method-description credit, unknown native revisions/entry studies, unavailable/failed access and invalid support, inert original readers and misbound method scope/citations (#108/#112) |
| Native supplied files | `tests/tools/test_source_snapshot_offline.py`, `test_bound_native_snapshots_offline.py`; affected source tests with applicable public/local scope |
| Source registration/card contribution | `test_source_registry_offline.py`, `test_enrichers_offline.py`, knowledge-state and packet coverage; `tools/source_registry.py --check` |
| Fixture delivery | `test_fixture_delivery_offline.py`, `test_fixture_licensing_offline.py`; `tools/fixture_delivery.py --check`; prove public tests with local inputs absent |
| Identity/relationships/selection | Owning resolver/mapping/aggregation/conflict tests; no sequence/name/number similarity merge |
| Card/schema/migration | Card, migration and frozen-card tests; `tools/card_shape.py`, `tools/validate_schema.py`; unpublished additive changes only |
| Refresh request scope | `test_refresh_scope_offline.py`, enricher/migration/source-acquisition and owning fixture cases; every declared selector, failed/blocked/excluded requests, nondefault parameters, historical gaps, conflicts before acquisition, caller overrides and exact original pins (#139) |
| Quantities | Quantity/measurement/native-unit tests, seals and non-default unit policy across serialization and consumers |
| Pinned persistence/packets | `test_knowledge_store_offline.py`, `test_knowledge_packets_offline.py`; historical pins, tampering, foreign/missing states, migration |
| HTTP response lifetime | `test_http_lifetime_offline.py`, HTTP/retrieval-archive/source-acquisition and affected source cases; discarded retry and replaced archival response closure, failure/interruption cleanup, readable caller-owned raw errors, source translation and body-dependent absence/fault classification (#151) |
| SQLite connection lifetime | `test_sqlite_lifetime_offline.py`, `test_storage_offline.py`, `test_deck_meta_offline.py`; explicit closure on success, empty reads and failures, committed round trips and rollback of failed deck replacement (#133) |
| Derived residue knowledge | `test_residue_knowledge_offline.py`, `test_residue_tracks_offline.py`, `test_residue_composition_offline.py`; declared axes, support and ambiguous denominator |
| Terms/admission | `test_terms_offline.py`, `test_packet_terms_offline.py`, `test_disease_deck_admission_offline.py`; original kept/excluded support |
| Attribution/literature/clinical | Source acquisition and relevant attribution/extraction/article/reference tests; original portable sidecars and bibliography gaps |
| GTEx access observation | `test_gtex_acquisition_offline.py`, owning GTEx/acquisition/attribution/refresh cases; requested dataset versus unknown revision, returned versus selected rows, fixture unavailable/failed/empty states, archive replay/retries and an independent inert pinned reader (#108) |
| UniRef page observation | `test_uniref_acquisition_offline.py`, owning UniRef/acquisition/attribution/refresh cases; individual page releases, caps, continuation, partial failure, fixture availability, replay/retries, scientific equivalence and independent inert pinned reading (#108) |
| UniRef pagination termination | `test_uniref_acquisition_offline.py`; empty/nonempty cycles, distinct empty chains, logical-page versus nested transport retry budgets, exact boundary exhaustion, row-ceiling precedence, failed card support and original archive reuse/replay (#140) |
| OMA operation observation | `test_oma_acquisition_offline.py`, owning OMA/acquisition/refresh/comparative cases; OMA versus UniProt name-resolution sources, native revision gaps, batch ambiguity/partial failure, local input availability, selected-row scope, retries/replay, exact scientific equivalence and independent inert reading (#108) |
| Independent scientific journeys | `test_user_journeys_offline.py`, `test_molecule_target_journey_offline.py`, `test_disease_entities_journey_offline.py`, `test_clinical_bibliography_journey_offline.py`; public examples and original readers |
| Scientific review dossier | `test_scientific_dossier_journey_offline.py`; explicit structural/assay criteria, native quantities/context, located-mention scope, exact support and original credit, independent inert reading and reacquisition, historical `@1` and native-context `@2`, missing qualifiers versus source absence, complete criterion inputs/outcomes/unknown reasons, refusal of coherently edited and rehashed artifacts with regenerated Markdown and original-stage isolation (#146) |
| Saved clinical/reference journey | `test_disease_entities_journey_offline.py`, clinical/registry/article/source-access and indication-bibliography cases; `@6` explicit NCT/PMID scope, native statement pins, collective authors, failure/unavailable/empty states, original sidecars after reacquisition, inert readers and refusal of rehashed scientific/access changes. Verify genuine historical `@5` without broadening its query. |
| Located primary-source review draft | `test_literature_source_review_journey_offline.py`, literature/curation-store/article and fixture-delivery cases; native publication/subject/rights, agent preparation with pending scientist review, drafts outside card knowledge, refusal of imported curations and unqualified @1, inert separate reader, rehashed semantic/provenance changes and preserved exports |
| HK2/notebook reports | `test_hk2_test_system_offline.py`, `tests/tools/test_card_notebook_offline.py`; exact saved card/report regeneration |

Core filenames in the table are relative to `tests/core/` unless another directory
is stated. Broaden the selected scope when changes affect shared contracts, schemas
or multiple routes. The full offline suite is a code checkpoint; it is not required
for every documentation-only or exploratory change.

## Clinical registry and bibliography guards in development

Native ClinicalTrials.gov study/reference observation, exact integrity, explicit
Europe PMC bibliography and collective authors preserve separate requested scopes,
original sidecars, missing/failed/unqueried states and publication pointers. The
[clinical report](pending_proposals/clinical_registry_checkpoint.md) records its
receipts; complete clinical breadth and bibliography remain #108 work. The separate `clinical_bibliography_example@1` journey selects one native NCT
and three PMID from the unchanged molecule input. Its independent subprocess
tests cover original pins/exports, distinct clinical-only reacquisition, absent
local files, failed registry access, missing PMID/module versus explicit empty
references, no citation parsing and refusal of coherently rehashed edits. The
saved reader forbids source clients, SDK scientific views and new credit.
These fixture checks do not establish live availability or clinical usefulness.

## Traceability and extraction guards delivered in 0.13.0

Per-source acquisition cases cover native bytes, query/time/version bases,
empty/failure/reuse/retries/cuts and detached traces. Attribution, extraction,
article metadata, pinned explanation and persisted-pipeline cases retain original
scientific support separately from observed execution and bibliography. Saved
readers forbid source access, derivation and new credit. Source-specific coverage
and the detailed delivered cases remain in the archived test descriptions and
[SOURCE_ACCESS.md](SOURCE_ACCESS.md).

## Independent-user journey acceptance (#112, after 0.13.0)

The [journey acceptance report](pending_proposals/independent_user_journeys.md)
records protein/comparator, molecule/activity and bounded disease/entity behavior.
Examples live in `examples/user_journeys/`; regression tests run producers/readers/
reacquisition in independent processes and reject modified or misbound artifacts.
Original reports preserve their named format/rules and gaps. A current reader must
not silently recompute an old report under new rules.

Public TcTIM/HsTIM/HK2 inputs provide generic acceptance without private program
content. Real consumer-owned Evidence, modeling and shared Recorda interpretation
remain independent owner-local integration work; stand-in consumers cannot close
those contracts.

## Fixtures

Frozen public source responses keep their own declarations in `temp_data/NOTICE.md`.
No private/pilot data enters fixtures. Preserve source, date, applicable licence,
native revision basis and modifications. Code MIT does not license source data.

The reviewed recovery inventory records repository versus local-only file delivery.
Local-only originals are ignored and rejected from the Git index by the delivery
gate; they remain available for explicit local native qualification. New fixtures
need reviewed file decisions; changed bytes or source terms invalidate an old
receipt. Unknown permission never becomes permission through a successful test.

## Local checks and CI checkpoints

Run each applicable gate separately and read its result:

Use the Ruff version pinned in `pyproject.toml` and CI. Run its format gate at
the repository root: it includes Python examples in Markdown, so a Python-only
path selection does not replace `ruff format --check .`.

```bash
ruff format --check .
ruff check .
python tools/fixture_delivery.py --check
python -m pytest -n 12 -m "not online" --receptor=llm
python tools/card_shape.py
python tools/source_registry.py --check
python tools/validate_schema.py
python devtools/moli_governance.py
python devtools/dependency_preflight.py
```

When local native source code changes, include its explicit qualification selectors
and a full local checkpoint as appropriate. Public CI validates its available
repository-input scope; retain local-original receipts separately. Do not pipe a
gate through `tail`/`grep` or chain a commit after a command whose exit code does not
reflect the gate.

When host memory headroom is limited, reduce local worker count and serialize
heavy checks. `-n 4 -o tmp_path_retention_policy=failed` removes successful
function-scoped pytest temporary outputs as their fixtures finish while preserving
failed-call outputs. Keep logs, useful diagnostics and original inputs separately.
Measure genuinely free RAM, available RAM, swap activity and the owned process
tree; use explicit resource stop limits rather than relying on worker count alone.
Record the actual options and stopped runs; an interrupted run is not qualification.

Linux Python 3.14 CI promotes unclosed-database ResourceWarnings and pytest
unraisable-exception warnings to errors (#133). The connection context manages
transactions, not lifetime: SQLite readers/writers use `closing` around it, and
direct test queries also close their handles. For a local checkpoint use
`-W "error:unclosed database:ResourceWarning"` and
`-W error::pytest.PytestUnraisableExceptionWarning`; unrelated ResourceWarnings
are not suppressed or promoted by the database-specific filter.

Documentation/evidence changes need applicable link/example/generated-content
checks. When `docs/` or a docstring changes, build with warnings fatal:

```bash
sphinx-build -W --keep-going -b html docs <output directory>
```

Use the provisioned docs dependencies with the checkout installed. Nitpicky `-n`
is additional qualification; unresolved references from that run are not a passing
nitpicky receipt. Source shape and published frozen-card gates remain separate.

Batch short exploratory commits locally when remote visibility is unnecessary.
The maintainer-approved direct-push policy also permits `[skip ci]` on intermediate
tested code when no immediate remote gate is needed. Run the applicable local
checks first; a full offline checkpoint can cover several short commits while
its code, inputs, environment and scope remain applicable. Repeat affected tests
when subsequent changes invalidate that result. Use twelve pytest-receptor workers
for routine local pytest. Passing Linux editable tests does not qualify the other
supported OS/minors or the installed public dependency route.

Record every deferred code block's actual head SHA, changed/tested scope, missing
remote gates, owning issue and recovery route in its issue and checkpoint record.
The [recovery ledger](pending_proposals/deferred_ci.md) distinguishes qualified
code checkpoints from later intermediate heads and their missing checks. A skipped
or older run is never a newer head's exact-source passing evidence. Required PR
checks and immediate security, dependency, packaging,
migration or integration gates cannot be deferred with this marker. Published
release candidates and installed-artifact admission retain every mandatory gate.

### Recovering deferred CI

Finish a block with an unskipped push and inspect the resulting exact-head CI and
governance runs. Alternatively, after explicit authorization, dispatch both
workflows against the published `main` head. Both support `workflow_dispatch`;
CI includes default-branch coverage publication on manual `main` runs, as on pushes.
The weekly scheduled run alone does not cover governance or coverage publication.
For the manual route, record the candidate before dispatch:

```bash
candidate_sha=$(gh api repos/uibcdf/sabueso/git/ref/heads/main --jq '.object.sha')
test "$(git rev-parse HEAD)" = "$candidate_sha"
gh workflow run ci.yml --repo uibcdf/sabueso --ref main
gh workflow run moli-governance.yml --repo uibcdf/sabueso --ref main
gh run list --repo uibcdf/sabueso --workflow ci.yml --event workflow_dispatch \
  --commit "$candidate_sha" --json databaseId,headSha,status,conclusion,createdAt,url
gh run list --repo uibcdf/sabueso --workflow moli-governance.yml --event workflow_dispatch \
  --commit "$candidate_sha" --json databaseId,headSha,status,conclusion,createdAt,url
```

Run each command separately and inspect its result; stop on failure or a changed
head. Identify the newly dispatched run IDs by workflow, event, SHA and creation
time. Follow each through gh-run-receptor with full captures:

```bash
gh-run-receptor watch <run-id> --repo uibcdf/sabueso --profile ci \
  --capture full --interval 30 --max-interval 30 \
  --output <checkpoint-directory> --receptor llm
```

Verify both runs' `headSha` against the recorded candidate. Check every job's
conclusion and full test summary, not just the workflow's overall green status.
The current matrix has thirteen test lanes (nine public OS/Python lanes and four
installed public-Ackredit lanes), Ruff and coverage publication, plus the separate
governance job. A missing, skipped, cancelled or failing applicable job leaves
qualification pending. Record run URLs and retained captures in the owning issue
and checkpoint receipt. If `main` has advanced, these results qualify only the
recorded candidate; the newer head still needs its own applicable checks.

GitHub's conclusions remain authoritative; native `gh run view` is the fallback.
Source/data delivery must pass before claiming a public qualified code checkpoint,
then [staged installed-package gates](../devtools/conda-build/README.md) qualify
releases across the required OS/minor matrix. Direct development publication with
deferred CI must be labelled as such and never presented as a qualified checkpoint.

## Quality rules for knowledge

- Every selected value retains supporting SourceAssertions; selection preserves
  alternatives and conflicts. Relationships retain their exact assertion support.
- Physical quantities keep `{value, unit}` and verified seals through boundaries.
- Derived classes/groups/states/findings carry named versioned rules and are never
  stored as SourceAssertions.
- Identity merging requires source-stated correspondence; equal names, sequences
  or residue numbers are insufficient.
- Missing, failed, unasked, unavailable and source-stated absence remain distinct.
- Every pin returns its original verified state or fails; it never falls back to
  a newer state. Independent saved readers add no acquisition or credit.
- Each receipt identifies code/artifact, input scope, environment and applicable
  limits; a local diagnostic wheel is not a public release.


Compact comparative credit qualification includes
`tests/core/test_comparative_credit_size_offline.py` together with comparative
operation and saved-journey readers: proportional host/workflow serialization,
exact owner/scope hashes and historical full contexts. This protects serialization
scale; it does not qualify whole-workflow memory, scientific algorithm complexity,
consumer routing or installed artifacts.


### Local temporary-storage capacity

The full local-original suite can retain substantial scratch until it exits.
If shared `/tmp` reaches its quota, inspect capacity and remove only finished
owned resources. A local recovery route uses an owned ignored directory on the
checkout filesystem with `--basetemp=recovered_work/<checkpoint>/pytest-scratch`,
using the same environment, workers and gates. This is scratch placement, not a
new environment. Independent-reader tests that need an outside-checkout working
directory still use their own native `TemporaryDirectory`. Preserve failed logs,
verify source/input hashes and repeat the complete affected gate; a quota failure
is not passing evidence. Remove the owned scratch after its final needed use.
The observed [2026-10-26 recovery](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6428403275)
is not a universal space requirement or permission to delete shared/caller paths.
