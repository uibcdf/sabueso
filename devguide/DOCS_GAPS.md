# Documentation Gaps (Content Needed)

This list captures **missing deep content** for the documentation.

## Core Concepts
- Formal definition of Card/Deck structures and expected field semantics.
- EvidenceStore lifecycle and how evidences are created/linked.
- Resolver logic with examples and conflict reporting.

## Field Paths
- Detailed description of each canonical field, type, and expected value shape.
- Differences by card type (Protein/Peptide/SmallMolecule).

## Data Sources
- Per-source coverage tables (what fields are populated by each DB).
- Known limitations and update frequency of each source.

## Selection Rules
- Full published ruleset with rationale per field.
- Examples of rule overrides.

## Storage & Cache
- Best practices for raw vs card persistence.
- Recommended layouts for lab projects.
- Tradeoffs for JSON/JSONL vs SQLite.

## Operations
- Examples for compare, extract, derive_deck.
- Expected outputs and error semantics.

## Testing
- What each test category validates.
- Guidance for running online tests (keys, env vars).

## Integration
- How Sabueso integrates with MolSysSuite (TopoMT, PharmacophoreMT, MolSysMT).
- Expected interoperability contracts.
