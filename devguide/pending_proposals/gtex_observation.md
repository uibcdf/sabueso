# GTEx tissue acquisition observation (#108)

Owner: [uibcdf/sabueso#108](https://github.com/uibcdf/sabueso/issues/108), following
the quality plan #112 and dependent-request correction #135.

## Development behavior

The existing online and fixture `tissues(dataset)` operations and public
`get_tissues` now retain detached acquisition records. These describe actual
access, returned row order/count, decoded envelope/result identities, original
transport bytes/times, retries, failures, fixture unavailability and archive
reuse/replay. The client still asks one `tissueSiteDetail` response with
`itemsPerPage=250`; neither a successful response nor a full requested page
establishes dataset completeness. Fixture coverage is a local subset.

The client answer's existing `version` remains the requested dataset label for
compatibility. Operation `source_version` is explicitly unknown: a request
parameter is not an observed native revision. `tissue_context` declares the
requested dataset, label basis, single-response scope and unknown completeness
under `gtex_tissue_observation@1`. Native tissue ids keep their order and are never
merged because they share an ontology term. Counts describe returned rows, not
the subset selected into a card's tissue-term mapping.

A valid empty response stays distinct from malformed required envelopes,
failed transport and unavailable fixtures. Missing fixture files now raise
`ConnectorError` with an explicit `unavailable` observation, preventing their
interpretation as a provider's absence statement. The established online
HTTP 404/422 `RecordNotFoundError` interpretation remains explicit as a client
interpretation rather than an independently received dataset-absence claim.
Unasked archive entries and blocked prerequisites add no completed-access credit.
The #135 prerequisite gate still runs before constructing the client and creates
no fabricated GTEx operation.

Completed access credits Sabueso and the GTEx Portal resource description using
the existing public Ackredit adapter. The Portal URL and acknowledgement are
already declared in the source registry and fixture notice; no DOI enrichment,
article lookup or new data-use permission is inferred. Native dataset/tissue
revisions and underlying publication metadata remain explicit bibliography gaps.
Custom clients still do not establish observed built-in access. Declared source
coverage becomes 36 families; UniRef, OMA, gnomAD, derived comparative operations
and complete bibliography retain their separate remaining #108 scopes.

Successful scientific values, assertion ids, mapping rules, published schema 0.3.13,
unpublished schema 0.3.14 and original fixture bytes are unchanged. Original
sidecars remain portable; a separate process reads exact saved card pins and
renders original attribution with source access, derivation and fresh credit
forbidden. This is source development, not installed-artifact or human acceptance.

## Qualification

`tests/core/test_gtex_acquisition_offline.py` supplies 34 public fixture/synthetic
cases. Owning GTEx, acquisition/attribution, taxonomy, refresh, comparative-envelope
and independent-report regressions exercise the shared boundaries. Python 3.14.7 / pytest-receptor with twelve workers passes 343 selected cases
in 14.77 seconds and all 5,930 local-original cases in 178.50 seconds, with eleven
expected fixture warnings and fatal SQLite/unraisable guards. Ruff, unchanged
1,627-path card shape/schema, source registry, fixture delivery (50 repository /
37 protected originals), dependency preflight, governance/canonical guide equality,
warning-fatal Sphinx, 104 relative file links and whitespace checks pass. Exact-SHA
CI qualification passes [15/15 jobs](https://github.com/uibcdf/sabueso/actions/runs/38038383487)
and [governance](https://github.com/uibcdf/sabueso/actions/runs/38038383380) for exact
source `2b5db5328e992bcd3eaf3a4c29b4b8de527f5adc`. The
[public receipt](gtex_observation_checkpoint.json) verifies complete GH Run Receptor
capture/replay, every captured member hash and all thirteen test-job summaries.
Nine public offline lanes pass 4,377 cases with ten declared fixture skips and
26 online deselections; four installed public-Ackredit lanes pass 1,015 cases.
After editable metadata refresh, 76 access/independent-report cases pass in
16.71 seconds; all six participating imports and metadata agree outside the checkout.
All four installed public-Ackredit compatibility lanes also include these cases
outside the checkout; local editable-provider tests do not establish that floor.
No new provider queries or private fixtures are used.
