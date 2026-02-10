# Sabueso — Recommended Storage Layout (Project-Level)

This is a **recommendation only**. There are **no default paths** in Sabueso.
Users must choose where to store Cards/Decks in their project.

## Suggested Layout

```
project_root/
  data/
    raw/                # raw source payloads (JSON/XML)
    cards/              # resolved cards
      cards.jsonl       # JSONL deck
      cards.db          # SQLite deck
    decks/              # optional per-deck files
      ligands.jsonl
      interactors.jsonl
```

## Notes
- JSON/JSONL is recommended for transparency and version control.
- SQLite is recommended for large datasets and fast queries.
- Raw payloads are optional, but recommended for reproducibility.
