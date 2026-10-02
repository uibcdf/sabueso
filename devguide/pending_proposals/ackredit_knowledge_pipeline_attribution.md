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

Status: required automatic packet-composition adapter implemented; broader pipeline
coverage and stable public dependency closure remain open and block the next release.
Owner: [uibcdf/sabueso#108](https://github.com/uibcdf/sabueso/issues/108).
Shared boundary: [uibcdf/moli#36](https://github.com/uibcdf/moli/issues/36).
Provider: [uibcdf/ackredit#75](https://github.com/uibcdf/ackredit/issues/75).
Reviewed: 2026-10-02, Ackredit source
`e4a006a6931f3fb5f97be5b09767c144dfb35662`.

## What the consumer needs

A pipeline should retain which sources, datasets and executed software it used,
with citation records for each result and the enclosing application workflow.
Ackredit's provisional `capture`, contextual `track_item`, detached `Attribution`
and `get_attribution` fit this need. Its canonical
[integration guide](https://github.com/uibcdf/ackredit/blob/main/standards/ACKREDIT_GUIDE.md)
owns the provider API; this report records Sabueso's initial use and remaining needs.

Three records have different responsibilities:

| Record | Responsibility |
| --- | --- |
| SourceAssertions and pinned relationships | What sources state and what supports returned knowledge |
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
Ackredit session/captures. It observes no source requests or arbitrary card views.
Query, packet, card and store payloads remain unchanged.

The public offline pilot in `examples/ackredit_pilot/` composes identity and
literature packets for HsTIM from frozen public responses. Both retain reused UniProt
references; only literature credits Europe PMC. Their enclosing workflow holds the
union. Saved JSON readers preserve versions and add no credits. Real-provider tests
exercise reused resources, nested scopes, detached ownership, installed failure,
fresh-process missing required provider diagnostics, lazy import and scientific result parity. Recorded
empty source outcomes do not imply new acquisition. Acquisition/replay/empty request
observation remains the next adapter, not a claimed feature of composition.

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
`devtools/dependency_routes.toml` inventories this provisional source route.

## Adoption gates

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
  Capture APIs are provisional and channel publication is pending in
  [Ackredit #22](https://github.com/uibcdf/ackredit/issues/22). The source interpreter
  contract is corrected under [Ackredit #80](https://github.com/uibcdf/ackredit/issues/80);
  its public-delivery qualification still requires an artifact and clean installation.
  No public-installation claim follows from source tests. The first stable API
  floor and exact public build pins must be set when the provider publishes.
- Coordinate the attribution/knowledge/terms boundary in MOLI #36; Ackredit and
  MolSysSuite keep ownership of provider/member contracts and rollout.

The maintainer first requested early integration on 2026-10-02, then chose a hard
dependency and automatic attribution. The initial optional decision is superseded.
`dependency_preflight.py --release` blocks build, staged installed-package and
promotion workflows until normal public closure is verified on Python 3.11–3.14.
The unversioned required metadata does not assert that old tagged APIs suffice.
Next work observes
actual acquisition boundaries, distinguishes successful/empty/replayed/failed
requests, and expands verified resource bibliography. This change makes no release.

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
gates remain open. #108 is kept open for acquisition/further-result coverage, complete
bibliography, provider publication and supported-Python closure. This is an initial
runtime integration, not a claim of full pipeline coverage or a public installation route.
