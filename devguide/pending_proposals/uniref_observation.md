# UniRef page acquisition observation (#108)

Owner: [uibcdf/sabueso#108](https://github.com/uibcdf/sabueso/issues/108), following
the quality plan #112 and shared UniProt identity/terms correction #136.

The existing built-in online/fixture `clusters` and `members` operations now emit
detached `uniref_clusters` and `uniref_members` records under scientific source
`UniProt`. Public `get_clusters` attaches its trace, including failed access.
This extends operation coverage within the existing 36 source families.
Custom clients remain unobserved; an unasked operation creates no resource credit.

`uniref_page_observation@1` preserves each completed or malformed decoded page's
identity, requested URL, native release header, continuation and native total
header. Shared transport records retain original wire hashes, retries and times.
Fixture envelopes declare a release label; they do not establish native headers
or complete pagination. Row counts distinguish all received rows from client
rows retained under the existing 5,000-member limit. Search remains one response
with requested size 10; members follow existing links with requested size 500.
A remaining link or discarded overrun is explicit truncation. Exhausting the
returned route does not establish global completeness or coherent revisions.

Uniform stated page releases yield a release value; conflicting, partially
unstated and completely unstated releases yield unknown with their actual basis.
The existing client `version` remains a compatibility label, including its final
member-page choice. It is not proof that all pages or separate cluster/member
operations share a revision. Original page metadata remains independently
inspectable even when the next page fails.

At source checkpoint `c6cb0e3`, the row limit did not bound attempts across empty
continuation pages or detect cyclic links. The subsequent
[pagination correction #140](../pending_bugs/uniref_pagination.md) has separate
qualification; it does not change this dated observation receipt.

Later failures retain completed-page counts and identities as partial access,
with the original terminal failure and no returned scientific result. Empty
pages before a failure do not establish complete absence. Valid empty answers
remain distinct from malformed required containers and failed transport.
Missing local fixtures now raise `ConnectorError` with an `unavailable` observation,
preventing local absence from becoming a provider absence assertion. Failed
member enrichment installs no partial cluster assertions or relationships.

Completed access credits the UniProt resource description and the specific
UniRef API resource URL already used by the connector. Cluster/member sequence
revisions and underlying member publications remain explicit bibliography gaps.
Resource descriptions do not establish identity, primary scientific support or
new data-use permissions. Cluster membership remains similarity; no entry or
UniParc sequence is merged by membership, name or sequence.

The observer does not alter scientific values, assertion identities, pins,
schemas or original fixture bytes. An independent process loads exact saved pins
and renders original portable attribution with acquisition, derivation and fresh
credit forbidden. Published 0.14.0 remains unchanged. OMA, gnomAD, derived
comparative operations and complete bibliography remain separate #108 work.

## Verification

The public fixture/synthetic module `test_uniref_acquisition_offline.py` covers
page revisions, pagination/caps, partial failures, native totals, empty/malformed
responses, missing/unreadable fixtures, transport retries, archive reuse/replay,
unasked/custom scope, scientific equivalence and independent saved reading.
Owning source, refresh, acquisition/attribution and comparative journeys exercise
the shared boundaries. Python 3.14.7 / pytest-receptor with twelve workers passes
322 selected cases in 25.44 seconds and all 5,963 local-original cases in 210.17
seconds, with thirteen expected fixture warnings and fatal SQLite/unraisable
guards. Ruff, unchanged 1,627-path card shape/schema, source registry, fixture
delivery (50 repository / 37 protected originals), dependency preflight,
governance/canonical guide equality, warning-fatal Sphinx, 128 relative file links
and whitespace checks pass. Exact source `c6cb0e3075681742dda3eba4d92b5bbbddc7c303`
passes [15/15 CI jobs](https://github.com/uibcdf/sabueso/actions/runs/38041493783)
and [governance](https://github.com/uibcdf/sabueso/actions/runs/38041493793).
The [public receipt](uniref_observation_checkpoint.json) independently verifies
all captured member hashes and thirteen test-job summaries: nine public offline
lanes pass 4,410 cases with ten fixture skips and 26 online deselections; four
installed public-Ackredit lanes pass 1,048 cases outside the checkout. After
editable metadata refresh, 75 access/independent-report cases pass in 21.15
seconds; all six participating runtime imports and metadata agree outside the
checkout. A separate synthetic transport reproduces the #140 termination defect;
it is not fixed or counted among the 33 new regression cases. No new provider
queries or private fixtures are used. Complete installed Sabueso artifact and
human/consumer-owned acceptance remain separate.
