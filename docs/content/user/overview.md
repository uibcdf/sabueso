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
- **Evidence links** for each selected field.
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

- Traceability first: evidence is never discarded.
- Canonical schema: dot-separated field paths and versioned rules.
- Practical interoperability: Card/Deck in memory, explicit persistence by user choice.

## Current Scope

Integrated sources include UniProt, PDB, ChEMBL, PubChem, GO, InterPro,
STRING, BioGRID, CATH, SCOPe, TED, and PhosphoSitePlus.

## See Also

- {doc}`quickstart`
- {doc}`concepts`
- {doc}`field_paths`
- {doc}`selection_rules`
- {doc}`storage`
- {doc}`testing`
