# Tools

Helper scripts for development and validation.

- `validate_schema.py`: checks alignment between `devguide/FIELD_PATHS.md` and
  `schemas/card_schema_0.3.3.yaml` (the current card schema).
- `card_shape.py`: records (`--write`) or checks the key paths of the cards Sabueso
  writes, per card schema version (`schemas/card_shape_<version>.json`, #42).
- `source_registry.py`: validates `devguide/sources/registry.yaml` and generates
  `docs/content/user/data_sources.md` (`--write`, `--check`).
- `build_showcase_notebook.py`: builds `docs/content/showcase/knowledge_baseline.ipynb`
  and executes it against live services. Its offline twin is
  `tests/core/test_knowledge_baseline_offline.py`.

Usage:

```
python tools/validate_schema.py
```
