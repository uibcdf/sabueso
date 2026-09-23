# Sabueso — Checkpoint (Current Repo State)

This file records the current repository baseline so new developers can resume exactly from this state.

## Repository Structure (Created)
- `sabueso/`
  - `core/` (placeholders: `card.py`, `deck.py`, `source_assertion_store.py`)
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
- SCOPe and TED online fetch now use remote dumps by default (override via env vars).
- InterPro online endpoint can be slow; online test may skip on timeout.
- InterPro fetch tries `fields=metadata` first to reduce payload, then falls back.
- Offline test suite: `pytest -m "not online"` → 31 passed, 12 deselected (2026-02-10).

## New Decisions (Today)
- **Field path notation**: dot‑separated paths (e.g., `properties.physchem.molecular_weight`).
- **SourceAssertion object** (formerly "evidence object"): includes `source` with `type`, `name`, `record_id`, plus optional `source_metadata` (fields aligned with MOLI's conceptual schema on 2026-09-23).
- **Location model**: general model with `kind` and sub‑blocks (sequence / structure / atom / substructure). To be refined with real cases, but accepted conceptually.

## New Artifacts
- `devguide/LOCATION_EXAMPLES.md`: real‑ID validation examples for location model.
- `devguide/SCHEMA.md`: link to `LOCATION_EXAMPLES.md`.
- `devguide/INTERFACES_MINIMAL.md`: minimal core interfaces for Card/Deck/SourceAssertionStore/Resolver.
- `sabueso/mappings/` (Python mapping stubs):
  - `uniprot.py`, `pdb.py`, `pubchem.py`, `chembl.py`, `base.py`
- `sabueso/core/source_assertion_store.py`: SourceAssertion records, `make_source_assertion`, and SourceAssertionStore with deterministic IDs.
- Mappings now emit `source_assertions` and `field_source_assertions` (minimal).
- `sabueso/core/aggregator.py`: minimal card builder from mapping outputs.
- `sabueso/core/card.py`: minimal Card implementation.
- `sabueso/core/deck.py`: minimal Deck implementation.
- `sabueso/tools/db/uniprot.py`: offline + online UniProt card creation helpers.
- `sabueso/tools/db/pdb.py`: raw RCSB entry fetch (`fetch_pdb_json`). The former PDB-entry card helpers were removed (#21); structures are `has_structure` relationships (`mappings/rcsb_structures.py`, `Card.structures()`).
- `sabueso/tools/db/pubchem.py`: offline + online PubChem card helpers.
- `sabueso/tools/db/chembl.py`: offline + online ChEMBL card helpers.
- `sabueso/tools/db/go.py`: offline + online GO term helpers.
- `sabueso/tools/db/interpro.py`: offline + online InterPro entry helpers.
- `sabueso/tools/db/stringdb.py`: online STRING interaction helper.
- `sabueso/tools/db/biogrid.py`: online BioGRID interaction helper (requires access key).
- `sabueso/tools/db/cath.py`: online CATH domain_summary helper.
- `sabueso/tools/db/scope.py`: SCOPe dump-backed helper (remote dump or local file).
- `sabueso/tools/db/ted.py`: TED dump-backed helper (remote dump or local file).
- `sabueso/tools/db/phosphositeplus.py`: PSP offline-only helper.
- `tests/core/test_mapping_uniprot_offline.py`: offline smoke test for UniProt mapping.
- `tests/core/test_mapping_pdb_offline.py`: offline smoke test for PDB mapping.
- `tests/core/test_mapping_pubchem_offline.py`: offline smoke test for PubChem mapping.
- `tests/core/test_mapping_chembl_offline.py`: offline smoke test for ChEMBL mapping.
- `tests/core/test_mapping_go_offline.py`: offline smoke test for GO mapping.
- `tests/core/test_mapping_interpro_offline.py`: offline smoke test for InterPro mapping.
- `tests/core/test_online_*.py`: online smoke tests (UniProt, PDB, PubChem, ChEMBL).
- `tests/core/test_online_go.py`: online smoke test for GO.
- `tests/core/test_online_interpro.py`: online smoke test for InterPro.
- `tests/core/test_mapping_string_offline.py`: offline smoke test for STRING mapping.
- `tests/core/test_mapping_biogrid_offline.py`: offline smoke test for BioGRID mapping.
- `tests/core/test_online_string.py`: online smoke test for STRING.
- `tests/core/test_online_biogrid.py`: online smoke test for BioGRID (requires BIOGRID_ACCESS_KEY).
- `tests/core/test_mapping_cath_offline.py`: offline smoke test for CATH mapping.
- `tests/core/test_mapping_scope_offline.py`: offline smoke test for SCOPe mapping.
- `tests/core/test_mapping_ted_offline.py`: offline smoke test for TED mapping.
- `tests/core/test_mapping_psp_offline.py`: offline smoke test for PSP mapping.
- `tests/core/test_online_cath.py`: online smoke test for CATH.
- `tests/core/test_online_scope.py`: online smoke test for SCOPe (dump-backed).
- `tests/core/test_online_ted.py`: online smoke test for TED (dump-backed).
- `tests/core/test_online_psp.py`: online smoke test for PSP (skips).
- `devguide/TESTS.md`: offline/online test strategy.
- `devguide/DATA_SOURCES_STATUS.md`: implemented DBs with quality/incidents report.
- `devguide/RESOLVER.md`: minimal resolver contract (0.2.0) and selection rules 0.1.0.
- Core Ops 0.1.0 semantics recorded in `devguide/PUBLIC_API.md` and `devguide/INTERFACES_MINIMAL.md`.
- `sabueso/resolver/field_resolver.py`: resolver implementation (field-level selection).
- `tests/core/test_resolver.py`: resolver unit tests (offline).
- `sabueso/core/aggregator.py`: resolver-integrated card builder.
- `tests/core/test_aggregator_resolver.py`: aggregator+resolver integration test.
- `devguide/SELECTION_RULES_EXAMPLES.md`: field-level selection rules examples.
- `tests/core/test_selection_rules_fields.py`: resolver tests using real field examples.
- `docs/selection_rules.rst`: published documentation page for selection rules.
- `docs/selection_rules.json`: machine-readable selection rules for agents/tools.
- `sabueso/resolver/selection_rules.json`: internal resolver rules for runtime use.
- `sabueso/resolver/loader.py`: selection rules loader.
- `sabueso/core/merge.py`: mapping merge helper.
- `tests/core/test_end_to_end_resolver_offline.py`: offline end-to-end pipeline test.
- `devguide/FIELD_PATHS.md`: canonical field paths catalog.
- `schemas/card_schema_0.2.0.yaml`: formal YAML schema aligned with field paths.
- `tests/core/test_end_to_end_protein_sources_offline.py`: protein end-to-end offline test (UniProt + PDB + InterPro).
- `devguide/CACHE_POLICY.md`: draft cache/storage policy options.
- `devguide/STORAGE_LAYOUT.md`: recommended project storage layout (no defaults).
- `tools/validate_card.py`: basic schema validator for Card dicts.
- `tests/core/test_card_schema_validation_offline.py`: card schema validation test.
- `tools/validate_deck.py`: basic schema validator for Deck JSONL.
- `tests/core/test_deck_schema_validation_offline.py`: deck schema validation test.
- `sabueso/core/errors.py`: common exception types (Resolver, Schema, Storage, Connector).
- `sabueso/tools/card/storage.py`: JSON and SQLite persistence for Card.
- `sabueso/tools/deck/storage.py`: JSONL and SQLite persistence for Deck.
- `tests/core/test_storage_offline.py`: persistence tests (offline).
- `tools/validate_schema.py`: schema alignment validator (used in pytest).
- `pyproject.toml`: minimal packaging config for editable installs.
- Mappings expanded:
  - UniProt: organism, pathway, subunit, catalytic_activity, subcellular_location,
    tissue_specificity, ptm, polymorphism, active_site, modified_residue,
    glycosylation, disulfide_bond.
  - PubChem: molecular_formula, inchi, inchikey, logp, tpsa, hbd, hba,
    rotatable_bonds.
  - ChEMBL: pref_name, molecule_type, mw_freebase, hbd, hba, tpsa, rtb,
    aromatic_rings, inchi, inchikey.
  - PDB: deposition_date, release_date, primary_citation (doi/pmid/title).
  - STRING: `functionally_associated_with` relationships through `resolve_protein_card(..., string={...})` (#21, part 2c).
  - ChEMBL bioactivities: `has_bioactivity` relationships through `resolve_protein_card(..., chembl={...})` and the derived view `Card.bioactivities()` (#23).
  - Small-molecule identity: SmallMoleculeCards anchored at the standard InChIKey, with `same_as` links from ChEMBL, the PDB CCD and UniChem (`resolve_molecule_card`, #25).
  - Ligand decks: `ligand_deck(protein_card)`, `Card.ligands(deck)`, `Card.compare_ligands(...)` and `Deck.intersect` / `Deck.difference` (#23, closed).
  - GO, InterPro, CATH, SCOPe, TED, PhosphoSitePlus and BioGRID card tools were removed on
    2026-09-23 (#21). GO, classification and curated-interaction knowledge now comes
    from UniProt as typed relationships.

## Terminology Migration (2026-09-23)
- Sabueso "evidence" renamed to **SourceAssertion** across code, schemas, tests and docs
  (`SourceAssertion ≠ Evidence ≠ Provenance`; see `devguide/DECISIONS.md`).
- Mappings build assertions with `make_source_assertion`; outputs verified identical to the
  pre-migration outputs apart from the renamed keys and the `SA_` ID prefix.
- `Card.to_dict()` now serializes `source_assertion_store`, so JSON/SQLite round trips keep
  every SourceAssertion.
- Formal schema: `schemas/card_schema_0.2.0.yaml`.
- SourceAssertion fields aligned with MOLI Platform Architecture 1.0 (`id`, `subject_ref`,
  `field_path`, `asserted_value`, `source_metadata`); cards carry a stable `meta.card_id`.
- Sabueso belongs to the MOLI Platform's Scientific Context, not to MolSysSuite.

## Pending Decisions
- Final **schema versioning policy**.
- Local cache policy (raw sources vs cards vs both).
- LLM integration policy (provider, prompts, SourceAssertion tracking).

## Next Steps
1) Expand mappings with additional fields and sources.
2) Validate location model with additional real cases when ready.
