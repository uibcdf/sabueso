---
summary: Admit source-bound canonical coordinates before ligand-site overlap.
issue: uibcdf/sabueso#163
status: open
opened: 2026-10-24
verification: source_ci_verified
area: [knowledge-integrity, scientific-views, packets]
---

# Ligand overlap coordinate scope

Qualification update, 2026-10-25: exact source
`680c6a1840783d4556f3f0d24fa407001f5e262c` passes
[CI 15/15](https://github.com/uibcdf/sabueso/actions/runs/40149749936) and
[governance 1/1](https://github.com/uibcdf/sabueso/actions/runs/40149749833).
Pause preparation independently verifies every full-capture member hash and
thirteen test summaries: nine public lanes pass 5,626 cases each and four
public-Ackredit lanes pass 1,431 each. See the
[pause receipt](../evidence/pause_checkpoint_20261025.json). The failed/incomplete
SDK97 results below are historical diagnostics. Current local originals are
unavailable, so no new local-original count is claimed. Owner issue #163 retains
closure; this source qualification does not complete broader #148 exploration.

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
previous readers. Canonical input IDs use the existing flat `inputs` reference shape as well as
the per-field grouping, so full/index terms retain the actual identity, sequence
and length sources even when admission is uncomputed. Generic historical terms
readers are unchanged. Full and index terms validate using the actual saved mapping,
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


Final review of intermediate `03abe2d` exposed missing canonical sources in packet
terms (the per-field grouped references alone were not traversed). Two full/index
regressions reproduce the omission; the flat declared `inputs` list corrects it
without changing historical readers. The intermediate full gate was deliberately
stopped at 1,131 passed / incomplete 7,177 and its CI was cancelled; neither is a
qualification receipt. Final validation uses the corrected source.

The final corrected receiving gate passes **185 cases / 76.41 seconds**, including
both new full/index support regressions and persisted packet reading, with twelve
receptor workers, local originals and fatal runtime/SQLite/unraisable guards.

The SDK97 full local-original gate completes with **7,178 passed / one failure**:
the naming-convention detector traversed original `recorded_residues` and treated
the retained Card key `observed_in[].structure` as a derived view key. The test
boundary now excludes only the two explicitly literal `recorded_annotation` and
`recorded_residues` subtrees. Derived view references still require `_ref`; raw
original inputs are not renamed. No runtime/source data change is made by this
follow-up. Final full qualification is repeated after this correction; the SDK97
full result and cancelled CI remain diagnostic, not passing receipts.

The corrected convention/literal-retention gate passes **89 cases / 13.95 seconds**
with twelve receptor workers, local originals and fatal runtime/SQLite/unraisable
guards. No runtime implementation changes occur in this final test-boundary fix.
