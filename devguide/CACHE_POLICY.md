# Sabueso — Cache and Storage Policy

## What Sabueso stores, as of 0.4.0

- **Cards and decks.** The `KnowledgeStore` keeps every saved state, content-addressed,
  with its revisions. JSON, JSONL and SQLite files are available for exchange
  (`STORAGE_LAYOUT.md`).
- **Curated statements.** They are kept in a `CurationStore`, which survives rebuilds.
- **Raw source payloads: not stored by Sabueso.** A card keeps enough to know where each
  value came from:
  - the source and its release;
  - the record id and the retrieval date;
  - the asserted value, per SourceAssertion.
  A user who needs the payloads keeps them, through the `tools.db.*.get_*` functions,
  which return them in a provenance envelope.
- **No default paths.** Sabueso writes only where it is told to.

## How this differs from the first draft

The first draft (2026-01) recommended "raw payloads + cards, with size-aware pruning":
- raw payloads kept for recent days or entities;
- cards kept long-term;
- user overrides by configuration.

Only the card half was built, as the knowledge store. Raw payloads were left out for
three reasons:
- a SourceAssertion already records what was taken from them;
- some sources' licences restrict redistribution (`LICENSING_AND_COMPLIANCE.md`);
- rebuilding from sources is `refresh_card`, which records what changed.

## Open questions

- **A raw-payload cache** for heavy enrichments (large bioactivity sets, many structures):
  where it would live, how it expires, and how licences constrain it. It would be a
  convenience cache, never a source of truth.
- **Selection-rule changes.** Rules are versioned (`RESOLVER.md`). Re-resolving stored
  cards under new rules means a refresh today, and a stored card keeps the rules it was
  built with.
- **Store size.** See `CARD_SIZE_RISKS.md`.
