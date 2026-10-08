# Fourteenth five-source integration follow-up

Reviewed **ProBiS, GtoPdb, COSMIC, ELM and CASTpFold** on 2026-10-07 in the
existing editable Python 3.14 environment. Recover a narrower native ProBiS
reference-chain catalog reader; the historical alignment/binding scope and the
other four providers remain unqualified. Original stash and exports are preserved;
recovery remains local, uncommitted and unpushed.

## ProBiS: a newly qualified native catalog artifact

The current official [database page](http://probis.cmm.ki.si/?what=database)
links a [nonredundant PDB chain catalog](http://probis.cmm.ki.si/download/nrpdb-2015-07-31.txt).
The exact public HTTP route responds 200 with **1003440 bytes**, **42270**
headerless five-column rows, SHA-256
`2a4f3dd8f3f186f482541c51f177899cbf3c174cc21838dd6a9b185646c12c0a`.
The current page is preserved at `/tmp/sabueso-followup14-probis-database.html`;
original artifact probe at `/tmp/sabueso-followup14-probis-nrpdb-2015-07-31.txt`.
The web reader upgrades these routes to HTTPS and cannot receive the native
artifact. Verified curl and the deployed reader use the exact provider-linked
HTTP URL, without altered TLS verification, credentials or a blocked-route bypass.
This is a distinct static artifact, not restored access to earlier failed REST
representative/alignment requests; those requests are not repeated.

The entire unchanged export is in `temp_data/probis/nrpdb-2015-07-31.txt`.
Its filename date is only an artifact label: dataset, PDB and sequence revisions
remain unknown, and `version=None`. The first probe's exact retrieval time is
unrecorded; fixture time stays `None`. Every row validates before selection.

Columns 3/4 contain native lowercase PDB/case-sensitive chain literals. Columns
1/2/5 remain original opaque strings, including column 2 padding. Their meanings
are unqualified: no index/cluster-size/rank/weight/probability/score/quantity is
assigned. Native column 1 gaps and repeated selectors survive unchanged.
The first row is data (`0`, padded `1`, `12as`, `A`, `1.0`), not a header.

Exact selection of `5a2q.h` returns **three** independent occurrences at native
lines **25465, 25466 and 42034**, including different original column values.
`2ww9.L` returns **five** occurrences. `5a2q.H` is not listed. The old documented
alignment example `1ytb.B` is not listed although `1ytb.A` is. No case repair,
chain merge, representative-query relation or protein identity follows from this
catalog; not listed is neither biological absence nor a negative alignment result.
The dated received artifact does not establish current full-provider coverage.

### Historical material and current delivery

The original `map_translational_source` in
`recovered_work/legacy_2026-07/sabueso/mappings/protein_translational_sources.py`
assigned generic `binding_sites`/`sites`/`results` rows to `sites.similar_binding_sites`
and supplied an accession as a fallback protein reference. Preserve its useful
precomputed-source intent; do not reuse that synthetic shape or implicit protein
identity for the native chain catalog.

Delivered:

- `sabueso.tools.db.probis.get_chain_catalog`, `OnlineProBiSClient`,
  `FixtureProBiSClient` and query-bound `SnapshotProBiSClient` for native TSV/gzip,
  original-byte SHA and caller-declared time/terms.
- `sabueso.mappings.probis.map_chain_catalog`, emitting standalone
  `annotations.reference_chain_listing` assertions on
  `probis:catalog_chain:<PDB.chain>`. Each occurrence retains original five strings,
  row/line, complete export hash and scope; IDs use document hash plus native line.
- Complete raw export and genuine retrieval support in acquisition/archive,
  with failure/malformed/unavailable distinct from validated not-listed results.

No automatic card enrichment or frozen-schema change is added. Historical ligand/
function transfer, local alignment, representative-query mapping, scores, protein
identity, coordinate acquisition, uploads or computation jobs remain outside scope.

### Terms and genuine live receipt

The native database/catalog route supplies no separately qualified data grant.
Terms remain **NOT-STATED**, with unknown automated use/sharing and attribution
to ProBiS-Database, the native artifact URL and original row/hash support.
Software/article licences and underlying input rights are independent.
The unchanged original factual artifact stays local unreleased qualification;
no public fixture or derivative-collection redistribution grant is claimed.

The deployed reader was checked from `/tmp`, verifying Sabueso import path and
editable installation metadata. At **2026-10-07T20:36:55+00:00**, one native
GET matched all original fixture bytes, retained **42270 rows** and produced
**three** `5a2q.h` assertions. Archive replay retained original text/time/hash and
identical assertions with **zero** network attempts. Receipts:
`/tmp/sabueso-followup14-live-receipt.json`,
`/tmp/sabueso-followup14-live.sqlite`; ignored preview
`recovered_work/current_preview/5a2q.h.probis_chain_catalog.json`.

## Other four sources: concrete pending conditions

| Source | Current review and remaining requirement |
| --- | --- |
| GtoPdb | The actual public download route redirects to login; official services require registered API-key access, with commercial fees explicit. Older indexed download/no-auth descriptions do not establish current access. Require authorized native target/subunit/ligand identities and original unit-qualified measurements; database ODbL and content CC BY-SA stay separate. No direct DATA-path guesses, account, credentials or bypass. |
| COSMIC | Current terms condition use/download on applicable registration/licence acceptance, restrict redistribution and require official download functions for bulk access. Human Cancer signatures v3.6 and Experimental v1.0 are publicly described without registration, which does not qualify use/download/public-sharing rights or the historical core-variant module. No native dataset or agreement acceptance acquired. Require authorized module/release/assembly/transcript/sample/count/support and exact applicable rights. |
| ELM | Current downloads and one exact academic-agreement browser acquisition time out; no agreement bytes or acceptance are obtained. Indexed primary motif descriptions retain noncommercial agreement conditions. Require native motif class/regex versus validated instance, original sequence/revision/bounds/status/support and applicable grant. No motif computation or canonical projection. |
| CASTpFold | Current tutorial separates representative clusters, exact identity, Foldseek similarity and DeepFRI predictions. SA area/volume units are stated separately from SE. Preserved frontend still exposes the same basic/measure example routes; earlier HTML-shell results are not repeated without a changed native-data condition. Require native existing pocket results and structure/model/assembly/sequence/parameters plus applicable grant. No coordinates, uploads or jobs. |

Primary references: [GtoPdb downloads](https://www.guidetopharmacology.org/download.jsp),
[GtoPdb services](https://www.guidetopharmacology.org/webServices.jsp),
[COSMIC terms](https://www.cosmickb.org/terms/),
[signature downloads](https://cancer.sanger.ac.uk/signatures/downloads/),
[ELM downloads](https://elm.eu.org/downloads.html),
[ELM academic agreement](https://elm.eu.org/media/Elm_academic_license.pdf), and
[CASTpFold tutorial](https://cfold.bme.uic.edu/castpfold/infos/allabout/tutorial.html).
Inaccessible agreement content is not represented as reviewed or accepted.

## Qualification and remaining original candidates

Focused ProBiS/registry qualification passes **87 tests in 8.34 seconds**,
including **70** new ProBiS cases, through pytest-receptor with **12 workers**.
An initial selection used an incorrect registry test path and collected no tests;
the corrected selection above passed. The full offline checkpoint passes
**4821 tests in 145.48 seconds**, with ten existing failed/cut enrichment warnings,
through pytest-receptor with **12 workers**. Ruff lint and format (**891 files**),
registry/page/terms/catalog, frozen card shape, schema/field alignment, strict Sphinx
HTML (`/tmp/sabueso-followup14-docs-build`) and `git diff --check` pass.

`/tmp/sabueso-followup14-integrity.json` verifies all **87** exported originals
against their original byte lengths/SHA-256, **91** accounted paths, original stash
`db04d97fef5a318c6d09f8312971558eafd9d14c`, empty index and frozen-card bytes equal
to HEAD (SHA-256
`bfd5007365209b19e45b59c064338c40afcb65ae04834198de393484fdd24b2f`).
The native ProBiS fixture equals the original probe byte for byte. Gate receipts:
`/tmp/sabueso-followup14-gates.json`.

Historical counts among the **87** original source declarations: **58 in use,
14 evaluating, 11 deferred, 3 retired, 1 out of scope, 0 unregistered**.
**19/27** reviewed original candidates have scoped readers; **8** remain pending:
GtoPdb, COSMIC, ELM, BioCyc, OMIM, Interactome3D, CASTpFold and FDA Orphan.
A scoped ProBiS catalog reader does not qualify the original broader alignment/
binding capability. Counts concern this historical list, not the entire backlog.

Original scientific artifacts are preserved separately from licensed fixtures and
current cards. The original stash and 87-file export remain intact; no stash
application/deletion, stage, commit, push, account action, separate development
environment, protected-card edit or cross-component change is made.
