# Public offline Ackredit pilot

This development workflow composes identity, literature and structure packets for
public HsTIM (P60174), using the frozen public UniProt entry, RCSB 1HTI/1KLG entries
and explicitly located Europe PMC annotations declared in `temp_data/NOTICE.md`.
It contains no private vertical-pilot content.

From the repository root, in the editable development environment:

```bash
python -m examples.ackredit_pilot.run --output /tmp/sabueso-ackredit-pilot
```

Ackredit >=0.9.0 is required. Runtime CI obtains it from public Conda; dedicated
receiving lanes pin its published 0.9.0/py_0 build on Python 3.11–3.14. The pilot and
unchanged integration tests run outside both checkouts against installed code and
public fixtures. Sabueso's staged Conda artifact receives its own full OS/minor
qualification before publication.

The output contains a knowledge store, the original `acquisition.trace.json`,
three detached result-attribution records, result references in text/CSL-JSON/BibTeX,
intake references and the application's original workflow attribution/references.
Results retain reused knowledge. Structural intake preserves RCSB's original
primary citations and credits the resource description. The old public fixtures
state neither entry revisions nor primary authors: those remain explicit gaps;
synthetic HTTP regression tests exercise the newly queried native metadata.
The workflow contains the union of intake and composition references. Saved readers
render the original records without source requests, provider registration or new
execution credit. No collector is required to activate automatic attribution.

Traceability is required. Built-in UniProt entry/search, Europe PMC
mentions/annotations and RCSB single/batch structure clients preserve queries,
versions, original response identities, reuse/replay, empty answers and failures.
RCSB batches retain per-entry outcomes and every transport fallback. Other sources
and custom clients are explicitly unobserved. The packet adapter observes completed
composition over pinned stored statements. Bibliography does not grant reuse rights;
target article/annotation-provider bibliography remains incomplete.
See `docs/content/user/attribution.md` for coverage and citation metadata sources.

Card/packet payloads have no runtime trace. This workflow saves original JSON beside
them. MOLI ProjectRecord/Recorda routing remains future platform work. The published
provider includes the corporate-author BibTeX correction (Ackredit #78).
