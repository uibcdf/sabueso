# Sabueso — Risks and Open Questions

## Risks
- **Licensing/Terms**: Some sources (DrugBank, eMolecules, ChemSpider) have licensing constraints that may affect redistribution and caching.
- **API Rate Limits**: Public APIs may rate‑limit or change formats.
- **Data Heterogeneity**: Conflicting values across sources require robust conflict handling.
- **Clinical Data Volatility**: Clinical information changes more frequently than core physchem data.

## Architecture Risks (General)
- **SourceAssertion growth**: preserving all values can create very large cards and stores.
- **Mapping fragility**: changes in source APIs can break field mappings.
- **Ambiguity**: input resolution may produce multiple valid entities.
- **Ops drift**: unstable ops contracts can break tools and downstream integrations.
- **Schema churn**: frequent schema changes can break cards, tools, and mappings.
- **Recorded Sabueso version in development environments**: `sabueso.__version__`, and
  therefore the `sabueso_version` of derivation records, comes from the installed
  distribution's metadata. If the imported code is another copy (a worktree on
  `PYTHONPATH`, or a stale `sabueso.egg-info` at the repository root), cards record a
  version that did not write them. Published packages are not affected. Frozen cards are
  therefore built from the published package (#42).
- **Concurrent curation stores** (uibcdf/sabueso#48): a `CurationStore` is rewritten
  whole on every save. The write is atomic (temporary file, then replace), but two people
  saving to the same file at the same time lose the first writer's new records: the last
  writer wins. Until the native store (#27) gives records a transactional home, use one
  store per curator or merge through version control.
- **Stored curation values** (#48): records keep the value in its stored form, so
  re-applying gives the same id. If a field's item shape changes in a new schema version,
  re-application raises instead of silently changing the id. Stores then need a
  migration.

## Open Questions
- What are the default **selection rules** per field?
- Should local cache include partial cards or only complete cards?
- How to handle **ambiguous inputs** (e.g., common names)?
- What is the **schema versioning policy** (major/minor compatibility rules)?
- What is the **local cache policy** (raw sources vs cards vs both) given licensing constraints?
- What is the **LLM integration policy** (provider, prompts, and SourceAssertion tracking)?
