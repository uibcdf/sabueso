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
Independent original Deck reading is now implemented at the explicit selection scope below. The existing #153 request retains broader performance/usability acceptance; no duplicate feature issue is needed.

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

S3.2 implemented these native return types and limits before the first Qt Deck
workflow. `Deck.explore()` and `access()` are now development APIs. Require homogeneous and mixed
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
Deck workspace is not saved by that Card file. `DeckView.save()` and the separate Save Deck reading action now preserve the outer Deck reading through the versioned contract below. Cross-member related-Card context is also received below; broader acceptance remains due.

## Persisted-envelope admission

The implementation exposed [#197](https://github.com/uibcdf/sabueso/issues/197):
JSONL and SQLite loaders previously ignored their envelope's format field.
Synthetic controls admitted version 999 without warning. The correction validates
format 1, metadata-object shape and JSONL header placement before interpretation.
Version-1 data and documented header-free/table-free legacy routes retain their
meaning; unknown/malformed declarations are refused without rewriting the input.
This does not change Card schema or claim a patched public package.

## Captured cross-member context

Opening any member now supplies the entire original Deck capture pool to the
native Card readers. The input order and repeated occurrences remain exactly as
captured, including when the chosen focal Card is not the first input or the
current Deck display excludes a related Card. The internal access/reader factories
reuse the already validated snapshots: opening or following a member does not
construct Cards, serialize them again, migrate them or acquire sources. Each
root reader retains its own operational state; a repeated identical Card state
can reuse its reader without merging its Deck occurrences.

Deck membership supplies context, **not identity**. Native source-supported
relationship/identity navigation remains authoritative. Equal names/sequences do
not create destinations, missing support and unsupplied targets stay explicit,
and multiple snapshots require a choice. Exact pins and source-record references
never fall back to a different revision. The public MONDO child/parent journey
and synthetic refusal/ambiguity controls are recorded in the
[cross-member receipt](../evidence/interactive_cross_member_checkpoint_20261113.json).

The application keeps `deck_context.card` and `member_ref` as the original entry
context. `scope="entry_occurrence"` and zero-based `entry_position` make that
meaning explicit; `current_card` separately describes the actual current reading,
including an unavailable destination with no Card pin. The UI shows the original
entry occurrence and Return to Deck preserves the exact selection/order/page.
The user can inspect a related Card and its sources, save/reopen that original
Card reading and return without assigning the destination to an arbitrary Deck
occurrence. These application fields are not new scientific entity identifiers.

A saved Card reading includes the whole supplied captured Card context under the
existing native original-reader format. It does **not** save original Deck
membership metadata, exclusions, operations, presentation selection/history or
layout. The UI states that limit. Independently opening that file supplies its
original Card reading, not a reconstructed Deck workspace. No new Card or saved
Card format, scientific rule or provider dependency is introduced. Capturing a
Deck still materializes all inputs; page bounds and shared input storage do not
bound total capture or derived-result memory.


## Independent original Deck reading

`DeckView.save(path, compression="none" | "gzip" | "zstd", ...)` and public
`sabueso.read_deck_exploration(path, expected_digest=None, ...)` deliver
`sabueso.deck_exploration@1`. This is a reading envelope, distinct from existing
Deck JSONL/SQLite data storage and from original Card files. It retains complete
Deck metadata (membership, exclusions, operations and extensions), all ordered
input occurrences, anonymous members, distinct revisions and the selected view's
original request/return chain. `mode` exposes `live` or `saved` without changing
original context handles. Literal filtering/selection/order remains available
in saved mode over original captured values; no current scientific analysis runs.

Each distinct focal Card uses its unchanged native original-reading bundle.
Existing Card verifiers own values, units, support, scientific interpretations
and retained navigation. The envelope verifies the exact common input order,
complete capture-pool agreement, focal/overview identity and Deck metadata/member
binding. Version 1 independently checks its closed literal operation grammar,
positions and exact parent/view references. It never constructs a Card/Deck,
migrates knowledge or invokes current Deck selection/scientific readers.
Unvisited scientific interpretations retain the native `not_saved` meaning;
saving a Deck does not silently calculate them. Original Card overviews remain
original even when the current route catalog differs. Resaving reuses the
verified Card bundles without reinterpreting them.

The application offers Save Deck reading from the outer Deck view. It also
retains the metadata panel, exact page and finite nonlinear Deck Back history
under `sabueso.deck_application@1`. Open reading and `--reading` admit the same
original Deck file independently, before replacing an existing session. Card
views still use Save reading for their original within-Card scope. A Deck file
does not restore a focused Card UI trail, source-query history, presentation
layout, model identity, camera or molecular scene; those are separate states.

Writes are validated and atomic; refusal leaves an existing destination intact.
Shared ArgDigest path/digest/compression/positive-budget contracts also hold with
`skip_digestion=True`. Defaults are 64 MiB encoded/decoded, 8 MiB codec window
and 256 MiB logical receiving work. The logical envelope budget conservatively
counts its physical JSON plus each Card's independently measured logical content.
Byte ceilings do not bound Python materialization/RSS. Version 1 can duplicate
the capture pool across distinct focal Card components; large-Deck scaling needs
measurement and reassessment under #153 before performance claims. This deliberate
composition preserves Card verification rather than introducing another Card codec.

The [receipt](../evidence/interactive_deck_saved_checkpoint_20261113.json) separates
selected regressions, public MONDO Qt save/source/return, independent process
startup, noneditable installed receiving and the remaining platform/acceptance
limits. Unknown versions, malformed/duplicate JSON, rebound inputs/metadata/views,
foreign pages, missing components, digest mismatch and budget overflow are refused
without rewriting the original. No Card schema, scientific rule, provider source
or public dependency changes.
