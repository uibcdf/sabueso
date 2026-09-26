# Quickstart

A first session: install, resolve two proteins, read what their cards know, and keep the
result so it can be cited.

## Install

Sabueso is distributed through the `uibcdf` conda channel, for Python 3.11–3.14:

```bash
conda install -c uibcdf -c conda-forge 'sabueso>=0.4.0'
```

pandas is optional, for tables as DataFrames: `conda install -c conda-forge pandas`. To
work on Sabueso itself, see *Developers*.

## Resolve a protein

`sabueso.resolve` takes an identifier, or a name and an organism, and returns the card
with the resolution that explains it:

```python
import sabueso
from sabueso.resolver import EntityQuery

card, resolution = sabueso.resolve(
    EntityQuery(name="triosephosphate isomerase", organism=9606)
)
print(resolution.status, card.id)  # resolved sabueso:protein:uniprot:P60174
print(resolution.decision["rules"])  # why this entry: ['preference:prefer_reviewed@1']
for finding in resolution.decision["identity_audit"][:3]:
    print(finding["finding"], finding["refs"])  # entries that could be mistaken for it
```

If several entries match and no rule decides, the status is `ambiguous`: Sabueso never
picks one silently. See {doc}`resolving`.

## Ask for more knowledge

Options add knowledge from more sources. A profile names a versioned set of them:

```python
card, resolution = sabueso.resolve(
    "P60174",
    profile="structural_baseline@1",  # structures, interfaces, sites, ChEMBL
    taxonomy=True,
    predicted_structures=True,
)
print(card.quality["enrichments"])  # what each source added, or why it did not
```

## Read what the card knows

```python
card.get("names.canonical_name")  # {"value": ..., "source_assertion_ids": [...]}
sa_id = card.get("annotations.subunit")["source_assertion_ids"][0]
# who says it, from which release, with which evidence
card.source_assertion_store.get(sa_id)

card.knowledge_state()  # known, conflicting, not stated, not queried, unavailable
card.structures()  # experimental structures, with construct, mutations and state
card.oligomer()  # subunit, assemblies and interfaces
card.bioactivities()  # measurements, grouped across sources, with derived classes
card.literature()  # the publications behind the statements

rows = card.table("structures")  # any view as flat rows
df = sabueso.to_dataframe(rows)  # quantities stay quantities
```

## Compare two proteins

```python
from sabueso.core.deck import Deck

focus, _ = sabueso.resolve("P52270", structures="all")
other, _ = sabueso.resolve("P60174", structures="all")
diff = focus.compare_knowledge(other)  # what both state, what only one does
# structures side by side, by state
inventory = Deck([focus, other]).structure_inventory()
```

## Keep it, and cite it

```python
store = sabueso.KnowledgeStore("knowledge.db")
ref = store.save(card, note="baseline")
print(ref)  # sabueso:protein:uniprot:P60174@sha256:… names this exact state
same = store.load(ref)  # read back exactly, whatever happens to the card later
```

## Query a source directly

Every database module also returns its raw records, with the release and retrieval
date, without building a card:

```python
from sabueso.tools.db import uniprot

entry = uniprot.get_entry("P60174")
print(entry["version"], entry["retrieved_at"], entry["record"]["primaryAccession"])
```

## Next steps

- {doc}`concepts` for cards, SourceAssertions, conflicts and quantities.
- {doc}`structures`, {doc}`bioactivities` and {doc}`literature_and_curation` for what a
  protein card knows.
- The showcase notebook for a full worked example.
