---
summary: Explicit fresh record queries from retained native links, original return and bounded entry reconciliation.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-13
verification: implementation_checkpoint
area: [human-exploration, source-access, deck, persistence]
---

# Query a referenced record without rewriting the original

The [living plan](interactive_implementation_0160.md) owns S4 completion.
Native source-free navigation still opens supplied captured destinations and
reports missing/ambiguous context. The application now separately offers
**Query referenced record** on a supported native subject/object/entity link.
It requests a fresh source record using `identity@1`; it does not turn a missing
supplied Card into a scientific absence or silently replace a supplied revision.

## Exact admission and meanings

The browser sends the exact current item/revisions, never a replacement target
string. The backend reads the original native link again on the current page,
including within a focused Deck occurrence. Only link-kind rows and admitted
roles qualify; a literal extension with `role`/`target_ref` keys does not.
Source assertions, scientific-question links and captured-revision choices do
not become general acquisition instructions.

Admitted routes are exact UniProt accessions, PDB entry IDs, PDB chemical
component IDs, positive PubChem CIDs and canonical MONDO IDs. Compatible unpinned
Sabueso protein/disease references retain their declared nature. PDB component
inputs have a 1–5 character application bound; that is not a claim that every
syntactically admitted component exists. The new component route disables UniChem
expansion. The ordinary four-kind entry selector remains unchanged.

Pinned Card/item revisions, names, arbitrary values/URLs, SMILES embedded as
link metadata, unsupported namespace/type combinations and off-page/stale/foreign
items are refused. Bare `chembl:` references are deliberately not interpreted as
molecule queries: ChEMBL names compounds, protein targets and assays, and spelling
alone cannot choose the scientific record type. This is an explicit application
limit, not a new resolver identity rule.

A retained reference is a query destination, not proof of source coverage,
identity, causal disease association or efficacy. Native support/conflicts and
unknowns remain authoritative. No new relationship or SourceAssertion is created
between the original Card and the newly returned Card. A source's current answer
may disagree with the old capture; both remain separately inspectable.

## Background, saving and return

This uses the existing single background worker, cancellation/discard and exact
adoption checks. Browsing continues while the source works. A late result waits
for explicit opening after a reading change. Return to previous query restores
the retained reading at adoption, including focused Card trails, original Deck
entry occurrence/filter/order and query history. Ordinary Back continues to mean
native source-free reading history.

The prior source-reference view is retained in normal query return history; a
pending job is not an archival source assertion or saved workspace component.
Explicitly replacing inputs while a job runs still has the documented late-result
adoption semantics. No mapping from the old relationship to a new identity is
inferred or retroactively inserted in a saved Card.

Whole workspaces additionally recognize the new `pdb_ligand` result kind, composing
unchanged native Card/Deck formats. Reading remains inert. Current `query_record`
button descriptors are ephemeral projections of original native links; they do
not rewrite older saved reports or claim those controls existed historically.
Original source-access outcomes now also appear in a compact visible summary,
including failed/empty/not-queried outcomes, independently of resolved identity.
The first 16 detailed access rows remain bounded while outcome counts describe
all retained original access observations. Scientific coverage retains its own
native reader and meaning.

## Obsolete terminology choices

An obsolete MONDO query now offers only the exact replacement/consideration
candidates declared by the original resolver. A choice queries a separate disease
record; the original obsolete term, candidate bases and prior reading remain.
Reopening keeps the original report and ordered choices. No replacement is followed
automatically and no historical disease identity is rewritten. Unsupported declared
candidates remain in the full original report.

## Product receiving and remaining scope

The public Qt journey uses the existing declared frozen inputs: P52270 with RCSB
1SUX → BTS chemical component; a ChEMBL compound's retained ClinicalTrials.gov
condition → MONDO disease; and a repeated disease entry → its MONDO-stated parent.
The compound's condition relation does not establish therapeutic efficacy.
Saving/reopening the fresh parent report retains exact return to the repeated
original Deck occurrence and filtered selection. An explicit synthetic InterPro
failure receives the visible distinction between resolved identity and failed
additional access; it is not a live-source observation.

No new fixture is added to `temp_data`; prepared public inputs, manifests and
receiving artifacts have their own owner/review trigger. A receiver selector
initially assumed typed relationship columns in a literal native reading; using
the actual retained row label corrects the observer without changing science or
the native readers. The failed run remains separate from passing qualification.

Supported molecular correspondence remains separate. The
[concrete Viewer receiving handoff](interactive_viewer_receiving_0160.md) specifies
the required current-model/event/index/lifetime semantics under #368 without
adopting private provider internals or changing a sibling repository. Chemical
2D, remaining disease association receiving, lifetime/platform/workload and human
acceptance retain their open scope.


## Reconcile the bounded S4 criteria

The original [implementation plan at `fb0d096`](https://github.com/uibcdf/sabueso/blob/fb0d09659f8d00685f829d6781e5d256751dac66/devguide/pending_proposals/interactive_implementation_0160.md#s4--entry-and-entity-specific-exploration)
defines S4.1 as bounded explicit entry, progress, chosen candidates and distinct
found/ambiguous/not-found/partial/failed outcomes, with no acquisition from browsing.
The combined entry/candidate/enrichment/record-link receiving covers that finite
application scope. Additional arbitrary source controls remain a possible extension;
they are not a new unlimited exit criterion for this microstage.

S4.2 calls for pertinent protein topics and source-linked sequence/annotations,
structures, ligands, changes and associations through existing Card readers,
including discoverable uncertain/unsupported scope. The retained topic index,
original overview/cell/unit/sequence presentation, supplied cross-Card navigation,
source controls and nature-specific Qt receiving cover that presentation scope.
Mapped annotation visuals keep their original S2.2/S2.5 owner; they are not supplied
by text indices or duplicated as a new protein-reader prerequisite.

The receiving receipt and living rows own actual closure of these scopes. S4.3's
chemical depiction, S4.4's complete disease-association journeys, S4.5's mapped
structural journey and S6 human/whole-version acceptance remain separate and open.
No user review is inferred from this technical reconciliation.


A presentation follow-up remains under #153/#154: the current Deck list uses full
pinned Card references as primary labels. The native capture makes their length
observable; no human navigation failure is inferred from it. A compact original
name/identifier with explicit occurrence and inspectable complete revision may
improve orientation. That is a usability hypothesis to assess in S6, preserving
exact input/revision identity and never using names as a join rule.
