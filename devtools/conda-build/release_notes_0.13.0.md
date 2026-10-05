# Sabueso 0.13.0 — Traced source access and pinned explanations

Prepared candidate scope (#121). Publication follows exact-SHA CI, immutable staging,
the installed-package matrix, unchanged promotion, clean public installation and
identical-tag Zenodo archival. These notes are not a publication receipt.

## Source acquisition and citations

- Extend required acquisition observation to ChEMBL, PubChem/BioAssay, BindingDB,
  PDB CCD, UniChem, PDBe-KB, AlphaFold DB and InterPro, alongside the published
  UniProt, Europe PMC and RCSB coverage. Molecular resolution and ligand-deck
  construction retain detached traces at exact result/input pins.
- Preserve logical queries, POST bodies, pages/chunks, response/archive identities,
  original retrieval times, limits/order, reuse/replay, retries, empty answers,
  unavailable fixtures, unqueried access, failures and received subsets.
- Retain source-native releases, assay revisions, model versions and mirror metadata
  with their actual scope and basis. Missing versions stay unknown; linked databases,
  structures, tools and annotation providers do not receive invented direct-access credit.
- Keep verified resource-description bibliography separate from original article,
  assay and annotation-provider citations. Missing bibliographic metadata stays explicit.
  Failed/unqueried operations retain host records without completed-access credit.
- BindingDB's documented empty-string absence forms follow evaluated-empty behavior;
  malformed envelopes and transport failures remain failures (#114).

## Original literature intake

- `extract_literature_mentions` records explicit UniProt mentions in identified supplied
  fragments under `literal_uniprot_mention@1`, retaining Unicode offsets, input hash,
  original tool/configuration and detached attribution.
- Explicit `Card.add_literature_extraction` and `ExtractionStore` preserve original
  support and supplied receipts through save/load/refresh/reuse without rerunning
  extraction or representing it as human curation.
- Explicit Europe PMC `get_article` queries by PMID/PMCID/DOI provide native
  bibliography, complete returned author lists and declared licence literals.
  `article_metadata_binding@1` retains separate metadata assertions, source-stated
  identity, alternatives and exact full/index packet support.
- Metadata does not authenticate arbitrary supplied text or grant fragment rights.
  No abstract/full text is projected; unknown fragment terms remain explicit and
  cannot bypass terms profiles. Broader extraction/validation stays open in #92.

## Explain the knowledge at its original pins

- Add `Card.explain_disease`, `Card.explain_knowledge_state`,
  `Card.explain_measurement`, `Card.explain_bioactivity`, `Card.explain_ligand_site`,
  `Card.explain_ligand` and `Card.explain_oligomer`.
- Retain actual scientific inputs/rules, selected and alternative support, conflicts,
  original assertion versions, bibliography and exact historical item locators.
  Missing support is partial. Readers acquire nothing and add no execution credit.
- `disease_grouping@2` preserves every source-stated identity path and leaves
  contradictory or unfinished branches ungrouped (#115). Names and source order
  cannot choose identity. Explicit `grouping_rule="disease_grouping@1"` remains readable.
- Keep all supporting UniProt versions in knowledge-state explanations (#116),
  and report missing activity-only originals without changing groups/classes (#117).
- `ligand_measurement_count@2` counts distinct included measurement groups and
  reports source records separately (#118). Explicit legacy `@1` remains selectable.
- `interface_site_agreement@2` compares only confirmed UniProt/1-based coordinates
  for this subject, with no conflicting numbering/positions (#120). Unknown or
  incompatible contexts retain reasons and uncomputed `None` sets; computed empty
  sets remain `[]`. Explicit `agreement_rule="interface_site_agreement@1"` reproduces
  the legacy view/explanation at current and historical pins.

## Persist and reuse the application workflow

`examples/persisted_pipeline/` runs independent producer, reader and reuse processes.
Original metadata/extraction support, full/index packets, historical item pins and
portable operation/result/workflow attribution survive reacquisition and advanced
heads. Readers need no source fixtures and add no credit. Guards refuse missing,
modified or misbound sidecars and inconsistent bibliography/context. This is a
public application exercise; Nextia Evidence and MOLI ProjectRecord/Recorda
correlation, reliability and transactional delivery remain consumer/platform work.

## Compatibility and limits

- Python 3.11–3.14; the candidate writes card schema **0.3.12**, with additive literal
  extraction intake and explicit article-metadata support. Published schemas,
  snapshots and saved packet payloads remain readable and unchanged.
- New full/index packet derivations declare the current versioned rules;
  `packet_aspects@6` and the scientific store/packet formats stay fixed.
- Ackredit >=0.9.0 stays a hard runtime dependency. Installed receiving gates use
  the qualified public minimum, independently of newer editable development tools.
- Traceability is required; other built-ins/custom clients, arbitrary derived
  operations and complete bibliography remain explicit gaps (#108). Applications
  persist original runtime sidecars; payload-only readers cannot reconstruct them.
- Literal occurrences are SourceAssertions; derived results carry rules; Nextia
  Evidence, provenance and source terms retain separate responsibilities.
- Diagnostic packaging now rejects stale generated module caches (#113). Published
  Conda installation and qualification use the exact immutable archive.

Tracking: #121 (release), #108 (traceability), #91 (explanations), #92 (literature),
#112 (design review); MOLI #3/#18/#22/#36 (shared consumer/record boundaries).
