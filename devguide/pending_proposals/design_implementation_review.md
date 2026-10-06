---
issue: uibcdf/sabueso#112
status: active
---

# Design and implementation review after 0.12.0

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
| Tissue-specific isoforms and variants | Partial: UniProt alternative products, gnomAD pext/consequences and GTEx terms, `core/tissue_usage.py` | Isoform sequences are not fetched (#80); additional transcripts only when actual coverage needs them (#102) |
| Comparing proteins and ligand sets | Implemented within stored source-supported identity and supplied residue-map scope: `card_diff.py`, `ligands.py`, `sequences.py` | General structure/sequence similarity and chemical-family enrichment are modeling/analysis or new scoped derived operations; never implicit identity |
| Literature as knowledge | Partial: curated assertions/claims, located Europe PMC annotations, explanations, literal intake/replay, explicit source-stated article bibliography/declared terms and original support/receipt persistence | #92: supplied-fragment rights, broader statement rules and explicit human validation; model extraction comes later |
| Structural representations and model preparation | Partial: structures, constructs, author numbering, sites/interfaces and pinned inventory explanations | Structure-level cards are a design re-evaluation (#20), not a prerequisite for current inventory; modeling exchange needs MOLI/MolSysSuite owner agreement |
| Query/packet contribution to Scientific Context | Partial: `core/packets.py`, pinned full/index packets, conflicts/unknowns, terms and automatic attribution | #71 / MOLI #22: bounded protein subject/aspects today; persistent Nextia consumer acceptance still needs an index, pinned read, explicit Evidence and citation surviving reacquisition |
| Temporal knowledge | Partial: saved revisions, local `as_of`/`changed_since` and source versions | #91/#100: asking remote sources at historical releases is not implemented; local store time is not source-release time |
| Patents and controlled/internal knowledge | Deferred/direction: SureChEMBL mentions do not establish patent-claim scope | #83/#29 and MOLI #17: access, rights and explicit promotion boundary; no automatic ingestion of project conclusions |
| CLI and developer experience | SDK, Sphinx, tests and immutable release qualification implemented | CLI has no demonstrated user need; showcase, small-molecule and per-source user documentation gaps remain in `DOCS_GAPS.md` |

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
