---
summary: Explicit versioned native nonpolymer component keys before adapter adoption.
issue: uibcdf/sabueso#173
status: open
opened: 2026-11-03
verification: owning_offline_qualification
area: [scientific-context, structural-context, public-api]
---

# Native nonpolymer component keys

## Public scope and rollout

`Card.assembly_generation(generation_rule="rcsb_assembly_generation@5")` opts in to
`native_entry_component_key@2`, using the [new original nonpolymer inputs](rcsb_nonpolymer_inputs.md).
The default remains @4. Explicit @1–@4, the live human/compact assembly adapters
and original saved interpretation retain their previous meanings. This native
slice introduces no saved scientific format, new acquisition or stored Card field.
Independent original saved verification must qualify @5 before the adapters adopt
it. Full #173 physical reconciliation, #148 researcher acceptance and paused 0.15.0
consolidation remain separate work.

## Identity and ambiguity contract

All matching stays inside one admitted RCSB entry SourceAssertion and its original
revision. Native label-asym identifiers supply keys. Author chain labels, residue
numbers and chemical component codes never supply a missing native identifier.
The [RCSB entity](https://data.rcsb.org/rest/v1/schema/nonpolymer_entity) and
[instance schemas](https://data.rcsb.org/rest/v1/schema/nonpolymer_entity_instance)
define the original identifier fields and entry/entity versus entry/instance
record-ID forms; reviewed snapshots remain owned with the source-capture proof.

A nonpolymer record is resolved under this conservative rule only with a valid
native `asym_id` plus explicit, coherent context: parent `entry_id`, `entity_id`
and `rcsb_id`; instance `entry_id`, `entity_id` and `rcsb_id`. Required missing/null
fields remain `identity_gaps` with `identity_state="incomplete"`. This is the rule's
admission requirement, not a claim that all those fields are mandatory in every
provider schema. Record IDs are checked against stated fields; they never fill
missing fields. Optional container `rcsb_id` values are checked when stated.
No parent field or another record/revision repairs an incomplete instance.

Optional author labels/numbering and chemical codes keep their own descriptor
states. Their absence does not erase an independently resolved native key. Retained
nontext descriptors, invalid identifiers, foreign entries, contradictory parent
entity/record IDs and component codes cause explicit ambiguity. Entity `asym_ids`
and `auth_asym_ids` arrays remain original context; their positions are not zipped
and a list's unrepresented identifier is not treated as a source-wide negative.

Original polymer-instance and ligand-neighbor references remain linked. A coherent
full nonpolymer instance and compatible neighbor references share an exact native
key while retaining each role, descriptor and original location. The full native
record can resolve the key without any neighbor reference. Incomplete new native
context with independent neighbors remains `referenced`; without neighbors it
remains `unresolved`. Missing input never establishes absence.

All duplicates and contradictions remain visible. Repeated instance keys, repeated
entity keys or entity/instance record IDs cause ambiguity even for identical rows.
A record-ID duplicate with an incompatible or missing label also marks the otherwise
coherent record ambiguous; the unknown label is not reconstructed. Exact duplicate
record-ID issues have original locations. A polymer/nonpolymer role conflict or
incompatible neighbor/native component codes cannot select a winner. Each source
assertion has its own registry; equal keys across revisions never pool information.

The resulting registry, generator bindings and expanded declared occurrences use
the same @2 key basis. All original paths remain usable through human literal
inspection and bounded compact access. The original Card and source support stay
unchanged. Key binding, complete delivery, declared count and physical membership
remain independent: even a resolved key does not establish a distinct physical
copy, geometry, assembly-specific contacts or biological relevance.

## Workload and delivery

The frozen compact @4 prefix supplies original admission, syntax/operators and
polymer/neighbor references without Card pin capture or expansion. A selected-source
nonpolymer preflight checks every entity/instance collection and interpreted
identifier/descriptor text before new registry construction. This is an additional
cumulative work ceiling using the existing positive/None `operation_budget`,
separate from original polymer/operator and expansion ceilings. Uninterpreted
source context and complete Card capture/transport are not bounded by that counter.

New key bindings are prepared before occurrence planning. Every requested operation
and occurrence count/text ceiling passes before actual pin capture or expansion.
The same visible diagnostic explains deliberately raising the budget or using
None; no request is clipped or replaced by a valid prefix. Unsupported expressions
can expose independent key bindings, while foreign generator parents never admit
them as members. Declared positions, repeats, unknown keys and factored large counts
retain their existing occurrence rule. No coordinate transforms are performed.

## Qualification and next step

Public originals are the unchanged 1SUX, 2V5B and 1HTI controls. Under @5, native
nonpolymer keys C–J of 1SUX resolve while generator K/L remain unresolved; 1HTI
PGA C resolves separately from author label B and polymer B. 2V5B's original null
scope leaves generator B unresolved. Under @4 those original neighbor-only keys
keep their earlier referenced basis. No provider queries are needed for this slice.

Owning tests cover public positives, absent/partial/unsupported context, independent
native records, exact original locations, duplicates and conflicting roles/IDs,
separate source revisions, explicit selected-source preflight, untouched original
rules/default/adapters, scoped budget refusal before pin/expansion and positive/None
overrides. Broader native, argument, human/agent/saved and quantity gates and
the [approved intermediate batching route](deferred_ci.md) apply to this native
step. Its actual head, local scope and missing remote gates are recorded in
#173/#148/#112. An unskipped exact-source checkpoint must recover the accumulated
native/original-reader/adapter block before adoption or completed-code qualification;
if the reader is deferred, recover the native checkpoint earlier. Pending/skipped
CI does not qualify it or close the issue.

The selected local checkpoint passes **650 cases /18 files**, in four serial
pytest-receptor invocations (63 + 263 + 183 + 141; 350.37 pytest seconds). Peak
owned RSS is 420,909,056 bytes, minimum host available RAM 13,844,025,344 bytes and
owned swap zero, under the existing @2 resource supervisor. All 67 checked original
native/mapping/policy/verifier files remain byte-identical, as do stored-form
semantics, fixtures, schemas and migration. The actual public @5 guide example
passes three new/original/synthetic-partial controls without acquisition or Card
mutation. Warning-fatal Sphinx and applicable Ruff, schema, registry/delivery,
governance and Markdown/Python checks pass. This is a scoped local receipt, not
a full local suite, remote matrix qualification or researcher acceptance.

Owner #173/#148/#112. Useful source/test/resource proof belongs under
`recovered_work/assembly_nonpolymer_binding_173_20261103/` until original saved
reader/adaptor adoption or pre-0.15.0 review. Remove completed owned test/build
scratch after its last use. Existing original fixtures and active remote captures
retain their owners. Next, freeze and qualify independent original @5 scientific
reading before making the new interpretation a human/agent exploration default.
