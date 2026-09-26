# Upgrading

## Cards written by older versions

Every card states the card schema it was written with (`meta.schema_version`):

| Release | Card schema |
|---|---|
| 0.1.0, 0.1.1 | 0.3.0 |
| 0.2.0 | 0.3.1 |
| 0.3.0 | 0.3.2 |
| 0.3.1 | 0.3.3 |
| 0.4.0 | 0.3.4 |

- A card of an older version of the same line (`0.3.x`) is read as it is.
- A card of a newer version of the line is read with a warning, keeping the keys this
  version does not know.
- A card of another line is refused until a migration exists.

To bring an older card up to date, and to know what it lacks:

```python
import json
import sabueso

data = json.load(open("old_card.json"))
card = sabueso.migrate_card(data)
for step in card.quality["migration"][-1]["steps"]:
    for gap in step["gaps"]:
        print(gap["introduced_in"], gap["path"], gap["kind"], gap["filled_by"])
# kind "missing": a refresh from the same sources brings it (e.g. names.gene_names)
# kind "available": an enrichment to ask for (e.g. taxonomy=True)

refreshed, _ = sabueso.refresh_card(card, curations="curation.jsonl")
print(refreshed.quality["migration"][-1]["completed"])
```

- The original is never changed. With `store=` (a `KnowledgeStore`), the original and
  the migrated card are kept as two revisions of one card.
- `refresh_card` rebuilds the card with the options it records, re-applies curations
  (keeping their ids), and says which gaps it completed and which the sources still do
  not state.

## Deprecated functions

They still work, warn with `DeprecatedUsageWarning`, and will be removed before 1.0:

| Deprecated | Use instead |
|---|---|
| `fetch_uniprot_json`, `fetch_chembl_json`, `fetch_pubchem_json`, `tools.db.pdb.fetch_pdb_json` | the `get_*` functions of `sabueso.tools.db` ({doc}`tools/db/sources`) |
| `create_protein_card_online`, `create_molecule_card_online`, `create_compound_card_online` | `sabueso.resolve` ({doc}`resolving`) |

The offline builders `create_*_card_from_json` and `create_*_card_from_file` stay, for
work on saved records and for tests.

## Notes per release

Each release's notes say what changed and whether stored cards are affected:
<https://github.com/uibcdf/sabueso/releases>. In particular:

- 0.3.0 changed the ids of curated assertions (#62); stores written by 0.2.0 are
  re-identified when read.
- 0.3.1 fixed copies of cards that shared their dictionaries with the original (#64).
