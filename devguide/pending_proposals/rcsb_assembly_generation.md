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

## Remaining native reconciliation

Issue #173 stays open. The next slice must bind exact source parent/entry/revision,
generator occurrence and label-asym identity before reporting physical members.
`asym_id_list` references `_struct_asym.id`, not author chain labels. Single
operator IDs, lists, ranges and parenthesized products need a strict symbolic
parser; products follow the source's right-to-left convention. Preserve operator
IDs as strings, duplicate/ambiguous occurrences and unsupported syntax. Count
potential work compactly before expansion, with visible refusal and an explicit
conscious override. No silent truncation is acceptable.

Version the native reconciliation rule and its independent original saved reader.
Keep missing identity, unsupported expression, foreign parent, duplicate operator
and unqueried context explicit. Contacts without an operation/assembly basis
remain unassigned. Neither generated membership nor a source assembly descriptor
establishes geometry, contact existence, biological relevance or project Evidence.
Any later coordinate transform must qualify quantities/units independently.

## Local qualification

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
