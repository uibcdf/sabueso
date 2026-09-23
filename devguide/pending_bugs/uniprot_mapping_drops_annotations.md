---
summary: UniProt mapping silently drops catalytic activity, subcellular location, sequence and ECO qualifiers.
issue: uibcdf/sabueso#13
status: open
opened: 2026-09-23
closed:
verification: reproduced
severity: high
area: [mappings, uniprot, source-assertions]
blocked_by: []
supersedes: []
---

# UniProt mapping silently drops annotated data

## What

`sabueso/mappings/uniprot.py::map_protein` claims to cover several UniProt comment types.
For two of them it produces nothing, it never maps the sequence, and it discards the
qualifiers UniProt attaches to its own statements. Because the loss is silent, a consumer
cannot tell "not annotated in UniProt" from "not mapped by Sabueso".

## How / evidence

Reproduced on `main` on 2026-09-23, using the three UniProt fixtures:

| Data | P52789 | P35372 | A0A140VJM9 | Cause |
|---|---|---|---|---|
| CATALYTIC ACTIVITY comments dropped | 3 | 0 | 1 | read from `texts`; UniProt stores them under `reaction` (`name`, `ecNumber`, cross-references including Rhea, `evidences`) |
| SUBCELLULAR LOCATION comments dropped | 1 | 2 | 0 | read from `texts`; UniProt uses `subcellularLocations[].location.value` (plus topology and orientation) |
| sequence present / mapped | 917 aa / no | 400 aa / no | 381 aa / no | no mapping for `sequence.value`, `length`, `molWeight`, `crc64`, `md5` |
| comment texts with ECO evidences | 10 | 11 | 2 | discarded |
| features with evidences | 134/135 | 80/83 | 7/7 | discarded |

```python
card = create_protein_card_from_file("temp_data/P52789.json")
card.get("annotations.catalytic_activity")  # None
card.get("annotations.subcellular_location")  # None
```

`devguide/DATA_SOURCES_STATUS.md` rated UniProt "green", including exactly these comment
types. The existing offline tests only check that some fields exist.

## Why

- UniProt is the primary source for ProteinCards. Catalytic activity (EC numbers,
  reactions) and localization are core knowledge for downstream work: target
  characterization, TopoMT or pocket analyses focused on catalytic sites, and Nextia
  Context Assembly.
- A card without a sequence cannot be checked against structures, which blocks
  sequence-structure mapping.
- Discarding ECO codes loses the source's own epistemic qualification. MOLI Architecture
  1.0 keeps it on the SourceAssertion as `source_metadata`, and never turns it into Nextia
  Evidence.

## Alternatives

- **Fix only the two comment types:** rejected as insufficient. The missing sequence and
  the lost qualifiers belong to the same defect class, silent loss of mapped UniProt
  content.
- **Carry the raw UniProt comment in `source_metadata`:** useful as a supplement, but not
  a substitute for canonical fields.
- **Selected:**
  - parse `reaction` and `subcellularLocations`;
  - map the sequence fields (field paths to be added to `FIELD_PATHS.md` and the schema);
  - attach ECO codes and references to each SourceAssertion's `source_metadata`;
  - add tests per fixture that assert the expected counts.

## Acceptance criteria

- On the three fixtures, catalytic activity and subcellular location are mapped with
  their counts preserved. Reactions keep their EC number and Rhea identifier where
  present.
- The sequence (value, length, and mass where given) is mapped with SourceAssertions.
- Evidence qualifiers appear in `source_metadata` under UniProt-native names.
- Offline tests assert these per fixture, so a regression cannot pass silently.
- `DATA_SOURCES_STATUS.md` reflects the verified coverage.

## Resolution

Pending.
