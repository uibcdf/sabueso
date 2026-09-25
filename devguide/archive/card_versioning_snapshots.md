---
summary: Version and snapshot cards so consumers can pin reproducible knowledge references.
issue: uibcdf/sabueso#7
status: resolved
opened: 2026-09-23
closed: 2026-09-25
verification: measured
area: [identity, persistence, provenance]
blocked_by: []
supersedes: []
guard: tests/core/test_knowledge_store_offline.py
normative: devguide/DECISIONS.md ("Card snapshots and the knowledge store")
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

## Resolution (2026-09-25)

Implemented locally; the external form is proposed to uibcdf/moli#3.

- **Identity: both.** A snapshot is content-addressed. `Card.snapshot_id()` is the
  SHA-256 of `Card.to_dict()` in canonical JSON, with the quantities seal left out and
  SourceAssertions and relationships in canonical order (`sabueso/core/snapshot.py`).
  The knowledge store (#27) records revisions: the order of a card's saves, their time
  and a note. The revision is for people; the hash is the identity and the integrity
  check.
- **What a snapshot keeps:** the whole stored card, including selected values,
  conflicts, SourceAssertions with their source releases, relationships, curation
  outcomes, selection rules, quality, the glossary of entities, and unknown keys of a
  newer schema.
- **Pinned reads.** `KnowledgeStore.load("<card_id>@sha256:<hex>")` returns that exact
  state or raises `StorageError`. A bare `card_id` means the latest revision. A
  malformed pin is an error, never a request for the latest card.
- **Items in a state.** `…@sha256:<hex>#SA_…` and `…#REL_…` cite an item as a pinned
  state holds it. An item reference without a pin is refused.
- **Migration.** Existing cards need none: their snapshot id is computed from what they
  store. `KnowledgeStore.import_card_table` turns the rows of a `save_card_sqlite`
  table into history.
- **Tests** (`tests/core/test_knowledge_store_offline.py`):
  - an older pin keeps resolving to its state, including a curation outcome, after a
    newer state is saved;
  - absent, foreign and malformed pins fail;
  - the id does not depend on build order, on JSON transit or on row order;
  - a tampered row is refused.
- **Left for uibcdf/moli#3:** the consumer-facing meaning of the forms, and their
  retention guarantees. Adopting the agreed form, or migrating from this one, is
  tracked in its own issue.
