# Core Concepts

Sabueso uses a small set of core concepts to convert heterogeneous source data
into auditable molecular objects.

## Card

A `Card` represents one molecular entity (protein, peptide, or small molecule). It has
a stable reference, `card.id` (`meta.card_id`), that does not depend on where the card is
stored: `sabueso:protein:uniprot:P52789` for a protein, anchored at its UniProt entry, and
`sabueso:small_molecule:inchikey:<standard InChIKey>` for a small molecule, whatever source
its records come from. A card never merges records of different entities: records about
several subjects are combined only after their identity is resolved. Each field is stored in a structured
node:

```text
{"value": <selected_value>, "source_assertion_ids": [<source_assertion_id>, ...]}
```

Cards expose core methods such as:

- `get(field_path)`
- `extract(field_paths)`
- `compare(other, fields=None, mode="strict|tolerant")`
- `to_dict()`, `to_json(path)`, `to_sqlite(path, ...)`
- `from_json(path)`, `from_sqlite(path, ...)`

## Deck

A `Deck` is a collection of Cards with batch operations:

- `filter(predicate)` for sub-decks
- `in_lineage(taxon)` keeps the cards whose organism is or descends from a taxon, and
  lists in `meta` the cards whose lineage is not stated; `group_by(field_path)` groups
  cards by a resolved value, e.g. `annotations.taxon_id`
- `identity_audit()` reports redundant entries, strain variants, fragments and
  paralogs among the protein cards, each with its basis. It never merges cards.
- `sort(field_path, reverse=False)` by resolved value; cards without a value go last
- `map(fn)`, `summarize(field_paths)`
- `compare(other, key_fields)`
- `to_jsonl(path)`, `to_sqlite(path, ...)`
- `from_jsonl(path)`, `from_sqlite(path, ...)`, which return `Card` objects with their
  SourceAssertionStore and identity

## SourceAssertion

A `SourceAssertion` records what an external source asserts about an entity or
property: the asserted value, the field it refers to, the source and record it comes
from, and when it was retrieved:

```text
{"id": "SA_UniProt_P52789_...",
 "subject_ref": "uniprot:P52789",
 "field_path": "annotations.organism",
 "asserted_value": "Homo sapiens",
 "source": {"type": "database", "name": "UniProt", "record_id": "P52789"},
 "retrieved_at": "2026-02-01"}
```

A SourceAssertion is not scientific *evidence* for a hypothesis (that concept belongs to
Nextia, the Discovery context of the MOLI Platform) and it is not provenance in general. It is an
external knowledge claim that carries its own provenance. Qualifiers the source attaches
to its own statements (for example, UniProt ECO codes) are kept as source metadata.

## SourceAssertionStore

The `SourceAssertionStore` holds every SourceAssertion referenced by
`source_assertion_ids`. Sabueso keeps all assertions, including alternative or
contradictory ones, and only selects canonical values for Card fields. This separates:

- field readability (resolved values in the Card)
- traceability (every source assertion in the store, serialized with the Card)

## Resolver

The Resolver turns the SourceAssertions of each field into resolved molecular
knowledge. Its output contains:

- `selected_value`
- `source_assertion_ids` (the assertions that support the selected value)
- `conflict` (when assertions disagree; the alternatives stay in the store)

Conflicts are always reported when there is a discrepancy. When two values of a quantity
differ by exactly 3 or 6 orders of magnitude, the conflict also carries
`scale_discrepancy`. That pattern is the usual sign of a unit slip, such as nM written for
µM. Neither value is corrected.

## Entities

A card mentions other molecules and proteins under the records its sources use. For
example, a ligand is `pdb.ligand:BTS` in a structure and `chembl:CHEMBL1161789` in a
measurement. `card.entities()` lists each entity once, with every record the card
mentions for it, its names and where it appears. `card.entity(ref)` finds the entity of
any record:

```python
card.entity(
    "pdb.ligand:BTS"
)  # {"key": "inchikey:...", "records": [...], "appears_in": [...]}
```

Records are grouped into one entity only when a source says they are the same molecule,
for example a resolved identity or UniChem's links. Otherwise they stay apart.

## Tables

Every view also comes as flat rows, one per structure, measurement, molecule, ligand,
interface partner, publication or entity. `sabueso.to_dataframe` turns them into a
pandas DataFrame. pandas is optional; install it with
`conda install -c conda-forge pandas`.

```python
rows = card.table("bioactivities", include_indirect=True)
df = sabueso.to_dataframe(rows)  # quantities stay quantities, each with its unit

potencies = [r for r in rows if r["units"] == "nM"]
df = sabueso.to_dataframe(potencies, units={"normalized": "micromolar"})
# column "normalized [micromolar]", numbers; df.attrs["units"] records the unit
```

The views with a table form are `structures`, `bioactivities`, `ligands` (pass
`deck=`), `ligand_sites`, `interfaces`, `literature` and `entities`. Asking for numbers
in a unit a column cannot take is refused. For example, bioactivities mix
concentrations and single-point percentages, so select the rows first.

## Quantities

A physical quantity is always stored with its unit, as `{"value": ..., "unit": ...}`. The
unit is the one Sabueso agreed for that place: dalton for molecular weights, ångström for
resolutions and contact distances, nanomolar or percent for normalized bioactivities.
Sabueso returns quantities, not bare numbers:

```python
card.quantity("sequence.molecular_weight")  # one value, a PyUnitWizard quantity
card.quantity_columns("relationships.has_structure.resolution")
# {"angstrom": <array quantity>}: every value at that place, one array per unit
```

A stored card seals its quantities, and loading refuses a card whose values or units were
changed outside Sabueso. The source's own value and unit text are kept, as stated, in its
SourceAssertion.

## Selection Rules

Selection behavior is controlled by versioned rules (`x.y.z`), including:

- priority source order
- per-field strategy (for example, `most_recent` or `priority_sources`)
- whether a field allows multiple selected values

## Pipeline

The operational flow is:

```text
source payloads
  -> mappings
  -> merge
  -> resolver
  -> card/deck
```

This pipeline preserves traceability while producing canonical outputs for downstream tools.

## Field Paths

Sabueso uses canonical dot-separated field paths (for example,
`identifiers.uniprot` or `features_positional.binding_site`).
See {doc}`field_paths`.

## Storage Model

Sabueso supports in-memory work by default and explicit persistence by user choice.
Recommended project layout and storage tradeoffs are documented in {doc}`storage`.

