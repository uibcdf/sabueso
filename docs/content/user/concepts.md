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

## What a card does not know

`card.knowledge_state()` (or `card.table("knowledge_state")`) lists, per area and
source:
- `known`: the card knows it;
- `conflicting`: sources disagree;
- `not_stated`: the source was consulted and states nothing;
- `not_queried`: it was not requested;
- `unavailable`: the source failed;
- `partial`: the source answered for some requests and failed, or answered
  incompletely, for others. `basis` names which (`unavailable_for`, `incomplete_for`).

Each row carries the source release and the basis. An absence is reported as a fact
about a source, never as evidence against something (rule `knowledge_state@2`).

## Structures

A protein's experimental structures are `has_structure` relationships, and its predicted
models are `has_predicted_structure`; the two are never mixed. `card.structures()` and
`card.predicted_structures()` read them, and `deck.structure_inventory()` puts several
proteins side by side. See {doc}`structures`.

## Comparing two cards

`card.compare_knowledge(other)` lists, per field, relationship predicate and knowledge
state, what both cards state, what only one states, and what they state differently.
Positional features are compared only when you pass `residue_map={position here:
position there}`, for example from a MolSysMT alignment. The same number in two
entries is not the same residue. Free text is never compared.

## Deck

A `Deck` is a collection of cards that records why each card is in it, which candidates
were left out, and how it was derived. It filters, sorts, groups by lineage and rank,
audits identities, lists names, inventories structures and compares; it is saved and
pinned like a card. See {doc}`decks`.

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

The views with a table form are `structures`, `predicted_structures`, `bioactivities`,
`ligands` (pass `deck=`), `ligand_sites`, `interfaces`, `literature`, `claims`,
`entities` and `knowledge_state`. Asking for numbers
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

The value shown for a field is chosen by versioned rules (`x.y.z`): which values are
comparable (`compare_within`, `numeric_agreement`), which source is shown first when
they agree or disagree (`priority_sources`), and whether a field holds several values.
Only comparable values are compared, and nothing is discarded. See {doc}`selection_rules`.

## Pipeline

The operational flow of `sabueso.resolve` (details in {doc}`resolving`):

```text
query
  -> entity resolution (which entity? ambiguity is reported)
  -> source records (tools.db clients)
  -> mappings (SourceAssertions and relationships)
  -> merge and selection (conflicts kept)
  -> card; views derive knowledge on demand
```

## Field Paths

Sabueso uses canonical dot-separated field paths (for example,
`identifiers.uniprot` or `features_positional.binding_site`).
See {doc}`field_paths`.

## Storage Model

Sabueso supports in-memory work by default and explicit persistence by user choice.
Recommended project layout and storage tradeoffs are documented in {doc}`storage`.

