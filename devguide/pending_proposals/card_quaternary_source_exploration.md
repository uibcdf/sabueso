---
summary: Original subunit, assembly and interface declarations with source/structure navigation and independent saved reading.
issue: uibcdf/sabueso#148
status: open
opened: 2026-10-26
verification: qualified_source_checkpoint
area: [human-exploration, protein, storage, navigation]
---

# Quaternary source exploration

`explorer.view("quaternary_structure")` and `answer("quaternary_structure")`
present three distinct grains: the original subunit annotation field, individual
assembly records inside exact-subject structure relationships, and exact-subject
interface relationships. This is source presentation, not a new oligomer reader.
This source pane did not change `Card.oligomer()` / `explain_oligomer()`.
The subsequent [native #165 correction](../pending_bugs/quaternary_interpretation_scope.md)
introduces independently versioned interpretation. A separate
[live human/agent adapter](card_quaternary_interpretation.md) now shares those
findings; original saved scientific interpretation remains pending.

The frozen `card_quaternary_source_v1.py` predicates bind full typed source
locations, original indices and field/relationship support. Equal assembly IDs in
different structures, or repeated IDs in one list, never merge items. Missing,
explicitly empty, malformed and non-applicable scope stays distinct; identity
prerequisites prevent selecting relationships for an inconsistent focal subject.
Whole-field subunit support is not invented as per-annotation attribution.

Readable cells select by kind, structure, assembly ID or partner. Preview limits
and HTML escaping preserve full values in `open()` / `native_payload`. Original
stoichiometry, methods, numbering and conflicting qualifiers remain visible.
Source curation, a symmetry label or a shared PDB reference does not establish
biological relevance, an interface-to-assembly projection or ligand occurrence
identity. Existing quantity/field-unit negotiation remains unchanged.

`quaternary_context_links@1` gives exact local source and containing-structure
destinations. Interface structure links require both its original declared PDB
reference and a retained structure relationship for the same subject; every
matching declaration remains a distinct typed destination. These links make no
external identity resolution or source request. Saved navigation verifies the
entire original link list and its actual source/detail origin.

Original source-pane reading uses the existing literal exploration format and
the explicit `quaternary_structure_fields@1` presentation. Its frozen membership,
scope and adapter are verified without a current field producer, Card construction,
native scientific calculation, fixture reads or network. Genuine @1/@2/@3 producer
capsules remain unchanged. No Card schema, packet, source registry or provider
acquisition change is introduced.

Agents can use `rows()` and the existing bounded literal `CardAccess.read` over
exact original locations, including nested `value_location` reads. Page-member
completeness is separate from nested-value inclusion. This does not implement a
named compact scientific quaternary selector by itself. The separate live
computed topic supplies that selector. Original scientific saved reading,
broader region/model/assembly transitions, agreed workloads and actual researcher
acceptance remain in the [completion inventory](card_exploration_completion_0150.md).

The initial integration passes **324 cases**, then the broad integration passes
**986 cases /94.01s**, with twelve receptor workers and
fatal runtime/SQLite/unraisable guards. It covers the public TcTIM source pane,
synthetic gaps/duplicates/foreign identity, complete sources/return paths, direct
structure navigation, independent original reading, old producer capsules and
rehashed adapter/scope/cell/membership/destination changes. Broader final gates
and exact-source remote qualification have separate receipts in #148/#112.

The preceding saved-comparison checkpoint's Windows CI exposed a test-fixture
encoding error on all four Python lanes (3.11–3.14): a sealed UTF-8 output was reloaded with the locale default before
preparing a fresh subprocess input. A regression forcing CP1252 reproduces digest
corruption before the fix; explicit UTF-8 reads preserve the original seals.
Independent fixture-access audit hooks also recognize both path separators.
The public writer/reader already use UTF-8; no hash verification is relaxed and
the original producer capsule is unchanged. Replacement exact-source Windows
qualification subsequently passes at `b4f7d31`: CI **15/15**, governance **1/1**,
including every Windows 3.11–3.14 lane, with full receptor captures and all
thirteen pytest summaries verified. Its local full suite passes **7,321** cases.
The [source-specific closeout](https://github.com/uibcdf/sabueso/issues/148#issuecomment-6431548974)
does not qualify the later native #165 correction automatically; the preceding
failed CI remains diagnostic history.

Owned local evidence: `recovered_work/quaternary_148_20261027/`; owner #148/#112,
review at the next exploration checkpoint or release acceptance. Retain useful
public proof and remove finished owned scratch; preserve active test/CI sessions.
Run one owned twelve-worker pytest tree at a time and verify actual descendant
termination after interruption, following the existing temporary-resource policy.
No separate environment, scientific online query or private pilot read is needed.

The maintainer-requested broader Swiss-Prot utilization audit is tracked separately
in [#164](https://github.com/uibcdf/sabueso/issues/164). It does not replace the
exploration order. 0.15.0 consolidation, schema freezing, staging and release remain
paused.
