---
summary: Preserve original RCSB assembly generation before physical instance reconciliation.
issue: uibcdf/sabueso#173
status: open
opened: 2026-10-29
verification: owning_offline_qualification
area: [source-access, structural-context, human-exploration]
---

# Original assembly generation

Fresh RCSB structure requests now ask for native assembly generator rows
(`assembly_id`, `ordinal`, `asym_id_list`, `oper_expression`) and operator identity
descriptors (`id`, `name`, `type`, `symmetry_operation`). The single, batch and
instance-feature fallback queries retain this scope. No matrices or translations
are acquired by this slice.

## Stored source contract

Unpublished schema 0.3.14 optionally records the fields in each source assembly's
`generation` context on `has_structure.qualifiers.assemblies[]`. Native field
names and values stay literal. An absent field, `null`, an empty collection and
an unrecognized value remain distinct. Array order, generator ordinals, duplicate
rows, unknown identifiers and conflicting parent labels are preserved. A malformed
generation field is inspectable original input, not admitted membership.

The supporting RCSB SourceAssertion additionally stores the complete original
assembly array at `asserted_value.assembly_generation_inputs.assemblies`. Its
native parent identifiers and array ordering remain available independently of
the existing sorted descriptor projection. The assertion retains entry accession
revision and retrieval context; an API/schema version is not a dataset revision.
Existing `ligand_contact_inputs.polymer_entities` preserves source label/author
instance identifiers. Missing nonpolymer instance identity is not reconstructed
from component names or author labels.

Old fixtures, assertions, frozen Cards and original saved readers remain
unchanged. The additions are optional and listed as explicit-only migration
changes: migration neither invents old inputs nor schedules a new acquisition.
A fresh structures request obtains a new source statement, not recovered history.

## Human and agent access

The existing quaternary source pane lists each original assembly declaration.
Opening its item exposes the complete `generation` field. Its source link opens
the supporting assertion with the unsorted original parent array. Typed literal
access gives agents bounded field-level navigation, and saved exploration keeps
the original data inspectable without querying or remapping. This is source
inspection; richer physical-member presentation remains pending.

```python
assemblies = (
    card.explore().view("quaternary_structure").filter("kind", equals="assembly")
)
item = assemblies.items()[0]
original_assembly = item.open().native_payload
generation = original_assembly.get("generation")  # None for unretained old context
```

## Public qualification inputs

`temp_data/rcsb_assembly_generation/` holds a separate capture for 1SUX, 2V5B and
1HTI. Exactly three network attempts returned 59,354 complete response bytes on
2026-10-29 UTC. The prepared envelope allowed at most six attempts, 20 seconds
each within 120 seconds, 2 MiB per response and 8 MiB total, with no secondary
queries. Requests and original HTTP JSON bytes are preserved unchanged; decoded
entries are explicitly re-encoded representations. The capture index records
hashes, UTC times, native revisions and observed acquisition traces. The fixture
notice and delivery inventory declare the recorded RCSB/wwPDB CC0 basis.

2V5B currently declares an assembly with expression `1,2` and ordinal 1, and a
second with expression `1` and ordinal 2. The same source lists label-asym IDs
`A,B` for each. Descriptive polymer counts of two and one do not establish the
identity or role of every listed component, much less assembly-specific contacts.

## Native symbolic plans (#173)

`Card.assembly_generation(structure_ref=None, relationship_id=None,
expand_operations=False, operation_budget=100_000,
generation_rule="rcsb_assembly_generation@3")` reads only retained RCSB assertions.
The current rule adds the component-key binding described below; explicit
`generation_rule="rcsb_assembly_generation@1"` preserves original syntax-only
output, using frozen
`assembly_operation_expression@1`, without querying sources or changing the Card.
An exact relationship selector requires its structure reference. Focal declaration
admission reuses `experimental_structure_admission@1`; assertions must bind the
same original subject, structure and native RCSB record identifier. Different
assertions/revisions remain separate. A selected qualifier never fills missing
original inputs. This checks retained declaration scope, not source authenticity.

Every source/parent/generator keeps its original ID/index, ordinal, entry revision
and retrieval context. Duplicate parent IDs and repeated ordinals are flagged;
they are not merged. Exact typed source/generator locations work with bounded
`Card.access().read(...).page(...)`. `quality_location` exposes original acquisition
context, preserving the distinction between unavailable input and scientific absence.

The supported syntax is an ASCII ID, comma list, inclusive unpadded numeric range,
or product of adjacent parenthesized groups. Spaces/tabs can surround tokens.
String IDs such as `X0`, `01` and `_X` stay exact. Zero-padded ranges, descending
ranges, nested groups and unsupported character-code syntax remain `unsupported`
with original text and no admitted partial group prefix. Unsupported nonstring
inputs stay available at their original location without aliasing mutable Card
content. This conservative grammar does not claim the whole dictionary lexical
space is interpreted. Products retain source order and apply right to left.

Compact plans retain exact decimal group counts. `operation_count` is an exact
integer when the product fits signed 64-bit representation; otherwise it is None,
`count_state` is `factored`, and the complete exact group factors remain available.
This representation does not clip or discard the count. Decimal conversion avoids
Python's decimal-int text digit ceiling without changing that process-wide setting.

By default no operation tuples are allocated. Explicit expansion first counts the
entire request, then materializes every admitted tuple. A finite `operation_budget`
bounds selected source array/text/label work before parsing, and separately the
total requested tuple expansion before the first tuple. A separate conservative
identifier-text upper bound uses the same ceiling: many long IDs can consume too
much memory even when tuple cardinality alone fits. Refusal labels that estimate
as an upper bound, not an observed size or a lower bound; callers can deliberately
raise/disable it. Refusal is visible and
explains raised/None overrides. None removes receiving ceilings, not syntax,
source validation or actual machine limitations. Compact mode can inspect huge
potential products without allocating them. Whole-Card capture/transport costs
remain distinct (#167/#174).

Under original @1, `operator_scope="not_reconciled"` is mandatory: recognized IDs have
not yet been verified against native operator descriptors. `tuple_expansion_state`
and `expanded_tuple_count` describe delivery, not molecular completeness. Duplicate
tuples are retained declaration occurrences, not proof of separate physical copies.
The complete Card stays unchanged. This native analysis has no new saved scientific
format; existing source exploration still reopens inertly. A dedicated human/agent
scientific adapter and independent original result reader remain pending.

```python
plans = card.assembly_generation(structure_ref="pdb:2V5B")
generator = plans["sources"][0]["assemblies"][0]["generators"][0]
original = card.access().read(generator["input_location"]).page(max_bytes=8192)
expanded = card.assembly_generation(
    structure_ref="pdb:2V5B", expand_operations=True, operation_budget=100_000
)
```

## Native entry-operator keys (#173)

Original `rcsb_assembly_generation@2` reuses the unchanged @1 expression grammar
and original declaration admission. It adds `native_entry_operator_key@1`:
`_pdbx_struct_oper_list.id` identifies a record within the PDB entry, under the
[wwPDB key definition](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_pdbx_struct_oper_list.id.html)
and [entry-operation category](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Categories/pdbx_struct_oper_list.html).
Each SourceAssertion has its own registry; no other source/revision supplies
missing records. Source names, operator names and equal transforms never merge
operator IDs. Canonical numeric ranges match exact unpadded numeric IDs; `01`
remains a different singleton ID from `1`.

Every original parent projection stays linked at its exact location. Repeated
consistent projections in different parent objects refer to the same native
entry key. Duplicate IDs within one original parent, contradictory retained
name/type/symmetry text, or malformed descriptor fields mark that registry entry
ambiguous. Missing/null descriptor fields retain their original state; another
projection does not fill them. Descriptor comparison covers those retained text
fields, not matrices, geometry or identity inferred from equal transforms.

Each parsed generator gains compact `operator_bindings` grouped like its source
expression. References list matching registry indices, resolved/identified counts
and exact decimal unrepresented counts. Large missing ranges stay symbolic;
they are not enumerated. `unrepresented_scope="retained_operator_records_only"`
never asserts source-wide absence. Per-parent input states, malformed/unidentified
record issues and partial registry input remain separately inspectable. A known
key can resolve despite unrelated incomplete input. Source `operator_registry`
records retain all projections and typed original locations.

The operating budget also bounds operator rows/descriptor text before indexing,
candidate checks before range lookup, and returned reference-ID text. A read-only
forwarding adapter defers whole-Card pin capture until these preflights pass.
Expansion still emits every admitted declaration tuple, including tuples with
unresolved operator references; `operator_scope` expresses binding while
`tuple_expansion_state` describes delivery. Neither means physical copies or
contacts. Source/component/transform closure remains outside this rule.
Defaults and positive/None overrides use the existing receiving contract.

The original @1 modules remain unchanged and explicitly selectable. No Card
schema, source fixture, source acquisition or new scientific saved format is
introduced. Dedicated human/agent scientific adapters and original saved-result
verification still follow native component/instance reconciliation.

## Native component references (#173)

Current `rcsb_assembly_generation@3` preserves original operator binding and adds
`native_entry_component_key@1` over the same SourceAssertion's retained
`ligand_contact_inputs.polymer_entities`. The
[wwPDB generation field](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_pdbx_struct_assembly_gen.asym_id_list.html)
points to native `_struct_asym.id`. The
[RCSB instance schema](https://data.rcsb.org/rest/v1/schema/polymer_entity_instance)
distinguishes instance `asym_id`, author `auth_asym_id` and ligand interaction
`ligand_asym_id`. Only exact native label-asym keys are joined. Author labels,
component codes, equal sequences and selected qualifiers never supply identities.
Other assertions/revisions never fill missing input.

Each source has a `component_registry`, original `references` with typed locations
and `component_input_issues`. A unique polymer instance record is `resolved` on
the basis `native_polymer_instance_identifier`. Consistent ligand-neighbor
references are only `referenced`, on basis `native_ligand_neighbor_reference`:
they do not establish a full nonpolymer instance record. Every original neighbor
occurrence remains available. Duplicate polymer instance records, conflicting
polymer/neighbor roles, contradictory retained ligand component codes, malformed
descriptors and explicit foreign entry/conflicting parent entity identities
are `ambiguous`; none selects a winner. Missing/null descriptors stay per-record,
without completing one record from another. Original source/entity locations
cover each retained descriptor's scope.
The retained entity `rcsb_id` must also agree with its entry and any declared
entity key, using the source's entry/underscore/entity convention from the
[RCSB entity schema](https://data.rcsb.org/rest/v1/schema/polymer_entity).
It is checked without completing an absent entity key from that string.

Every parent-bound generator has `component_input_state`, `component_scope` and
ordered `component_bindings`. Each original list position keeps its location,
exact ID, registry index, repeated-label flag and state: `resolved`, `referenced`,
`ambiguous`, `unresolved` or `unrecognized_label`. A generator is `resolved` only
when every nonempty label reference resolves to a polymer instance; mixed or
neighbor-only positive context is `partial`. Missing/null/malformed/empty lists
retain their own states rather than becoming positive membership. Unsupported
operation syntax can still expose independently retained component references;
an unbound parent does not admit them. Repeated labels remain declarations, not
distinct molecular copies. Unresolved labels concern retained input only.

The existing operation budget bounds raw generator label work. New selected
component collection/identifier-text preflight runs before registry construction,
Card pin capture and tuple expansion; reference work is also checked/accounted.
The same explicit positive/None override applies. Declared operation tuples stay
available independently of component resolution. Operator binding, source/order
scope and original generation `@1`/`@2` remain unchanged and selectable. No new
source acquisition, Card schema or scientific saved format follows.

The three public controls distinguish actual retained scope: 1SUX resolves A/B as
polymer records, references C–J through ligand neighbors and leaves K/L unresolved;
2V5B resolves A but leaves B unresolved; 1HTI resolves A/B and references C as a
ligand neighbor. These are retained-key findings, not proof of complete source
inventory, molecular occurrence counts or assembly-specific contacts.

## Remaining native reconciliation

Issue #173 stays open. The next slice must preserve exact source parent/entry/revision,
generator occurrence, label-asym basis and operator scope when defining
operation-qualified occurrences. The symbolic parser/expansion preflight, native
entry-operator lookup and retained polymer/ligand-neighbor key binding are
implemented; full nonpolymer/other component closure and physical occurrence
reconciliation remain pending. Missing
polymer records are not absence of all source role references: ligand-neighbor
records also name identifiers retained in the generation inputs. Keep each
original reference's basis instead of inferring a physical identity from matching
identifier text. No silent truncation is acceptable.

Version the native reconciliation rule and its independent original saved reader.
Keep missing identity, unsupported expression, foreign parent, duplicate operator
and unqueried context explicit. Contacts without an operation/assembly basis
remain unassigned. Neither generated membership nor a source assembly descriptor
establishes geometry, contact existence, biological relevance or project Evidence.
Any later coordinate transform must qualify quantities/units independently.

## Local qualification

The component-key slice (2026-10-30) passes 116 native owning cases and a final
15-file integration of 472 cases /119.77 seconds (including those 116), serial
through pytest-receptor with fatal warning/resource guards. Peak sampled
integration RSS is 531,062,784 bytes, with zero owned swap. Both guide blocks
execute over the three public controls and a historical Card without acquisition
or mutation. All 45 protected original modules remain byte-identical to `6f94043`.
Whole-tree pinned Ruff, warning-fatal Sphinx, local links/snippets/Python 3.11
parsing, unchanged Card shape/schema, registry, fixture delivery, dependency and
governance checks pass. The added synthetic entity-record identity regression
first demonstrated the omitted check; the final owning/integration receipts
include its correction. Earlier intermediate runs and a collection-only syntax
failure are separate from this final qualification. Hosted gates are explicitly
deferred under the [intermediate recovery route](deferred_ci.md), with exact
source/SDK receipts in #173/#148/#112. Neither these checks nor earlier green
sources establish full human acceptance or release qualification.

The entry-operator binding slice (2026-10-30) passes 80 owning cases and a selected
14-file integration of 436 cases /121.88 seconds (including those 80), serial
through pytest-receptor with warning guards. Peak sampled integration RSS is
558,796,800 bytes with zero owned swap. The two updated guide blocks execute on
three public controls and one historical Card without acquisition or mutation.
All 43 protected original modules are byte-identical to source checkpoint
`0df1d56`. Whole-tree Ruff, warning-fatal Sphinx, local links/snippet syntax,
Python 3.11 parsing, unchanged Card shape/schema, source registry, fixture delivery,
dependency preflight and governance checks pass. These are selected local checks;
exact-source hosted qualification belongs to #173/#148/#112 and researcher
acceptance remains separate.

The native symbolic slice (2026-10-30) passes 50 owning cases and a selected
13-file integration of 406 cases /114.32 seconds (including those 50), serial
within each pytest-receptor invocation, with warning guards. Peak sampled
integration RSS is 564,940,800 bytes; owned swap stays zero. The two new public
guide blocks execute over three native public controls and one historical Card
without acquisition or mutation. An initial final-gate launcher typo executed
zero tests; the corrected final invocation supplies this receipt. These checks
are not a full local-original suite, exact-head hosted qualification or uncoached
researcher acceptance; source-bound hosted receipts belong to #173/#148/#112.

The preceding source-retention slice has its own historical qualification:

The selected 17-file integration passes 383 cases /173.81 seconds, including the
20 owning cases, through pytest-receptor with warning guards. The generated
source-registry gate passes another 41 cases /2.78 seconds. Sampled integration
RSS peaks at 542,142,464 bytes with zero owned swap. All 14 earlier RCSB fixtures
produce exactly the same complete mapping as the original mapper at `bbf5c84`;
the three legacy assertion sets also retain explicit regression pins. This is
selected local qualification, not a full local-original suite or a newer hosted
receipt. Owning #173/#148/#112 records exact-head CI/governance separately.

Primary source contracts: [RCSB assembly JSON schema](https://data.rcsb.org/rest/v1/schema/assembly),
[RCSB API migration guide](https://data.rcsb.org/migration-guide.html),
[wwPDB operator expressions](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_pdbx_struct_assembly_gen.oper_expression.html),
[wwPDB asym ID lists](https://mmcif.wwpdb.org/dictionaries/mmcif_pdbx_v50.dic/Items/_pdbx_struct_assembly_gen.asym_id_list.html)
and [RCSB identifiers](https://www.rcsb.org/docs/general-help/identifiers-in-pdb).
