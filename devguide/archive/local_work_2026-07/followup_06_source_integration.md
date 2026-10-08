# Sixth five-source integration follow-up

Reviewed **HPO, MEROPS, TCDB, PDBTM and ELM** on 2026-10-07 in the existing editable
Python 3.14 development environment, on updated main `68dac8f`. TCDB's literal
native accession assignments are recovered; the other four retain concrete scope,
access and terms conditions. This is local uncommitted/unpublished work, not a
release. The original stash and all 87 exported files remain intact.

## TCDB: full native export and independent assignment occurrences

The [official download page](https://tcdb.org/download.php) identifies the public
[`acc2tcid.py` export](https://tcdb.org/cgi-bin/projectv/public/acc2tcid.py) as a
tab-delimited accession-to-TC-system mapping. It describes UniProt/RefSeq inputs,
without a per-row namespace column. The new
`sabueso.tools.db.tcdb.get_assignments(identifier, client=None)` reads this entire
native export in one GET and validates every row before literal selection.
Online, fixture and query-bound native TSV/gzip clients preserve original text,
raw-file SHA, original time and acquisition/archive observation. Generic TSV
header inference is not used: the first native row must survive.

`sabueso.mappings.tcdb.map_assignments` records standalone
`annotations.transporter_classifications` SourceAssertions on
`tcdb:accession:<literal>`. Each selected row retains native line/fields/text and
the complete export hash; duplicate pairs and conflicting/multiple assignments
keep distinct occurrence IDs. Case and version suffixes stay exact. The mapping
does not assign UniProt/RefSeq/protein identity, current sequence, taxonomy,
substrate, mechanism, transporter role, family function, experimental method or
MOLI Evidence. No family/sequence/publication acquisition, search, prediction,
automatic card enrichment or frozen-schema change occurs.

The unchanged export contains **24956** two-column rows, **13** blank accessions,
**128** nonempty accession literals with multiple occurrences and **two** duplicate pairs.
The earlier count of 129 repeated literals included the blank-accession bucket;
it does not mean 129 identified accessions.
There are **24954** five-component and **two** six-component TC codes. Blank
accessions remain auditable unbound rows in the whole envelope; they are not
filled from neighbours, assigned a namespace or silently dropped. The extra TC
component is neither truncated nor interpreted as an inferred hierarchy.

For example, exact `Q39253` selects native lines **3138** and **23892**, preserving
`2.A.19.2.3` and `1.A.1.9.2.3` independently. Versioned `ATE86338.1` selects
`1.M.1.3.37` and `1.M.1.4.1.1`; it is not reduced to a base accession. Native
lowercase `q15049` is distinct from `Q15049`. `OLS27678` has two identical pairs,
both retained. `P60174` is not listed in the received export: this is not biological
absence, a failed request or an empty export. Empty/error/header bodies, malformed
late rows and unsafe query text fail explicitly. All currently qualified native
rows must validate before any selected assertion is returned.

`truncated=False` describes the whole received export, without a provider total or
current-database completeness guarantee. Export/assignment/sequence revisions
are unstated; website/file dates are not substituted. Supplied-file metadata binds
source, kind, exact literal query, export scope and unknown version, but is still
a caller declaration rather than identity or permission proof. Optional SHA checks
use original bytes before decompression. Original CRLF text is not replaced by
normalized output; line occurrences support the native table independently of
biological numbering.

### Native bytes, rights and live receipt

- Unchanged `temp_data/tcdb/accession_assignments.tsv`: **486702 bytes**, SHA-256
  `c59e2b2c5293e0f33e75bcc0bf89e0eb6988be54fb7f2121935749bda3feef8a`.
  Original public probe is from 2026-10-06 with exact retrieval time unrecorded;
  fixture time remains `None`. A fresh public export on 2026-10-07 matches its bytes.
- Live qualification from `/tmp`, using this checkout's existing editable Python,
  at **2026-10-07T07:27:48+00:00** receives all **24956** rows and maps the two
  `Q39253` occurrences in **one GET**. Raw and decoded hashes match the fixture;
  decoded export identity is
  `sha256:c59e2b2c5293e0f33e75bcc0bf89e0eb6988be54fb7f2121935749bda3feef8a`.
  Archive replay preserves text, timestamp, download hash and all assertions with
  **zero network attempts**. Local receipt:
  `/tmp/sabueso-followup6-live-receipt.json`; ignored preview:
  `recovered_work/current_preview/Q39253.tcdb_assignments.json`.
- The [official FAQ](https://tcdb.org/faq.php), successfully read on 2026-10-07,
  declares CC BY-SA 3.0 and GFDL for website text. A separate export/database/input
  grant is not established and remains **NOT-STATED** in source terms. Credit
  TCDB/Saier Laboratory and preserve native literals/export URL. The factual
  original export stays local unreleased recovery; no blanket redistribution
  permission or input-resource licence is inferred. Resource bibliography is the
  official TCDB dataset URL, separate from row support.

## Other four candidates

| Candidate | Follow-up finding | Remaining integration condition |
| --- | --- | --- |
| HPO | Current repository LICENSE still points to `hpo.jax.org/app/license`, which returns HTTP 404. Current genes-to-phenotype documentation separates OMIM/HPO and Orphanet annotations and preserves original frequency kinds. | Qualify an exact released native asset and its annotation/contributor grant. Summary rows do not supply all disease/study/modifier support. Cohort fractions, percentage/frequency terms, contributor NOT and missing values remain distinct; no gene penetrance, ancestor or protein transfer. Older attribution/version/integrity terms are not substituted for current contributor rights. |
| MEROPS | A fresh availability-page GET again calls the complete database the Library under GNU Library GPL, linking generic `gnu.org/copyleft/lgpl.html` without a version. The earlier native accession table remains auditable, including its three displaced four-column rows. | Resolve applicable version/fixture obligations and explicit representation issues before delivering an export reader. Do not repair incomplete split accessions, discard malformed rows or shift taxonomy columns. Accession/family mapping is separate from native cleavage and unit/full-length sequence contracts. No SQL, sequence library, cleavage or search job is downloaded. |
| PDBTM | Official documents remain readable and describe a PDB-style 3x3 rotation plus separate fourth-column translation. The existing 1c3w XML still supplies its original nonprofit/no-modification/commercial-agreement notice. | Qualify raw/derived representation rights and physical units/axes before mapping or distributing transforms. Sequence and author endpoints, generated chains, biological matrices and membrane transform are independent. No transform execution, constant offset, canonical placement, coordinate acquisition or membrane prediction. |
| ELM | The exact linked academic agreement PDF again times out after 20 seconds; no agreement is accepted and no database export is requested. | Reach the applicable agreement and original native class/instance export; qualify investigated sequence/revision, instance bounds/status/publication support. Class regexes, described instances and pattern-match predictions are separate. No paper licence substitution, motif search, canonical projection or synthetic instance fixture. |

Primary references: [HPO genes-to-phenotype format](https://obophenotype.github.io/human-phenotype-ontology/annotations/genes_to_phenotype/),
[current HPO LICENSE](https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/LICENSE.md),
[older HPO terms](https://human-phenotype-ontology.github.io/license.html),
[MEROPS availability](https://www.ebi.ac.uk/merops/about/availability.shtml),
[PDBTM documents](https://pdbtm.unitmp.org/documents),
[native PDBTM XML](https://pdbtm.unitmp.org/api/v1/entry/1c3w.xml), and
[ELM academic agreement](https://elm.eu.org/media/Elm_academic_license.pdf).
Neither failed access nor an unspecified field establishes scientific absence or
resource retirement. No credentials, provider contact, uploads or new jobs occur.

Fresh public text probes remain outside package data: TCDB FAQ **21328 bytes**,
SHA-256 `6fa9d4b4b92dde2ed4190133c4912c3b2f0958325292106492a40086fe95bc0a`;
MEROPS availability **7930 bytes**, SHA-256
`caf8b691977e408f0814fd52dcc96c199aed93b7c9b12a7b0244d87e3e1ffacc`;
PDBTM documents **16953 bytes**, SHA-256
`9811e9e138d17c46f2778dd0e6fafbc9920f1bef3f7925b5b82587c69b7f6dbc`.
No ELM agreement bytes were received. Earlier native MEROPS/PDBTM probes remain
unchanged and unqualified for fixture publication.

## Qualification and remaining material

- Focused TCDB/snapshot/registry/acquisition/fixture-licensing selectors:
  **138 passed in 4.15 seconds**, pytest-receptor, **12 workers**. All **70** new
  TCDB guards pass in the full checkpoint: **4342 passed in 150.21 seconds**, with
  **10** existing exercised failure/cut warnings. No pytest or qualification gate
  fails in this slice.
- Ruff check/format (**861 files**), registry/generated page/terms/catalog,
  frozen card shape, FIELD_PATHS/schema and strict Sphinx pass. HTML receipt:
  `/tmp/sabueso-followup6-docs-build`. Final diff and original-byte receipts are in
  [validation.md](validation.md).
- Historical catalog: **51 in use, 21 evaluating, 11 deferred, 3 retired,
  1 out of scope, 0 not registered**. Twelve of the original 27 reviewed candidates
  have scoped recovered readers; **15** await integration. Those remaining are
  GtoPdb, MEROPS, COSMIC, HPO, ELM, BioCyc, OMIM, Interactome3D, PDBTM, MetalPDB,
  ECOD, 3did, CASTp, ProBiS and FDA Orphan. Scoped readers do not imply all source
  capabilities or card enrichment are delivered.
- Original stash `db04d97fef5a318c6d09f8312971558eafd9d14c`, all **87** exported
  bytes/hashes, empty index and unchanged frozen schema-0.3.12 card are verified.
  No stash drop, stage, commit or push. No separate environment/worktree or GitHub
  Actions run is needed; actual workflow qualification continues to use
  gh-run-receptor when required.
