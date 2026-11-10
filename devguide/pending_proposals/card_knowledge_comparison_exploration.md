---
summary: Explicit typed comparison of captured protein knowledge and caller-supplied residue maps.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-09
verification: inspected
area: [public-api, human-exploration, scientific-views]
blocked_by: []
---

# Captured knowledge comparison

This B6 increment implements LIVE `knowledge_differences` and the compact-agent
`comparative_context` mode `knowledge`. Both require an exact explicitly supplied
protein capture. They share one cached `card_knowledge_diff@2` result over inert
capture facades. No Card is reconstructed and no source, alignment or geometry
calculation is requested. MolSysMT remains the alignment/modeling owner.

## Native meaning and compatibility

`Card.compare_knowledge(..., comparison_rule="card_knowledge_diff@2")` explicitly
selects typed stored-representation comparison. The published/default
`card_knowledge_diff@1` stays available with its original meaning; B2 default review
is deferred. Source inspection of tag 0.14.0 and synthetic controls show that @1
uses Python scalar equality and selects the first list identity candidate. Real
source prevalence and clean installed-release impact remain unverified. The concrete
defect report is [published in #193](https://github.com/uibcdf/sabueso/issues/193),
separate from #148's already published preceding saved-profile report.

The new rule retains booleans, integers and floats distinctly, including nested
values. Quantity values retain their declared units; this is comparison of stored
representations, not a new physical-equivalence policy. Original fields, selected
and other field assertions, missing/misbound references, conflicts and both input
pins stay visible. List item-level source attribution is not reconstructed.

Each matched item keeps its original index and complete payload. Multiple items
sharing a comparison identity remain ambiguous; none is chosen by order. Free text
is not compared. Relationship object-reference sets keep full original records,
direction, channels, qualifiers, derivations and separately retained sources.
Knowledge-state groups keep every original row, including repeated area/source
scopes; unmatched fields never establish source-stated absence.

## Caller maps

The native API accepts `{self_position: other_position}`. Portable exploration
options also accept `[[self_position, other_position], ...]` and canonicalize those
pairs without loss. Both endpoints must be positive integers, one-to-one and within
stated sequence lengths when available. Empty and omitted maps remain different.
The exact pairs and both input pins are recorded, not merely a pair count.

Positional comparison requires source-declared canonical sequence axes and complete
coverage of each annotation. Foreign/unstated axes, unsupported indexing, uncertain
boundaries, unplaced values and incomplete maps remain explicit. Large source
intervals are checked against map coverage before expansion. Mapping removes only
sequence coordinates for content comparison; structure context and other metadata
remain original. A supplied map does not validate biological correspondence or
entity identity. Sabueso never aligns or transfers positions implicitly.

## Shared human and agent projection

`protein_knowledge_comparison_exploration@1` and `protein_knowledge_projection@1`
retain separate field, predicate, knowledge-state and supplied-map row grains.
Human rows show both original values, comparison state and source support. Existing
typed column filters, stable ordering, exact item membership, bounded pages and
atomic value/support/meaning deferral apply to the new result. State keys derive
from exact native paths, never rendered labels; equal labels do not merge rows.

`open()` retains the complete native entry; `explain()` retains original support
and interpretation; `related()` reaches exact supplied captures and selected or
other field assertions. Incoming questions and actual back edges remain intact.
The original native result is shared rather than recomputed by each access route.

## Independent saving and receiving

Public human/source/compact saving uses logical `sabueso.card_exploration@35` and
shared @36. `knowledge_comparison_exploration_binding@1` freezes native @2,
`knowledge_state@5`, source declarations/item identities, typed selection, literal
catalogs and presentation/navigation. It checks original input/source/row bindings
without current comparison engines, Card reconstruction or acquisition.
`knowledge_comparison_access_origins@1` preserves actual runtime instances and
aliases, including equal focal values. Only generated rule constructors receive
producer labels; source-owned lookalikes stay literal. All earlier originals,
frozen resources and meanings remain fixed.

Retain all actual observed views and finite executed normalized requests, with
distinct human-only and machine-only scope. An observed new question menu has
its own frozen catalog even when no science was executed. Earlier formats never
gain that question. Unexecuted requests/topics remain `not_saved`. Older co-retained
protein/variant/sequence profiles use their owning predicates. A nonempty public
bioactivity crossing validates the exact incoming knowledge question/catalog
before applying the unchanged bioactivity meaning.

Prepare implicit literal support for the saved root and its originating trail,
together with executed scientific rows; retain every other observed view without
recursively materializing its unexecuted literal support. Capabilities remain
explicit when an unretained closure is needed. Production byte defaults stay
fixed. Complete archived public graphs use an explicitly declared 2 GiB logical
test allowance, while ordinary public save/read controls use defaults. Coverage
states the exact retained inputs as `not_evaluated`, without claiming global
knowledge completeness or adding members to original wires.

The [saved receipt](../evidence/knowledge_comparison_saved_checkpoint_20261110.json)
owns selected source, copied and separate local installed diagnostic qualification,
exact scopes/resources and earlier red/stopped epochs. This does not supply a
full-suite/candidate/public/OS-matrix gate, broader historical scope or B6/B7
scientific, uncoached researcher/agent, workload or actual-consumer acceptance.
B2 default review is deferred and B8/release remains unresumed.

## Clean SDK243 original captured

The [genuine original receipt](../evidence/knowledge_comparison_live_original_20261110.json)
owns the 37 complete public/synthetic cases, unchanged clean producer, all actual
source/view/access graphs and finite human/compact operations. Four bounded batches
use one prepared input set; byte-preserving assembly and SDK-free complete checking
precede immutable packaging. Every case uses one shared native comparison during
observation, with acquisition, Card reconstruction and assertion creation blocked.
All 412 selected source cases and all 42 copied original cases outside checkout
pass on their recorded scope. Source-owned packaging/version lookalikes and equal
focal actual access instances stay distinct. Both installed routes include the
complete original module and capsule; their actual hosted/installed runs remain open.

Independent receiving now preserves those bytes/outcomes and actual catalog/access
instances through the separately versioned reader above. Complete original,
coherent alteration, finite-request, transport, copied and local diagnostic controls
retain their explicit scope; broader acceptance and candidate gates remain open.
