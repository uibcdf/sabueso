# Source-local upstream prerequisites (#143)

Archived on 2026-10-10 after exact-source qualification of development main.
Published 0.14.0 and historical stored classifications remain unchanged.

Six built-in request gates previously returned `not_found` before any source
access: DISEASES without an Ensembl protein, ClinVar without an NCBI Gene id,
SKEMPI and SAbDab without a PDB cross-reference, MedGen without a usable MedGen
concept id, and MONDO disease identity when the card names no disease.

These gates now raise the existing `RequestPrerequisiteMissing`. The runner
records `not_queried`, unknown knowledge counts and the requested options with the
blocking explanation before client construction or calls. Other Ensembl gene or
transcript identifiers do not substitute for DISEASES's protein prerequisite.
Unsupported organisms retain `not_applicable` before prerequisite checks. MONDO
also remains unqueried when a named condition provides no queryable identity:
text only, an unsupported namespace, a placeholder, or a MedGen concept without
its required UID. A named condition alone cannot trigger source-stated absence.

The generic runner's legacy `NothingToAsk` semantics stay unchanged. Actual queried
empty or missing answers retain `not_found`/`not_stated`, and failures retain
`error`/`unavailable`. Supplied unobserved clients do not invent source operations
or resource credit. Four synthetic fixture cases explicitly preserve completed
empty observations and credit in the already observed DISEASES, ClinVar, MedGen
and MONDO clients. SKEMPI and SAbDab acquisition instrumentation is not added here.

Fifty-one public regression cases cover default and supplied forbidden clients,
request scope, valid request outcomes, actual empty observations, coverage order
and explicit historical refresh. Refresh retains original SourceAssertions and
both historical/corrected pins. Saved reads produce no new acquisition or credit;
DISEASES's tuple/list JSON representation is compared canonically without changing
its stored scientific pin. Existing normal source/mapping tests remain applicable.
The new module also runs outside the checkout in installed public-Ackredit CI.

Local qualification passes: 292 selected cases in 9.18 seconds and all 6,143
local-original offline cases in 163.60 seconds, with 13 expected fixture warnings.
Python 3.14 uses twelve pytest-receptor workers and fatal SQLite/unraisable guards.
Six separate valid-input comparisons preserve exact prechange scientific payloads
and pins. Style, shape/schema (1,627 paths, 0.3.14), source registry, fixture delivery,
dependency preflight, MOLI governance/canonical guide, warning-fatal Sphinx and
201 relative-file links pass. Source `c45af442335bf7f2c0f898b16e3d12637a7c51fd` passes
[15/15 exact-SHA CI jobs](https://github.com/uibcdf/sabueso/actions/runs/38059778704)
and [governance](https://github.com/uibcdf/sabueso/actions/runs/38059778786).
The [source receipt](source_prerequisites_checkpoint.json) independently verifies
all full GH Run Receptor capture members and 13 terminal test summaries:
nine public offline lanes each pass 4,590 cases (10 fixture skips, 26 online
deselections), and four installed public-Ackredit lanes each pass 1,228 cases.
After installing the source editable, 157 cases pass in 5.40 seconds and all six
participating imports/metadata match local checkouts outside the repository.
The qualified producer is `0.14.0+30.gc45af44`; later documentation metadata does
not overwrite its original receipt.

An independent public producer/reader pair outside the checkout retains all twelve
historical and corrected scientific payloads/pins with source access, derivation
and fresh credit forbidden in the reader. A changed runtime version cannot rewrite
stored classifications. Six additional valid-input fixture comparisons preserve
exact scientific payloads and pins of prechange source gates.

This corrects six built-in source gates; it does not establish live source absence, new observation coverage, full installed-artifact
qualification or human/consumer acceptance. No new provider queries, private
fixtures, schema fields or changes to published 0.14.0.

Owning issue: [#143](https://github.com/uibcdf/sabueso/issues/143).
A separate synthetic reproduction finds that historical `disease_grouping@1/@2`
treat the presence of a MONDO enrichment record as proof of a completed identity
query. A blocked MedGen-only condition can still be labelled
`no_stated_equivalence` in those derived views. Versioned coverage correction is
tracked separately in [#144](https://github.com/uibcdf/sabueso/issues/144); this
source-gate change does not reinterpret existing derivation rules.

Derived comparative operation and bibliography work remains
[#108](https://github.com/uibcdf/sabueso/issues/108).
