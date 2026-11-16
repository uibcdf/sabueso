---
summary: Session-local reading scroll and focus continuity over exact native view/page/history identities.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-15
verification: implementation_checkpoint
area: [human-exploration, navigation, presentation, accessibility]
---

# Reading position and focus continuity

This resolves the concrete scroll/focus follow-up from the
[heading/history increment](interactive_reading_navigation_0160.md). The native
reading already returned exactly; this change concerns its visible position and
keyboard control, not scientific identity or saved meaning.

## Reproduction and behavior

The baseline real Qt control opens a public protein source statement with the
parent scrolled to 790 px. The child inherits 847 px and lacks heading focus.
Back happens to return to 790 px in this case, but loses the original item focus;
a repeated new visit again inherits 847 px. The baseline remains a failed
receiving record, with unchanged public input and exact native references.

With the change, the new child starts at 0 px and focuses its heading when the
initiating action still owns focus. Back restores the parent's 790 px and the
original native item button. A new visit to the same child starts fresh rather
than replaying a discarded visit's position. A separate second-page control
retains offset 40, 695 px and its own original item, independently of page zero.
Exact native result/view/text and source-parent return remain unchanged.

The frontend stores at most 256 transient presentation points. Keys combine the
exact native result/view references, Card-versus-Deck context, declared current
Card pin and Deck entry occurrence, item/text page offsets and retained history
depth. A title, matching
label, sequence or residue number never supplies identity. Native history indices
still select return points; this cache does not create a scientific navigation
authority. New branches replace a point's prior presentation; returns may reuse
only a matching retained key.

Remembered focus uses fixed control roles and native item/field/column/history
references, without source-derived selectors or copied user text. The hook restores
root scroll within current browser bounds and focuses the original control when
it still exists and is visible. Otherwise it focuses the reading container without
scrolling an unavailable control into view. A cache miss starts at the top. Layout
changes, evicted/shifted history and changed disclosure heights can cause clamping
or fallback; identical pixels across different layouts are not promised.

The frame callback is canceled on unmount and guarded against a newer reading.
If another control takes focus while an action is pending, the response does not
take it back. Background query adoption requests no automatic focus. Opening a
different Card/Deck/original workspace or a source-query context clears the local
cache; cross-query or cross-execution scroll restoration is not claimed. Saving
the current workspace keeps its current position, but positions/focus are never
serialized into original readings, Knowledge or presentation-layout files.

## Receiving

The [receipt](../evidence/interactive_reading_position_checkpoint_20261115.json)
binds the actual source, runtime/artifact payloads and completed/failed controls.
`--receive-position` on the Card/model receivers exercises new-reading top/heading,
parent scroll/control, a fresh repeat visit and page-bound return. It also holds
one real action response unchanged in the browser, lets the user type into Search,
then releases it and checks that focus/text remain there. That is an explicit
synthetic delivery-order control, not a source/server latency measurement.

The original Deck receiver additionally checks two source-declared occurrences
of the same captured Card: each new entry starts at its own top/heading and
Return to Deck focuses that occurrence's native member button. Real model
receiving checks that source/history/position navigation keeps the exact live
client, registration/readiness and initial-input binding. These are independently
owned software-rendered Qt scopes, not nonempty mapped molecular picking.

The source application/package-data and copied installed runtime gates use the
published receptor, with the existing source-only frontend declaration case
qualified separately in the source gate. Headless genuine pre-change workspace
receiving still forbids current Card/Deck construction, acquisition and optional
GUI/provider imports. Native schemas, original verifiers, scientific values and
provider interfaces are unchanged. Actual participant understanding/accessibility
remains separate from automated keyboard/DOM/native observations.

The initial draft hook used a source extension outside the existing sdist glob.
The final React hook uses the received `.tsx` closure; an independent build from
the final unpacked source archive reproduces the compiled resources exactly.
All 954 package runtime files are byte-identical across that source-only correction.
A later explicit Card-pin key refinement changes only compiled `app.js`: the
other 953 package payloads, including all Python/scientific code, are identical.
Completed Python gates keep their actual earlier file epoch. Final noneditable artifact
and Qt receiving use the final file/digest. Unpublished preliminary artifacts and
draft typecheck failures never count as final qualification or a public release.

## Plan boundary

The [twenty-journey inventory](functional_inventory_review_0160.md) now links this
bounded scroll/focus implementation. The main ledger remains **20 done, 11 partial
and 2 todo**. Supported mapped 3D, the separate MolSysSketcher implementation,
the reviewed MolSysMT #763 correction, broader workload/native-platform and
human/#192/#194/version decisions retain their owners. No workflow, release or
public package publication is selected by this UI increment.
