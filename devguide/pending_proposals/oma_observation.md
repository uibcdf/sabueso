# OMA operation observation (#108)

Owner: [uibcdf/sabueso#108](https://github.com/uibcdf/sabueso/issues/108), following
the #112 quality plan and the source-qualified UniRef termination correction #140.

Development observes built-in online/fixture `xrefs`, `protein` and `orthologs`
as `oma_xrefs`, `oma_protein` and `oma_orthologs` under scientific source `OMA`.
`accessions` is `oma_entry_names` under `UniProt`: OMA does not assert the result
of a subsequent UniProtKB entry-name search. Public `get_orthologs` attaches the
two OMA operations' detached trace, including failed access. Declared observation
coverage becomes 37 source families; custom clients and unasked routes stay explicit.

`oma_operation_observation@1` retains response identities, request URLs, native
continuation links, counts and actual revision bases. OMA's existing response
containers do not state a record revision; unrelated service headers are not
promoted to one. UniProtKB search batches retain their individual
`X-UniProt-Release` values, including conflicting, partly unstated and unknown
revision bases. Neither one response nor a fixture subset proves completeness.
Remaining next links are observed without adding unasked follow-up requests.

Name resolution preserves the existing policy: a wanted name resolves only to
one unique accession among rows not marked `Inactive`. Duplicate identical hits
remain one binding; multiple distinct hits stay unresolved. Omitted `entryType`
is handled by the existing client policy, not proof of native active status.
Missing, blank or non-string accessions in consumed native rows and malformed
fixture bindings raise `ConnectorError`. Generator inputs are materialized once
before observation; batching does not consume them twice. Per-batch requested,
resolved and unresolved names are retained separately from returned mapping count.

Received rows precede client filtering and the enricher's taxon/limit selection.
The trace labels client counts separately from card-selected relationships;
the card's original quality record retains the actual mapping count, limit and
filters. Source-stated `seq_match` gates remain unchanged. A modified mapping can
acquire the existing diagnostic protein lookup, but never acquires or joins that
protein's orthologs. Orthology, identical sequences and shared canonical names
never merge entities or strain-specific relationships.

Later name-batch failure keeps completed responses, counts and original resource
credit as partial access, without returning a partial name mapping or installing
partial card assertions. An empty batch before failure does not establish complete
absence. A direct empty online name request makes no query and earns no resource
credit. Missing local files are unavailable; unreadable/malformed files are failed,
and explicit empty records remain distinct. Archive reuse/replay preserves original
wire hashes, response times and headers with no new provider query.

The existing outer OMA service retries remain separately visible in shared request
records; retry attempts are not duplicate completed pages. This slice adds no
strict wall-clock deadline or general pagination/cost policy. Bibliography credits
the actual OMA REST API resource and, for name resolution, the existing UniProt
description and UniProtKB search API resource. No publication metadata is invented;
entry/orthology method publications and sequence revisions remain explicit gaps.

Normal scientific client results, assertion identities, relationships and pins
equal the equivalent unobserved fixture client. Original schemas/fixtures and the
published 0.14.0 artifact stay unchanged. An independent saved reader restores exact
pins and original portable attribution without acquisition, derivation or fresh
credit. gnomAD, derived comparative operations, complete bibliography and full
installed-artifact/human/consumer-owned acceptance remain separate #108/#112 work.

## Verification

Local qualification passed: 323 selected tests in 16.77 seconds and the full
offline suite of 6,031 tests in 161.39 seconds, with 12 pytest-receptor workers.
The full run retains 13 expected fixture warnings and makes SQLite/unraisable
warnings fatal. Ruff, schema/shape, registry, fixture delivery, dependency
preflight, MOLI governance, warning-fatal Sphinx and relative-link checks passed.
Remote source qualification is in progress. The public fixture/synthetic module
`test_oma_acquisition_offline.py` adds 47 cases for source boundaries, native and
unknown revisions, name ambiguity, generators/batches, missing/malformed inputs,
continuations, retry exhaustion, partial failure, archive reuse/replay, taxon/limit
selection, modified mappings, scientific equivalence and independent inert reading.
Owning source, acquisition, refresh and comparative journeys exercise shared
boundaries. The required CI compatibility lane includes these cases outside the
checkout with the installed public Ackredit. No new provider queries or private
fixtures are used.
