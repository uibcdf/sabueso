# Sabueso — Checkpoint (Current Repo State)

This file records the current repository baseline so new developers can resume exactly from this state.

## Repository Structure (Created)
- `sabueso/`
  - `core/` (placeholders: `card.py`, `deck.py`, `evidence_store.py`)
  - `resolver/` (placeholder: `base.py`)
  - `tools/db/`, `tools/card/`, `tools/deck/`
  - `ops/` (placeholders: `card_ops.py`, `deck_ops.py`)
  - `mappings/` (README placeholder)
  - `utils/` (internal utilities only; currently empty)
- `docs/`
  - `conf.py` (Sphinx, **pydata_sphinx_theme**)
  - `index.rst` (minimal)
  - `README.md` (placeholder)
- `tests/` (directories created with `.gitkeep`)

## Notes
- `schemas/card_schema.yaml` remains a **conceptual** schema draft.
- The `schemas/` directory is **temporary** until Card/Deck classes are fully defined.
- Phase‑0 focus is on structure, interfaces, and documentation, not implementation.

## New Decisions (Today)
- **Field path notation**: dot‑separated paths (e.g., `properties.physchem.molecular_weight`).
- **Evidence object**: includes `source` with `type`, `name`, `record_id`, plus optional `source_meta`.
- **Location model**: general model with `kind` and sub‑blocks (sequence / structure / atom / substructure). To be refined with real cases, but accepted conceptually.

## New Artifacts
- `devguide/LOCATION_EXAMPLES.md`: real‑ID validation examples for location model.
- `devguide/SCHEMA.md`: link to `LOCATION_EXAMPLES.md`.

## Pending Decisions
- Final **schema versioning policy**.
- Local cache policy (raw sources vs cards vs both).
- Minimal core ops guaranteed for Card/Deck.
- LLM integration policy (provider, prompts, evidence tracking).

## Next Steps
1) Define minimal **interfaces** for Card, Deck, EvidenceStore, Resolver (no implementation).
2) Align evidence object structure in schema and docs (if needed).
3) Validate location model with additional real cases when ready.
