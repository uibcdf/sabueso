# Quickstart

This guide walks through a minimal but real Sabueso workflow:

1. install in editable mode
2. build Cards from online/offline sources
3. save/load Cards and Decks
4. run offline tests

## Prerequisites

- Python 3.11+
- A project environment with Sabueso available

## Install (editable, no dependencies)

From the repository root:

```bash
pip install --no-deps --editable .
```

## Create a Protein Card (online)

The example below creates a Protein Card from UniProt ID `P52789`.

```python
import sabueso

card = sabueso.create_protein_card_online("P52789")
print(card.get("identifiers.uniprot"))
print(card.get("names.canonical_name"))
```

## Create a Small Molecule Card (offline)

If you already have source JSON files, build a Card without network access.

```python
import sabueso

card = sabueso.create_molecule_card_from_file(
    "temp_data/CHEMBL90555.json",
    retrieved_at="2026-02-10",
)
print(card.get("identifiers.chembl"))
print(card.get("properties.physchem.molecular_weight"))
```

## Save and Load a Card

Cards support JSON and SQLite persistence.

```python
# Save
card.to_json("card.json")
card.to_sqlite("cards.db", id_field="identifiers.chembl")

# Load
loaded_from_json = card.__class__.from_json("card.json")
loaded_from_sqlite = card.__class__.from_sqlite(
    "cards.db",
    card_id="CHEMBL90555",
)
```

## Save and Load a Deck

Decks support JSONL and SQLite persistence.

```python
from sabueso.core.deck import Deck

deck = Deck([card])

# Save
deck.to_jsonl("deck.jsonl")
deck.to_sqlite("deck.db", id_field="identifiers.chembl")

# Load
loaded_deck_jsonl = Deck.from_jsonl("deck.jsonl")
loaded_deck_sqlite = Deck.from_sqlite("deck.db")
```

## Run Offline Tests

Run the full offline suite:

```bash
pytest -m "not online"
```

Run only schema alignment and validation:

```bash
pytest tests/core/test_schema_alignment.py \
       tests/core/test_card_schema_validation_offline.py \
       tests/core/test_deck_schema_validation_offline.py
```

## Next Steps

- Read {doc}`concepts` for Card/Deck/Evidence/Resolver semantics.
- Review {doc}`field_paths` for canonical paths.
- Review {doc}`selection_rules` to understand canonical value selection.

