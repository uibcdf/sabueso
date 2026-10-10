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

The existing row limit does not bound attempts across empty continuation pages
or detect cyclic links. This observer preserves the existing pagination behavior;
a separate termination policy remains #108 work before claiming bounded requests
for arbitrary malformed pagination.

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
and whitespace checks pass. Exact-source CI qualification is pending. No new
provider queries or private fixtures are used.
