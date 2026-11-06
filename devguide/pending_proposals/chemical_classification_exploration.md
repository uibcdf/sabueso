---
summary: Source-bound classes and roles as the scientific foundation of the required rich molecule profile.
issue: uibcdf/sabueso#148
status: live_human_agent_implemented_saved_reading_pending
opened: 2026-11-06
verification: selected local receiving; independent original saved reading and acceptance remain pending
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

## Required continuation

Independent original chemical-profile saved reading is **not implemented yet**.
Human and agent `capabilities["save"]` are false; save refuses before creating a
file. The opening and machine descriptor explain the limitation and raw Card export.
Original saved molecule sessions retain their earlier rows and scientific meanings;
a new saved catalogue may show this new route explicitly `not_saved`, never execute
it. This temporary development boundary does not complete the required panel or B5.

Capture a genuine producer chemical adapter session, add an explicit independently
verified saved format with mixed-nature navigation, and preserve every frozen
historical verifier/codec. Qualify copied installed receiving, genuine historical
controls, representative measured workloads and independent researcher/scientific
acceptance. All broad-profile requirements before0.15.0 remain in force.

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
