# Sabueso — Risks and Open Questions

## Risks
- **Licensing/Terms**: Some sources (DrugBank, eMolecules, ChemSpider) have licensing constraints that may affect redistribution and caching.
- **API Rate Limits**: Public APIs may rate‑limit or change formats.
- **Data Heterogeneity**: Conflicting values across sources require robust conflict handling.
- **Clinical Data Volatility**: Clinical information changes more frequently than core physchem data.

## Open Questions
- What is the canonical **field path** naming scheme (dot‑separated vs another notation)? Current docs use dot‑paths, but this is not yet frozen.
- What are the default **selection rules** per field?
- How do we represent **positional locations** (start/end, sequence indexing)?
- Should local cache include partial cards or only complete cards?
- How to handle **ambiguous inputs** (e.g., common names)?
