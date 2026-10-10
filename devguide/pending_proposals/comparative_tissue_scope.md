# Versioned comparative tissue scope and coverage

Owner: [#138](https://github.com/uibcdf/sabueso/issues/138), within #91/#102 and
accepted quality plan #112. Development source, outside published 0.14.0.

## Implemented scientific boundary

Card views default to `pext_at_variant@2` and `isoform_exon_usage@3`;
variant/isoform explanation envelopes use `@2`. Keyword-only `usage_rule` selects
explicit historical `pext_at_variant@1` or `isoform_exon_usage@2`, including
original explanation `@1`. Existing algorithms, frozen schemas and saved reports
are unchanged. Independent readers retain the original rule and producer version.

A variant uses the first genomic base of its source identifier, never its protein
location. Its assembly must be explicitly recorded or supplied by coordinate
context on a matching selected SourceAssertion; old source-version labels do not
supply missing context. Only pext intervals on exactly the same assembly/chromosome
can contribute. Missing, incompatible and invalid input scopes remain explicit.
No liftover, sequence alignment or identity inference occurs.

Isoform subtraction requires a single consistent explicit CDS axis across usable
inputs, and exact source-stated Ensembl transcript-to-isoform links. Base identifiers
match under Ensembl's version syntax; explicitly stated versions must agree, and
an unstated version cannot confirm a stated one. Rejected CDS rows stay inspectable.
An isoform with unsupported rows has incomplete CDS support; a declared transcript
without an accepted CDS row makes own/variable-base completeness false. Known bases
remain a comparison among known inputs, not a claim of unique biological expression.
Different CDS axes prevent own/variable-base derivation rather than combining
integer coordinates. Empty/unasked inputs do not prove external absence.

## Coverage policy

Closed own/variable intervals are partitioned at pext boundaries. Each base counts
once. For each tissue, every covering record must state the same valid finite pext
in [0, 1]. Agreeing duplicates are counted once with all original inputs retained;
disagreement is `conflicting`, and a null, omitted, invalid or absent tissue value
is `missing`. A disagreement among stated values remains conflict even if another
input is missing. No first/last-record preference or averaging of conflict occurs.

`coverage_by_tissue` reports resolved, missing and conflicting bases and completeness.
`by_tissue` is a length-weighted mean over that tissue's resolved bases only, or
`None` with none resolved. Missing bases never become zero. Top/threshold lists
use resolved means and must be read with coverage. `bases_with_pext` is union
region coverage, independently of measured tissue values; uncovered bases and
`overlapping_bases` are explicit. A single unambiguous variant region preserves
its stated mean; overlapping regions have no silently selected source mean.

Explanations retain exact partition boundaries, every contributing/excluded input
locator and SourceAssertion, tissue decisions, CDS/transcript inputs, source text
inclusion/exclusion and stored field alternatives/conflicts. These are scientific
support, not reconstructed acquisition observation, bibliography or Evidence.

## Additive storage and independent readers

Unpublished schema 0.3.14 adds only optional gnomAD variant assertion metadata
`source_metadata.coordinate_scope`. `gnomad_query_coordinates@1` records GRCh38
as the requested reference genome under the current `gnomad_r4` client/mapping
contract, with `native_assembly_echo="not_stated"`. It does not assert a returned
native assembly or verified source release. Asserted biological values and all
published 0.3.13 paths remain unchanged; five metadata paths are added.

Migration records the missing context for existing gnomAD variant assertions and
never fills it from an old dataset label. A refresh restores the recorded gnomAD
variant/pext options and variant limit to acquire it; empty/unrelated
cards have no applicable gap. Reading or explaining an old pin never substitutes
context from a newer card. New public example format
`sabueso.comparative_support_example@2` uses the corrected rules; `produce --legacy`
retains historical `@1`. Both formats have inert readers and format-preserving
reacquisition without source access, fresh derivation or new credit in readers.

## Acceptance and remaining limits

Public regressions cover wrong/missing axes, transcript links/versions, incomplete
CDS, overlapping agreement/conflict, duplicate tissue rows, null/absent/invalid
values, zero expression, per-tissue denominators, uncovered bases, permutations,
variable runs, exact support, old/new pins, migration/refresh and both independent
report generations. Existing native public fixtures preserve values on complete
compatible inputs. A frozen response is not current live availability.

This correction does not independently verify a source's coordinates or native
release. #108 comparative source-operation/bibliography observation, a future
installed-artifact checkpoint and human scientific usefulness acceptance remain
separate. Broader declared-enricher refresh routing is tracked in
[#139](https://github.com/uibcdf/sabueso/issues/139); this slice corrects only the
recorded gnomAD variant/pext options needed for the coordinate-context refresh.
Source qualification is recorded after applicable gates and exact-SHA CI.


## Local source qualification (2026-10-10)

Python 3.14 / pytest-receptor with twelve workers passes 187 selected cases and
5,819 full local-original offline cases (173.34 seconds, ten expected simulated
source-failure/truncation warnings). SQLite/unraisable guards are fatal in the
full checkpoint. Ruff, fixture delivery, current recorded shape/schema, dependency
preflight, governance, maintained relative links and warning-fatal Sphinx pass.
Frozen 0.3.13 schema/shape/card files have no changes; 0.3.14 adds exactly five
metadata paths and removes none. Independent historical archived-envelope reading
and versioned native-answer replay pass without new provider queries; their
payloads/results remain private. Exact-commit CI and current editable metadata
confirmation are recorded in the completed source receipt.
