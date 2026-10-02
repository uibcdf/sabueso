# Optional packet attribution

In development after 0.11.0, `sabueso.attribution()` observes completed packet
composition. It keeps the resources behind selected stored statements, their
original source-record versions and pins, and the software executing composition.
The records are separate from the packet, its hashes and its terms report.

The application owns the Ackredit session:

```python
import ackredit
import sabueso

with ackredit.session("my knowledge workflow"):
    with ackredit.capture("workflow") as workflow:
        with sabueso.attribution() as run:
            identity = sabueso.compose_packet(identity_query, card)
            literature = sabueso.compose_packet(literature_query, card)

result_records = run.records
workflow_references = workflow.attribution.to_dict()
```

`card` and both queries are supplied by the application. Each completed composition
gets a record, including resources reused by the preceding result. The application's
workflow collects their union. Nested Sabueso contexts retain their contained
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

`run.records` returns independent copies. Save them beside the corresponding packets:

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

## Activation and failures

Ordinary composition and empty attribution contexts never import Ackredit or load
the bibliography. When attribution is enabled and Ackredit is absent, host records
still retain source support and declared bibliography, with `provider.status: absent`.
A broken installed provider produces `SABUESO-W-ATTRIBUTION-001`, marks attribution
`failed`, and preserves the completed packet and host record. Missing stored support
marks `support_status: unavailable` and skips provider credit. These statuses never
mean that missing references were successfully collected. A provider failure after
some credits can leave a partial enclosing workflow; inspect the result records and
diagnostics before claiming completeness.

Ackredit is optional and lazy through DepDigest. This pilot does not enable import
hooks, journals, automatic DOI enrichment or reminders. Its reviewed capture API is
provisional; channel publication and Python 3.14 compatibility remain open. No public
installation extra is claimed yet. CI installs a tracked source candidate and tests
the real provider on Python 3.11–3.13; ordinary Sabueso CI retains 3.11–3.14.

## Scope and bibliography

The initial adapter observes **composition over stored statements**. It does not
observe source acquisition, resolve-only calls, arbitrary card views or every
resource of a pipeline. It does not infer a new download from card provenance,
replay metadata, an evaluated-empty outcome or a failed request. Source acquisition
is a separate next adapter in [Sabueso #108](https://github.com/uibcdf/sabueso/issues/108).

Full and index packets use the same stored-support closure as packet terms. Unused
statements receive no credit. Exact unrecorded mapping lineage cannot be recovered:
disease grouping includes broader stored MONDO/MedGen identity and hierarchy context.
The record says so. A resource's version is its source-record version, not an inferred
global database release.

The initial offline resource-description declarations were verified on 2026-10-02:

- UniProt's [recommended citation](https://www.uniprot.org/help/publications), with
  complete metadata from the [original paper](https://academic.oup.com/nar/article/53/D1/D609/7902999):
  *UniProt: the Universal Protein Knowledgebase in 2025*, DOI `10.1093/nar/gkae1010`.
- Europe PMC's *Europe PMC in 2023*, with the full 22-author list and metadata from
  [the publication record](https://pubmed.ncbi.nlm.nih.gov/37994696/), DOI
  `10.1093/nar/gkad1085`. Its bibliographic year is 2024; the title is not its year.
- Sabueso's software metadata comes from its `CITATION.cff`, using the project
  concept DOI and the executing package's version. A preceding release's version DOI
  is not attached to an unreleased checkout.

Other resource descriptions are explicit gaps. Target publications and annotation
providers also need their own citations; a service-description paper does not replace
them. No missing authors, dates or release identifiers are invented. Terms and
fragment reuse rights are answered separately by the terms report.

CSL-JSON and text preserve the corporate UniProt author. BibTeX rendering of explicit
author objects is currently defective in the inspected provider
([Ackredit #78](https://github.com/uibcdf/ackredit/issues/78)); the public pilot retains
the original metadata and does not export BibTeX until the provider is corrected.

The complete runnable public workflow is in `examples/ackredit_pilot/`, using only
the frozen public HsTIM fixtures declared in `temp_data/NOTICE.md`.
