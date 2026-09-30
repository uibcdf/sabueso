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
  - Only sources whose licence allows keeping copies are cached (PHI-base and DISEASES:
    CC BY 4.0).
  - DISEASES updates its files in place, so its cache is keyed by each file's
    publication date (`diseases/<channel>_<date>.json`). A newer file is a new entry.
  - Orphadata's file is dated only inside it, so it is kept in memory only.
  - All three share one implementation (`tools/db/_release.py`, #86): the same memory
    store, the same resolution of the cache directory, and atomic writes (staged, then
    renamed), so an interrupted write never leaves a release half cached.

## Direction adopted (2026-09-30, #100)

Built so far: the retrieval archive records (`sabueso.RetrievalArchive`,
`archive.recording()`): every answer through `_http.urlopen`, a 404 included, stored once
per distinct content (compressed, SHA-256), and listed on the card
(`quality.retrievals`). Next: retrieval times taken from the answers, `replay` and
`archive_first`, retention by licence, and `provenance_ref` per SourceAssertion.


"Raw payloads: not stored" answered the first draft, and it is being replaced. MOLI's
reproducibility policy asks every external retrieval to keep what it returned, when
the licence allows, and to say so when it does not (`uibcdf/moli`,
`REPRODUCIBILITY_AUDIT_AND_REPLAY.md`). Three layers, each opt-in, for three kinds of
user: an independent user of Sabueso as a tool, UIBCDF's own research, and Sabueso as
MOLI's Knowledge component.

- **Retrieval archive.** Every request as a `RetrievalRecord`: source, query, release,
  time, the response and its hash, and whether it was retained (licence). Each
  SourceAssertion links to it through `provenance_ref`. It serves audit, replay without
  the network, reformulating questions over what was downloaded, and reuse of fresh
  answers under a declared freshness policy, which replaces a separate lookup cache.
- **Local source mirrors.** Whole releases installed once, with an update policy
  (`manual`, `notify`, `auto`), several releases side by side, read through the same
  clients with parity tests. The release caches below are their first case.
- **Knowledge states.** The `KnowledgeStore`, as today (#99).
- **Access modes**, recorded in each enrichment: `online` (default), `archive_first`,
  `mirror_first`, `replay` and `offline`. In `replay` and `offline` no source is asked
  online, and a missing answer is `not_queried` with its reason, never an absence.
- **Defaults do not change:** online, nothing written, no default paths.

The shared contract and the platform side are proposed in uibcdf/moli#33.

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

- **A raw-payload cache** for heavy enrichments of API sources: answered by the
  direction above (#100), where the archive's freshness policy decides reuse and each
  source's stated retention decides what is kept.
- **Selection-rule changes.** Rules are versioned (`RESOLVER.md`). Re-resolving stored
  cards under new rules means a refresh today, and a stored card keeps the rules it was
  built with.
- **Store size.** See `CARD_SIZE_RISKS.md`.
