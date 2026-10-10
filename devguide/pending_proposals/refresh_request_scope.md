# Preserve recorded enrichment scope during refresh (#139)

Owner: [uibcdf/sabueso#139](https://github.com/uibcdf/sabueso/issues/139), under
#86/#108/#112; #138 delivered the earlier bounded gnomAD repair.

## Implemented development behavior

Refresh routes through the 24 declared enrichers' 25 exact source/data selectors.
It reads requested scope from quality records, including failed, missing,
unqueried, excluded and inapplicable outcomes. Selected scientific fields never
determine whether a recorded request should be restored. Bespoke protein routes
keep their acquisition/aggregation implementations while restoring their recorded
ChEMBL, BindingDB and PubChem parameters and RCSB structure requests.

New protein records preserve independently copied `request_options` before client
construction/acquisition, including terms exclusions and missing prerequisites.
Only validated supplied flags/dictionaries are recorded, without clients or keys.
An omitted parameter remains omitted: its future client default is not frozen.
The original `structures="all"` remains distinct from an explicit structure list.

Historical restoration uses per-enricher `historical_parameters`: limits, STRING
score (including zero), DISEASES channels and OMA filters when recorded. Explicit
Europe PMC article ids are unioned without changing their request route. Historical
missing arguments are reported, not invented or backfilled. Mixed/conflicting
requests and missing essential known-route ids require explicit overrides before
resolution or source access. Caller flags/dictionaries and disabled requests take
precedence. Unsupported source/data selectors are recorded separately and omitted;
an unsupported provider is never activated from a similar name. ChEMBL copy
pointers remain dependent on the newly requested PubChem results.

Unpublished schema 0.3.14 adds optional `request_options` and the refresh record's
`request_restoration`, using `enrichment_request_restoration@1`. Its rows retain
original record indices/statuses, restored option, status/basis and unrecorded
parameters. Published 0.3.13 and frozen cards are unchanged. These quality records
are explicit-only schema additions, not automatic migration gaps. Refresh keeps
migration history and supplied literature support; `store=` retains both original
and refreshed pins. New acquisitions do not silently import stale old facts.

## Qualification and limits

Public synthetic scope tests cover every declared selector; public frozen-response
rebuilds cover UniRef, filtered/bounded OMA and dependent gnomAD pext/GTEx. They also
exercise source failure, missing prerequisites without client construction, terms
exclusion, overrides, historical missing/contradictory parameters, dependent and
unsupported selectors, exact scientific support and inert stored readers. No new
provider query or private fixture is involved.

Python 3.14.7 / `pytest-receptor`, twelve workers: 77 new cases (76 in the refresh
module and one runner-copy regression), 273 selected cases in 21.83 seconds, and
5,896 full local-original cases in 155.16 seconds. The full checkpoint retains
eleven expected fixture failure/cut warnings in seven groups and passes fatal
unclosed-SQLite/unraisable guards. Ruff, fixture delivery (50 repository inputs /
37 protected originals), 1,627-path additive shape, schema/field-path alignment,
source registry, dependency preflight, governance/canonical guide comparison,
warning-fatal Sphinx, 211 maintained relative links and whitespace checks pass.
The 31 additional recorded shape paths include previously existing filter/cutoff
and migration keys exercised by expanded fixtures; only the request options and
restoration quality records are new stored contracts. No paths were removed.
Code `ff32cb684904910dcd4051def95ebba06120a256` passes
[15/15 CI jobs](https://github.com/uibcdf/sabueso/actions/runs/38034709963) and
[1/1 governance](https://github.com/uibcdf/sabueso/actions/runs/38034709969).
Nine public offline lanes pass 4,343 cases with ten declared skips and 26 online
deselections; four installed public-Ackredit compatibility lanes pass 981 cases.
GH Run Receptor full capture/replay and independent manifest member hashes verify
the exact source; the [public receipt](refresh_request_scope_checkpoint.json)
preserves these results. After editable metadata refresh, 116 scope/migration/
independent-report cases pass, and all six participating imports/metadata agree
outside the checkout.

Private original-answer revalidation reconfirms eight existing original SDK cells
and five actual archived-context refreshes against the current scientific baseline.
An independent inert reader verifies ten original/refreshed pins and 9,094 exact
assertions through sealed states, with thirty individual pin reads and unchanged
active-session credit. Input directories remain unchanged; no provider query or
additional original notebook cell is involved. Detailed receipts remain private.
This slice does not provide frozen client defaults, native release verification,
all molecule/disease refresh routes, new comparative acquisition observation or
bibliography (#108), installed-artifact or human scientific acceptance.
