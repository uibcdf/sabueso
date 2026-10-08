# Fifteenth five-source integration follow-up

Reviewed **Interactome3D, BioCyc, OMIM, ELM and FDA Orphan** on 2026-10-07 in
the existing editable Python 3.14 environment. Recover a native archived human
representative protein metadata reader. Original interaction-pair/API/complete
dataset capabilities and the other four sources remain separately unqualified.
Recovery stays local, uncommitted and unpushed; original stash/exports are preserved.

## Interactome3D: newly reachable archived metadata

The official [download page](https://interactome3d.irbbarcelona.org/download.php)
links archive `2024_12`, whose human
[representative directory](https://interactome3d.irbbarcelona.org/downloadset.php?path=representative&queryid=human&release=2024_12)
is newly received by verified curl: **HTTP 200**, **28401 bytes**, preserved at
`/tmp/sabueso-followup15-interactome3d-2024_12-representative.html`.
The web reader has a cache miss for this directory. The newly linked
[proteins.dat](https://interactome3d.irbbarcelona.org/data/previous_releases/2024_12/human/representative/proteins.dat)
also returns **HTTP 200**, **1618274 bytes**, **18000** fourteen-column records,
SHA-256 `bb1671bedacab71e528a18c1d7f662046fe61d299b70da791f1b61325098d83d`.
The first probe is `/tmp/sabueso-followup15-interactome3d-proteins.dat`; the entire
unchanged file is `temp_data/interactome3d/human__2024_12__representative__proteins.dat`.

This is a concrete changed transport/data condition: previously failed current
complete-file/API requests are not repeated or silently reclassified. Use the
exact provider-linked archived route without TLS bypass, credentials, alternate
hosts, jobs or coordinate tarballs. The selected archive label is explicit query
scope, not an independently stated native-export/PDB/sequence revision. Those
revisions stay unknown (`version=None`). First exact probe time is unrecorded;
fixture time remains `None`.

### Native records, percentages and independent occurrences

The original header states UNIPROT_AC, RANK_MAJOR, RANK_MINOR, TYPE, PDB_ID,
CHAIN, SEQ_IDENT, COVERAGE, SEQ_BEGIN, SEQ_END, GA431, MPQS, ZDOPE and FILENAME.
All rows validate before exact native accession selection. The received artifact
contains **10636 Structure** and **7364 Model** occurrences, including **251**
whitespace-only chain labels. Preserve those labels and native case; do not infer
a missing chain from a filename. Duplicate occurrences retain separate IDs using
full-export hash and native line. Filenames are pointers and are not downloaded.

`P60174` selects one native Structure, `1wyi`/A, rank pair `1`/`0`, sequence
endpoints `2`/`249`, identity `100.0` and coverage `99.6`. `Q8WZ42` selects
**thirty** native occurrences: a representative dataset can retain multiple
partial structures/models. Not listed in the received representative artifact
does not establish biological absence or no result in a complete/current dataset.

The independently received native [help](https://interactome3d.irbbarcelona.org/help.php)
is **61920 bytes**, SHA-256
`e65af6994408c1f72a37b9ee9b4d64e17fd3fd103c006582cc2654fcd8224061`.
It explicitly qualifies SEQ_IDENT and COVERAGE as percentages; they become
PyUnitWizard `{value, unit}` nodes with unit `percent`, keeping original strings
in native row support. Reported endpoints remain strings on the provider's axis:
they are not an exact full-chain correspondence or current canonical mapping.
PDB IDs can be model templates; they do not assign the model an experimental method.
GA431/MPQS/ZDOPE remain opaque original literals, including `-1.000`, without
probability, threshold, missing-value or unit guesses.

### Useful historical intent and bounded delivery

The preserved `protein_sources.py::fetch_interactome3d` requested both protein
and pair operations with `queryProt`, contrary to the documented distinct
contracts, and its XML helper discarded root context. The old structural mapper
expected synthetic lower-case fields and supplied caller/fallback identity.
Recover the useful independent structure/model, rank, template and coverage
requirements with the actual protein metadata table; do not import the old
request implementation or invent an interaction-pair response.

Delivered:

- `sabueso.tools.db.interactome3d.get_protein_structures`, online/fixture clients
  and source/query-bound native TSV/gzip snapshots with optional byte SHA/time/terms.
  Existing `identifier` and `release` digesters plus backend checks enforce exact
  accession and sole qualified `2024_12`/human/representative/proteins.dat scope.
- `sabueso.mappings.interactome3d.map_protein_structures`, producing standalone
  `annotations.structure_model_occurrences` on
  `interactome3d:protein:<native accession>`. Native row/line/export hash and
  independent occurrences support every value, with explicit scope and percent basis.
- Full original response/hash/time in acquisition/archive and zero-network replay.
  Missing/failed/malformed acquisition differs from validated not-listed results.

No frozen-card field, automatic enrichment, similarity identity merge, residue
projection, interaction-pair/API access, complete export, coordinate acquisition,
modelling or alignment job is added.

### Terms and deployment receipt

The official [provider description](https://interactome3d.irbbarcelona.org/about.php)
identifies IRB Barcelona's Structural Bioinformatics and Network Biology Group
without qualifying a separate metadata reuse grant. Terms remain **NOT-STATED**,
with source attribution, unknown automated use/sharing and independent input rights.
Software/articles are not assigned as data licences. Original factual qualification
stays local unreleased; no public fixture/derivative redistribution grant is claimed.

The deployed reader was verified from `/tmp`, checking editable metadata and
Sabueso import path. At **2026-10-07T20:51:35+00:00**, **one** native GET matched
the complete original fixture, retained **18000** rows and returned one P60174
assertion. Archive replay preserved text/time/hash and identical percent-valued
assertions with **zero** network attempts. Receipts:
`/tmp/sabueso-followup15-live-receipt.json`, `/tmp/sabueso-followup15-live.sqlite`;
ignored preview `recovered_work/current_preview/P60174.interactome3d_protein_structures.json`.

## Other four candidates

| Source | Useful historical requirement and remaining qualification |
| --- | --- |
| BioCyc | Native organism/release/frame and gene/protein/reaction/pathway relations precede membership/direction. Current flat-file request still requires agreement/manual review before emailed download instructions. Open-versus-Limited Database rights and notification obligations stay separate from session/subscription conditions. No form, agreement, authenticated data or provider message. |
| OMIM | Independent MIM gene/locus, phenotype, inheritance/mapping key, allelic-variant and narrative scope remain useful. Current NCBI description points to the provider and API without native entries or a data grant. Restricted routes are not retried; require authorized current native release/terms. HPO pointers are neither direct OMIM records nor licences. |
| ELM | Native motif class/regex and validated instance, sequence/revision/bounds/status/context/support remain separate. Current downloads browser acquisition times out; no native artifact or agreement accepted. Historical synthetic motifs and universal curated class do not qualify a native reader. No motif computation or canonical projection. |
| FDA Orphan | Original designation/approval/indication and independent product identity remain useful. Current canonical instructions preserve AND filters and designation versus orphan-indication approval date basis. No new search/export or blocked database retry. Require authorized unblocked native artifact plus OOPD/input terms; no protein-target, modality or intervention-status defaults, and no openFDA licence substitution. |

Primary references: [BioCyc native terms/request](https://bioinformatics.ai.sri.com/ptools/licensing/all-reg.shtml),
[NCBI OMIM description](https://www.ncbi.nlm.nih.gov/omim/),
[ELM downloads](https://elm.eu.org/downloads.html), and
[FDA canonical instructions](https://www.fda.gov/industry/designating-orphan-product-drugs-and-biological-products/instructions-searchable-designation-database).
Descriptions/inaccessible agreements are not native data or accepted permissions.

## Qualification and remaining original candidates

Focused Interactome3D/registry qualification: **102 passed in 9.93 seconds**,
including **85** new cases, through pytest-receptor with **12 workers**. An initial
mapper test incorrectly expected another valid accession selector on a full export
to fail; it was corrected to test an unsupported complete-set relabel instead.
Client/snapshot request binding and every received row remain independently checked.
The full offline checkpoint passes **4906 tests in 124.54 seconds**, through
pytest-receptor with **12 workers**, with ten existing failed/cut enrichment
warnings. Ruff lint and format (**895 files**), source registry/page/terms/catalog,
frozen card shape, schema/FIELD_PATHS alignment, strict Sphinx HTML build and
`git diff --check` pass. An example import wrap was formatted; format and strict
Sphinx were checked again after that cosmetic adjustment.

`/tmp/sabueso-followup15-integrity.json` verifies all **87** original exports
against their original byte lengths/SHA-256, **91** accounted paths, stash
`db04d97fef5a318c6d09f8312971558eafd9d14c`, empty index and frozen-card bytes
identical to HEAD (SHA-256
`bfd5007365209b19e45b59c064338c40afcb65ae04834198de393484fdd24b2f`).
The native Interactome3D fixture equals the original public probe byte for byte.
Receipts: `/tmp/sabueso-followup15-gates.json`; documentation output:
`/tmp/sabueso-followup15-docs-build`.

Historical counts among the **87** original source declarations: **59 in use,
13 evaluating, 11 deferred, 3 retired, 1 out of scope, 0 unregistered**.
**20/27** reviewed original candidates have scoped readers; **7** remain pending:
GtoPdb, COSMIC, ELM, BioCyc, OMIM, CASTpFold and FDA Orphan. Scoped delivered
capabilities do not qualify every original broader requirement or the whole backlog.

The original stash and 87-file export remain preserved separately from licensed
fixtures/current cards. No stash application/deletion, stage, commit, push, separate
environment/worktree, account action, provider message or protected-card edit.
