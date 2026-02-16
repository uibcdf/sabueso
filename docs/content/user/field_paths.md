# Field Paths

Sabueso uses canonical dot-separated field paths for mappings, resolver rules,
evidence links, and downstream tooling.

## Core Convention

- Dot-separated paths, for example:
  - `identifiers.uniprot`
  - `names.canonical_name`
  - `properties.physchem.molecular_weight`
  - `features_positional.binding_site`

- Identifiers use direct keys:
  - `identifiers.uniprot`
  - `identifiers.pdb`
  - `identifiers.chembl`
  - `identifiers.pubchem`

No `secondary_ids` level is used.

## Top-Level Path Groups

- `meta.*`
- `identifiers.*`
- `names.*`
- `properties.*`
- `annotations.*`
- `features_positional.*`
- `interactions.*`
- `clinical.*`
- `quality.*`

## Domain Representation

Domains can be represented in two complementary ways:

- `annotations.domains` for non-positional domain summaries.
- `features_positional.domains` for positional domain features.

Both can coexist in the same Card.

## Reference Catalog

The canonical list is maintained in:

- `devguide/FIELD_PATHS.md`

## Schema Alignment

Schema and field paths are validated with:

```bash
python tools/validate_schema.py
```

The same check is covered in pytest via:

```bash
pytest tests/core/test_schema_alignment.py
```
