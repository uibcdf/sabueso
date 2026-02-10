# Sabueso — Public API (Conceptual)

## Core Objects
- **Card**: single entity representation with evidence.
- **Deck**: collection of Cards with consistent operations.

Users can choose to operate on a single Card or a Deck.

## Ops (Internal, Consistent Semantics)
Ops are methods on Card/Deck with predictable behavior.
Core Ops version: **0.1.0** (x.y.z).

Examples:
- CardOps: `compare`, `extract`, `expand`, `to_deck`, `to_dict`.
- DeckOps: `filter`, `sort`, `compare`, `map`, `reduce`.

## Minimal Stable Ops (Approved)
These ops define the minimum stable surface for a usable Sabueso release.

CardOps (minimum):
- `get(field_path)`
- `to_dict()`
- `to_json(path)`
- `to_sqlite(path, table="cards", id_field=None)`
- `from_json(path)`
- `from_sqlite(path, table="cards", card_id=None)`
- `extract(field_paths)`
- `compare(other_card, fields=None, mode="strict")` → `dict`
- `derive_deck(kind)` → `Deck`
- `to_deck()`

DeckOps (minimum):
- `get_card(index)` → `Card`
- `filter(predicate)`
- `extract(predicate)` → `Deck`
- `sort(key)`
- `map(fn)`
- `compare(other_deck, key_fields, mode="strict")` → `dict`
- `summarize(fields)`
- `to_jsonl(path)`
- `to_sqlite(path, table="cards", id_field=None)`
- `from_jsonl(path)`
- `from_sqlite(path, table="cards")`

### Compare Modes
- `strict`: exact equality on values, ordered list equality, no normalization.
- `tolerant`: relaxed equality (unordered list equality, numeric tolerance, basic string normalization).

## Tools (Public, Heterogeneous)
Tools are standalone functions grouped by module:
- `tools.db.*`: per‑database modules
- `tools.card.*`: tools operating on Card
- `tools.deck.*`: tools operating on Deck

Tools are **ad‑hoc by design** and can return any output type.

### Current Tooling (Example)
- `tools.db.uniprot` provides offline and online helpers to build a Protein Card from UniProt data.
- `tools.card.storage` provides `save_card_json`, `save_card_sqlite`.
- `tools.deck.storage` provides `save_deck_jsonl`, `save_deck_sqlite`.

## Mixed API Style
The public API is mixed OO + functional:
- Cards/Decks expose ops as methods.
- Tools are standalone functions.
