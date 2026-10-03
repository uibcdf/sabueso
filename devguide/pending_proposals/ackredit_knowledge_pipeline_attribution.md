---
summary: Required automatic result and workflow attribution for knowledge pipelines.
issue: uibcdf/sabueso#108
status: open
opened: 2026-10-02
closed:
verification: local_runtime_tested
area: [attribution, knowledge_packets, source_access]
blocked_by: [uibcdf/moli#36, uibcdf/ackredit#75, uibcdf/ackredit#22]
supersedes: []
---

# Required attribution for knowledge pipelines

Status: required automatic packet-composition and bounded source-acquisition adapters
implemented; broader pipeline
coverage remains open with explicit gaps in the prepared 0.12.0 scope (#110).
Stable public dependency closure blocks building and publishing that release.
Owner: [uibcdf/sabueso#108](https://github.com/uibcdf/sabueso/issues/108).
Shared boundary: [uibcdf/moli#36](https://github.com/uibcdf/moli/issues/36).
Provider: [uibcdf/ackredit#75](https://github.com/uibcdf/ackredit/issues/75).
Reviewed: 2026-10-03, CI source `383a64b2fdbc5472a7cdeb92c464b87433aabd76`
and independently installed staging source `598abf993a2409c025de5e912acd7eb45a257ebd`.

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
automatically observes built-in UniProt entry/search and Europe PMC
mentions/annotations. Provisional host records `sabueso.source_acquisition@1` in a
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

Complete UniProt/Europe PMC description citations were verified against primary
publication records; missing descriptions and target article/annotation-provider
bibliography remain gaps. The required candidate includes the correction reported
in [Ackredit #78](https://github.com/uibcdf/ackredit/issues/78): explicit CSL corporate
and personal author objects render correctly in BibTeX. Saved-reader consumer
regressions check original metadata in text, CSL-JSON and BibTeX without new credits.
No renderer is copied.

Consumer CI installs the full source commit above and requires real-provider tests
and the public workflow on Python 3.11–3.14. Every runtime CI lane installs the
provider normally and verifies installed imports outside both checkouts. The
provider interpreter contract is corrected under ackredit#80; no Requires-Python
override is used. Ordinary source installation is separate from public artifacts.
`devtools/dependency_routes.toml` inventories this unpublished source route. The
dedicated lanes copy unchanged integration tests to a temporary working directory
and run the public workflow outside both checkouts, exercising installed code.

The provider accepted the portable contract for its prepared 0.9.0 candidate under
Ackredit #75; public delivery remains open. The earlier
[local diagnostic receipt](https://github.com/uibcdf/sabueso/issues/108#issuecomment-5968486124)
is superseded for receiving qualification by the actual staging file below.

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
The hosted descriptor/caller needs are already owned by MolSysSuite #89/#88;
promotion and verified public installation remain Ackredit #22/#75 work. Keep
`dependency_preflight.py --release` blocked and retain source overlays/public-pin
placeholders. Repeat qualification if the bytes change; a version alone is no artifact identity.

## Adoption gates

The staged 0.12.0 preparation is tracked in #110. Its installed-file matrix now
requires provider import/metadata/API checks, the unchanged acquisition/attribution
regressions and the public workflow on every supported OS/minor, outside both
checkouts. This is a prepared gate, not an artifact receipt. Public delivery and a
clean installed frozen 0.3.11 card precede selection of the final candidate.

- Keep Ackredit required in metadata and the recipe. Lazy required import keeps
  saved readers free of backend loading. Missing/broken installations emit SMonitor
  diagnostics and retain failed attribution alongside completed scientific results.
- Results receive attribution automatically; applications own sessions. Libraries enable no import
  hooks, persistence journals, automatic enrichment or reminders.
- Exercise a real provider with two results reusing sources, an enclosing workflow,
  cached/offline and evaluated-empty requests, genuine absence, failure, fresh-process
  lazy import, detached ownership and saved readers without new credit.
- Obtain published provider/dependency closure for every claimed Python minor.
  The pinned provider declares `>=3.11,<3.15`, matching Sabueso's 3.11–3.14 range.
  The portable contract is accepted for prepared 0.9.0; channel publication is pending in
  [Ackredit #22](https://github.com/uibcdf/ackredit/issues/22). The source interpreter
  contract is corrected under [Ackredit #80](https://github.com/uibcdf/ackredit/issues/80);
  the exact staging file has Linux receiver proof but hosted qualification and clean
  public installation remain pending. No public-installation claim follows from
  source, diagnostic or staging tests. The
  accepted API's floor and exact public build pins must be set after the published
  artifact is verified.
- Coordinate the attribution/knowledge/terms boundary in MOLI #36; Ackredit and
  MolSysSuite keep ownership of provider/member contracts and rollout.

The maintainer first requested early integration on 2026-10-02, then chose a hard
dependency and automatic attribution. The initial optional decision is superseded.
`dependency_preflight.py --release` blocks build, staged installed-package and
promotion workflows until normal public closure is verified on Python 3.11–3.14.
The unversioned required metadata does not assert that old tagged APIs suffice.
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
  public closure blocks the next release rather than weakening the product contract.

## Acceptance criteria and resolution

Two public offline packet results retain their own original attribution, including
reused resources, and the application's workflow captures both. Unused sources earn
no credit. Saved readers, absence and provider failures preserve result knowledge.
The local automatic-composition pilot passes; published compatibility and shared boundary
gates remain open. #108 is kept open for remaining acquisition/further-result coverage, complete
bibliography, provider publication and supported-Python closure. This is an initial
runtime integration, not a claim of full pipeline coverage or a public installation route.
