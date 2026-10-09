---
issue: uibcdf/sabueso#112
status: active
---

# Design and implementation review after 0.12.0

The [post-recovery global audit](post_recovery_global_audit.md) supplements this
matrix with measured local source expansion, architectural alignment, documentation
drift and proposed consolidation/delivery acceptance after stash closure (#112).

Reviewed 2026-10-04 at the maintainer's request, after the ChEMBL observation and
first literal literature-extraction slice. This is an implementation audit and
priority proposal, not a replacement architecture or a commitment to every
illustrative capability in the long-term vision.

After publication of 0.13.0, the maintainer approved the next development roadmap
on 2026-10-05: standalone user journeys, the query/explanation/traceability guarantees
they need, peptide scope, and parallel consumer contracts. The current order and
decision/acceptance matrix live in [ROADMAP](../ROADMAP.md#next-roadmap-after-0130).
The matrices below remain implementation evidence and capability gaps; the earlier
slice order is retained as a record of what led to 0.13.0.

## Inputs and interpretation

The original [phases 0–5](../archive/ROADMAP_original_2026-01.md) and conceptual
[`card_schema.yaml`](../../schemas/card_schema.yaml) are historical design inputs.
Current [VISION](../VISION.md), [ARCHITECTURE](../ARCHITECTURE.md),
[SCIENTIFIC_POTENTIAL](../SCIENTIFIC_POTENTIAL.md), [USE_CASES](../USE_CASES.md),
[DECISIONS](../DECISIONS.md), [PUBLIC_API](../PUBLIC_API.md) and
[ROADMAP](../ROADMAP.md) determine how those intentions evolved. Public code and
regression tests provide implementation evidence. A reserved schema field, an
illustrative method name, a connector or a producer-side prototype alone does not
complete a scientific use case or a consumer contract.

Status: **implemented** (the stated bounded behavior exists), **partial** (remaining
behavior is named), **pending** (no implementation), **blocked/deferred** (an owner
decision, access/terms or explicit postponement applies), **changed** (a recorded
decision replaced the original representation), **direction** (non-binding vision).

## Original foundations and core concepts

| Intended capability | State and concrete evidence | Remaining implementation or decision |
| --- | --- | --- |
| Uniform assertions, aggregation and field selection | Implemented: `core/source_assertion_store.py`, `aggregator.py`, `merge.py`, `resolver/field_resolver.py`; mapping, selection and conflict tests | Additional sources must retain alternative assertions and declared selection rules; no alternative knowledge model is needed |
| Entity resolution before composition | Implemented for proteins, small molecules and MONDO-anchored diseases: `tools/resolve.py`, `resolver/entity_resolver.py`, `tools/card/disease.py`; resolution/identity/disease tests | EFO identities without a MONDO anchor remain #96; FASTA/structure-file intake needs a separate identity contract |
| Source-supported identity and explicit ambiguity | Implemented: identity audits, source-stated cross-references, molecule InChIKey anchors, `core/entities.py`; 0.13.0 deterministic disease grouping `@2` preserves all identity paths (#115) | Explicit historical `@1` retains its exposed lookup limitation. Similarity, names and equal residue numbers never authorize merging; sequence alignment belongs to MolSysMT |
| First-class relationships | Implemented: `core/relationship_store.py`, supported predicates and qualifiers; relationship/measurement/curation tests | More predicates require a scientific use and support contract; storage re-evaluation stays #19 |
| Derived knowledge with named rules | Implemented: structure inventory, oligomer, ligand classes, measurement groups, diseases, identity audits, knowledge state; 0.13.0 pinned disease-group, knowledge-state, measurement-group, bioactivity-class, ligand-crossing, site-class and oligomer explanations; versioned ligand group/record count correction (#118) | Explanation of every derived view remains partial (#91); other derived items still need pinned support |
| Reproducible decks | Implemented: `core/deck.py`, membership, exclusions, lineage, intersect/difference, comparison and pinned revision tests | General heterogeneous joins, rankings, neighbors and subgraphs remain directions, not missing promised API |
| Physical quantities across boundaries | Implemented: `core/quantities.py`, PyUnitWizard quantities/seals, integrity and measurement tests | New fields and consumer exchanges must negotiate units; they cannot use bare values or computed field-name units |
| History, pins and exact item reads | Implemented: `core/snapshot.py`, `knowledge_store.py`, migration/refresh and pin regression tests | Shared reference acceptance still depends on MOLI #3/#53; application-level runtime persistence is separate |
| Known/conflicting/not stated/not queried/unavailable | Implemented: `core/knowledge_state.py`, source/enricher coverage, pinned classification-input explanations and regression tests; all UniProt versions retained (#116) | Extend declared coverage with each source; an empty result remains limited to the actual query. Enrichment reports do not record per-request assertion membership |
| Two access levels | Implemented: source `get_*` envelopes and semantic resolution/views | Raw access does not by itself imply complete semantic, licensing or runtime observation coverage |

## Intended scientific functions

| Function or use case | State and concrete evidence | What remains / owner |
| --- | --- | --- |
| Protein and small-molecule knowledge baseline | Implemented: protein/small-molecule builders, stated identity, physchem values, source-supported structures and bioactivities | More source breadth is #83; source keys/terms are #95; computed chemistry remains MolSysSuite's responsibility (#25) |
| Disease as a knowledge entity | Implemented within MONDO scope: cards, disease groups and target/drug decks | #96 for EFO terms lacking source-stated MONDO identity; richer mechanistic knowledge needs explicit sources |
| Peptide cards and commercial availability | Pending: `entity_type: peptide` and supplier fields are placeholders | Define identity, peptide modifications/sequence scope and a real supplier use before CPPsite/eMolecules/ChemSpider integration; audit #112 and registry queue |
| Clinical knowledge | Partial: `core/clinical.py`, ChEMBL phase/indications and cited NCT trials | ADMET, pharmacovigilance, pharmacology, contraindications and drug interactions are unimplemented; source/terms review first (#81/#83/#95). DrugBank remains deferred |
| Tissue-specific isoforms and variants | Partial: UniProt alternative products, gnomAD pext/consequences and GTEx terms, `core/tissue_usage.py` | Explicit native isoform FASTA access is recovered in development; automatic reconstruction/resolution/remapping and additional transcripts remain scoped future work (#80/#102) |
| Comparing proteins and ligand sets | Implemented within stored source-supported identity and supplied residue-map scope: `card_diff.py`, `ligands.py`, `sequences.py` | General structure/sequence similarity and chemical-family enrichment are modeling/analysis or new scoped derived operations; never implicit identity |
| Literature as knowledge | Partial: curated assertions/claims, located Europe PMC annotations, explanations, literal intake/replay, explicit source-stated article bibliography/declared terms and original support/receipt persistence | #92: supplied-fragment rights, broader statement rules and explicit human validation; model extraction comes later |
| Structural representations and model preparation | Partial: structures, constructs, author numbering, sites/interfaces and pinned inventory explanations | Structure-level cards are a design re-evaluation (#20), not a prerequisite for current inventory; modeling exchange needs MOLI/MolSysSuite owner agreement |
| Query/packet contribution to Scientific Context | Partial: `core/packets.py`, pinned full/index packets, conflicts/unknowns, terms and automatic attribution | #71 / MOLI #22: bounded protein subject/aspects today; persistent Nextia consumer acceptance still needs an index, pinned read, explicit Evidence and citation surviving reacquisition |
| Temporal knowledge | Partial: saved revisions, local `as_of`/`changed_since` and source versions | #91/#100: asking remote sources at historical releases is not implemented; local store time is not source-release time |
| Patents and controlled/internal knowledge | Deferred/direction: SureChEMBL mentions do not establish patent-claim scope | #83/#29 and MOLI #17: access, rights and explicit promotion boundary; no automatic ingestion of project conclusions |
| CLI and developer experience | SDK, Sphinx, tests and immutable release qualification implemented | CLI has no demonstrated user need; showcase, small-molecule and per-source user documentation gaps remain in `DOCS_GAPS.md` |

## Final historical review and public HK2 baseline (#112/#83/#95)

[Follow-up 35](../archive/local_work_2026-07/followup_35_final_review_and_hk2.md)
closes all remaining file and scientific-artifact reviews. Native GO-term subject
scope, peptide/supplier/clinical/patent scope and historical query-hint qualification
are retained in [the owning issue update](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6062691987). No further ready generic
runtime restoration is required from the old tree. Future native capabilities and
access-dependent providers retain their own acceptance; audit closure is not their
implementation. [HK2](../HK2_TEST_SYSTEM.md) is now a current public regression
baseline rebuilt from the qualified UniProt response; multi-source expansion needs
additional native fixtures, rather than migration of old cards or notebook outputs.

## Grouped knowledge mapper review follow-up (#112/#83/#95)

[Follow-up 34](../archive/local_work_2026-07/followup_34_grouped_knowledge_mapper_review.md)
reconciles four grouped mappers (30 functions) and ten historical enrichment tests.
Current native measurements, ligand/disease identity, pathways, population/variant
context, source-specific observations, composition and persistent reports replace
their ready behavior. Future native scopes remain explicit: Proteins API peptide/
PTM/HPP provenance beyond PRIDE projects; Open Targets drug/clinical candidates;
DepMap dependencies and quantitative HPA expression; interaction pairs/DDI contacts,
conservation/stability/pocket geometry; direct Rhea descriptions and additional
PDBe-KB provider predictions. Each needs actual native scope, identity, numbering,
units, revisions, support and rights rather than defaults from a synthetic mapper.
Current adoption/deferral decisions remain in force. The
[owning issue update](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6062086611)
preserves acceptance independently of the stash and obsolete Evidence/card fields.

## Protein-query review follow-up (#112/#83)

[Follow-up 33](../archive/local_work_2026-07/followup_33_protein_query_review.md)
reconciles five original resolver/test/UniProt/SCOPe helpers. Current named identity
resolution, exact-sequence candidates without entity resolution and explicit native
isoforms replace their ready behavior. Additional taxonomy common-name/alias
normalization, explicit gene/entry-name lookup and PDB chain/polymer selection are
future native query contracts, with source identity, revisions, namespace, requested
scope, alternatives and failure distinctions preserved independently of the stash.
SCOPe remains retired; a SUNID description row is not a protein or coordinate map.
The [owning issue update](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6061946457)
records acceptance without reviving automatic ranking or sequence identity fallback.

## Native annotation and specialist review follow-up (#83/#112)

[Follow-up 32](../archive/local_work_2026-07/followup_32_uniprot_and_specialist_review.md)
recovers 57 native UniProt statements in unpublished schema 0.3.13: five additional
comment kinds and eight positional kinds with original bounds/molecule scope,
ECO and entry/sequence revisions. Uncertain and revision-mismatched placements are
refused while source statements remain supported. Published 0.3.12 stays frozen.
The preceding UniProt comment/feature requirements are now implemented for these
explicit kinds; broader native metadata and other kinds remain separate.

Five grouped specialist mappers are individually reconciled against bounded current
routes and registry decisions. Remaining gene-level GTEx expression, BRENDA/SABIO-RK
kinetics, NCBI Gene descriptive metadata, QuickGO qualifiers/extensions and richer
Pharos/reference-site/transcript context have explicit native identity/unit/rights/
revision/query/placement acceptance in the report. Existing source adoption or a
prototype caller-protein label does not establish these richer capabilities. Provider
conditional matrices and computation ownership remain authoritative.

## Remaining source metadata and domain requirements (#83/#112)

[Follow-up 31](../archive/local_work_2026-07/followup_31_native_mapper_review.md)
reviews five native mappers and recovers PubChem's independently supported summary
title. Current scoped routes replace the old Evidence constructors. Remaining
requirements have explicit scientific boundaries and can be evaluated without the
historical package tree: additional UniProt comment/feature kinds and record metadata,
protein-associated InterPro domain fragments, structure-scoped RCSB entry titles and
conditionally re-evaluated TED predicted-domain assignments. Current accession dates
and primary citation already belong to RCSB structure context.

Native public UniProt fixtures already include additional text and positional kinds;
that is input availability, not complete typed mapping. Comments need appropriate
unpublished schema decisions; domain endpoints need original modifiers, source
sequence/isoform/revision and separate occurrence support before placement. InterPro
family sites and classification links do not supply matched-domain boundaries. TED
remains retired until native access/rights and model/sequence/domain identity qualify.
Source similarity, cautions, prediction/confidence and classification stay source
statements rather than identity, experimental Evidence or quality conclusions.
The [source acceptance](https://github.com/uibcdf/sabueso/issues/83#issuecomment-6061022497) and report retain individual
conditions and distinguish existing routes from these
remaining capabilities; #83 owns source scope and #112 the implementation review.

## Historical source configuration and persistence requirements

[Follow-up 30](../archive/local_work_2026-07/followup_30_configuration_and_persistence_review.md)
closes two five-file reviews against current source access, versioned resolution
profiles, detached registry metadata, explicit archive reuse and verified card/deck
storage. Useful implemented behavior is already covered; the old dispatcher,
indefinite cache and Evidence store do not supply a further runtime feature.

A unified source input convenience API remains a proposal, with explicit exclusive
client/payload/file choices, native validators and source identity/quantity/sequence
binding, declared-versus-observed retrieval, rights, status and profile override
acceptance retained independently of historical code. Existing bounded supplied-file
routes remain #131; provider/native scope remains #83. Additional convenience
must reuse declared adapters rather than silently activate historical comprehensive
profiles or treat caller licences/releases as source grants/revisions.

## Required traceability and operational closure

Published 0.12.0 observes UniProt, Europe PMC and RCSB acquisition and pinned packet
composition. Release 0.13.0 extends observation to ChEMBL's five logical
operations, preserving page/chunk identities, retries, empty answers, unavailable
fixtures, failures and received subsets. It also observes PubChem compound/structure
lookups and BioAssay target queries, with native per-assay revisions, batches/caps,
PubMed pointers and declarative depositor context. BindingDB REST/fixture/mirror
affinity observation retains query/cutoff bases, caps/order, native publication
forms, original response identities and declared mirror manifests/releases. The
source-local empty-string parsing fix (#114) recognizes declared absence while
malformed/unexpected responses remain failed, retaining wire/archive identities.
Resource descriptions and source-native primary citations remain separate;
missing metadata stays explicit. The new
`literal_uniprot_mention@1` returns original extraction attribution. Explicit intake
and `ExtractionStore` preserve its original support and supplied runtime receipts;
refresh does not rerun extraction. Scientific intake metadata uses published
schema 0.3.12; published 0.3.11 stays fixed. Payload-only refresh states the missing
original runtime sidecar, and unknown fragment terms cannot bypass terms profiles.

Chemical identity observation now covers CCD batches and both UniChem lookup
methods, retaining normalized POST/query identities, native forms, original archive
times, retries, distinct empty/unavailable/unqueried/failed outcomes and completed
subsets on later failures. Versions stay unknown; linked providers are declarative
context. Verified CCD/RCSB and UniChem resource descriptions have separate roles
from source statements. Molecular resolution and ligand-deck construction retain
detached exact result/input pins; saved/ordinarily derived decks acquire nothing.
Identity/mapping/schema policies and published artifacts remain unchanged.

PDBe-KB ligand-site and interface-residue queries now retain separate aggregate
traces, native group locators, distinct mapped/interacting structural references,
unknown versions, original archive identities and empty/failure outcomes. Resource
description credit does not replace missing structure/method/provider citations;
listed resources are PDBe-KB statements, not direct access. Original mapping,
scientific cards, refresh and payload-only saved reads remain unchanged.

AlphaFold DB observation retains native per-record model identities/versions,
including isoforms/fragments and distinct versions at repeated ids. Declared tools,
providers and artifact URLs are context, not extra access or generation execution.
Recommended resource/background citations remain distinct from unreturned model-
specific method/provider references. Unknown versions, partial lists, empty answers,
original archives and failures remain explicit. Existing science and schemas stay fixed.

InterPro's existing family-site residue query now retains signature/member/position
scope, native header/fixture releases, original archive identities and distinct
empty/absent/unavailable/unqueried/failed outcomes. Empty answers cannot establish
accession existence. Member resources are declarations, not direct access;
positions are source-supplied, with no local alignment/InterProScan execution.
Resource-description credit does not fill missing member/signature/site citations.
Scientific maps/cards/schema and payload-only saved readers remain unchanged.

Development ClinicalTrials.gov study/reference queries now observe native NCT,
page/version/reuse/empty/failure scope; explicit Europe PMC lookups contribute
original article metadata, including collective authors (#127/#128). Clinical
SourceAssertions and frozen schema remain unchanged. Linked targets are not followed
automatically; wider clinical semantics and bibliography remain pending.

#108 is still partial: other built-ins/custom clients remain
unobserved; arbitrary views/deck operations and full bibliography are not covered.
Applications explicitly persist original runtime sidecars. Payload-only readers
cannot reconstruct execution and add no credit. ChEMBL's existing release cache is
declared as client-reported metadata, not per-page release proof; coherent historical
release handling remains a retrieval/cache design concern in #100/#108.

All eight read-only pilot notebook copies execute with public Sabueso 0.12.0 in a
separate installed-package environment. Temporary application instrumentation saves
original traces and portable attribution outside both repositories. This is an
operational test, not disclosure of pilot scientific content, validation of every
source's availability, or a claim that every source is observed. Original notebooks
remain unchanged. Their application must explicitly retain sidecars when adopted.

The development checkpoint passes 1,924 offline cases in the required Python 3.14
editable environment (26 online cases deselected). A byte-checked clean diagnostic
wheel passes 613 unchanged acquisition/attribution/extraction/intake/explanation/application cases
outside the checkout with public Ackredit 0.9.0, the public three-packet workflow
and pip check. Ruff, frozen card shape, schema/registry, governance, dependency
preflight and warning-failing Sphinx gates pass. The wheel check also rejects the
observed stale incremental artifact (#113); generated `build/` output is no longer
versioned. Exact remote commit CI is tracked in the owning issue, separately from
these local checks and the immutable 0.12.0 release receipts.

The remaining ProjectRecord/Recorda correlation, routing, reliability and strict
recording policy belong to MOLI #36/#18. Sabueso's provisional record formats must
not be promoted unilaterally to a shared platform contract. Nextia owns project
Evidence; MolSysSuite owns calculations, alignments and modeling interfaces.

## Implementation slices reviewed before 0.13.0

This earlier sequence records delivered slices and remaining acceptance boundaries.
For the approved next priorities, use
[the roadmap after 0.13.0](../ROADMAP.md#next-roadmap-after-0130).

1. **Literal extraction intake (#92): implemented within the delivered rule.**
   Explicit intake/replay preserves original text identity/location, tool/version,
   terms gaps and supplied original attribution. Save/load/refresh retain historical
   support; no extraction passes through `CurationStore` as human curation. Schema
   0.3.12 is published and frozen in 0.13.0. Explicit article bibliography/declared terms are implemented;
   fragment rights, broader rules and validated model extraction remain #92 work.
2. **Extend chemical observation (#108).** PubChem compound/structure/BioAssay
   observation is implemented, including native per-assay revisions, batches/caps,
   original PubMed pointers and distinct empty/rejected/unavailable/failure outcomes.
   BindingDB REST/fixture/mirror affinity observation is also implemented, with
   native response/manifest identities, cutoff/retrieval-time bases, limits/order,
   DOI/PubMed forms and original empty/unavailable/unqueried/failed/partial outcomes.
   Assay summaries do not prove row/property versions; mirror manifests do not
   establish a live REST release. Keep custom-client gaps explicit. The source-local
   #114 parser fix recognizes declared empty strings without turning malformed
   responses into absence. Further source slices follow exercised use.
3. **Disease-group explanations (#91/#115): versioned correction implemented.**
   `Card.explain_disease` retains selected association/annotation support,
   source-stated identity/hierarchy, alternatives and named grouping rules at exact
   pins without requests, mapping reruns or card mutation. Ungrouped context is
   explicitly whole-card; incomplete stored support is partial. Default `@2`
   retains every identity path, leaves contradictory or unfinished branches
   ungrouped and preserves alternative labels/hierarchy paths. Explicit `@1`
   reproduces historical lookup and partial explanation at original pins.
   `Card.explain_knowledge_state` now retains exact classification inputs and
   selected/alternative scientific support at original pins, separately from
   source coverage and request outcomes. Missing support is partial, including
   rows lost through missing assertions; absence never becomes a negative assertion.
   #116 fixes the multi-version UniProt crash without choosing a release. Other
   derived-view explanations remain #91 work. `Card.explain_measurement` and
   `Card.explain_bioactivity` now retain actual grouping/class-voter decisions,
   precision/threshold quantities and original support at exact pins. Whole-card
   candidate/glossary context and stored identity locators remain explicit; no
   identity path or assertion membership is invented. `Card.explain_ligand_site`
   and `Card.explain_ligand` now trace site classes and protein/molecule crossing,
   retaining annotated fields/conflicts, structural instances, actual identity/class
   choices and native deck snapshot/membership metadata. Duplicate members remain
   explicit. `Card.explain_oligomer()` now retains actual partner/agreement inputs,
   source assemblies/alternatives, family members, original support and historical
   pins (`oligomer_explanation@2`). Missing support and unconfirmed numbering stay
   partial. The #120 correction defaults to confirmed agreement `@2`, with native
   reasons/uncomputed sets for unknown, incompatible or conflicting inputs.
   Explicit agreement `@1` reproduces the prior view/explanation at historical
   pins; existing packet payloads stay unchanged. Other derived items still
   need explanations. The #118 correction
   counts distinct included groups across matched molecule/parent items under
   `ligand_measurement_count@2`, with explicit source records, exact counted ids
   and `ligand_deck_explanation@2`. Explicit `@1` retains the published numeric
   counter at current/historical pins. Group/class/voter/scope policies stay fixed.
   The #117 correction reports missing activity-only originals while preserving
   groups/classes and exact copy pointers; later local joins remove the singleton
   diagnostic. Current and historical readers remain inert.
4. **Receive consumer acceptance (#71/#53, MOLI #22/#3/#36).** Implement a real
   persistent consumer exercise in the consumer repository when ready. This is a
   coordination dependency, not missing Nextia code to add inside Sabueso.
   `examples/persisted_pipeline/` now closes the bounded public application exercise:
   independent producer/reader/reuse processes, full/index packets, exact historical
   item reads, original metadata/extraction support and verified sidecar/workflow
   bindings survive reacquisition. Consumer-owned Evidence and shared ProjectRecord/
   Recorda reliability acceptance remain open.
5. **Scope the next scientific expansion.** Choose peptide/supplier or clinical
   coverage from a stated use, define identity, quantities and rights before a
   connector. Keep #101 mirror work postponed until the maintainer reschedules it.

Do not treat generalized graph/RAG infrastructure, model-generated conclusions,
descriptor/fingerprint calculations, automatic project-to-knowledge promotion or
an immediate new release as implied by this review. The implemented foundations
support focused scientific additions; the remaining gaps above have distinct owners
and acceptance conditions.

## Explicit article metadata follow-up (#92/#108)

The literal intake route now accepts explicit source-stated article metadata under
`article_metadata_binding@1`: native complete returned authors/bibliography/identifiers,
licence literals and original acquisition/support survive store replay, card refresh
and pinned full/index packet reads. Alternatives stay separate; no text is fetched
through full-text access or inferred from metadata. Fragment rights, broader rules,
validation, shared platform/consumer acceptance and remaining source coverage
remain open. This extends foundational support/terms integrity and the generic need
to preserve original source references across receiving pipelines.

## Published 0.13.0 checkpoint (#121)

The bounded implementation above is published and exact-artifact qualified in
0.13.0: CI 15/15, all 12 installed OS/minor lanes and clean public installation
pass 613 receiving cases and the public workflow; all 960 Zenodo source files
equal the qualified tag. The local full offline checkpoint passes 1,926 cases.
Receipt: `devtools/conda-build/receipts/sabueso_0.13.0_public_2026-10-05.json`.
Broader source/result/bibliography coverage, extraction/explanation gaps and
consumer-owned Nextia Evidence / MOLI ProjectRecord / Recorda acceptance remain
the next work, not completed by publication.

## Quality completion proposal (2026-10-09, #112)

This proposal makes the approved roadmap's acceptance concrete. The
[roadmap](../ROADMAP.md#immediate-resumption-sequence) owns development order;
this is neither a replacement architecture nor approval to publish a new release.
Sabueso's strength is source-supported knowledge that a scientist can inspect,
reuse and cite. Source counts and passing test counts measure bounded scope,
not complete scientific usefulness.

Current baseline: 0.14.0 is exact-artifact qualified. Subsequent SQLite lifetime
(#133), GTEx prerequisite (#135) and shared-source attribution (#136) corrections
are exact-SHA qualified on main and need separate installed-artifact delivery.
The existing protein/comparator, molecule/activity and disease/entity examples
provide public producer/reader/reacquisition routes. Broader consumer, bibliography,
explanation, terms and query guarantees remain open.

| Work package | Concrete improvement | Acceptance and owner |
| --- | --- | --- |
| Finish current consumer validation | Complete the declared original-answer routes and evaluate whether their outputs answer the scientific questions | Every exercised question has a supported answer, conflict, explicit unknown or failed/unqueried scope; saved independent readers preserve original statements, quantities, pins and citations. Human usefulness review and installed-artifact validation remain distinct. #132/#112 |
| Reconcile delivery and maintained guidance | Remove false current claims that delivered fixes remain unpublished; link each completed defect to its actual release evidence | Issue closure cites the exact source/artifact and regression modules; living risk/gap documents agree with CHECKPOINT. Dated receipts and frozen reports remain unchanged. #112 |
| Make scientific inspection consistent | Let users inspect values, alternatives, support, source scope, units, revisions, rights and gaps through the existing SDK views and reports | A public journey identifies those facts without private helper code; each selected value leads to its supporting assertions and each unknown explains its scope. Current-source terms are labelled separately from historical scientific state. #112/#91/#29 |
| Complete explanations along exercised routes | Extend pinned explanations to remaining source-supported sequence/tissue/comparative findings where real use requires them | Exact inputs, rule/version, parameters, inclusion/exclusion and incomplete support remain inspectable at original pins; inert readers acquire nothing and never substitute current heads. #91 |
| Complete observed operations and bibliography along those routes | Make actual access, reused answers, failed subsets and missing citations visible, independently of scientific support | Tests cover successful, empty, unavailable, failed, truncated and replayed operations; received response identities/times and portable sidecars survive independent reading. Uncovered/custom clients remain explicitly unobserved. #108 |
| Extend literature beyond identifiers and bibliography | Add a bounded, rights-qualified way to retain a scientifically useful statement from its actual source location | The original fragment, article identity, extraction/curation method and version, review status and contradictory assertions remain inspectable and survive storage/refresh. A project interpretation remains consumer-owned Evidence. Broader extraction starts from a real question and explicit human validation. #92/#29/#112 |
| Finish one bounded clinical/query/terms slice | Integrate explicit study/publication references into a saved journey, then select one non-protein question or finer use-term filter | Public example and regressions declare identity, constraints, terms, retained/excluded support and unresolved bibliography; historical examples keep their original versions. #108/#112, then #71/#91 or #29 |
| Qualify cost and failure behavior | Measure a bounded ordinary workload and a larger workload before changing storage or acquisition defaults | Record import baseline, elapsed time, response/archive/card/store bytes and process-memory scope. Pagination, rate limits, retries and partial failures remain visible; bounded requests do not discard scientific support silently. Set workload-specific budgets from measurements. #98/#88/#100 |
| Deliver a coherent installed checkpoint | Propose a maintenance release after the selected corrections and acceptance are ready | Candidate CI, exact staging artifact, all supported installed OS/Python lanes, clean public installation and archive checks pass for the same candidate. No earlier source or artifact receipt qualifies a later candidate. Local release governance |

Treat consistency work as targeted changes to an exercised contract, with meaningful
regressions. A new facade, broad refactor, source wave, automatic model interpretation
or performance rewrite needs a demonstrated gap and its own bounded acceptance.
The public showcase and comparative-source user pages should be refreshed from
qualified public fixtures as these routes become ready; private consumer content
and results stay in their controlled workspace.

Cross-component acceptance remains with its owners: MOLI for shared references,
packets and recording; Nextia for project Evidence; MolSysSuite for modeling,
alignment and computed geometry. Nextia's recorded design pause does not prevent
standalone Sabueso improvements and is not permission to implement Discovery here.
Peptide identity and other domain expansion follow the approved roadmap after
these journey and contract decisions.
