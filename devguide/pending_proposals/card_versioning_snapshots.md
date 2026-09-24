---
summary: Version and snapshot cards so consumers can pin reproducible knowledge references.
issue: uibcdf/sabueso#7
status: partial
opened: 2026-09-23
closed:
verification: inspected
area: [identity, persistence, provenance]
blocked_by: [uibcdf/moli#3]
supersedes: []
---

# Card versioning and snapshots

## What

Sabueso Cards need version or snapshot identity, so that a reference can distinguish
"the current card" from "the card as used at a given time". This is what a Nextia
Evidence or Decision must pin (MOLI Architecture 1.0, stress test 12 and
`OBJECT_IDENTITY_AND_PORTABILITY.md` "Versioned references").

## How / evidence

Inspected on `main` on 2026-09-23:

- Cards have a stable `meta.card_id` and `meta.schema_version`, but no revision, snapshot
  or creation time.
- SQLite persistence appends one row per `card_id` and `load_card_sqlite` returns the
  latest, so no earlier state can be addressed.
- The SourceAssertion contract has `source.version`, but no mapping fills it. UniProt
  provides `entryAudit.entryVersion` and `sequenceVersion`.
- SourceAssertion ids exclude `source.version`, so the same assertion observed in two
  source releases shares one id.

## Why

- Consumers must be able to reproduce what they relied on after the sources change.
- The reference syntax and the pinning semantics are shared with Nextia, so they are
  decided in uibcdf/moli#3. This record owns the Sabueso implementation.

## Alternatives

Shared options are analysed in uibcdf/moli#3: content-addressed snapshots, revisions or
timestamps, or both. Locally, and not blocked:

- fill `source.version` where sources expose it;
- decide what a snapshot captures: card state, SourceAssertionStore, selection-rules
  version, source versions.

## Acceptance criteria

- Mappings record `source.version` where the source provides it (UniProt at minimum).
- Cards can be snapshotted and a pinned snapshot can be resolved from persistence,
  following the contract decided in uibcdf/moli#3.
- Offline tests show that a pinned reference keeps resolving to the same content after a
  newer card is stored.

## Implementation progress (2026-09-24)

These are local steps that uibcdf/moli#3 explicitly allows (capturing `source.version`, and
provisional internal identities):

- **Source releases.** `source.version` is filled where the source states it:
  - UniProt: the entry version (`entryAudit.entryVersion`); sequence fields also carry
    `source_metadata.sequence_version`;
  - ChEMBL, InterPro, STRING and UniChem: their release.

  The version is not part of the assertion id, so the same statement in two releases
  stays one assertion (test in `tests/core/test_source_assertions_offline.py`).
- **Curated SourceAssertions** are stable across card rebuilds through the curation store
  (#48). Their ids derive from what was stated.
- RCSB entry revisions (`rcsb_accession_info`) and the resolver's identity-link
  assertions do not carry a version yet.

Still open, and blocked by uibcdf/moli#3: card snapshots and pinned references. The
minimal workflow moli#3 asked for exists now
(`docs/content/showcase/knowledge_baseline.ipynb`).

## Resolution

Pending.
