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
- Editable install works offline with: `pip install --no-deps --editable .`

## New Decisions (Today)
- **Field path notation**: dot‑separated paths (e.g., `properties.physchem.molecular_weight`).
- **Evidence object**: includes `source` with `type`, `name`, `record_id`, plus optional `source_meta`.
- **Location model**: general model with `kind` and sub‑blocks (sequence / structure / atom / substructure). To be refined with real cases, but accepted conceptually.

## New Artifacts
- `devguide/LOCATION_EXAMPLES.md`: real‑ID validation examples for location model.
- `devguide/SCHEMA.md`: link to `LOCATION_EXAMPLES.md`.
- `devguide/INTERFACES_MINIMAL.md`: minimal core interfaces for Card/Deck/EvidenceStore/Resolver.
- `sabueso/mappings/` (Python mapping stubs):
  - `uniprot.py`, `pdb.py`, `pubchem.py`, `chembl.py`, `base.py`
- `sabueso/core/evidence_store.py`: EvidenceStore implementation with deterministic IDs.
- Mappings now emit `evidences` and `field_evidence` (minimal).
- `sabueso/core/aggregator.py`: minimal card builder from mapping outputs.
- `sabueso/core/card.py`: minimal Card implementation.
- `sabueso/core/deck.py`: minimal Deck implementation.
- `sabueso/tools/db/uniprot.py`: offline + online UniProt card creation helpers.
- `tests/core/test_mapping_uniprot_offline.py`: offline smoke test for UniProt mapping.
- `tests/core/test_online_*.py`: online smoke tests (UniProt, PDB, PubChem, ChEMBL).
- `devguide/TESTS.md`: offline/online test strategy.
- `pyproject.toml`: minimal packaging config for editable installs.

## Pending Decisions
- Final **schema versioning policy**.
- Local cache policy (raw sources vs cards vs both).
- LLM integration policy (provider, prompts, evidence tracking).

## Next Steps
1) Commit/push the latest UniProt online helper changes (if not yet done).
2) Add `tools.db` stubs for PDB / PubChem / ChEMBL (offline + online).
3) Expand mappings with additional fields and sources.
4) Validate location model with additional real cases when ready.
