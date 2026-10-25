---
summary: Admit source-bound canonical coordinates before ligand-site overlap.
issue: uibcdf/sabueso#163
status: open
opened: 2026-10-24
verification: in_progress
area: [knowledge-integrity, scientific-views, packets]
---

# Ligand overlap coordinate scope

An explicitly synthetic native UniProt feature on an unidentified foreign molecule
was compared with canonical PDBe-KB contact positions solely because their numbers
were equal. The previous `annotated_site_overlap@2` could report an overlap, or a
negative overlap, without establishing a shared coordinate axis. No affected live
record or private pilot content is asserted by this reproduction.

## Correction

`ligand_site_coordinate_scope@1` admits original coordinate inputs before
`annotated_site_overlap@3` compares them. This is pure reading over the captured
Card: no service request, sequence alignment, atom projection or identity inference.

- The focal protein needs a consistent canonical UniProt identity, sequence and
  integer sequence length with actual matching source records. Conflicting selected
  values or original support prevent comparison.
- Each retained annotation remains a row with `recorded_annotation`, exact original
  support and a `scope` status/reason. An unsupported collection is retained too.
  Unknown, foreign, fuzzy, compound or invalid coordinates stay uncomputed. Native
  UniProt feature type, molecule, original bounds/modifiers, record identity and
  normalized canonical axis must agree. Explicit InterPro family fragments keep
  their disjoint position set and original model support.
- Each contact requires an exact focal subject, source-bound ligand object and
  explicitly canonical numbering. Original PDBe-KB residue numbering, both exact
  endpoints and ligand identity must support the mapped positions. A normalized
  value cannot conceal different native coordinates. Literal supplied support must
  bind both object and qualifiers; bare qualifiers alone are insufficient.
- Known invalid or conflicting sequence revisions block comparison. Missing
  revisions stay explicitly `not_stated` or `partially_stated`: no version agreement
  is inferred. PDBe-KB contact revision is `not_stated`. The result describes
  source-declared canonical numbering, not atomic completeness, sequence revision
  equivalence or proximity.
- `comparison_not_computed` is never `no_annotated_overlap`. A positive may be
  `partial` if other annotations cannot be compared. A negative requires all
  retained annotations to be comparable. `no_annotated_sites` means only that none
  are retained on this Card. Contact `positions` / `residues` are null when their
  scope is not admitted; `recorded_residues` retains the input.

The native explanation retains canonical reference fields and their original
source support beside the classification inputs. Its existing presence/support
status is separate from `comparison.status`; a well-supported statement can still
be scientifically incomparable. Derived scope/results are never SourceAssertions.

## History and boundary

Default `packet_aspects@11` declares both new scientific rules alongside unchanged
`annotated_site_source_support@1` and `ligand_instance_scope@1`. The exact native
site reader from `b991384` is frozen for `@10`; `@8`/`@9` and `@6`/`@7` keep their
previous readers. Full and index terms validate using the actual saved mapping,
without reinterpreting historical results as current classifications.

Oligomer family-site reading retains that original projection and its independent
scoped agreement rule. No stored Card field, schema version, migration, identifier,
shared MOLI wire format, Evidence or project conclusion is added. Unpublished
schema 0.3.14 and shape coverage of 1,938 paths remain unchanged. Broader isoform
mapping, original metadata losses, aggregate/instance/assembly reconciliation,
region/structure navigation and human/agent acceptance remain separate work under
#148, all required within the complete design before 0.15.0.

## Verification and retained work

The initial corrected selection passes 224 cases / 66.49 seconds with twelve
pytest-receptor workers and fatal runtime/SQLite/unraisable guards. Broader local,
full-source and exact-SHA remote qualification are recorded when complete; this
initial result is not a release claim. The subsequent local-original integration
passes **393 cases / 116.20 seconds** with the same guards. Ruff, unchanged
schema/shape, fixture delivery, registry, dependency/governance, Markdown/Python
3.11 syntax, 37 offline public guide blocks and warning-fatal Sphinx pass. Final
full and remote qualification remain pending.

Reproductions, exact frozen-body proof and gate logs are retained in
`recovered_work/ligand_overlap_scope_163_20261024/`, owned by #163/#148 and reviewed
at the next exploration checkpoint or release. Previous #162 originals remain
unchanged. Scientific services queried: zero. Private pilot reads: zero.
