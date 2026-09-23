# Sabueso

Sabueso is a scientific Python library for aggregating and normalizing biomolecular data across multiple public databases. Given a molecular system (protein, peptide, small molecule, etc.), it produces a structured **Card** of resolved molecular knowledge in which every value is linked to the **SourceAssertions** (what each external source asserts) that support it. A **Deck** is a collection of cards with consistent operations.

## Status
Early design and scaffolding phase. The developer guide is the source of truth.

Supported Python versions: 3.11, 3.12, 3.13 and 3.14 (offline test suite in CI).

## Quick Start (for developers)
- Read `devguide/VISION.md` and `devguide/ARCHITECTURE.md`.
- Use `devguide/CHECKPOINT.md` for the current repo baseline.
- The conceptual schema lives in `schemas/card_schema.yaml`.

## Repository Layout (Phase 0)
```
sabueso/
  core/
  resolver/
  tools/
    db/
    card/
    deck/
  ops/
  mappings/
  utils/
docs/
tests/
```

## Documentation
Sphinx docs live in `docs/` and use the **pydata_sphinx_theme**.
