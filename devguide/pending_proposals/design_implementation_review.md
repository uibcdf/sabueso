---
issue: uibcdf/sabueso#112
status: active
---

# Design and implementation review after 0.12.0

Reviewed 2026-10-04 at the maintainer's request, after the ChEMBL observation and
first literal literature-extraction slice. This is an implementation audit and
priority proposal, not a replacement architecture or a commitment to every
illustrative capability in the long-term vision.

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
| Source-supported identity and explicit ambiguity | Implemented: identity audits, source-stated cross-references, molecule InChIKey anchors and `core/entities.py` | Similarity, names and equal residue numbers never authorize merging; sequence alignment belongs to MolSysMT |
| First-class relationships | Implemented: `core/relationship_store.py`, supported predicates and qualifiers; relationship/measurement/curation tests | More predicates require a scientific use and support contract; storage re-evaluation stays #19 |
| Derived knowledge with named rules | Implemented: structure inventory, oligomer, ligand classes, measurement groups, diseases, identity audits, knowledge state | Explanation of every derived view is partial; disease-group explanations are a bounded next candidate in #91 |
| Reproducible decks | Implemented: `core/deck.py`, membership, exclusions, lineage, intersect/difference, comparison and pinned revision tests | General heterogeneous joins, rankings, neighbors and subgraphs remain directions, not missing promised API |
| Physical quantities across boundaries | Implemented: `core/quantities.py`, PyUnitWizard quantities/seals, integrity and measurement tests | New fields and consumer exchanges must negotiate units; they cannot use bare values or computed field-name units |
| History, pins and exact item reads | Implemented: `core/snapshot.py`, `knowledge_store.py`, migration/refresh and pin regression tests | Shared reference acceptance still depends on MOLI #3/#53; application-level runtime persistence is separate |
| Known/conflicting/not stated/not queried/unavailable | Implemented: `core/knowledge_state.py`, source/enricher coverage and regression tests | Extend declared coverage with each source; an empty result remains limited to the actual query |
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
| Literature as knowledge | Partial: curated assertions/claims, located Europe PMC annotations, explanations and the new detached `tools/literature.py` literal rule | #92: original extraction intake/replay without relabeling it as curation, article metadata/terms, broader statement rules and explicit human validation; model extraction comes later |
| Structural representations and model preparation | Partial: structures, constructs, author numbering, sites/interfaces and pinned inventory explanations | Structure-level cards are a design re-evaluation (#20), not a prerequisite for current inventory; modeling exchange needs MOLI/MolSysSuite owner agreement |
| Query/packet contribution to Scientific Context | Partial: `core/packets.py`, pinned full/index packets, conflicts/unknowns, terms and automatic attribution | #71 / MOLI #22: bounded protein subject/aspects today; persistent Nextia consumer acceptance still needs an index, pinned read, explicit Evidence and citation surviving reacquisition |
| Temporal knowledge | Partial: saved revisions, local `as_of`/`changed_since` and source versions | #91/#100: asking remote sources at historical releases is not implemented; local store time is not source-release time |
| Patents and controlled/internal knowledge | Deferred/direction: SureChEMBL mentions do not establish patent-claim scope | #83/#29 and MOLI #17: access, rights and explicit promotion boundary; no automatic ingestion of project conclusions |
| CLI and developer experience | SDK, Sphinx, tests and immutable release qualification implemented | CLI has no demonstrated user need; showcase, small-molecule and per-source user documentation gaps remain in `DOCS_GAPS.md` |

## Required traceability and operational closure

Published 0.12.0 observes UniProt, Europe PMC and RCSB acquisition and pinned packet
composition. Unreleased development extends observation to ChEMBL's five logical
operations, preserving page/chunk identities, retries, empty answers, unavailable
fixtures, failures and received subsets. Resource descriptions and source-native
primary citations remain separate; missing metadata stays explicit. The new
`literal_uniprot_mention@1` returns original extraction attribution without changing
stored card schema 0.3.11. It is a detached extraction, not automatic card intake.

#108 is still partial: PubChem, BindingDB and other built-ins/custom clients remain
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

The development checkpoint passes 1,397 offline cases in the required Python 3.14
editable environment (26 online cases deselected). A byte-checked clean diagnostic
wheel passes 89 unchanged acquisition/attribution/extraction integration cases
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

## Proposed order and acceptance

1. **Complete extraction intake (#92).** A publication-scoped, explicitly invoked
   intake/replay path must preserve each original text identity/location, named tool
   and version, terms gaps and original attribution. Save/load/refresh retains
   historical support and does not route extractions through `CurationStore` as
   human assertions. Any added persisted metadata starts the next unpublished schema.
2. **Extend chemical observation (#108).** PubChem then BindingDB, based on exercised
   use. Preserve source-specific queries, versions, caps, native citations and actual
   local/network/archive routes; test empty/unavailable/unqueried/failed/partial
   outcomes with the published Ackredit floor. Keep custom-client gaps explicit.
3. **Close one derived explanation gap (#91).** Disease groups should explain the
   selected sources, source-stated identities/hierarchy, alternatives and named
   grouping rule at exact pins without source requests or silent recomputation.
4. **Receive consumer acceptance (#71/#53, MOLI #22/#3/#36).** Implement a real
   persistent consumer exercise in the consumer repository when ready. This is a
   coordination dependency, not missing Nextia code to add inside Sabueso.
5. **Scope the next scientific expansion.** Choose peptide/supplier or clinical
   coverage from a stated use, define identity, quantities and rights before a
   connector. Keep #101 mirror work postponed until the maintainer reschedules it.

Do not treat generalized graph/RAG infrastructure, model-generated conclusions,
descriptor/fingerprint calculations, automatic project-to-knowledge promotion or
an immediate new release as implied by this review. The implemented foundations
support focused scientific additions; the remaining gaps above have distinct owners
and acceptance conditions.
