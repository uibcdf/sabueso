# Sabueso — Cache and Storage Policy

## What Sabueso stores

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
- **Release caches for bulk sources** (since #83). A source published only as whole
  releases, such as PHI-base on Zenodo, is downloaded once, checked against its
  published checksum, and indexed.
  - By default the index is kept in memory for the process, and nothing is written.
  - With a cache directory (`cache_dir=`, or `$SABUESO_CACHE_DIR`), it is written there
    once per release: `phi-base/<version>/` holds each curation session once, an index
    by UniProt accession, and `release.json` (record, version, checksum, retrieval
    time).
  - A release never changes once published, so a cached release does not expire. A
    newer release goes to its own directory, and the old one can be deleted freely.
  - It is a convenience, never a source of truth. What a card took from it is recorded
    in its SourceAssertions, with the release.
  - Only sources whose licence allows keeping copies are cached (PHI-base: CC BY 4.0).

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

- **A raw-payload cache** for heavy enrichments of API sources (large bioactivity sets,
  many structures): how it expires, and how licences constrain it. The release cache
  above is its first, simpler case: releases do not change, so they need no expiry.
- **Selection-rule changes.** Rules are versioned (`RESOLVER.md`). Re-resolving stored
  cards under new rules means a refresh today, and a stored card keeps the rules it was
  built with.
- **Store size.** See `CARD_SIZE_RISKS.md`.
