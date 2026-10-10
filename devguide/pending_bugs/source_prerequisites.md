# Source-local upstream prerequisites (#143)

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
201 relative-file links pass. Exact-source remote qualification is pending. This corrects six built-in source gates; it does not
establish live source absence, new observation coverage, full installed-artifact
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
