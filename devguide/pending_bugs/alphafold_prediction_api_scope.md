---
summary: Keep AlphaFold prediction-API misses separate from database-wide absence and expose the retained query scope.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-05
verification: bounded_public_probe_and_selected_receiving
area: [source-access, predicted-structures, human-exploration]
---

# AlphaFold prediction API: distribution and absence scope

## Observed problem and bounded correction

The genuine Q8WZ42 prediction request retained by the preceding fragment review
returned HTTP 404 and the two-byte body `{}`. AlphaFold's
[download documentation](https://alphafold.ebi.ac.uk/download) and
[EMBL-EBI access guide](https://www.ebi.ac.uk/training/online/courses/navigating-alphafold-database/what-is-the-afdb/accessing-searching-afdb/)
state that long human-protein fragments are distributed through proteome archives.
An API miss therefore cannot establish their database-wide absence.

Pre-fix source `8dbfec7`, actual SDK `0.14.0+175.g8dbfec7`, says
`AlphaFold DB has no model for Q8WZ42`. The enricher suppresses the not-found
detail, so a newly built coverage row also lacks the explanation of what was
actually consulted. The original exception/trace, synthetic-counterfactual public
P52270 Card and saved coverage are retained before editing the implementation.
This is an original implementation control, not a claim that P52270 lacks a model.

The correction scopes messages to the prediction API or missing supplied fixture,
retains the API miss detail on new enrichment records, and records
`structural_context.access_scope` on new acquisition events. It identifies the
route, unqueried alternative distributions and unestablished global absence.
Text/HTML coverage shows the original retained detail in **Source/request scope**;
full details remain inspectable. Native state rules, count mechanisms, public
client error classes, retry behavior, source assertions and model rules remain
unchanged. No archive fallback,
coordinate download or new request is started implicitly.

Empty arrays, malformed/unobserved envelopes, HTTP404 and missing fixtures retain
their separate acquisition outcomes. A new Card built with the known fixture
client's missing input now records an enrichment error and `unavailable`, rather
than source-stated absence. The public fixture client still raises its existing
`RecordNotFoundError`; the enricher converts this input gap to its existing
connector-failure path. A retained empty fixture list remains a received empty
input and `not_stated`. Archive replay keeps original wire/request
facts while applying the current client's diagnostic. Saved exploration instead
preserves its original retained interpretation: an old missing detail is not
backfilled from current knowledge or a new provider request. Earlier verifiers,
capsules and published schemas remain unchanged.

## Current source contract and outstanding public fragment receiving

One additional bounded P52270 metadata GET on 2026-11-05 returns HTTP200,
1,962 original bytes, SHA256
`f4a42682a479b14597601351fa5cec6402ee8287c7edb86f30f1100deb193917`.
Its decoded content equals the existing declared public P52270 fixture; byte
formatting differs and the original fixture is preserved. This receives current
metadata availability, not an acquisition/scientific acceptance claim for every
route or protein.

The source currently co-serves `uniprotStart`/`uniprotEnd` and
`sequenceStart`/`sequenceEnd`. Its
[published deprecation notice](https://www.ebi.ac.uk/pdbe/news/breaking-changes-afdb-predictions-api)
announces the latter names, but a current outage from that rename is **not**
observed. A modern-only range record is a separate compatibility prerequisite;
the current range interpreter still uses the old names. Do not silently rewrite
source records or the original versioned model rules to implement it.

The genuine partial-model input remains pending. A native archive model or
BigQuery record is not automatically the prediction-API contract: the
[original BigQuery schema](https://github.com/google-deepmind/alphafold/blob/main/afdb/README.md)
defines its checksum as CRC64, whereas this model context uses API MD5.
No synthetic API record substitutes for those originals. Complete a bounded,
source-specific intake and the original interval/sequence/identity bases before
claiming the real-fragment journey qualified. This does not close B3 or resume
0.15.0 consolidation; B2 scientific review remains deferred.

## Receiving and experience review

The owning acquisition gate covers route-scoped HTTP404, empty versus unobserved
responses, fixture availability, exact replay facts, preserved public model
content, retained Card/human/agent detail and inert saved reading. The complete
module already runs in both installed receiving routes. Broader source/knowledge/
enrichment/coverage/history/diagnostic gates and exact-source CI are recorded
separately in the [dated receipt](../evidence/alphafold_prediction_api_scope_20261105.json).

Observed improvement: the missing result now explains its acquisition scope and
shows it in the coverage table, without requiring the researcher to know native
paths. The old saved gap remains explicit. Independent researcher acceptance,
genuine archive fragment intake and whole-session workload acceptance are still
pending. Owned original wire/control/receipts are in
`recovered_work/alphafold_public_contract_20261105/`, owner #148/#173/#112, review
at hosted completion or the next source/structural review.
