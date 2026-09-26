# Sabueso — Card Size Growth: Risks and Mitigations

Preserving **all values** in the SourceAssertion store can generate very large cards and expensive serialization.
This file documents concrete risks and mitigation strategies.

## Risks
- **Serialization cost**: large cards are slow to serialize/deserialize.
- **Memory pressure**: SourceAssertion stores can grow to thousands of entries per entity.
- **User friction**: cards become hard to inspect interactively.

## Measured growth
- A TcTIM ProteinCard grows from about 37 KB to about 1.0 MB of compact JSON when its 493
  ChEMBL bioactivities are added (2026-09-23; uibcdf/sabueso#23). That is about 2 KB per
  measurement: roughly 1.1 KB for the verbatim SourceAssertion and 0.9 KB for the
  relationship.
  - Assay records are already shared per assay.
  - A target with tens of thousands of activities would give cards of tens of MB.
  - Storage re-evaluation: uibcdf/sabueso#19.
- The same card with every source of 0.4.0 weighs about 2.8 MB of indented JSON
  (2026-09-25). The build asks ChEMBL for all its records, plus BindingDB and PubChem
  BioAssay (1002 PubChem records, whose declared copies pull in the ChEMBL assays they
  name). The frozen card of schema 0.3.4 was kept at 380 KB by leaving PubChem BioAssay
  out and limiting ChEMBL to 25 records.

## Mitigations (Recommended)
1) **Lazy SourceAssertion loading**
   - Store only SourceAssertion IDs in the card.
   - Fetch full SourceAssertions on demand.

2) **Externalized SourceAssertionStore**
   - Keep heavy SourceAssertions in a separate store (file or DB).
   - Card contains a reference to the store and version.

3) **SourceAssertion compaction**
   - For highly redundant fields, keep normalized values + hashes.
   - Store raw values only when unique or explicitly requested.

4) **Scopes / modes**
   - Support `minimal` vs `full` output modes.
   - Minimal cards carry selected values + minimal provenance.

5) **Indexing and caching**
   - Index SourceAssertions by field path for quick retrieval.
   - Cache frequently used SourceAssertion subsets.

## Implemented
- The `KnowledgeStore` (since 0.3.0; uibcdf/sabueso#27, `devguide/archive/native_store.md`)
  is a normalized SQLite store. SourceAssertions and relationships are rows shared by
  content across revisions and cards, so storing many revisions of a large card does not
  multiply its size. The card itself is still whole in memory, so mitigations 1–4 remain
  open for very large targets.

## Open Decisions
- Which mitigation(s) will be the default for 1.0.0?
- How is an externalized SourceAssertion store referenced (URI, ID, local path)?

## Glossary of entities (#52)

The glossary adds one entry per molecular entity the card mentions. On TcTIM, with the
structural baseline and 493 ChEMBL measurements, it holds 264 entities in 53 KB, about 4%
of the card. It also removes the repetition that curated measurements would have had
(each carried the molecule's full list of records).

