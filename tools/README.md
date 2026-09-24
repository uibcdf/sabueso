# Tools

Helper scripts for development and validation.

- `validate_schema.py`: checks alignment between `devguide/FIELD_PATHS.md` and
  `schemas/card_schema_0.3.1.yaml` (the current card schema).
- `card_shape.py`: records (`--write`) or checks the key paths of the cards Sabueso
  writes, per card schema version (`schemas/card_shape_<version>.json`, #42).

Usage:

```
python tools/validate_schema.py
```
