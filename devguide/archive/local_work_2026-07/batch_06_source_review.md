# Batch 06: final two historical source candidates (2026-10-06)

Review **FDA Orphan and EMA Orphan** together, the final two candidates after five
batches of five. Recover native EMA orphan-designation page declarations, exact
EU-number selection and complete-export access. FDA remains evaluating with the
native access/query/terms requirements below. Review completion and delivered
integration are separate outcomes.

| Candidate | Outcome | Useful material | Outstanding qualification |
| --- | --- | --- | --- |
| FDA Orphan | Reviewed; evaluating | Native orphan-product designation and independently stated approval/sponsor/condition/date context | Accessible original record/export, explicit query/date/approval/page scope and exact data terms |
| EMA Orphan | Scoped reader recovered | Independent designation pages, literal status/date/product context and declared full-export coverage | Additional product/approval identity resolution and separate designation-number scopes remain outside this reader |

Historical counts after this batch: **44 in use, 28 evaluating, 11 deferred,
3 retired, 1 out of scope and 0 not registered**. All 87 declarations have a current
registry comparison; no unreviewed candidates remain from this 27-candidate list.
Of the six batches, five scoped readers are recovered and **22** reviewed sources
still await integration. Other earlier evaluating/deferred decisions remain separate.
Preserve the original stash and all 87 unchanged exported files.

## Shared legacy defect: unsupported target, modality and intervention projection

The preserved `map_orphan_designations` consumed synthetic designations/products/
interventions, attached a caller UniProt accession as `target_ref` and defaulted
modality to `small_molecule`. It also generated generic treatment relationships
from names and substituted `orphan_designation` when a native status was missing.
The synthetic FDA fixture supplied `FDA:1` and an invented candidate name; it
qualified neither a native regulatory identity nor an original provider payload.
No `fetch_fda_orphan` or `fetch_ema_orphan` implementation exists in the retained
`protein_sources.py`; the old integration called delegated client methods.

Designation, refusal, withdrawal/expiry, marketing authorisation, indication and
product/target identity need their own source scope. A product name does not
identify a molecule or protein, and a designation does not imply treatment efficacy.
The useful historical requirements are retained without restoring those projections.

## FDA: query semantics qualified, native access pending

The [official database search page](https://www.accessdata.fda.gov/scripts/opdlisting/oopd/index.cfm)
and [official instructions](https://www.fda.gov/industry/designating-orphan-product-drugs-and-biological-products/instructions-searchable-designation-database)
describe product/sponsor/designation/date filters and condensed/detailed/spreadsheet
output. Multiple populated fields combine with AND. Dates refer to designation
for all-designation queries and to approval for only-approved-for-designation
queries. Defaults, date basis, approved-only scope, sorting, pagination and result
coverage must be recorded explicitly. The CF Grid Key is for FDA use; it is not a
qualified biological or chemical identity. Non-English search characters can
prevent results, so an empty search response alone is not a scientific negative.

The [FDA programme page](https://www.fda.gov/industry/medical-products-rare-diseases-and-conditions/designating-orphan-product-drugs-and-biological-products)
distinguishes designation from approval/licensing. Exact original indication,
sponsor, procedural dates, designation and approval fields must survive independently.
No sponsor portal submission, provider message, account or credential was used.

A single direct public database GET returned **HTTP 404** with a **420-byte**
`FDA Apology` HTML body that redirects to an excessive-requests apology page.
SHA-256: `1aeeafbfc6ff01d8c02199c303c80f5e8c8956751b5d93dd2d44bbeb137e5897`.
The result is a blocked acquisition, not no designations or database retirement.
Do not reinterpret it as an empty export or bypass the restriction. No further
native database request or export download was made. The exact first-request time
was not captured and remains unknown; no FDA fixture or SourceAssertion was added.

The official [openFDA licence](https://open.fda.gov/license/) concerns a separate
service. Its CC0 grant is not assigned to the OOPD search/export by association.
Qualify the specific export and contributing-material conditions when native access
is available. General government-work status is not a substitute for that source
contract or an identity join to a caller protein.

## EMA: native complete-export coverage and independent page identity

The [official JSON download documentation](https://www.ema.europa.eu/en/scientific-guidelines/download-website-data-json-data-format)
links a distinct orphan-designation file and documents its native metadata fields.
The raw export separates `meta` (declared total and file-generation timestamp) from
`data` (page occurrences). Source generation, designation/refusal, publication,
page update and actual retrieval times remain separate; no scientific release or
sequence revision is inferred from any date.

The unchanged [official orphan JSON export](https://www.ema.europa.eu/en/documents/report/medicines-output-orphan_designations-json-report_en.json)
contains **3310** rows, **2070548 bytes**, SHA-256
`8a83500533765c0d43a63b58581ef9c51d2df6f709fdc1d61c6f0ac74a80fd54`.
Native metadata declares total 3310 and generation **2026-10-06T18:05:23Z**.
Status literals comprise Positive 2205, Withdrawn 981, Expired 88 and Negative 36.
The number field contains 35 `-`, one `N/A` and one `EMA/OD/0000149115`, alongside
EU numbers. They remain native reference literals, not invented canonical IDs.
All 3310 rows retain the ten documented string fields; empty medicine names/product
references/date cells remain empty. Future finite fields survive unchanged.

Six valid EU numbers occur twice. For example, **EU/3/23/2858** has two
Elesclomol-copper pages with designation dates **22/06/2025** and **08/11/2023**,
and separate original page URLs (one includes a `-0` suffix). The reader does not
strip URL suffixes, overwrite dates, merge products or collapse equal EU numbers.
**EU/3/18/2020** retains daratumumab, intended use Treatment of AL amyloidosis,
status Withdrawn and empty medicine/product links. **EU/3/18/2115** retains the
source name Isembyld and product reference EMEA/H/C/005909 without transferring a
product's authorisation status or inferring molecular modality.

`get_designations(identifier, client=None)` uses an exact `EU/3/YY/number` query,
with digits retained literally. Names, protein IDs, multiple IDs, lowercase IDs,
placeholder values and alternate EMA-number queries are unsupported. Full native
meta/data shape, finite JSON, declared count matching received rows, UTC generation
time, required field types and independent official page URLs are validated before
local selection. One online GET receives the entire original export; no native
page, medicine export, linked document, chemical or biological search is fetched.

`map_designations` creates one SourceAssertion per matching original occurrence,
on `ema:orphan_page:<original URL>`, with the index/full-export hash and original
row value. Procedural status, substance and medicine labels, intended use, EU-number
literal, related product reference and native dates remain independent source context.
Repeated/conflicting rows are retained even when both page URLs are equal. There
is no protein/molecule identity merge, modality assignment, status ranking or
marketing-authorisation/efficacy inference. Not-listed differs from access failure
and does not state biological absence or lack of approval. No card intake is added.

Online, frozen fixture and source/kind/exact-query-bound JSON/gzip clients preserve
original response, original byte identity, optional SHA validation and actual/declared
retrieval time. The first fixture download's exact time was not recorded; it remains
`None` rather than borrowing the generation time. Shared archive replay preserves
the original response/time and hash without new network access. Supplied metadata
adds a local receipt and no remote acquisition credit. The qualified fixture is
unchanged; see [validation.md](validation.md) for code, live and backup receipts.

The [current official EMA legal notice](https://www.ema.europa.eu/en/about-us/about-website/legal-notice)
was checked with a successful direct public GET. EMA-owned information may be
reproduced/distributed with EMA acknowledgement in every copy, for commercial and
noncommercial use. Third-party content and logo rights are excluded. The registry
uses FREE-WITH-ACKNOWLEDGEMENT for this EMA-owned metadata; no CC licence, logo,
third-party report or approval dossier was imported. Retain EMA attribution,
the native data URL and actual access month/year. Underlying linked publications
and documents are not acquired and keep separate rights.
