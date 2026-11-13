---
summary: Initial Deck reuse audit and the concrete boundary required before implementing the 0.16.0 Deck explorer.
issue: uibcdf/sabueso#153
status: open
opened: 2026-11-13
verification: source_review
area: [deck, human-exploration, interoperability]
---

# Deck exploration: reuse audit

This completes the initial source inventory in S3.1 of the
[implementation checkpoint](interactive_implementation_0160.md). The native human/agent contract and its first Qt workflow are now implemented
in development; final checkpoint qualification is recorded in the living plan.
No independent saved Deck exploration format is implemented. The existing #153
request owns that remaining contract; no duplicate feature issue is needed.

| Existing surface | Reuse and boundary |
| --- | --- |
| [`Deck.cards`, `meta`, `snapshot_id`](../../sabueso/core/deck.py) | Ordered members and a content address over metadata plus pinned Card states. Capture the chosen state explicitly; the mutable live Deck is not a frozen UI session |
| `basis`, `explain`, `excluded`, `operations` | Retain why members belong, original support, exclusions and operation reproducibility. Existing membership is keyed by Card ID; repeated occurrences/revisions must not gain invented occurrence-specific support |
| `filter`, `sort`, `group_by`, `summarize` | Reuse declared operations where scientifically applicable. Do not force heterogeneous fields/quantities into one universal comparison. A Python predicate already records that it is not reproducible |
| `identity_audit` and `unique_names` | Reuse stated identity findings; a label or sequence similarity cannot merge members. Keep repeated occurrences separately addressable |
| [`Deck` JSONL/SQLite storage](../../sabueso/tools/deck/storage.py) | Both preserve metadata and verify Cards when loading. JSONL has a versioned metadata header; SQLite stores metadata by table. Reuse them; do not claim they lose metadata or silently replace them with a new archival format |
| [`Card.explore()`](../../sabueso/core/card.py) and [original saved reading](../../sabueso/core/card_exploration_storage.py) | Reuse the captured Card readers, exact result/item/source bindings, quantity codecs and independent saved verification |

Requirements under #153 (implementation status follows below):

- A captured Deck overview with finite human/agent member pages, original member
  occurrences/revisions and complete metadata/support access.
- Typed selection/filter/order discovery and exact Deck → Card → item → source
  → Deck return, without choosing a latest revision or recomputing membership.
- Explicit empty, unknown, ambiguous, missing and unsupported member context;
  search candidates do not automatically become scientific membership.
- A bounded independent saved Deck reading, or explicit references to existing
  saved Cards plus retained Deck context, with a versioned admission rule.

Next S3.2 specifies and implements these return types and limits before adding
GUI-only Deck behavior. Public names such as `Deck.explore()`/`access()` remain
API candidates until that implementation review. Require homogeneous and mixed
public walkthroughs, repeated IDs/revisions, original quantity/support retention
and inert reopening after the live Deck changes. No new shared MOLI contract or
provider implementation is selected by this audit.

## Implemented native contract

`Deck.explore()` captures detached original metadata and every ordered member
occurrence, using the same validated Card capture factory as Card exploration.
`Deck.access()` exposes the same typed finite root view. `overview()` yields a
`DeckView` with `items()`, exact `member(member_ref)`, `select(member_refs)`,
literal identifier/nature `filter(text)`, `sort("label" | "kind")`, bounded
`page(limit=..., max_bytes=..., cursor=...)`, `inspect()` and `back()`.

Pages retain exact Card pins/snapshots and original ID-keyed membership scope.
Oversized member metadata is explicitly deferred, not silently truncated; inspect
the exact member/context for full data. Page bounds do not bound complete Deck
capture/materialization. Each occurrence has a distinct `DM_` handle, including
repeated identical Cards. Anonymous members remain anonymous: no Card identity
or native Deck snapshot is invented for them. A separate `DX_` capture reference
and `DV_` view reference bind the local captured workflow. These are Sabueso-local
exploration handles, not a new shared MOLI entity contract.

`member.open()` returns `DeckCardContext`, combining the original `CardExplorer`
and the exact outer Deck return point. Its `overview()` and `access` reuse the
Card readers; its `back()` returns the original Deck selection/order. Existing
`CardView.back()` retains its within-Card semantics, preserving original saved
formats. Reader instances are cached for identical captured Card states without
merging the corresponding Deck occurrences.

The Qt application accepts stored JSONL Decks through `--deck` or the file chooser.
It supports member paging, literal filtering, identifier/nature order, complete
Deck metadata, Card/topic/source reading and exact outer return. Saving a selected
Card preserves that Card reading; the UI explicitly states that its surrounding
Deck workspace is not saved. `DeckView.capabilities` exposes `save=False` until a
proper independent Deck reading contract is delivered. Cross-entity related-Card
context, independent saved Deck reading and broader acceptance remain due; this
first contract does not promise them.

## Persisted-envelope admission

The implementation exposed [#197](https://github.com/uibcdf/sabueso/issues/197):
JSONL and SQLite loaders previously ignored their envelope's format field.
Synthetic controls admitted version 999 without warning. The correction validates
format 1, metadata-object shape and JSONL header placement before interpretation.
Version-1 data and documented header-free/table-free legacy routes retain their
meaning; unknown/malformed declarations are refused without rewriting the input.
This does not change Card schema or claim a patched public package.
