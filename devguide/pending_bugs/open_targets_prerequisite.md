# Open Targets upstream gene prerequisite (#142)

A public P60174 fixture with Ensembl cross-references removed previously returned
quality `not_found` and knowledge state `not_stated` with count zero despite no
Open Targets access. Four regression variants reproduce the old failure: missing
all Ensembl cross-references or only `GeneId`, with a supplied client or a forbidden
default constructor. A retained protein/transcript cross-reference is not a gene.

The source-local `OpenTargets.requests` gate now raises the existing
`RequestPrerequisiteMissing`. The runner retains request options, records
`not_queried` with unknown counts and explains the missing upstream input before
constructing/calling a client. It creates no Open Targets acquisition or resource
credit. No generic runner semantics, public arguments or schema change.

A synthetic native query whose target omits the caller protein still records the
actual completed source access, source bibliography and existing `not_found`/
`not_stated` outcome. Valid-gene public fixture cards equal the equivalent unobserved
client's exact scientific payload and pin. Explicit refresh of a saved
historical missing-gene result records the corrected state while both original and
refreshed pins remain independently readable without acquisition or fresh credit.

Seven new public cases and 229 selected cases pass with Python 3.14, twelve
pytest-receptor workers and fatal SQLite/unraisable guards. All 6,092 local-original
offline tests pass in 160.53 seconds with 13 expected fixture warnings. Style,
schema/shape, fixture delivery, registry, dependency preflight, MOLI governance,
warning-fatal Sphinx and 165 relative-file links pass. Remote source qualification
is in progress. No new provider queries, private fixtures
or changes to published 0.14.0. Existing installed public-Ackredit CI copies the
owning `test_disease_source_acquisition_offline.py` module outside the checkout.
Full installed-artifact and human/consumer acceptance remain separate.

Static inspection and six synthetic forbidden-constructor probes found remaining
legacy `NothingToAsk` gates, tracked for
source-local public review in [#143](https://github.com/uibcdf/sabueso/issues/143).
This correction does not qualify those gates; original historical classifications
are not silently reinterpreted. Broader derivation/bibliography work stays #108.
