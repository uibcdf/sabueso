---
summary: Required automatic result and workflow attribution for knowledge pipelines.
issue: uibcdf/sabueso#108
status: open
opened: 2026-10-02
closed:
verification: local_runtime_tested
area: [attribution, knowledge_packets, source_access]
blocked_by: [uibcdf/moli#36]
supersedes: []
---

# Required attribution for knowledge pipelines

Status: required automatic packet-composition and bounded source-acquisition adapters
implemented; broader pipeline
coverage remains open with explicit gaps in the published 0.12.0 scope (#108).
Public Ackredit 0.9.0 delivery is adopted; Sabueso's own candidate/release gates remain.
Owner: [uibcdf/sabueso#108](https://github.com/uibcdf/sabueso/issues/108).
Shared boundary: [uibcdf/moli#36](https://github.com/uibcdf/moli/issues/36).
Provider: [uibcdf/ackredit#75](https://github.com/uibcdf/ackredit/issues/75).
Reviewed: 2026-10-03, published Ackredit 0.9.0/py_0 from source
`598abf993a2409c025de5e912acd7eb45a257ebd`.

## What the consumer needs

A pipeline should retain which sources, datasets and executed software it used,
with citation records for each result and the enclosing application workflow.
Ackredit's accepted `capture`, contextual `track_item`, detached `Attribution`
and `get_attribution` fit this need. Its canonical
[integration guide](https://github.com/uibcdf/ackredit/blob/main/standards/ACKREDIT_GUIDE.md)
owns the provider API; this report records Sabueso's initial use and remaining needs.

Four records have different responsibilities:

| Record | Responsibility |
| --- | --- |
| SourceAssertions and pinned relationships | What sources state and what supports returned knowledge |
| Acquisition trace | Observed source operation, route, response identity and outcome, including failures |
| Runtime attribution | Resources and software actually reached, with bibliography and contextual uses |
| Terms report | Source-stated obligations, restrictions and unknowns for an intended use |

Neither a citation nor an acknowledgement supplies permission to redistribute
article text. A publication mentioned by a database is not automatically that
database's description citation. Nextia Evidence remains separate from all three.

## Proposed integration boundaries

1. **Acquisition:** distinguish attempted requests from successful acquisitions,
   including evaluated-empty responses and local replay. Record the actual route,
   release (unknown when unstated) and outcome. A failed request does not claim a
   completed scientific acquisition; an unqueried source receives no usage credit.
2. **Composition and views:** retain the pinned statements and rules actually used.
   Whole-card source summaries include unrelated knowledge and cannot define a
   result's citation scope. Reading stored knowledge differs from downloading it.
3. **Result and workflow:** each result owns detached original records and versions,
   including resources reused by earlier results. Contribute to the current
   application session; do not create isolated component sessions or infer a
   result's bibliography by subtracting deduplicated session IDs.
4. **Saved readers:** preserve original attribution and render it without new credit,
   backend loading or DOI enrichment. The initial local record is stored beside
   scientific data, with no change to shared knowledge payloads. Shared record
   coordination remains MOLI #36.

Bibliographic declarations must be complete, verified offline against original
works, and versioned where appropriate. Sabueso's registry currently supplies
terms/attribution text, not a complete resource bibliography. Literature records
may supply identifiers and partial metadata; missing authors, dates and releases
must not be invented. The provider owns rendering; Sabueso must not copy its
renderers or inspect its private registry.

## Current pre-release work

`Card.explain_literature(publication_ref)` provides pinned links, both legs of
structure mention context, preserved alternatives and recorded unlinked requests.
`KnowledgePacket.terms(use, store)` provides a detached support manifest and a
terms report for `packet_aspects@6`, independently of full/index detail. It reads
exact saved cards and follows represented statements, conflicts and stored
relationship dependencies. Disease identity context is explicitly broader than
exact grouping lineage, which was not recorded.

These read-time operations keep their support/terms meaning. The initial runtime
adapter now follows the same stored-statement closure independently of licence
verdicts, automatically after every completed composition. `packet.attribution` owns
the detached record; `sabueso.attribution()` optionally collects several results.
It records `sabueso.packet_attribution@1` locally, credits selected stored knowledge
and executed software, and contributes per-result references to the application's
Ackredit session/captures. Composition itself observes no source requests or arbitrary card views.
Query, packet, card and store payloads remain unchanged.

Traceability is required by the maintainer and MOLI. The first acquisition slice
automatically observes built-in UniProt entry/search, Europe PMC
mentions/annotations and RCSB single/batch structure lookup. Provisional host records
`sabueso.source_acquisition@1` in a
`sabueso.acquisition_trace@1` retain independent operation identities, actual routes,
original producer/source versions with explicit bases, retrieval times, decoded/raw
response identities and archive references. Empty/not-found, unavailable fixtures,
unqueried offline access, failure and partial transport remain distinguishable.
Supported public envelopes retain the trace separately from raw records. Cards,
resolutions (including no-card failures), refreshed final states and one-call
packets retain independent copies. Exceptions retain their failed trace.

Completed access contributes contextual resource use and bibliography through the
accepted Ackredit API, including empty/local replay access. Failed/unqueried access
remains a host record without completed-access credit. `AttributionRun.acquisitions`
collects these source events separately from packet composition `records`.
Other sources/custom clients are explicitly unobserved. Original JSON sidecars are
saved by the application; payload-only readers have no trace and add no execution
credit. MOLI owns ProjectRecord composition and future Recorda routing/correlation/
reliability policy; the local experiment does not implement that platform boundary.

The public offline pilot in `examples/ackredit_pilot/` composes identity and
literature packets for HsTIM from frozen public responses. Both retain reused UniProt
references; only literature credits Europe PMC. Their enclosing workflow holds the
union of intake and composition references. The pilot saves the original acquisition
trace beside the knowledge store. Saved JSON readers preserve versions and add no credits. Real-provider tests
exercise reused resources, nested scopes, detached ownership, installed failure,
fresh-process missing required provider diagnostics, lazy import and scientific result parity. Recorded
empty source outcomes do not imply a new download. Source regression tests verify
replay/reuse, empty answers, absence/failure, partial batches, retry facts, custom-client
coverage, refresh pins and one-call packet intake independently of composition.

Complete UniProt/Europe PMC/RCSB description citations were verified against primary
publication records; missing descriptions and target article/annotation-provider
bibliography remain gaps. The required candidate includes the correction reported
in [Ackredit #78](https://github.com/uibcdf/ackredit/issues/78): explicit CSL corporate
and personal author objects render correctly in BibTeX. Saved-reader consumer
regressions check original metadata in text, CSL-JSON and BibTeX without new credits.
No renderer is copied.

Consumer CI now obtains Ackredit from public Conda on every runtime lane;
dedicated receiving lanes pin 0.9.0/py_0 on Python 3.11–3.14. Metadata, recipe and
all runtime environments require `ackredit>=0.9.0`; the source overlay and blocker
are removed together. The installed Conda gate retains the delivered public SHA-256
and rejects a different hash, channel, imported version or portable API.

The earlier
[local diagnostic receipt](https://github.com/uibcdf/sabueso/issues/108#issuecomment-5968486124)
is superseded for receiving qualification by the actual staging/public file below.

## Independent exact-staging receiving qualification (2026-10-03)

The provider's [handoff](https://github.com/uibcdf/sabueso/issues/108#issuecomment-5971254953)
supplies `noarch/ackredit-0.9.0-py_0.tar.bz2`, built from
`598abf993a2409c025de5e912acd7eb45a257ebd` in successful producer
[37136075066](https://github.com/uibcdf/ackredit/actions/runs/37136075066).
Independent download SHA-256 is
`37661090f6ad19a74b8155d8a4d4b4a068c9099f4ceba0743b3abfe887e97fe1`.
It matches retained `noarch-artifact.json` and the verified `uibcdf.conda-upload@1`
staging receipt in artifact `noarch-publication-37136075066-1`, including producer
identity, source, label and coordinate. Archive metadata also matches 0.9.0/py_0/noarch.

Sabueso independently repeats the receiving tests with its prepared source
`7352cf4437dca6d0249c3af9777ad123926d2f31`. A disposable clone supplies a normal
local wheel, SHA-256
`2520fd3e07fa6db5c65f66f3087175c7657a3c7b519fbf9a1cf3c4d9ccf38f61`.
All 348 Python modules excluding generated `_version.py`, plus packaged
selection/profile/terms resources, match that source without extra modules.
Cleaning tracked generated build copies in the disposable clone explains its
development suffix; this wheel is compatibility input, not a published artifact.

Four fresh Linux environments use strict public channels and the exact core builds
planned for Sabueso's installed gate: SMonitor 0.17.0/py_0, ArgDigest 0.13.0/py_1,
DepDigest 0.11.0/py_2 and PyUnitWizard 0.27.0/py_0. Public Pytest/Receptor tooling
is installed with Conda. Only the verified Ackredit file comes from staging; the
consumer wheel is installed normally with `pip --no-deps`, not editable.

| Python | Unchanged acquisition/attribution cases | Public workflow | Pip check |
| --- | --- | --- | --- |
| 3.11.16 | 36 passed, no skips | passed | passed |
| 3.12.14 | 36 passed, no skips | passed | passed |
| 3.13.15 | 36 passed, no skips | passed | passed |
| 3.14.7 | 36 passed, no skips | passed | passed |

Tests execute outside both checkouts using only frozen public fixtures. Provider,
consumer and core dependencies import non-editable code from the isolated prefix's
site-packages; runtime and distribution versions agree. Installed package bytes
match their archive/wheel, and the installed Conda record keeps the exact staging
URL/version/build/SHA-256. The pilot verifies the original trace, two result
bibliographies, reused references, workflow union and saved readers without new credit.
The compact durable
[receiving receipt](../../devtools/conda-build/receipts/ackredit_0.9.0_staging_2026-10-03.json)
retains file/source identities, pins and each result. The primary workspace environment
retains editable packages.

This establishes Linux receiving compatibility with the actual staged provider,
including Sabueso's older public core pins. It does not replace Ackredit's hosted
Linux/macOS-arm64 installed matrix or Sabueso's eventual Conda installed matrix.
At that checkpoint, the hosted descriptor/caller needs were MolSysSuite #89/#88
work and public dependency closure remained blocked. Those delivery gates have now
closed through the public handoff below. Repeat qualification if the bytes change;
a version alone is no artifact identity.

## Public delivery adoption (2026-10-03)

The [published handoff](https://github.com/uibcdf/sabueso/issues/108#issuecomment-5973768120)
identifies the first released portable minimum, **Ackredit >=0.9.0**.
[Installed 37152044426](https://github.com/uibcdf/ackredit/actions/runs/37152044426)
passes all eight Linux/macOS-arm64 × Python 3.11–3.14 cells;
[promotion 37152421084](https://github.com/uibcdf/ackredit/actions/runs/37152421084)
preserves the same archive. Independent anonymous public download matches the
staging bytes and digest. Normal clean public-channel receiving installs on all
four Linux minors repeat the 36 tests, public workflow and pip check with the
planned exact public core builds. Ackredit #22/#75/#80 are closed.

Sabueso adopts the published floor in metadata, recipe and environments, pins
0.9.0/py_0 and the qualified digest in installed gates, and removes source overlays
and the public-dependency blocker together. Development and release preflight pass.
This delivery closes the provider dependency gate. Sabueso's preliminary local
Conda candidate now passes all four Linux minors and supplies the clean-installed
frozen 0.3.11 card; receipt:
`devtools/conda-build/receipts/sabueso_0.12.0_local_schema_freeze_2026-10-03.json`.
Its preliminary candidate `4ef9ddc` passed the actual staged archive and all 12
Linux/macOS-arm64/Windows × Python 3.11–3.14 installed lanes, with 36 integration
tests and the public workflow in each. Independent clean Linux 3.14 also verifies
installed bytes, the frozen card and pip check; receipt:
`devtools/conda-build/receipts/sabueso_0.12.0_staged_2026-10-03.json`.
The final RCSB extension is published from `7739317` as `py_1`, after fresh
CI/installed qualification, unchanged promotion, clean public installation and
identical-tag Zenodo archival. Its complete receipt is
`devtools/conda-build/receipts/sabueso_0.12.0_public_2026-10-04.json`.

The maintainer's editable workspace initially exposed a 0.8.0-based Git-version
mismatch, reported in [provider #81](https://github.com/uibcdf/ackredit/issues/81).
On 2026-10-04 the provider's 0.9.0 tag yields editable
`0.9.0+8.ga8219b8.dirty`; runtime/distribution versions agree, the floor is met
and the primary environment's pip check passes. All 14 workspace packages remain
editable. Receiving confirmation is reported upstream; #81 is closed through provider #82.
Clean public distributions satisfy the floor; broader trace/result/bibliography
and MOLI record work remain open in #108/#36.

## Adoption gates

The staged 0.12.0 preparation is tracked in #110. Its installed-file matrix now
requires provider import/metadata/API checks, the unchanged acquisition/attribution
regressions and the public workflow on every supported OS/minor, outside both
checkouts. Public delivery and the clean-installed frozen 0.3.11 card are verified. The
preliminary candidate `4ef9ddc` passed its actual staged artifact gates. On
2026-10-04 the maintainer requested RCSB before stable publication: native revisions,
per-entry batch outcomes, all fallback requests and original primary citations.
Final source `7739317` and build `py_1` repeat every gate: all 12 installed lanes
and independent clean public installation pass 56 integration cases and the public
three-packet workflow. Stable publication, unchanged promotion and identical-tag
Zenodo archival are complete under #110. The historical `py_0` receipt/archive stays
immutable. Native primary citations retain different stated metadata forms without
overwriting earlier references; missing fields remain explicit.

- Keep Ackredit required in metadata and the recipe. Lazy required import keeps
  saved readers free of backend loading. Missing/broken installations emit SMonitor
  diagnostics and retain failed attribution alongside completed scientific results.
- Results receive attribution automatically; applications own sessions. Libraries enable no import
  hooks, persistence journals, automatic enrichment or reminders.
- Exercise a real provider with three results reusing sources, an enclosing workflow,
  cached/offline and evaluated-empty requests, genuine absence, failure, fresh-process
  lazy import, detached ownership and saved readers without new credit.
- Published provider/dependency closure is verified and adopted for every supported
  Python minor. The released portable API minimum is 0.9.0; installed gates pin the
  actual public build/hash. Ackredit #22/#75/#80 are resolved. Sabueso's own Conda
  installed matrix passes separately from receiving tests; see its staged receipt.
  The consumer verifies the editable version consistency fix in Ackredit #81.
- Coordinate the attribution/knowledge/terms boundary in MOLI #36; Ackredit and
  MolSysSuite keep ownership of provider/member contracts and rollout.

The maintainer first requested early integration on 2026-10-02, then chose a hard
dependency and automatic attribution. The initial optional decision is superseded.
`dependency_preflight.py --release` now passes public closure on Python 3.11–3.14.
Its generic safeguards still reject stale floors, omitted pins and future unpublished
providers. Required metadata names the delivered minimum 0.9.0.
Next work extends observed acquisition to other sources and result types, expands
verified resource bibliography and coordinates the platform record boundary.
This change makes no release.

## Alternatives

- Use whole-card provenance as a citation list: rejected because it includes unused
  sources and lacks complete bibliography and runtime meaning.
- Use terms reports as usage logs: rejected because permissions/obligations and
  execution usage answer different questions.
- Keep Ackredit optional: superseded by the maintainer's hard-dependency decision.
  Failure tolerance and installation requirements are separate decisions; missing
  a missing public closure blocks release rather than weakening the product contract.

## Acceptance criteria and resolution

Two public offline packet results retain their own original attribution, including
reused resources, and the application's workflow captures both. Unused sources earn
no credit. Saved readers, absence and provider failures preserve result knowledge.
The automatic-composition/acquisition pilot and published receiving compatibility
pass. #108 is kept open for remaining acquisition/further-result coverage, complete
bibliography and the shared record boundary; #110 owns Sabueso release qualification. This is an initial
runtime integration, not a claim of full pipeline coverage or a public installation route.

## ChEMBL development slice after 0.12.0 (#108)

All five built-in online/fixture logical operations are observed. Normalized queries,
page/chunk metadata, raw transport identities, retries, caps, documents and received
subsets survive original failures. Native document citation forms use content-based
identities; missing authors/indication bibliography remain gaps. Empty answers,
unavailable fixture datasets and empty/unqueried batches remain distinct. Existing
client release-cache metadata is explicitly not independent release proof per page.
Scientific returns/exceptions and the frozen card schema remain unchanged.

The first standalone literal extraction in #92 additionally retains detached original
Ackredit attribution without treating it as packet composition, human curation or a
source download. `literal_uniprot_mention@1` names its tool/version/configuration and
input hash. Explicit `Card.add_literature_extraction` and `ExtractionStore` now
preserve original scientific support and supplied runtime receipts through
storage/refresh. Reuse retains original producer/use contexts; readers add no credit.
Payload-only refresh states the missing sidecar instead of reconstructing attribution.
New scientific intake fields use unpublished schema 0.3.12, with all published
schemas/receipts unchanged. Broader rules and article metadata/terms remain #92.

Tests: `test_chembl_acquisition_offline.py` and
`test_rule_literature_extraction_offline.py` join the unchanged installed-provider
CI/release tests, alongside `test_literature_intake_offline.py` for original support
and receipt replay, terms-profile boundaries and honest missing-sidecar refresh.
The current checkpoint passes 1,468 source offline cases and 160 unchanged installed
integration cases. Source and installed diagnostic receiving evidence uses public
Ackredit 0.9.0; this development slice is not a new published Conda package.
All eight read-only public-installed 0.12.0 notebook copies execute. Temporary host
instrumentation preserves 19 observed acquisition records (18 received, one empty)
and two composition records with available attribution, plus original sidecars.
Private content stays outside public reports and repositories; original notebooks
remain unchanged.

The design review (#112) makes further sources/results,
complete bibliography and MOLI record/consumer boundaries explicit remaining work.
Local wheel testing uncovered stale incremental `build/lib` modules (#113); a
source-byte/membership guard rejects them before installed receiving qualification.
Published 0.12.0's independently qualified public Conda artifact is unaffected.

## PubChem development slice after 0.12.0 (#108)

Built-in online/fixture compound, structure-match and BioAssay target operations are
observed. Native per-assay version/revision/date metadata (including zero) is
preserved without inventing global or per-row versions. Source-described depositors
are contextual declarations, not directly consulted providers. Resource-description
citations and original PubMed pointers retain distinct roles; absent publication
metadata and depositor bibliography remain explicit gaps.

Queries, POST-body identities, CSV/summary/property hashes, row totals/caps/order,
chunks, retries and archive reuse/replay retain original retrieval times. Received
subsets survive a later failing batch, with the terminal outcome and counts explicitly
scoped to received target rows before completion. Empty, absent, rejected-input,
unavailable-fixture and offline-unqueried outcomes remain distinct. Rejected input
does not receive completed-data credit. Scientific payloads, exceptions and schema
0.3.12 are unchanged; saved readers add no credit.

`test_pubchem_acquisition_offline.py` is copied unchanged into installed-provider
CI and future staged gates. These component-local traces do not define the shared
MOLI ProjectRecord/Recorda contract.

## BindingDB development slice after 0.12.0 (#108)

Built-in REST, fixture and mirror affinity queries are observed without scientific
payload/exception/schema changes. Queries, cutoff/limit/order, total/kept counts,
original response hashes, DOI/PubMed forms, archive reuse/replay and retries survive.
Resource-description citations and native measurement pointers retain separate
roles; incomplete forms cannot replace fuller host citations. REST versions/origins
and missing bibliography remain unknown. A mirror's declared data origin does not
claim direct access to an imported provider.

Mirror queries retain local access, known manifest release/URL/checksum/installation
time and a manifest hash without network attempts. The manifest does not prove
live REST release or index integrity on every query; its installation-time retrieval
basis and current event times stay distinct. Fixture cutoffs are not reapplied;
their scope is explicit. Installation/update and constructor failures remain outside
query observation.

Decoded-empty, absent-fixture, offline-unqueried, failed and partial-before-processing
outcomes remain distinct. Original HTTP and corrupt-index failures are retained.
The documented empty-string compatibility gap is owned by Sabueso #114, with
regressions preserving its failure receipts and no successful credit.
`test_bindingdb_acquisition_offline.py` joins unchanged installed-provider CI and
future staged gates; saved readers add no credit. Other sources/custom clients,
full bibliography and MOLI's shared record/consumer coordination remain open.
