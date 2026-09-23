# Overview

Sabueso transforms heterogeneous biomolecular and chemical source payloads into
structured, traceable outputs.

Tagline:
- From database fragments to structured molecular intelligence.

## What Sabueso Produces

- **Card**: one entity (protein, peptide, small molecule) with canonical field values.
- **Deck**: a collection of Cards for batch operations and downstream workflows.

## What Sabueso Preserves

- **Canonical values** for usability.
- **SourceAssertion links** for each resolved field.
- **Conflict records** whenever sources disagree.

## Core Pipeline

Sabueso's processing model is deterministic and auditable:

```text
source payloads
  -> mappings
  -> merge
  -> resolver (selection rules)
  -> card/deck
```

## Design Principles

- Traceability first: source assertions are never discarded.
- Canonical schema: dot-separated field paths and versioned rules.
- Practical interoperability: Card/Deck in memory, explicit persistence by user choice.

## Current Scope

Integrated sources include UniProt, RCSB PDB, ChEMBL, PubChem and STRING. GO annotations,
InterPro/Pfam/CATH/SCOP-family classifications and curated IntAct interactions reach a
protein card as typed relationships stated by UniProt.

## See Also

- {doc}`quickstart`
- {doc}`concepts`
- {doc}`field_paths`
- {doc}`selection_rules`
- {doc}`storage`
- {doc}`testing`
