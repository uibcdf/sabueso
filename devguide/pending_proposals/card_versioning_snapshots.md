---
summary: Version and snapshot cards so consumers can pin reproducible knowledge references.
issue: uibcdf/sabueso#7
status: partial
opened: 2026-09-23
closed:
verification: inspected
area: [identity, persistence, provenance]
blocked_by: []
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
- Sabueso owns the Card model, snapshot representation, local identifiers, storage,
  pinned reads, tests and a proposal for the public reference form. MOLI #3 reviews
  only the fields and guarantees another component needs to rely on.

## Alternatives

Sabueso can choose content-addressed snapshots, revisions or timestamps, or a
combination, provided a pinned historical read cannot silently return the latest
card. This local work is not blocked by MOLI #3. Sabueso should:

- fill `source.version` where sources expose it;
- preserve enough card state and interpretation context to recover selected values,
  conflicts, provenance and curation outcomes;
- implement and test pinned reads and explicit missing-pin behavior;
- propose an external Card and SourceAssertion reference form with examples to
  MOLI #3 before presenting it as a stable cross-component contract.

## Acceptance criteria

- Mappings record `source.version` where the source provides it (UniProt at minimum).
- Cards can be snapshotted and a pinned snapshot can be resolved from persistence.
- Offline tests show that a pinned reference keeps resolving to the same content after a
  newer card is stored, and that an absent pin never falls back to the latest card.
- The external reference form and its consumer-facing guarantees are proposed to
  uibcdf/moli#3; only cross-component adoption waits for that agreement.

## Implementation progress (2026-09-24)

These are local steps completed while public cross-component references remain
provisional:

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

Still open: implement card snapshots and pinned reads, and bring the resulting
external-reference proposal to MOLI #3. The minimal workflow requested there exists
now (`docs/content/showcase/knowledge_baseline.ipynb`). Local implementation no
longer waits for MOLI #3; publishing a stable cross-component contract does.

## Resolution

Pending.
