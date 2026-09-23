# Showcase

This page captures representative Sabueso workflows supported by the current
architecture.

## Typical Workflows

### Build a protein Card from UniProt

```python
import sabueso

card = sabueso.create_protein_card_online("P52789", retrieved_at="2026-02-04")
print(card.get("identifiers.uniprot"))
```

### Resolve a protein and list its experimental structures

```python
import sabueso

card, resolution = sabueso.resolve_protein_card("P52270", structures=["1TCD"])
for item in card.structures()["items"]:
    print(
        item["structure_ref"], item["method"], item["coverage_class"], item["sources"]
    )
```

### Build a small-molecule Card from PubChem

```python
import sabueso

card = sabueso.create_compound_card_online("66414", retrieved_at="2026-02-04")
print(card.get("identifiers.pubchem"))
```

### Persist Cards and Decks

```python
from sabueso.tools.card import save_card_json
from sabueso.tools.deck import save_deck_jsonl

save_card_json(card, "data/cards/example.json")
# save_deck_jsonl(deck, "data/decks/example.jsonl")
```

## What This Demonstrates

- Source integration from heterogeneous databases.
- Canonical field retrieval through consistent field paths.
- Reproducible local persistence for downstream pipelines.

For complete step-by-step tool usage, see the User section under `Tools`.
