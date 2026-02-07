# Sabueso — Risks and Open Questions

## Risks
- **Licensing/Terms**: Some sources (DrugBank, eMolecules, ChemSpider) have licensing constraints that may affect redistribution and caching.
- **API Rate Limits**: Public APIs may rate‑limit or change formats.
- **Data Heterogeneity**: Conflicting values across sources require robust conflict handling.
- **Clinical Data Volatility**: Clinical information changes more frequently than core physchem data.

## Architecture Risks (General)
- **Evidence growth**: preserving all values can create very large cards and stores.
- **Mapping fragility**: changes in source APIs can break field mappings.
- **Ambiguity**: input resolution may produce multiple valid entities.
- **Ops drift**: unstable ops contracts can break tools and downstream integrations.
- **Schema churn**: frequent schema changes can break cards, tools, and mappings.

## Open Questions
- What are the default **selection rules** per field?
- Should local cache include partial cards or only complete cards?
- How to handle **ambiguous inputs** (e.g., common names)?
- What is the **schema versioning policy** (major/minor compatibility rules)?
- What is the **local cache policy** (raw sources vs cards vs both) given licensing constraints?
- What are the minimal **core ops** guaranteed on Card/Deck objects?
- What is the **LLM integration policy** (provider, prompts, and evidence tracking)?
