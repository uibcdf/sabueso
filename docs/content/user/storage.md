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

## Knowledge Store: Versioned Cards

To keep cards over time and cite the exact state you used, save them in a knowledge
store. It is one SQLite file:

```python
import sabueso

store = sabueso.KnowledgeStore("project/knowledge.db")
ref = store.save(card, note="baseline for the docking run")
# 'sabueso:protein:uniprot:P52270@sha256:3b1f…' pins this exact state

store.load(ref)  # exactly that state, or StorageError
store.load(card.id)  # the latest state saved for the card
store.history(card.id)  # every revision: reference, time, note

# Which stored proteins was this molecule measured on?
store.relationships(object_ref="chembl:CHEMBL1288605", predicate="has_bioactivity")
```

- A snapshot id is the content address of the card. `card.snapshot_id()` and
  `card.pinned_ref()` compute it without a store, so a JSON copy of a card can be
  checked against a reference.
- A pinned reference never resolves to another state of the card. If that state is not
  in the store, you get a `StorageError`.
- An assertion or relationship is cited within a pinned state:
  `store.source_assertion(f"{ref}#SA_…")`.
- Decks are versioned too. `store.save_deck(deck, "ligands")` returns
  `sabueso:deck:ligands@sha256:…`. `store.load_deck("ligands")` gives the latest
  revision, and `store.load_deck(ref)` the exact one, each card in the state it was
  saved in. `store.deck_history("ligands")` lists the revisions.
- To bring in cards saved earlier with `card.to_sqlite`, use
  `store.import_card_table(path)`. Each row becomes a revision.
- Saving a card again when nothing it knows has changed costs little: each statement is
  stored once, with the time it was read kept per revision, and the store is
  compressed. A store written by Sabueso 0.7.0 or earlier is upgraded in place the
  first time a newer Sabueso opens it; older versions of Sabueso cannot open it after
  that.

### What the store knew on a date

```python
from datetime import date

store.as_of(card.id, date(2026, 9, 1))  # the card as stored by the end of that day
store.as_of("ligands", date(2026, 9, 1))  # a deck or a packet, the same way
store.changed_since(card.id, date(2026, 9, 1))
# {'changed': True, 'then': '…@sha256:…', 'latest': '…@sha256:…', …}
```

- `as_of(ref, when)` gives the latest revision stored by `when`, loaded, or None when
  nothing had been stored yet. `when` is a date (up to the end of that day, UTC), a
  datetime or an ISO string. `revision_as_of(ref, when)` gives the revision entry.
- `changed_since(ref, when)` compares a card's or a packet's knowledge then and now,
  without retrieval times. `changed` is None when nothing had been stored by then.
- The store answers only from what it saved, to the second. It never reconstructs what
  a source said on a past date: for that, save the cards when you use them.

The reference forms are provisional until they are agreed across MOLI (uibcdf/moli#3).

## What was downloaded

To keep what the sources answered, build inside a retrieval archive:

```python
archive = sabueso.RetrievalArchive("project/retrievals.db")
with archive.recording():
    card, _ = sabueso.resolve("P52270", chembl={}, structures=["1SUX"])
card.quality["retrievals"]["records"]  # every answer: URL, status, time, content hash
archive.get(ref)["content"]  # the response itself, checked against its hash
```

- Nothing is kept unless you ask. The archive is a file of yours, and each distinct
  response is stored once, compressed: building TcTIM with ChEMBL, BindingDB, PubChem
  BioAssay, three structures and Europe PMC kept 1.4 MB of responses in 158 KB.
- A 404 is an answer ("not found") and is kept too.

The same archive rebuilds a card without the network, or saves asking again:

```python
with archive.replaying(of=card):  # never asks the network
    same, _ = sabueso.resolve("P52270", chembl={}, structures=["1SUX"])
# same knowledge, and every statement keeps the time its answer was read

from datetime import timedelta

with archive.reusing(timedelta(days=30)):  # answers younger than 30 days are reused
    card, _ = sabueso.resolve("P52270", chembl={}, bindingdb={})
```

- `replaying(of=card)` answers each request with what that card's build received. A
  request the archive does not hold is not asked: the source shows as `not_queried`
  (`not_in_archive`), never as absent.
- Replaying the TcTIM build above took 4 s instead of 55 s online, and gave the same
  card.
- Each answer is its source's. `archive.sources()` counts them per source, with what the
  source's licence allows with a copy: `keep` and `share`, with conditions such as
  attribution or share-alike. Sources whose terms are per record, or not recorded, are
  `keep: internal`, `share: unknown`: check them before passing a copy on.
- `card.explain([source_assertion_id])` names the answers the statement's source gave
  the build (`retrievals`).

## Local mirrors

Some sources publish their whole data as releases. A mirror installs one on your disk,
so that cards read it instead of asking the source record by record: faster, without
the network, and every card of a project on the same release.

```python
import sabueso.mirrors as mirrors

mirrors.install("bindingdb", mirror_dir="/data/mirrors")  # the latest monthly release
mirrors.status("/data/mirrors", check=True)  # installed releases, size, newer ones
with mirrors.using("/data/mirrors"):
    card, _ = sabueso.resolve("P00533", bindingdb={})  # BindingDB from the mirror
```

- Nothing is downloaded unless you ask, and only where you say (`mirror_dir=` or
  `$SABUESO_MIRROR_DIR`). BindingDB's release is about 600 MB to download and 700 MB
  once indexed. The download is checked against the checksum BindingDB publishes.
- `mirrors.update("bindingdb", policy)`: `"notify"` says whether a newer release exists;
  `"manual"` installs it; `"auto"` installs it and keeps the previous `keep` releases.
  Releases sit side by side; `using(..., releases={"bindingdb": "202609"})` pins one.
- Each card records how it read the source: `access: "mirror"` and the release.
- `using(..., mode="offline")` never asks the network: a source without a mirror, or an
  archived answer, is `not_queried` (`offline`). With a retrieval archive in
  `replaying()`, a whole build can run offline.
- The mirror states the values as BindingDB publishes them (e.g. 112.4 nM, where its
  web service rounds to 112), and a monthly release may differ slightly from the live
  service. Molecules are still identified through UniChem.

## Old Cards

Cards written by older versions are read, or migrated with what they lack reported; see
{doc}`upgrading`.

## What Sabueso stores

- **Cards and decks**, in the knowledge store or in files, where you choose. There are
  no default paths.
- **Curated statements**, in a curation store ({doc}`literature_and_curation`).
- **Not the raw source records.** Each SourceAssertion keeps what was taken from a
  record: the source, its release, the record id, the retrieval date and the asserted
  value. To keep raw records yourself, use the `get_*` functions
  ({doc}`tools/db/sources`), and check each source's terms before redistributing them.

## Recommended Project Layout

```text
project_root/
  data/
    knowledge.db        # KnowledgeStore: cards and decks with their revisions
    curation.jsonl      # CurationStore: curated statements, kept across rebuilds
    raw/                # optional: raw source records you keep yourself
    exports/            # optional: JSON/JSONL/SQLite files to share
```

The developer guide explains the reasons (`devguide/STORAGE_LAYOUT.md`,
`devguide/CACHE_POLICY.md`).

## Tradeoffs

- JSON/JSONL: easiest to inspect and diff.
- SQLite: best for larger collections and query performance.
- Knowledge store: the place to keep cards you will cite, with their history.
