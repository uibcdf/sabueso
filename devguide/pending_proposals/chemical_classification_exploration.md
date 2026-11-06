---
summary: Source-bound classes and roles as the scientific foundation of the required rich molecule profile.
issue: uibcdf/sabueso#148
status: locally_verified_code_checkpoint_hosted_pending
opened: 2026-11-06
verification: 705 selected local cases and public whole-session receiving at0f197e5; hosted/scientific/researcher acceptance pending
area: [chemical-context, scientific-views, human-exploration, release]
---

# Chemical classes and source-stated roles

This is B5 work in the [continuation plan](../CONTINUATION_PLAN_20261104.md),
supporting the [required molecule classification panel](card_exploration_detailed_design.md#scientific-topics-and-questions).
`Card.chemical_classification()` now supplies a detached native reading under
`chemical_classification_context@1`. The live human and compact-agent
classification adapter now shares that exact capture. Independent original saved reading, whole-profile qualification and
researcher acceptance remain required. All broad-profile requirements before
0.15.0 remain in force; the release is not authorized.

## Scientific question and original basis

Which chemical classes and roles are retained for this exact molecular entity,
which roles are direct or inherited, and what original source supports each item?
A class or role does not establish target activity, mechanism, therapeutic effect
or drug status. Public vincristine and 2-phosphoglycolic-acid inputs exercise both
drug-oriented and biochemical context without requesting new data.

The reader captures the current Card and reports its exact pin. A standard
InChIKey Card anchor must not contradict its selected InChIKey. A ChEBI source
statement requires its explicit original ChEBI subject/record identity and a
source-supported `same_as` link to that focal anchor. The link and field statement
must carry the same retained source/version, retrieval and source metadata.
Observation comparison uses typed canonical JSON: false and zero are not the same
retained metadata. An absent or unrecognized retrieval token stays unavailable.
This checks consistency of retained observation metadata, not source authenticity
or an independently retained original provider response. The role booleans are
the retained ChEBI mapping's statements; this reader does not reconstruct an
ontology traversal or directness from absent native relations.
Missing observation context stays unknown. Coherent competing anchors remain
ambiguous; names, structures, equal values and the derived entity glossary do not
substitute for source identity.

Only declared selected assertion IDs support selected items. Exact original
asserted-list membership and its indices are retained. A changed normalized role
is not relabelled as an original ChEBI statement. Unselected alternatives, missing
IDs and stored field conflicts remain inspectable. False booleans stay false;
numbers, text, null and missing flags are never coerced into booleans.

`rows` retain separate typed locations and row references for repeated entries.
`source_memberships` points to original whole-field assertions and member positions;
it does not fabricate independently acquired per-item lineage. Complete original
assertions and identity relationships are retained once in centralized inputs,
avoiding repeated full source lists on every row. Mutating a returned reading does
not alter the Card.

Rows carry compact `support_reason` codes; field `support_checks` and centralized
`identity_bindings` explain missing records, mismatched paths and unknown/ambiguous
identity without requiring an agent to digest every original source list.

`unknown`, `partial`, `missing_prerequisite` and `not_applicable` remain distinct
from an explicitly retained empty list. Original nodes, malformed containers,
unrecognized terms and flags stay readable. The result covers retained fields;
it does not establish source-wide completeness or absence.

## Live human and agent journey

For a captured small-molecule Card:

```python
explorer = molecule.explore()
classes = explorer.answer("classification")  # Also explorer.view("classification")
direct = classes.filter("assignment", equals="direct")
item = direct.items()[0]  # Inspect items() before choosing when context is unknown.
item.open()  # Original value, assignment, admitted category flags.
item.explain()  # Original field and explicit identity statements.
item.related()  # Source, original member/field, identity and quality routes.
item.open().back()  # The exact selected view.

selected = explorer.access.select(
    "chemical_classification",
    fields=["term_ref", "assignment", "application"],
    where={"application": True},
    order_by={"column": "label"},
)
page = selected.page()
```

The nature-specific human key `classification` retains disease semantics on disease
Cards. Its molecule label is Chemical classes and source-stated roles. The machine
key is `chemical_classification`, adapter `chemical_classification_exploration@1`.
Only opening that topic/question materializes the frozen native v1 kernel; human
and agent requests within one exploration reuse it. No Card or current mapping is
constructed from the capture. Genuine SDK192 public readings match canonical bytes.

Each original selected member position stays separate, including duplicates.
Direct, inherited, unstated and unknown assignments are distinct. False role-category
flags stay false; null means not stated or not admitted, including flags inapplicable
to class rows. Typed flag filtering accepts booleans/null and rejects zero/text.
Projection never drops the mandatory interpretation and source-membership routes.
Exact item membership, missing-last stable order, bounded pages/cursors and atomic
value/scope/support deferral retain complete inspection destinations.

The readable opening states the original field and interpretation states and the
limits of the knowledge. Unknown/partial science stays visible through empty display
selections. Item detail preserves original malformed values; source/identity/field
support, alternatives and stored conflicts remain reachable. Text and HTML preserve
the same meaning. Original whole-field sources do not become independently acquired
per-item lineage or reconstructed ontology traversal.

## Independent original saved-reading candidate

The explicit semantic format `sabueso.card_exploration@15` now adds original
chemical result, human/agent request, row/flag/support and display bindings.
The separate sharing representation @16 carries this semantic format while
keeping earlier @13/@14 representations and every @1–@12 semantic verifier
unchanged. Earlier supported scientific views retain their own frozen predicates;
the new @15 verifier includes those original predicates and adds chemical dispatch.
No Card is constructed, no current chemical scientific engine or profile catalogue
runs, and expected frozen findings verify retained output rather than replace it.

The genuine clean SDK193 live capsule predates this saved reader. Its original
native/wire/row inputs are authoritative controls, including the original member
order. Mapping iteration after canonical JSON sorting cannot reorder those members.
Original lookup handles are resolved against their retained locations; a fresh
reader's nonce never substitutes for original request identity. Live/saved display
mode may differ explicitly while original science, focal identity and context stay
fixed. False/null category states, retained uncertainties, typed selections and
whole-field support grain remain unchanged.

Saving now retains already executed chemical agent requests in the same session,
without issuing new queries or materializing a new scientific topic. Exact saved
queries return their retained selections; unvisited projections/filters report
`not_saved`. Filtered/focused/root and source navigation remain inspectable, and
repeat saving preserves original science. Focused detail keeps its original
member payload through summary/table/sort/filter operations, including an empty
display selection. Human and agent origins can reuse the same source links: the
only admitted human chemical question has empty scientific options, and original
request context remains recorded. Positive/None byte-budget overrides
remain explicit; no silent truncation or larger default budget is introduced.

The first selected controls exercise plain/gzip/Zstandard, explicit @16 receiving,
fresh-process reading with Card/current engines/catalogues forbidden, and resealed
changes to source statements, rules, role flags, order, membership and scope.
These are development observations. Full mixed-nature, copied installed, wider
historical, representative workload and exact-source qualification remain required
before declaring this panel complete. Scientific/researcher acceptance and the
entire broad 0.15.0 design remain open; no release is authorized.

## Current receiving checkpoint

Code checkpoint `0f197e5` now commits the unchanged candidate runtime/test blobs.
The [local receiving receipt](../evidence/chemical_saved_checkpoint_20261106.json)
records 95 chemical, 428 adjacent, 123 historical, 57 metadata and 2 isolated
outer cases: **705 distinct selected cases**. It also records shape/registry/
schema/governance/Ruff and warning-fatal Sphinx plus two whole public molecule
save/read/resave controls with 114 source/context routes, default transport limits,
zero source queries and frozen-current-engine-independent reading.

Agent cell parity compares original typed targets, payload hashes, values,
states/reasons and support; raw page lookup tokens follow their session-local
lifecycle. The initial raw-token workload assertion was an incorrect test oracle,
not a library defect. Earlier failing/stopped receipts remain historical.
Hosted exact-final-source, installed-artifact and independent scientist/researcher
acceptance remain pending; broad B3–B7 and paused B8 are unchanged.

### Historical precommit receiving

The [literal metadata routing correction](../pending_bugs/chemical_literal_metadata_routing.md)
now has a reproduced false-context regression and ownership-based dispatch.
All ten adapter/type controls and a separate hostile scientific-manifest claim
pass with minimal synthetic Cards under the 128 MiB focused guard. Three further
related/back controls reproduce and correct the literal item-link discriminator;
the combined14-case gate passes. This is not a replacement for public-input
scientific qualification.

The [saved candidate receipt](../evidence/chemical_saved_candidate_20261106.json)
preserves81 earlier native/live/saved cases and428 adjacent navigation/argument/
quantity/literal cases,509 distinct cases before the namespace correction.
Current-source receiving passes the14 focused controls and57 separate registry/
licensing/delivery cases and the delivery/registry/schema/governance tools.
An initial final Ruff rerun deferred at the128MiB preflight. Both complete root
Ruff gates subsequently pass under a stricter32MiB static-tool cap and unchanged
6GiB reserve. Earlier copied consumers must receive the final38-case saved module
again. The latest complete95-case source attempt again deferred before launch:
6673874944 available bytes are below the6GiB reserve plus512MiB preflight.
The123-case historical run stopped at the unchanged6GiB host-available reserve;
the bounded watch timed out without launching a test, and the current full source
gate deferred before launch. None is passing qualification. Split historical
modules and complete applicable public, mixed, copied and workload gates when
headroom returns; do not raise resource limits. The source remains an uncommitted
development candidate, with no release or complete-panel claim.

Resource resumption: complete source/history/copied/shape/docs/workload receiving
when host available RAM safely meets each original guard, keeping one low-priority
CPU and zero owned swap. The repeated reserve blocker has recurred across at least
three goal continuations; no active monitor or gate remains. All broad B3–B7 and
maintainer-deferred B2 requirements remain in force. Do not interpret the resource
block as implementation completion or authority to commit an unqualified block.

## Experience review during receiving

Observed: the classification opening distinguishes chemical membership from
source-stated roles, explains direct/inherited labels and preserves important
unknowns through a filtered result. Original member, source, field and identity
links give the researcher distinct next actions and a way back. The namespace
regressions correct interrupted save/navigation rather than merely adjusting
wording. These are developer observations, not uncoached researcher acceptance.

Remaining friction: the conflict/support wording still refers the human to
`native_payload`, despite the retained field-context link. The field-context
destination also remains a literal inspection. It is a hypothesis that this
slows a researcher unfamiliar with Card internals; evaluate a clearer direct
conflict/alternative route in the whole-molecule walkthrough. The complete
profile must let the researcher inspect consequential alternatives without
requiring internal field paths. Do not declare the exceptional experience from
the current passing tests or source controls alone.

## Adjacent integrity correction

The public-input tests exposed [shared mutable field/source values](../pending_bugs/selected_value_source_alias.md).
The selected field now owns a separate value and support-ID list. Explicit Card
and source edits remain possible, but neither silently rewrites the other. Initial
serialized values, units, schemas and original saved verifier meanings are unchanged.

The [native receiving record](../evidence/chemical_classification_20261106.json) retains
its original passing/stopped checks. The
[live-profile receiving record](../evidence/chemical_profile_live_20261106.json)
records668 distinct selected cases, the isolated27-case capsule consumer, actual
public task measurements and unchanged historical kernels/verifiers/storage.
These are engineering observations, not independent scientific/researcher or
representative-workload acceptance. B2 scientific review stays maintainer-deferred;
B3 scope/acceptance and B4/B6/B7 work remain pending. No default measurement
policy, schema freeze, candidate selection or 0.15.0 publication follows.
