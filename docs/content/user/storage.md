# Storage

Sabueso is designed for in-memory work first, with explicit persistence when the
user decides to save artifacts in a project directory.

## Supported Formats

- **Card**:
  - JSON
  - SQLite
- **Deck**:
  - JSONL (one Card per line)
  - SQLite

## API Methods

Card persistence:

- `card.to_json(path)`
- `card.to_sqlite(path, table='cards', id_field=None)`
- `Card.from_json(path)`
- `Card.from_sqlite(path, table='cards', card_id=None)`

Deck persistence:

- `deck.to_jsonl(path)`
- `deck.to_sqlite(path, table='cards', id_field=None)`
- `Deck.from_jsonl(path)`
- `Deck.from_sqlite(path, table='cards')`

## Cache Policy

Current policy is Raw + Cards.

- Raw payloads support reproducibility and re-resolution.
- Cards support fast reuse in workflows.
- There are **no hard-coded default paths**.

## Recommended Project Layout

See:

- `devguide/STORAGE_LAYOUT.md`
- `devguide/CACHE_POLICY.md`

## Tradeoffs

- JSON/JSONL: easiest to inspect and diff.
- SQLite: best for larger collections and query performance.
