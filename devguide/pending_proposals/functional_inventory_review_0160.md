---
summary: Trace the accepted interactive 0.16.0 journeys to implementation, receiving and concrete remaining work.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-15
verification: functional_inventory_review
area: [human-exploration, acceptance, visualization, interoperability]
---

# Functional inventory toward 0.16.0

Reviewed 2026-11-15, from implementation parent `c778768` and the navigation
increment linked below. This is the first S6.3 reconciliation, not functional
acceptance, a release checklist completed by an agent or a change to the accepted
scope. The [living plan](interactive_implementation_0160.md) owns its 33 microstages;
the [experience requirements](interactive_exploration_0160.md) own the product
objective. The accepted 0.15.0 milestone remains separate.

Here `implemented` means the named bounded behavior exists with applicable
receiving; `partial` identifies a working part and a material remainder; `pending`
means the stated result or human decision has not been received. These twenty
journey rows overlap plan stages and are not a percentage, effort estimate or
replacement acceptance rule. Historical receipts qualify their own source,
provider, artifact and platform epochs, not every later commit.

| ID and accepted journey | State and inspectable implementation | Receiving and concrete remaining work |
| --- | --- | --- |
| F01 — Open and orient | `implemented`: light opening, supplied Card/Deck/original-reading entry and captured entity overview; optional Qt host and separate Python service | [S1 receipt](../evidence/interactive_card_app_checkpoint_20261113.json), [source-entry receipt](../evidence/interactive_entry_checkpoint_20261113.json). Checkout/diagnostic artifact behavior; public installation and human first-use acceptance are separate |
| F02 — Discover pertinent topics | `implemented`: scrollable native topic index, descriptions, local search and complete access beyond curated previews | [Native/source query and presentation receiving](../evidence/interactive_rich_workspace_checkpoint_20261113.json); [navigation increment](interactive_reading_navigation_0160.md). No acquisition follows from ordinary browsing |
| F03 — Read values, units and scope | `implemented`: source-linked original overview, native bounded cell cards/tables, quantity units and visible retained/unknown/missing states | [Presentation tests](../../tests/explorer/test_presentation_offline.py), [rich receipt](../evidence/interactive_rich_workspace_checkpoint_20261113.json). Previews retain explicit limits; original readers own complete values and scientific meaning |
| F04 — Inspect complete original sources | `implemented`: native items, original scope, complete text pages, source statements and Support remain available | [Application session tests](../../tests/explorer/test_session_offline.py), [navigation receipt](../evidence/interactive_reading_navigation_checkpoint_20261115.json). Compact headings disclose the complete original heading; neither labels nor display position select a source |
| F05 — Navigate and return exactly | `implemented`: Back, Overview, exact indexed trail return and keyboard access to older points beyond the five recent buttons | [Navigation increment and real Qt checks](interactive_reading_navigation_0160.md), [backend presentation/history controls](../../tests/explorer/test_presentation_offline.py). Native results, history indices and original text remain authoritative; human accessibility review stays open |
| F06 — Explore a Deck | `implemented`: original membership/metadata, filters/order, repeated occurrences, supplied related Cards and exact Card/source/Deck return | [Deck contract](deck_exploration_contract_0160.md), [cross-member receipt](../evidence/interactive_cross_member_checkpoint_20261113.json), [original Deck receipt](../evidence/interactive_deck_saved_checkpoint_20261113.json). A shared label or sequence establishes no identity or membership |
| F07 — Enter identifiers and retain ambiguity | `implemented`: explicit UniProt/PDB/SMILES/MONDO-ID queries, candidate/alternative follow-up and original query return | [Candidate receipt](../evidence/interactive_source_candidates_checkpoint_20261113.json), [referenced-record receipt](../evidence/interactive_record_queries_checkpoint_20261113.json). PDB is a structure record with related proteins; disease free-text search and arbitrary source controls are outside the delivered bounded entry |
| F08 — Choose further acquisition | `implemented`: identity-only default, explicit InterPro/AlphaFold scope, observed source outcomes and one background query with cancellation/discard/late-result adoption | [Source-enrichment receipt](../evidence/interactive_source_enrichment_checkpoint_20261113.json), [query tests](../../tests/explorer/test_queries_offline.py). An active provider HTTP request may finish after discard; fixture delays do not measure live source speed |
| F09 — Investigate a protein | `implemented`: source-linked sequence/annotations, structures, ligands, changes, associations and supporting records | [Bounded S4.2 reconciliation](interactive_record_queries_0160.md#reconcile-the-bounded-s4-criteria), [rich presentation receipt](../evidence/interactive_rich_workspace_checkpoint_20261113.json). Sequence-strip positions index retained text; mapped structural annotations belong to F14 |
| F10 — Investigate a small molecule | `partial`: source-stated identity/representations, properties with units, targets, activity, assay and publication are readable | [Chemical context](card_chemical_context_reading.md), [scientific workspace receipt](../evidence/interactive_rich_workspace_checkpoint_20261113.json). Qualified 2D belongs to F15; available 3D requires supported coordinates and mapping, without an invented conformer |
| F11 — Investigate a disease | `implemented`: definition/hierarchy, retained associations, literal directed graphs, original support and exact related-Card/Deck return | [Disease receipt](../evidence/interactive_disease_associations_checkpoint_20261113.json). Native association scope is finite; missing supplied context does not establish global absence, causality or clinical judgment |
| F12 — Follow a scientific Knowledge journey | `implemented`: public protein → source-bound BTS → activity quantity → original assay/full publication → exact repeated Deck return, including workspace saving/reopening | [Rich workspace receipt](../evidence/interactive_rich_workspace_checkpoint_20261113.json), [guarded composition receipt](../evidence/interactive_workspace_composition_checkpoint_20261115.json). This closes the bounded Knowledge route, not S4.5's separate mapped structural route |
| F13 — Use a live molecular workspace | `partial`: experimental Viewer drawing, rotation, retained float/reset viewport and explicit owned close/reopen from the initial copy | [Molecular receipt](../evidence/interactive_molecular_checkpoint_20261113.json), [lifetime receipt](../evidence/interactive_model_lifetime_checkpoint_20261114.json), [longer-session receipt](../evidence/interactive_model_scale_checkpoint_20261115.json). Models remain correspondence-not-established; supported lifecycle/background/shared-session contracts and scene recovery remain open |
| F14 — Follow annotation ↔ molecular selection | `pending`: no supported source-bound nonempty annotation selection/picking journey is claimed | [Concrete Viewer handoff](interactive_viewer_receiving_0160.md), [Viewer #368](https://github.com/uibcdf/molsysviewer/issues/368). Receive current model/index/occurrence and event identity, exact mapping, stale-domain refusal and actual bidirectional picking in Qt |
| F15 — Explore chemical 2D and interaction views | `pending`: MolSysSketcher belongs to the separate team; no renderer is adopted by Sabueso | [Consumer handoff](interactive_2d_component_0160.md), [MolSysSuite #199](https://github.com/uibcdf/molsyssuite/issues/199). Receive a supported implemented surface with exact input/atom/bond/support mappings, lifecycle and chemical-provider authority |
| F16 — Save and independently reopen | `implemented`: original Card/Deck/whole-workspace readings, exact inner trails, query history and independent layout persistence | [Whole-workspace contract](interactive_workspace_persistence_0160.md), [composition receipt](../evidence/interactive_workspace_composition_checkpoint_20261115.json), [navigation artifact/original receiving](../evidence/interactive_reading_navigation_checkpoint_20261115.json). Pending jobs, model scene/camera and provider capabilities are separate; original verifiers stay mandatory |
| F17 — Recover and stay responsive | `partial`: owned service-loss/restart, pending-query shutdown, original saved recovery, bounded workload and model-lifetime observations exist | [Researcher/workspace receipt](../evidence/interactive_rich_workspace_checkpoint_20261113.json), [larger-model diagnosis](interactive_model_scale_0160.md). Receive the reviewed [MolSysMT #763](https://github.com/uibcdf/molsysmt/issues/763) fix before qualifying 3WU2/5XNL; agree workload/session targets and expand native platform coverage. Finite RSS/USS/PSS changes do not establish or exclude a leak |
| F18 — Deliver the optional application | `partial`: compiled frontend/resources, headless separation and noneditable diagnostic wheel/source closure receive | [Application receipt](../evidence/interactive_card_app_checkpoint_20261113.json), [navigation artifact receipt](../evidence/interactive_reading_navigation_checkpoint_20261115.json). Exact-final-source full/hosted/candidate, claimed installed platforms and public distribution remain separate uncompleted gates |
| F19 — Obtain actual researcher feedback | `pending`: public uncoached tasks, input preparation and worksheet are ready; human fields remain `not_reviewed` | [Researcher review kit](interactive_researcher_review_0160.md). A maintainer and independent researcher must supply actual observations of understanding, navigation, uncertainty and accessibility; automated screenshots cannot supply them |
| F20 — Accept the version's scope | `pending`: this inventory begins S6.3; it neither accepts 0.16.0 nor authorizes delivery | Reconsider [#192](https://github.com/uibcdf/sabueso/issues/192) aggregation semantics and [#194](https://github.com/uibcdf/sabueso/issues/194) macOS scope, record workload/human decisions, then actual functional acceptance separately from S6.4's exact-candidate/publication route. No 0.15.0 exception silently closes a 0.16.0 decision |

## Immediate order and completion boundary

The navigation increment completes the concrete long-heading/older-trail polish
item, with original-reference and keyboard receiving. The narrow-panel native
capture also records vertical scroll below the heading; scroll/focus restoration
across reading changes remains a concrete local usability follow-up. Keep
the native scientist/agent/saved contracts
shared. Do not replace open provider requirements with a consumer imitation.

Receive the reviewed MolSysMT #763 correction and the supported Viewer #368
surface in their actual cohorts; receive MolSysSketcher's implemented surface
from its team. Revisit each affected row when its code/contract exists, rather
than treating issue closure or a design document as usable provider qualification.

S6.3 becomes **partial** because this inspectable inventory exists. F14/F15/F19/F20
and the stated remainders stay open; no entire-version reconciliation/acceptance
or release is complete. The main microstage ledger becomes **20 done, 11 partial
and 2 todo**, a status count rather than a completion percentage. At the next
version review, identify exact source/artifacts, repeat the applicable final
qualification and record the maintainer's explicit decisions against these rows.
