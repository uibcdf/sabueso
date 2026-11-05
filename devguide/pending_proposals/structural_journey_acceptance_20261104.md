---
summary: B3 source-supported structural questions, observed public journeys and the remaining assembly-scope decision.
issue: uibcdf/sabueso#173
status: open
opened: 2026-11-04
verification: source_contract_review_and_selected_receiving
area: [scientific-review, structural-context, human-exploration, agent-access]
---

# B3: structural knowledge and the assembly boundary

Owner [#173](https://github.com/uibcdf/sabueso/issues/173), experience #148,
coordination #112. The [continuation plan](../CONTINUATION_PLAN_20261104.md#execution-order)
requires a defined scientific question and source-supported acceptance before
further reconciliation code. This report supplies that preparation and actual
public observations. **It does not close B3, redefine its accepted release scope,
or establish independent scientist/researcher acceptance.** The maintainer's
separate six-case bioactivity review remains explicitly deferred.

## What geometric reconstruction and calculated contacts mean

Consider a hypothetical source that declares component A under operations 1 and 2.
Sabueso can preserve that declaration, the two operator references and their source
basis. A coordinate engine reads the admitted atomic coordinates and applies each
specified rotation/translation to produce the requested coordinate sets. Repeated
sets or special positions require an explicit uniqueness criterion; two operation
declarations alone do not prove two distinct physical molecules.

A subsequent geometric task can identify atom/residue pairs satisfying an explicit
distance criterion on those coordinate sets, with model, symmetry, alternate-location
and unit scope. Such geometric contacts do not by themselves establish chemical
binding, affinity or biological relevance. A contact already reported by a provider
is instead retained source knowledge, including that provider's original scope and
uncertainty; Sabueso need not recalculate it to make it inspectable.

MolSysMT already implements the coordinate engine through public
`build.make_bioassembly()`, `structure.rotate()`, `structure.translate()` and
`structure.get_contacts()`. The 2026-11-05 UTC review below receives 62 selected
local cases on its current editable source. General importer coverage, the
Sabueso handoff and installed-artifact qualification remain distinct. Sabueso
continues its own deterministic knowledge interpretations, identity admission,
coverage and scope checks. It may supply original declarations, supported source
transforms and exact references to a coordinated modeling operation. The application
can expose one coherent journey while preserving separate knowledge support and
calculation provenance. No shared invocation or result schema is adopted here.

**Technical ownership and release delivery are different decisions.** A MolSysSuite
implementation can still be required as an integrated pre-0.15.0 capability. Its
proposed owner does not implicitly postpone it. Both the concrete task/consumer
and its release-blocking status need disposition before B3 can be closed.

## Questions and permitted answers

| Question | Required basis | Permitted answer and important limit |
| --- | --- | --- |
| What does an entry declare for an assembly? | Exact retained entry/revision, original assertion, parent/generator position, native component IDs and operation expression | Original declarations and source-supported bindings; alternative assemblies stay separate |
| Which original record does this component name? | Explicit coherent native entry/entity/instance identifiers in that same source context | Polymer/nonpolymer record, neighbor-only reference, ambiguity or unknown; author labels and chemical codes do not fill missing identity |
| How many declarations does the generator describe? | Component-list positions and supported operation tuples, with source order and exact factors | Declaration counts, including repeated positions; these are not counts of unique physical molecules or protein subunits |
| Which contact belongs to which assembly occurrence? | Source-stated contact/instance/assembly/operation scope, consistent entry/revision and compatible residue axes | A source-supported join only when those bases exist; a shared PDB ID, author chain label or residue number is insufficient |
| What physical copies and transformed contacts exist? | An agreed modeling task with admitted coordinates, transforms, units, model/alternate-location and symmetry scope | A modeling result with its own provenance and acceptance, separate from retained knowledge; no such calculation is delivered here |
| What does an experimental structure say about this model or region? | Exact original model/reference identity, source-supported sequence axis, range and checksum/context admission | Existing whole-reference question where admitted; fragments, isoforms, missing mappings and unobserved atoms remain distinct and explicit |

The [wwPDB generator category](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Categories/pdbx_struct_assembly_gen.html)
connects assembly specifications with component and transformation declarations.
Its [component list](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_pdbx_struct_assembly_gen.asym_id_list.html)
points to `struct_asym.id`; it is not an author-label identity rule. The
[operation expression](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_pdbx_struct_assembly_gen.oper_expression.html)
defines products with right-to-left application. The
[operation category](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Categories/pdbx_struct_oper_list.html)
describes Cartesian rotations/translations. These primary definitions were checked
on 2026-11-04. They do not make declaration multiplicity proof of physical uniqueness.

## Four retained public controls

The input is the genuine pre-reader `assembly_nonpolymer_live_v2.json.gz` capsule,
producer `7084894ed822dae8df4cb3707036522dd666f2d7`, SDK152, with immutable
[provenance and hashes](../../tests/core/data/README.md#original-live-nonpolymer-assembly-adapter).
No new molecular-provider call or private pilot is needed. Expected declarations
were transcribed from original input records before exercising the current reader.
The [reproduction script](../evidence/check_structural_journey_scope_20261104.py)
and [observations](../evidence/structural_journey_scope_20261104.json) preserve scope.

| Control | Original declaration / descriptor | Native interpretation and necessary uncertainty |
| --- | --- | --- |
| 1HTI | Assembly 1: A/B/C under operation 1; source oligomeric count 2 | Three declared positions, with native polymer A/B and nonpolymer C. C's author label B does not identify it with native polymer B. Physical membership remains uncomputed |
| 1SUX | Assembly 1: A–L under operation 1; source oligomeric count 2 | Twelve declared positions; ten native keys bind and K/L have no retained match. Their molecular roles and source-wide presence/absence are not inferred |
| 2V5B | Source parent order 2 then 1: A/B under 1, and A/B under 1/2; source oligomeric counts 1 and 2 respectively | Two and four declarations in separate alternative assemblies. A binds; B remains unresolved. The reader does not choose which assembly is biologically relevant |
| Legacy 1SUX Card | The original generation/component inputs were not retained | No delivered occurrence rows, but the declared count is unknown. This is not zero assemblies or zero molecular components |

Contact inputs are separate: the retained 1HTI neighbor collections contain eleven
records and one null collection; 1SUX contains 24 retained records. The 2V5B
collection is null, which does not establish zero source contacts. The legacy Card
still has 24 neighbor records despite lacking generator inputs. None of the queried
neighbor fields records an assembly/operation identity. No joining all these records
to each declared occurrence is justified. This describes retained query inputs,
not the full external database's capabilities or absent external experiments.

The current query requests operation ID/name/type/symmetry text, without numeric
matrix/vector fields or atom coordinates. Inspectable operator-key matches do not
validate transformed geometry. Source-stated transforms could be retained as
Knowledge in a future versioned input contract; applying them, validating physical
uniqueness and computing geometry require a separately accepted modeling task.
Preserve units through PyUnitWizard if translations or distances cross that boundary.

## What was exercised

For each original Card, the script follows the actual structure question, checks
one native evaluation shared with the exact compact agent request, then deliberately
requests expanded occurrences and checks one further evaluation shared with that
agent request. Compact and expanded requests are different requests, not duplicated
science for one request. Selected component positions, original bindings and source
records remain navigable, with a working return route and unchanged Card/pin.

All four journeys save and reopen in a fresh process with current Card construction,
assembly readers, network access and fixture reads forbidden. The original result
identity, delivered declaration rows and exact retained agent request survive.
Original saved verifier predicates and genuine producer capsules remain unchanged.
This is verified technical receiving, not a claim that original knowledge is true
because its historical reader agrees.

Six separate synthetic perturbations check repeated component positions,
right-to-left operation products, a missing operator, repeated operator keys,
incomplete nonpolymer identity and a foreign generator parent. They retain explicit
uncertainty and `physical_membership="not_computed"`. The script creates new
synthetic SourceAssertion IDs; it does not rewrite original source assertions or
present the perturbations as public provider observations.

Selected existing native-key, component-navigation and model-question receiving
passes 106 cases through pytest-receptor, in series, with no owned swap. The
receipt records resource observations and exact source/fixture/script identities.
No runtime, source query, native rule, schema, original fixture or frozen reader
changes are introduced by this preparation.

## Existing MolSysMT capability review — 2026-11-05 UTC

At the maintainer's suggestion, review of clean MolSysMT source
`71fbe4f46d3c70e4e973c8025f01752a8c9b1084`, SDK `0.23.0+322.g71fbe4f46`,
confirms existing implementations and 62 passing selected receptor cases. The
[receipt](../evidence/molsysmt_structural_capabilities_20261105.json) records exact
source/test hashes, resource scope, warnings and the supported limits. No MolSysMT
file, environment or source coordinate file is modified; no molecular provider
request or private pilot is involved.

The [public builder](https://github.com/uibcdf/molsysmt/blob/71fbe4f46d3c70e4e973c8025f01752a8c9b1084/molsysmt/build/make_bioassembly.py)
accepts stored/named or explicit rotation/translation dictionaries and selected
structures. The [contact reader](https://github.com/uibcdf/molsysmt/blob/71fbe4f46d3c70e4e973c8025f01752a8c9b1084/molsysmt/structure/get_contacts.py)
computes contacts under an explicit distance/PBC/endpoint policy. Native operations
also have tested H5MSM persistence with length units. Building a new geometric
engine in Sabueso is unnecessary for those supported tasks.

Two limits matter before accepting a general source-to-geometry handoff:

- **Documented builder scope:** different per-operation chain sets are currently
  refused with `NotImplementedError`; validated storage of such scopes is not
  evidence that assembly construction supports them.
- **Confirmed importer defect, [molsysmt#563](https://github.com/uibcdf/molsysmt/issues/563):**
  the mmCIF converter overwrites earlier generator rows with the same assembly ID.
  A synthetic two-row/common-chain input should produce two coordinate sets and
  1,728 atoms, but the parsed named assembly retains only the last operation and
  864 atoms. Reversing row order changes the survivor. An explicit common-chain
  dictionary preserves both operations and matches analytical coordinates. This
  establishes a provider defect, not a failure of the builder's supported direct
  route or a claim about the deposited 1BRS assembly. The owner issue contains a
  complete offline reproducer; its fix/receiving remains provider work.

The concrete next engineering task is **bounded reuse and integration**: qualify
exact entry/revision/native-instance correspondence, numeric source transforms
and units, explicit assembly/structure selection and a map from generated indices
to original declaration/operation context. Generated chain IDs and preserved author
names cannot replace that map. Choose atomic/center/group-reduction semantics and
PBC deliberately for contacts; pair output still has dense-map memory cost. Retain
provider-reported contacts separately from newly calculated results. Existing
Sabueso symbolic inputs alone do not supply admitted atomic coordinates or numeric
transforms. No new shared wire or invocation contract is adopted by this review.

Engine availability is now observed rather than hypothetical. The required scope
and pre-0.15.0 delivery of that integrated journey remain pending maintainer
choices; #173/B3 stay open. Receipt-level tests and a consumer-owned positive route
are required after the provider defect is fixed or an explicitly qualified input
route avoids it. No importer repair or workaround is installed in Sabueso here.

## Proposed exit criteria and remaining work

1. Keep the six questions above distinct in native, human, compact agent and saved
   answers. Include every consequential qualifier, source alternative and unknown.
2. Preserve exact entry/revision, assertion and generator/component/operation scope.
   Positive explicit membership must have an original source basis; repeated labels
   or coincident values cannot create identity.
3. Demonstrate readable source/open/back routes, empty/ambiguous recovery and compact
   selection over identical results. A missing historical result remains `not_saved`;
   missing source context remains unknown rather than a negative finding.
4. Complete the other B3 model/fragment/region/site transitions with their own
   source-supported axes and original saved/agent parity. This audit does not deliver
   fragment mapping, model-selection advice or complete broad structural profiles.
5. **Obtain the maintainer's assembly-scope disposition below.** Do not reinterpret
   this proposal as permission to remove a pre-0.15.0 prerequisite.
6. Qualify subsequent changed runtime at its own exact source, and obtain scientific,
   consumer, workload and actual researcher acceptance under the existing plan.

### Assembly-scope decision needed

The existing inventory repeatedly asks for "full physical reconciliation" without
an independently specified positive physical task, admitted coordinate inputs or
uniqueness criterion. The MolSysMT review identifies the existing geometric
provider. Its availability resolves the earlier engine-discovery uncertainty;
the exact consumer handoff and acceptance task remain to be defined.

Recommended disposition for review: Sabueso completes original declared membership,
source-supported contact scope, input gaps and coherent human/agent/saved access.
It preserves source-stated transforms if required by an accepted knowledge task.
Coordinate reconstruction, physical-copy deduplication and transformed-contact
calculation belong to a coordinated MolSysSuite modeling task. This follows the
existing [MOLI functional boundary](https://github.com/uibcdf/moli/blob/main/architecture_1.0/FUNCTIONAL_VIEW.md),
not a proposed transfer of Sabueso's semantic ownership.

With MolSysMT identified, the maintainer must disposition the concrete integrated
modeling task and consumer responsibilities, and say whether its successful
receiving must also block B3/0.15.0, or whether B3's scientific obligation is the complete
source-supported knowledge route with its explicit limits. If required, identify
its exact question and consumer acceptance and open/cross-link the owning provider
work before coding. Neither option permits silently guessing geometry or declaring
unknown contact membership resolved. **Decision pending; #173 and B3 stay open.**

## Experience review

Observed: the structure question is discoverable without typing native rule names;
its original assembly/component/source route, exact agent request and saved reading
work on the four controls. Unresolved declarations remain visible alongside positive
bindings. The researcher can inspect why source dimer descriptions coexist with
three or twelve component declarations.

Still unaccepted: users have not performed these tasks uncoached. The distinction
between protein subunits, component positions, alternative assemblies and physical
copies requires explicit scientific wording and user review. Broad model/fragment
transitions, contact reconciliation and whole-session workload budgets remain open.
Review the count/identity questions above with a scientist and a researcher; do not
predict satisfaction from a passing script or add navigation indefinitely without
resolving its scientific scope.
