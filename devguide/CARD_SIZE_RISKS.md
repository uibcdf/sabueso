# Sabueso — Card Size Growth: Risks and Mitigations

Preserving **all values** in the SourceAssertion store can generate very large cards and expensive serialization.
This file documents concrete risks and mitigation strategies.

## Risks
- **Serialization cost**: large cards are slow to serialize/deserialize.
- **Memory pressure**: SourceAssertion stores can grow to thousands of entries per entity.
- **User friction**: cards become hard to inspect interactively.

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

## Open Decisions
- Which mitigation(s) will be the default for 1.0.0?
- How is an externalized SourceAssertion store referenced (URI, ID, local path)?
