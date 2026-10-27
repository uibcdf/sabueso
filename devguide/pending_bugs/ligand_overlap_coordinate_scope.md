---
summary: Admit source-bound canonical coordinates before ligand-site overlap.
issue: uibcdf/sabueso#163
status: resolved
opened: 2026-10-24
closed: 2026-10-26
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
SDK97 results below are historical diagnostics. The pause receipt records
unavailable local originals in its Diego checkout; on 2026-10-26 this Liliana
checkout has all 37 originals with matching hashes. Availability is not a new
pytest result. [Issue #163 is closed](https://github.com/uibcdf/sabueso/issues/163#issuecomment-6425149264); this source qualification does not complete broader #148 exploration.

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

The original correction's default `packet_aspects@11` declares both new scientific rules alongside unchanged
`annotated_site_source_support@1` and `ligand_instance_scope@1`. The exact native
site reader from `b991384` is frozen for `@10`; `@8`/`@9` and `@6`/`@7` keep their
previous readers. Canonical input IDs use the existing flat `inputs` reference shape as well as
the per-field grouping, so full/index terms retain the actual identity, sequence
and length sources even when admission is uncomputed. Generic historical terms
readers are unchanged. Full and index terms validate using the actual saved mapping,
without reinterpreting historical results as current classifications.

The subsequent [quaternary correction](quaternary_interpretation_scope.md) advances
the development default to `packet_aspects@12`. It retains this ligand-site
admission and changes the quaternary interpretation/dependency scope separately.

Oligomer family-site reading retains that original projection and its independent
scoped agreement rule. No stored Card field, schema version, migration, identifier,
shared MOLI wire format, Evidence or project conclusion is added. Unpublished
schema 0.3.14 and shape coverage of 1,938 paths remain unchanged. Broader isoform
mapping, original metadata losses, aggregate/instance/assembly reconciliation,
region/structure navigation and human/agent acceptance remain separate work under
#148, all required within the complete design before 0.15.0.

## Verification and retained work

The original SDK98 checkpoint at `680c6a1` passes all **7,179 local-original cases /
624.17 seconds**, twelve receptor workers, fatal SQLite/unraisable guards and
thirteen expected fixture warnings. Its exact-source CI15/15 and governance1/1
qualification is recorded above and was independently verified again on
2026-10-26 from complete capture member hashes, all job steps and thirteen test
summaries. This source qualification closes #163, not broad #148 exploration.

Sixty-four regression cases cover scope and packet support. Earlier selections
pass 224/66.49s, integration393/116.20s, support185/76.41s and literal naming89/13.95s.
Earlier interrupted/failed full runs and cancelled CI are diagnostic only: the
canonical-support omission and literal naming-test boundary were corrected before
the qualified checkpoint. Historical receipts and inputs remain unchanged.

Reproductions, frozen-body proof, original Cards/saved readings, source/input hashes
and logs remain under `recovered_work/ligand_overlap_scope_163_20261024/`, owner
#163/#148, review at the next exploration checkpoint or release. Previous #162
originals stay fixed. Scientific service queries and private pilot reads: zero.
