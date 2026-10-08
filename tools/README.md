# Tools

Helper scripts for development and validation.

- `validate_schema.py`: checks alignment between `devguide/FIELD_PATHS.md` and
  `schemas/card_schema_0.3.4.yaml` (the current card schema).
- `card_shape.py`: records (`--write`) or checks the key paths of the cards Sabueso
  writes, per card schema version (`schemas/card_shape_<version>.json`, #42).
- `source_registry.py`: validates `devguide/sources/registry.yaml` and generates
  `docs/content/user/data_sources.md` (`--write`, `--check`).
- `build_hk2_test_system.py`: rebuilds the public HK2 card and notebook offline
  from the qualified UniProt response, using the current schema. Run as
  `python -m tools.build_hk2_test_system --output DIR`; see
  [the HK2 test system](../devguide/HK2_TEST_SYSTEM.md).
- `build_showcase_notebook.py`: builds `docs/content/showcase/knowledge_baseline.ipynb`
  and executes it against live services. Its offline twin is
  `tests/core/test_knowledge_baseline_offline.py`.
- `rehearse_public_curation.py`: rehearses the public HsTIM review draft on frozen
  fixtures, with explicitly simulated curations; verifies conflicts, rebuilds and
  historical support. Run as `python -m tools.rehearse_public_curation --output DIR`.
  See `examples/literature_curation/README.md` for its scope and actual intake.

Usage:

```
python tools/validate_schema.py
```
