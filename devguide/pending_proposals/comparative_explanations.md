---
issue: uibcdf/sabueso#91
status: active
---

# Pinned comparative explanation slice

Development adds three Card readers: `explain_sequence_differences(other)`,
`explain_variant_tissue_usage(threshold=0.1)` and
`explain_isoform_tissue_usage(threshold=0.1)`. Their respective envelope rules are
`sequence_differences_explanation@1`, `variant_tissue_usage_explanation@1` and
`isoform_tissue_usage_explanation@1`. They retain the existing ordinary views under
`equal_length_positions@1`, `pext_at_variant@1`, `isoform_exon_usage@2` and
`gtex_tissue_key@1` without changing stored cards or published schemas.

Each envelope retains exact card pins, selected fields and their assertions,
alternatives/conflicts/selection context, original values, source labels and
parameters. Tissue collectors record the actual first matching variant region,
CDS subtraction inputs, weighted intersections and tissue-specificity inclusion
or exclusion. Row support distinguishes an exact asserted value from a whole
selected-list assertion; finer mapping lineage is never reconstructed. Tissue
joins preserve original term records, other colliding keys and the historical
last-match choice; a shared ontology term never merges tissues.

Missing sequences, unequal lengths, unplaced genomic variants, outside-region
variants, missing transcripts/exons/terms and incomplete isoform support retain
their original reasons. `partial` denotes recorded support or scope gaps,
including limits of the comparison; it does not claim source completeness or
pathogenicity. Equal positions do not establish residue correspondence or
identity. Expression cutoffs are finite dimensionless numbers in [0, 1].

The gnomAD dataset/pext and requested GTEx labels remain separate from independently
verified native release identity. Enrichment reports and other source relationships
are context, not reconstructed per-request or per-assertion membership. Comparative
operation observation is explicitly `not_observed`; no original execution credit
or bibliography is manufactured from scientific payloads (#108).

The standalone public journey `examples/user_journeys/comparative_support.py`
uses P52270/Q4DV43 and P60174 frozen public fixtures already declared in
`temp_data/NOTICE.md`. Independent readers verify exact saved fields, assertions,
relationships, input locators, original rules/parameters and role bindings without
fixtures or source access. Reacquisition changes fixture-read times and current
heads, while original envelopes and pins survive. Regression readers disable
resolution, comparative derivation/explanation, assertion explanation and fresh
Ackredit registration, and change the reader version deliberately. Modified or
misbound inputs are refused even when the report digest is updated.
The manifest is a local example format, not a shared MOLI provenance contract.

Historical view limits require a versioned correction in
[#138](https://github.com/uibcdf/sabueso/issues/138): assembly/chromosome confirmation,
overlapping pext coverage and per-tissue missingness. New explanations expose
mixed-axis and duplicate-count gaps and compute uncovered bases from the union
of original recorded intersections, keeping historical denominators visible.
This slice is outside published 0.14.0. Installed qualification and human
scientific usefulness review remain open; the broader #91/#108/#112 scopes are
not closed by this public fixture journey.
