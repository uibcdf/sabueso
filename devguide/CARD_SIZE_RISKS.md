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

## Proposal under evaluation
- A normalized SQLite store (cards, SourceAssertions and relationships as rows, JSON/JSONL
  kept for exchange): uibcdf/sabueso#27, `devguide/pending_proposals/native_store.md`.

## Open Decisions
- Which mitigation(s) will be the default for 1.0.0?
- How is an externalized SourceAssertion store referenced (URI, ID, local path)?
