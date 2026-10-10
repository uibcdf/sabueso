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
warning-fatal Sphinx and 165 relative-file links pass. Source
`94ad9eb669f6e36b5f2ea710a64db12d4d3bf054` passes
[15/15 exact-SHA CI jobs](https://github.com/uibcdf/sabueso/actions/runs/38053932696)
and [governance](https://github.com/uibcdf/sabueso/actions/runs/38053932729).
The [source receipt](open_targets_prerequisite_checkpoint.json) independently checks
all full GH Run Receptor capture members and 13 terminal test summaries: nine
public offline lanes each pass 4,539 cases (10 fixture skips, 26 online
deselections), and four installed public-Ackredit lanes each pass 1,177 cases.
After installing the qualified source editable, 82 cases pass in 6.36 seconds and
all six participating imports/metadata match local checkouts outside the repository.
The qualified producer is `0.14.0+28.g94ad9eb`; subsequent documentation metadata
does not rewrite that original receipt.

A separate public-fixture producer/reader pair outside the checkout preserves both
historical and corrected scientific payloads/pins with source access, derivation
and fresh credit forbidden in the reader. Changing its runtime version cannot
rewrite either stored state. No new provider queries, private fixtures or changes
to published 0.14.0. Existing installed public-Ackredit CI copies the
owning `test_disease_source_acquisition_offline.py` module outside the checkout.
Full installed-artifact and human/consumer acceptance remain separate.

Static inspection and six synthetic forbidden-constructor probes found remaining
legacy `NothingToAsk` gates, tracked for
source-local public review in [#143](https://github.com/uibcdf/sabueso/issues/143).
This correction does not qualify those gates; original historical classifications
are not silently reinterpreted. Broader derivation/bibliography work stays #108.
