# gnomAD operation observation (#108)

Owner: [uibcdf/sabueso#108](https://github.com/uibcdf/sabueso/issues/108), within
the #112 quality plan. The prerequisite correction is owned by
[uibcdf/sabueso#141](https://github.com/uibcdf/sabueso/issues/141).

Development observes built-in online/fixture `variants`, `transcript_variants`,
`consequences` and `pext` as `gnomad_variants`, `gnomad_transcript_variants`,
`gnomad_consequences` and `gnomad_pext`. All belong to scientific source `gnomAD`;
public `get_variants`, `get_transcript_variants` and `get_pext` attach detached
traces, including failed access. Declared observation coverage becomes 38 source
families. Arbitrary derived operations and custom clients remain explicit gaps.

## Native scope and interpretation

`gnomad_operation_observation@1` retains decoded response identities, request
body/wire hashes and original times. Each native page records its actual GraphQL
query and variables or requested consequence aliases. Gene/transcript metadata
retain source-stated transcript identifiers/versions; consequence bindings retain
queried versus natively stated variant identifiers and transcript versions.
These do not become a service release or an inferred entity correspondence.

`gnomad_r4` is a requested GraphQL dataset for variant/consequence queries.
`GRCh38` is an explicit argument of gene/transcript/pext queries, but not the
consequence-alias query. The pext query has no dataset argument. The client label
`gnomad_r4 pext (GTEx v10)` is a description, not a native dataset or GTEx revision.
Native release is unknown for all four operations; fixture version labels retain
their declared scope and never establish a live release. No sequence/genomic
correspondence is invented from coordinates, a shared protein change or a label.

Received variant bindings, transcript-consequence rows, returned client items and
card-selected/placed assertions are distinguished. Fixture consequence access reads
a saved mapping, then returns its requested subset: its page count describes the
read mapping and its operation count the returned subset. The original enricher
still records transcript merge, protein placement, selected count and limit in
card quality. A successful response or frozen subset does not prove global
completeness or biological absence.

Consequence iterables/generators are materialized once. Native aliases explicitly
answered `null` remain separate from a variant with an empty consequence list.
An omitted alias, malformed consumed container or GraphQL error with a partial
record fails; completed earlier batches remain partial access, including a
completed batch with zero bindings. No partial scientific mapping is returned.
The existing client interpretation of explicit not-found messages remains labeled
as that policy. Null entities, null pext and explicitly empty pext regions retain
the existing `RecordNotFoundError` with the received response and precise absence
basis; this establishes only the actual query's scope.

Missing local files are unavailable, including `consequences.json`; unreadable or
malformed files fail before mapping. Missing consequence files no longer install
an incomplete scientific result as if the source returned nothing. Explicit empty
local mappings retain fixture-subset scope. A direct empty online consequence
request makes no query and earns no data-resource credit. Shared transport retries
remain separately visible and are not duplicate completed GraphQL pages.

## Upstream identity prerequisite (#141)

Both gnomAD enrichers require an Ensembl gene cross-reference stated by the entry.
Previously, no gene caused `NothingToAsk`, enrichment `not_found` and knowledge
state `not_stated` despite no source access. Development uses the existing
`RequestPrerequisiteMissing` route: `not_queried`, unknown counts and a prerequisite
explanation, before constructing a client. No operation or resource credit is
created. Supplied-gene scientific results, assertions and pins stay unchanged;
historical stored cards are not reclassified on read.

## Attribution and persistence

Resource bibliography identifies the actual gnomAD GraphQL API URL from the
existing connector. It invents no entry or method publication metadata. Native
dataset/GTEx revisions and variant/pext publications remain explicit gaps. This
slice adds no new provider route, general cost/pagination policy or wall deadline.

Normal scientific values, assertion identities, quantities and pins equal the
equivalent unobserved fixture client. Original fixtures, card shape/schema and
published 0.14.0 remain unchanged. Archive reuse/replay retains original POST
body/wire hashes, times and portable credit without new provider queries. An
independent saved reader restores exact pins and original attribution without
acquisition, derivation or fresh credit. Derived comparative operations, complete
bibliography and full installed-artifact/human/consumer-owned acceptance stay open.

## Verification

Local qualification passed: 340 selected tests in 18.04 seconds and all 6,085
offline tests in 158.48 seconds with 12 pytest-receptor workers. The full run
retains 13 expected fixture warnings and makes SQLite/unraisable warnings fatal.
Ruff, schema/shape, registry, fixture delivery, dependency preflight, MOLI governance,
warning-fatal Sphinx and 174 relative-file links pass. Remote source qualification
is in progress. The public fixture/synthetic module
`test_gnomad_acquisition_offline.py` adds 54 cases for three public envelopes,
four operations, native/query/fixture revision bases, consequence generators,
alias/null/empty scope, partial failures, unavailable/unreadable/malformed local
inputs, retries, archive reuse/replay, original scientific pins, placement/limits,
unqueried prerequisites and independent inert saved reading. The installed
public-Ackredit CI lane includes this module outside the checkout. No new provider
query or private fixture is involved.
