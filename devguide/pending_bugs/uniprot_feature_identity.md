---
summary: Preserve complete native UniProt feature identity before normalization.
issue: uibcdf/sabueso#162
status: resolved
opened: 2026-10-24
closed: 2026-10-24
verification: tested
area: [knowledge-integrity, source-access, schema]
blocked_by: []
supersedes: []
---

# Native feature context and assertion identity

Two explicitly synthetic UniProt positional features with equal normalized values
but different native molecule labels received the same SourceAssertion ID. The
store retained only the last native context. A second confirmed case uses the same
molecule/positions/description but different native PubMed citation IDs. Keeping
only a normalized molecule label fixes the first example, not the second.
An additional explicit synthetic canonical case retains a compound location in
one source feature and an exact location in another with the same normalized value.
The actual pre-fix mapper loses the compound context and the question is `ready`;
the correction retains both originals and reports `unsupported`. This demonstrates
a context-admission consequence, not an affected live record or atom mapping.

## Correction and compatibility

Keep each complete unmodified native feature in `asserted_value`, and its Card
annotation in `normalized_value`. The existing source/record/field/asserted-value
ID algorithm now distinguishes native molecule, citation, compound-location and
otherwise unprojected feature contexts. Exact native duplicates retain one ID.
Equal normalized values may share all their exact source support without dropping
the original statements. The generic ID generator/store algorithm and mappings
outside native UniProt positional features are unchanged.

Fresh feature IDs change, including canonical features whose Card values otherwise
stay the same. Existing stored assertions, Cards, frozen schemas, saved capsules
and pins remain unchanged. Existing field, residue and annotation readers use the
normalized-value contract, with their historical asserted-value fallback. Direct
source inspection now distinguishes the original native statement from its Card
representation. Original metadata `uniprot_feature` remains too, preserving
existing consumers and historical structural-input paths.

The native ligand-site reader also matches through the existing normalized-value
contract and keeps each matching original statement with its own source/ECO codes,
under `annotated_site_source_support@1`. Packet mapping `packet_aspects@10` declares
that new support rule for full/index receiving. Original @8/@9 site projections
are frozen from `f206474`; @6/@7 keep their preceding frozen projection. Old packet
values/terms are never reinterpreted by the new source-support reader. The overlap
classification rule at this checkpoint remains @2; the separate
[coordinate-scope correction](ligand_overlap_coordinate_scope.md) advances it to @3.

The normalized annotation also retains a stated `molecule` literal, including an
empty/unidentified string. Missing/null source labels add no such member. A label
does not establish isoform identity or map coordinates; foreign/unidentified axes
remain unplaced. Malformed non-string labels fail explicitly. See the
[official UniProt manual](https://web.expasy.org/docs/userman.html) for source
canonical/isoform location semantics; no new molecular service queries are used.

Optional additions remain in unpublished 0.3.14. Migration reports absent native/
normalized feature context through `source_assertion_store[].normalized_value`,
alongside the earlier missing-native-input gap. It never reconstructs dropped
contexts from the last surviving metadata. Refresh records a new acquisition and
retains the original pin. Shape coverage includes explicitly synthetic optional
molecule labels for all 17 mapped fields; the shape has 1,938 paths.

## Verification and remaining work

Final source `b991384` / SDK `0.14.0+95.gb991384` passes all **7,115 local-original
cases / 659.24 seconds**, exact-SHA CI **15/15** and governance **1/1**. Nine OS lanes
pass 5,562 public cases each and four Ackredit lanes pass 1,431 cases each. Full
receptor captures and member hashes are verified; #162 is
[closed within this scope](https://github.com/uibcdf/sabueso/issues/162#issuecomment-6391409715).
The receipt is `recovered_work/native_feature_context_162_20261024/checkpoint.json`.
Earlier exploratory failures below are superseded by that final checkpoint.

Forty new regressions cover all 19 mapped feature types, distinct molecule
labels, native citation/compound/unprojected contexts with equal normalized values,
exact duplicate IDs, order/retrieval stability, malformed labels, exact item support,
persistence, migration/refresh and an independent inert saved reader. A canonical
compound context cannot be hidden by a matching normalized exact feature, in either
input order. The owning gate passes 251 cases with one explicit local-original
skip, twelve pytest-receptor workers and fatal runtime/SQLite/unraisable guards.
The subsequent full gate exposed an unadapted ligand-site reader and stale test
representations (7,106 passed / six failures). The reader now uses normalized
values and retains each original matching statement with its own source/codes;
the additional regression covers that integration. Two additional packet cases
retain the old @8/@9 singular support projection and verify saved terms with the
current reader forbidden. Corrected full-suite and
publication qualification are recorded separately in #162.
The integration gate passes 441 cases / 83.39 seconds, followed by 260 final packet/
history receiving cases / 99.92 seconds, twelve receptor workers with local originals
and fatal runtime/SQLite/unraisable guards. Ruff, shape/schema alignment, fixture
delivery, source registry, dependency preflight and governance pass. The 37 public
guide blocks execute offline; Markdown/snippet syntax and Python 3.11 grammar pass,
and Sphinx builds with warnings fatal. Source and history qualification stay separate
from researcher usefulness or release-artifact acceptance.

Actual pre-fix synthetic Card/exploration inputs and hashes, failure reproductions
and gate logs are retained under `recovered_work/native_feature_context_162_20261024/`,
owned by #162/#148 for review at the next exploration checkpoint or release.
The separate confirmed [overlap-axis defect #163](https://github.com/uibcdf/sabueso/issues/163)
was confirmed under @2. Its [separate correction](ligand_overlap_coordinate_scope.md)
qualifies coordinate scope independently before broad aggregate/assembly acceptance;
this identity fix alone does not establish that scope.
Historical lost associations, broad isoform/other-source mappings, generic
cross-version metadata retention and full researcher acceptance are not claimed
solved. All ongoing work targets 0.15.0; candidate preparation remains paused.
