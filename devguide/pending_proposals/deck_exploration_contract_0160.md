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
[implementation checkpoint](interactive_implementation_0160.md). It implements
no new Deck API or saved-reading format. The existing #153 request already owns
the missing human/agent contract; no duplicate issue is needed.

| Existing surface | Reuse and boundary |
| --- | --- |
| [`Deck.cards`, `meta`, `snapshot_id`](../../sabueso/core/deck.py) | Ordered members and a content address over metadata plus pinned Card states. Capture the chosen state explicitly; the mutable live Deck is not a frozen UI session |
| `basis`, `explain`, `excluded`, `operations` | Retain why members belong, original support, exclusions and operation reproducibility. Existing membership is keyed by Card ID; repeated occurrences/revisions must not gain invented occurrence-specific support |
| `filter`, `sort`, `group_by`, `summarize` | Reuse declared operations where scientifically applicable. Do not force heterogeneous fields/quantities into one universal comparison. A Python predicate already records that it is not reproducible |
| `identity_audit` and `unique_names` | Reuse stated identity findings; a label or sequence similarity cannot merge members. Keep repeated occurrences separately addressable |
| [`Deck` JSONL/SQLite storage](../../sabueso/tools/deck/storage.py) | Both preserve metadata and verify Cards when loading. JSONL has a versioned metadata header; SQLite stores metadata by table. Reuse them; do not claim they lose metadata or silently replace them with a new archival format |
| [`Card.explore()`](../../sabueso/core/card.py) and [original saved reading](../../sabueso/core/card_exploration_storage.py) | Reuse the captured Card readers, exact result/item/source bindings, quantity codecs and independent saved verification |

Missing application contract under #153:

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
