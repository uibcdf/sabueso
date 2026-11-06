---
summary: Source-bound classes and roles as the scientific foundation of the required rich molecule profile.
issue: uibcdf/sabueso#148
status: native_foundation_implemented
opened: 2026-11-06
verification: selected local receiving; rich human/agent/saved profile remains pending
area: [chemical-context, scientific-views, human-exploration, release]
---

# Chemical classes and source-stated roles

This is B5 work in the [continuation plan](../CONTINUATION_PLAN_20261104.md),
supporting the [required molecule classification panel](card_exploration_detailed_design.md#scientific-topics-and-questions).
`Card.chemical_classification()` now supplies a detached native reading under
`chemical_classification_context@1`. It is a scientific prerequisite, not delivery
or acceptance of the full human panel. All broad-profile requirements before
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

## Required continuation

Integrate the native reading into the nature-specific classification topic with
readable classes/roles, direct/inherited/unknown basis, exact source/open/back
routes and compact targeted agent access. Add independent original saved reading
with an explicit version boundary as required; do not broaden an old frozen
profile verifier. Keep old molecule/disease menus and scientific meanings intact.
Qualify copied installed receiving, genuine historical controls, mixed nature
navigation, measured workloads and independent researcher/scientific acceptance.
The native method alone does not complete this panel or B5.

## Adjacent integrity correction

The public-input tests exposed [shared mutable field/source values](../pending_bugs/selected_value_source_alias.md).
The selected field now owns a separate value and support-ID list. Explicit Card
and source edits remain possible, but neither silently rewrites the other. Initial
serialized values, units, schemas and original saved verifier meanings are unchanged.

The [receiving record](../evidence/chemical_classification_20261106.json) retains
actual passing/stopped checks. B2 scientific review stays maintainer-deferred;
B3 scope/acceptance and B4/B6/B7 work remain pending. No default measurement
policy, schema freeze, candidate selection or 0.15.0 publication follows.
