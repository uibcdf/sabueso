# Follow-up 22: LIGYSIS initial displayed residue declarations

Recovered on **2026-10-08** in the existing editable Python 3.14.7 environment.
This advances the preserved LIGYSIS `binding_residues` capability through a
qualified native slice, rather than restoring `protein_priority_sources.py` and
its generic guessed payload shapes. The original stash, 87 exports, published
card and empty index remain preserved; the work remains uncommitted/unpushed.

## Native input and delivered behavior

The already preserved original public HsTIM page
`temp_data/ligysis/result__P60174__1.html` includes two site summaries and an
initial residue-panel table. Its **96597 bytes** and SHA-256
`3ccb0df740fe353b1f2a12f1362459e0296e6cfacda1736ca8a4e23479d6aacc` are unchanged.
Original acquisition date remains **2026-10-06**; its exact remote retrieval time
and source/result revisions remain unknown. This is reused original input, not a
newly observed source response or current service-health qualification.

The provider's [official help](https://www.compbio.dundee.ac.uk/ligysis/help),
checked on 2026-10-08, describes the residue panel's UPResNum/MSACol, AA/SS,
DS/MES/p and RSA columns. Native page tooltips independently state these labels.
Its [about page](https://www.compbio.dundee.ac.uk/ligysis/about) allows website
access and links software licensing; separate data redistribution permission
remains unestablished (`NOT-STATED`). No code/article grant is assigned to data.

Development `sabueso.mappings.ligysis.map_displayed_residues(envelope)` now:

- Validates the existing six-literal site/page contract and the additional native
  `cc`/`newChartData` declarations. Parsing is unique whole-line JSON under
  `ligysis_displayed_residue_literals@1`; no JavaScript is evaluated.
- Validates every column and row before returning annotations: declared column
  order, equal lengths, source binding membership, numbering/label types, finite
  numbers and supported score ranges. Changed/missing/duplicate literals, query,
  revision, cuts or column contracts fail explicitly.
- Preserves all **20** received initial rows, native UPResNum/MSACol, AA/SS,
  DS/MES/p, unknown declared columns, and repeated or contradictory occurrences.
  Row ordinals and original response hashes distinguish support; no row is silently
  selected or discarded.
- Represents RSA as a PyUnitWizard percent quantity while retaining the original
  scalar in native fields. Zero and native `"NaN"` remain different; missing RSA
  has no quantity. Scores and p-values get no Sabueso significance/function class.
- Returns standalone `annotations.ligysis_residue_records` assertions on the
  source-scoped displayed-table subject. Query, column order, row index/count,
  original page hash, receipt and parser accompany each occurrence.

The selected site is **not stated by these table literals**. Equal residue sets
do not identify it. The page's initial panel is not the complete collection of
binding residues or other site tables. An empty displayed table is only empty
display input, not a statement of segment-wide biological absence. Source sequence,
alignment numbering revision and result revision remain unknown. There is no
canonical location, reconstructed sequence, structure correspondence, coordinate
request, ligand identity, new calculation or automatic card enrichment.

The existing `get_result_page` and `map_sites` keep their site-only contract:
new detail declarations are required only when explicitly mapping the initial
residue panel. Acquisition observation still reports the received result page/site
count; the new mapper performs no acquisition. No card schema or persisted shape
changes. Original fixture bytes and NOTICE date/hash remain unchanged.

## Remaining useful material

This closes an additional native residue-reading slice within already adopted
LIGYSIS; source counts do not change. Its other-site residue tables, ligand
records, additional segments, full sequence and exact structural projection still
need their own original input and contracts. Other source/consumer requirements
are retained in [follow-up 21](followup_21_supplied_native_files.md).

Expanded queue: **6 scoped / 7 pending / 0 unreviewed**; original 27-list:
**21 scoped / 6 pending / 0 unreviewed**. Pending providers remain **ASD, GtoPdb,
COSMIC, ELM, BioCyc, OMIM and CASTp**. Historical catalog remains **65 in use /
7 evaluating / 11 deferred / 3 retired / 1 out of scope**. No restricted/failed
provider route is retried and no source account, agreement, upload or job is used.

## Qualification

Focused native detail and existing AlphaFill/LIGYSIS regression gate:
**126 passed in 3.82 seconds**, pytest-receptor with **12 workers**, including
**44 new cases**. These guard the native 20 rows, missing versus zero, units under
host context, contradictory occurrences, unknown columns, late malformed rows,
changed identity/column/literal contracts and unchanged site-only parsing.

Full offline checkpoint: **5272 passed in 166.04 seconds**, pytest-receptor with
**12 workers**, 10 expected failed/cut enrichment-fixture warnings. Ruff lint and
format (**921 files**), registry/generated metadata checks, strict Sphinx HTML
(`/tmp/sabueso-followup22-docs-build`), frozen-card shape/schema and diff gates pass.
All selected invocations passed; no failed run is counted as passing evidence.

Outside-checkout native reading in the verified editable environment yields all
20 independently supported rows with no scientific network request, current
canonical location or identified selected site. Receipt:
`/tmp/sabueso-followup22-native-receipt.json`; ignored local preview:
`recovered_work/current_preview/P60174.ligysis_displayed_residues.json`.
`/tmp/sabueso-followup22-integrity.json` verifies 87 original lengths/hashes,
91 accounted paths, original stash, empty index, frozen-card equality to HEAD,
unchanged LIGYSIS fixture and catalog counts. Gate receipt:
`/tmp/sabueso-followup22-gates.json`.

The owning [GitHub issue #129](https://github.com/uibcdf/sabueso/issues/129) records
the native scope, local fix and acceptance evidence under the repository's MOLI
issue-feedback requirement. It remains open until a repository code checkpoint;
this report does not claim a commit, push, remote CI or release. The official
help/about reads qualify documentation only, not a new scientific acquisition.
No separate environment, stage, source account/agreement/job or stash deletion.
