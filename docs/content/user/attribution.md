# Automatic traceability and attribution

Since 0.12.0, every completed packet composition attaches
`packet.attribution`. It keeps the resources behind selected stored statements, their
original source-record versions and pins, and the software executing composition.
The records are separate from the packet, its hashes and its terms report.
Traceability is a required Sabueso property. The first source-access slice also
retains automatic acquisition traces for built-in UniProt, Europe PMC and RCSB PDB clients;
its declared gaps prevent a claim of complete pipeline coverage.

The application owns the Ackredit session:

```python
import ackredit
import sabueso

with ackredit.session("my knowledge workflow"):
    with ackredit.capture("workflow") as workflow:
        identity = sabueso.compose_packet(identity_query, card)
        literature = sabueso.compose_packet(literature_query, card)

result_records = [identity.attribution, literature.attribution]
workflow_references = workflow.attribution.to_dict()
```

`card` and both queries are supplied by the application. Each completed composition
gets a record, including resources reused by the preceding result. The application's
workflow collects their union. An optional `sabueso.attribution()` collector retains
records from several compositions. Nested collectors retain their contained
results, and the enclosing context retains those results too. No isolated component
session is created. Composition inside `knowledge_packet` uses the same adapter.

Each record carries:

- `format: sabueso.packet_attribution@1`: a provisional local record for this pilot;
- the packet snapshot, original producer version and its runtime-metadata basis;
- `scope`: pinned statement/relationship support, including conflicts and both legs
  of derived relationships;
- `resources`: source-record identities, explicitly unstated versions as `null`,
  original retrieval/acquisition metadata and contextual uses;
- `bibliography` and `bibliography_gaps`: declared descriptions and missing records;
- `provider`: status, original Ackredit version and detached provider attribution.

`packet.attribution` and a collector's `run.records` return independent copies.
Save them beside the corresponding packets:

```python
import json
from pathlib import Path

Path("result.attribution.json").write_text(json.dumps(result_records[0], indent=2))

saved = json.loads(Path("result.attribution.json").read_text())
original = ackredit.Attribution.from_dict(saved["provider"]["attribution"])
references = original.report(format="csl-json")
text = original.report(format="text")
```

Reading the saved JSON or packet adds no credit. Ackredit's detached reader renders
original records without new registration, source requests or DOI enrichment. Do
not substitute the reader's current version or a current card head for saved pins.
In a source checkout, runtime package metadata can be stale; use an installed
candidate when exact producer-version evidence matters.
The knowledge store and `packet.to_dict()` retain scientific payloads only: a packet
loaded from them has `attribution is None`. Retain and read the original JSON sidecar
alongside it; never manufacture execution attribution while loading saved knowledge.

## Source acquisition

`resolve` and `refresh_card` retain `card.acquisition_trace` and
`resolution.acquisition_trace`. A failed resolution returning no card still has a
trace on its resolution; an escaping exception retains `error.acquisition_trace`.
`knowledge_packet` attaches its intake trace to `packet.acquisition_trace`.
`compose_packet` reads existing knowledge and makes no new acquisition claim.

```python
with ackredit.session("my source workflow"):
    with ackredit.capture("workflow") as workflow:
        card, resolution = sabueso.resolve("P60174")

trace = resolution.acquisition_trace
Path("acquisition.trace.json").write_text(json.dumps(trace, indent=2))
```

These traces observe built-in UniProt entry/search, Europe PMC
mentions/explicit-annotation and RCSB structure clients. The corresponding public source envelopes
add `acquisition_trace` while retaining the original raw `record`. Other sources
and custom clients are explicitly unobserved. A source not asked has no event or
credit. `sabueso.attribution()` can collect the same events as `run.acquisitions`,
separately from completed packet composition in `run.records`.

Each event keeps the query, original producer and source versions, observed route,
original retrieval time, response identity and outcome. Entry versions, service
versions and database releases have distinct bases. Archive reuse/replay retains
original response hashes and retrieval references with no new network attempt.
Fixture reads are local fixture access. Empty answers, actual HTTP absence,
unavailable fixtures, unqueried offline requests and failures remain distinct;
partial failed batches retain their completed transport observations.

Completed access contributes contextual uses and references to the application's
Ackredit capture, including evaluated-empty answers and local replay. A failed or
unqueried access remains in the host trace with provider status `not_attempted`;
it does not claim successful acquisition. Provider or recording failures diagnose
explicit gaps while preserving the scientific return or exception.

Save original JSON beside the scientific objects. The provisional local formats
`sabueso.acquisition_trace@1` and `sabueso.source_acquisition@1` are separate from
card and packet schemas. Payload-only saved readers have `acquisition_trace is None`
and add no execution credit. There is no implicit persistence. MOLI owns future
ProjectRecord/Recorda correlation, routing and recording policy; this local slice
does not establish a complete project record.

## Structural queries and citations

A built-in RCSB lookup records the normalized PDB identifiers and GraphQL request
identities. A batch is one logical acquisition event with `entries` and
`completed_ids`; its `requests` include every chunk, retry and individual or
instance-field fallback. Per-entry outcomes retain received, partial, empty and
failed results without treating a failed entry as acquired. An empty identifier
list is `not_queried`; a missing fixture is `unavailable`. A mixed batch is `partial`
and credits only its completed entries, with failed entries retained in context.

RCSB's native `major_revision`, `minor_revision` and `revision_date` are retained
when stated. Complete entry revisions use `entry_revision`; a batch reports
`per_entry_revision`. Missing revisions remain `not_stated`, with any supplied date
retained as partial metadata. These are entry revisions, never a global database
release: the public RCSB envelope's `version` remains `null`. Archive reuse/replay
retains original revisions, citations, retrieval times and response hashes.
The GraphQL query also requests `rcsb_authors` for primary citations; existing raw
records are returned without tracing edits. Native field names are documented in
RCSB's [data migration guide](https://data.rcsb.org/migration-guide.html).

Completed structural intake credits the RCSB description and each source-stated
primary publication, including DOI/PubMed identifiers, title, authors, year and
journal when supplied. Missing citation metadata is an explicit bibliography gap;
no runtime lookup fills it. Identical citation metadata reuses one reference.
Different source-stated forms retain distinct metadata-based identifiers so that
partial or changed references cannot overwrite earlier ones in the same workflow.
The original per-entry metadata remains in the trace. A structure packet's stored
support credits the RCSB description; save the intake or enclosing workflow record
to retain its original primary-publication references as well.

## Dependency and failures

Ackredit is a required runtime dependency. Importing Sabueso and entering an empty
collector do not load it; composition and completed observed source access
automatically load it and credit their respective uses.
A missing or broken provider in an invalid installation produces
`SABUESO-W-ATTRIBUTION-001`, marks attribution
`failed`, and preserves the completed packet and host record. Missing stored support
marks `support_status: unavailable` and skips provider credit. These statuses never
mean that missing references were successfully collected. A provider failure after
some credits can leave a partial enclosing workflow; inspect the result records and
diagnostics before claiming completeness.

The adapter uses a lazy required import, without DepDigest's optional-library path.
This integration does not enable import hooks, journals, automatic DOI enrichment
or reminders. Ackredit **>=0.9.0** supplies the published portable contract
`ackredit.attribution@1`. Runtime CI installs public Conda dependencies; the receiving
lanes pin public Ackredit 0.9.0/py_0 on Python 3.11–3.14 and run the unchanged
integration tests and public workflow outside both checkouts. Provider delivery
issues [#22](https://github.com/uibcdf/ackredit/issues/22),
[#75](https://github.com/uibcdf/ackredit/issues/75) and
[#80](https://github.com/uibcdf/ackredit/issues/80) are closed. Sabueso 0.12.0 passes its own exact-artifact OS/minor matrix and clean
public installation, with the full receipt in the repository's
`devtools/conda-build/receipts/sabueso_0.12.0_public_2026-10-04.json`.

## Scope and bibliography

The packet adapter observes **composition over stored statements**. The separate
acquisition adapter observes the bounded clients above. Arbitrary card views,
other sources and further result types remain open in
[Sabueso #108](https://github.com/uibcdf/sabueso/issues/108). Neither adapter infers
a new download from stored card provenance or a failed request.

Full and index packets use the same stored-support closure as packet terms. Unused
statements receive no credit. Exact unrecorded mapping lineage cannot be recovered:
disease grouping includes broader stored MONDO/MedGen identity and hierarchy context.
The record says so. A resource's version is its source-record version, not an inferred
global database release.

The offline resource-description declarations were verified on 2026-10-02/04:

- UniProt's [recommended citation](https://www.uniprot.org/help/publications), with
  complete metadata from the [original paper](https://academic.oup.com/nar/article/53/D1/D609/7902999):
  *UniProt: the Universal Protein Knowledgebase in 2025*, DOI `10.1093/nar/gkae1010`.
- Europe PMC's *Europe PMC in 2023*, with the full 22-author list and metadata from
  [the publication record](https://pubmed.ncbi.nlm.nih.gov/37994696/), DOI
  `10.1093/nar/gkad1085`. Its bibliographic year is 2024; the title is not its year.
- RCSB's [citation policy](https://www.rcsb.org/pages/policies) recommends
  *Updated resources for exploring experimentally-determined PDB structures and
  Computed Structure Models at the RCSB Protein Data Bank*, DOI
  `10.1093/nar/gkae1091`. The full 51-author metadata comes from the
  [publisher-deposited Crossref record](https://api.crossref.org/works/10.1093/nar/gkae1091).
  Its bibliographic issue year is 2025, distinct from its online publication date.
- Sabueso's software metadata comes from its `CITATION.cff`, using the project
  concept DOI and the executing package's version. A preceding release's version DOI
  is not attached to an unreleased checkout.

Other resource descriptions are explicit gaps. Target publications and annotation
providers also need their own citations; a service-description paper does not replace
them. No missing authors, dates or release identifiers are invented. Terms and
fragment reuse rights are answered separately by the terms report.

CSL-JSON, text and BibTeX preserve the corporate UniProt author. The published minimum includes the provider's correction for explicit CSL author objects
([Ackredit #78](https://github.com/uibcdf/ackredit/issues/78)); saved-reader regression
tests check corporate-name grouping and Europe PMC's personal names without new credit.

The complete runnable public workflow is in `examples/ackredit_pilot/`, using only
the frozen public HsTIM fixtures declared in `temp_data/NOTICE.md`.
