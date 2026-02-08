# Sabueso — Card Size Growth: Risks and Mitigations

Preserving **all values** in the evidence store can generate very large cards and expensive serialization.
This file documents concrete risks and mitigation strategies.

## Risks
- **Serialization cost**: large cards are slow to serialize/deserialize.
- **Memory pressure**: evidence stores can grow to thousands of entries per entity.
- **User friction**: cards become hard to inspect interactively.

## Mitigations (Recommended)
1) **Lazy evidence loading**
   - Store only evidence IDs in the card.
   - Fetch full evidence on demand.

2) **Externalized EvidenceStore**
   - Keep heavy evidence in a separate store (file or DB).
   - Card contains a reference to the store and version.

3) **Evidence compaction**
   - For highly redundant fields, keep normalized values + hashes.
   - Store raw values only when unique or explicitly requested.

4) **Scopes / modes**
   - Support `minimal` vs `full` output modes.
   - Minimal cards carry selected values + minimal provenance.

5) **Indexing and caching**
   - Index evidence by field path for quick retrieval.
   - Cache frequently used evidence subsets.

## Open Decisions
- Which mitigation(s) will be the default for 1.0.0?
- How is external evidence referenced (URI, ID, local path)?
