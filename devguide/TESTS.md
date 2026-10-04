# Sabueso — Tests and Quality Gates

## Running the tests

Agents run pytest through pytest-receptor, as MOLI's developer-tools policy asks
(`MOLI_GUIDE.md`):

Use the Python 3.14 development environment for routine local tests. The
supported 3.11–3.13 interpreters remain in CI and release compatibility gates.

```bash
python -m pytest -m "not online" --receptor=llm   # offline suite, the default
python -m pytest -m online --receptor=llm         # online tests, on demand
```

CI runs the offline suite with `--receptor=ci`. Read the receptor's summary line (`PASS`
or `FAIL`, with the exit code) before doing anything that depends on the result.

## Test kinds

- **Offline tests** (`tests/core`, `tests/ops`, `tests/resolver`, `tests/tools`). They
  need no network, and read frozen public responses from `temp_data/`.
- **Acceptance tests.** Flows on real test systems, TcTIM (P52270) and HsTIM (P60174),
  from public data. Examples: the knowledge baseline (`test_knowledge_baseline_offline`),
  identity hygiene, measurement identity, the structural inventory.
- **Online tests** (`@pytest.mark.online`). Smoke tests against live services. Any test
  that reaches a remote endpoint must carry the mark. Some skip when a service is slow
  or needs a key (BioGRID: `BIOGRID_ACCESS_KEY`).
- **Schema guards.**
  - Frozen cards (`temp_data/frozen_cards/`) of every published card schema must stay
    readable, and must migrate.
  - The recorded card shape (`schemas/card_shape_<version>.json`) must match the cards
    built from the fixtures (`tools/card_shape.py`). An unannounced change fails.
  - `tools/validate_schema.py` keeps `FIELD_PATHS.md` and the schema aligned.
- **Registry guard.** Every source module is an `in_use` entry of
  `sources/registry.yaml`, and the generated page matches it
  (`tools/source_registry.py --check`).
- **Argument contracts.** Every public signature has its digesters
  (`ARGUMENT_CONTRACTS.md`).
- **Installed-package gates.** Release candidates are tested from the exact conda
  artifact, on Linux, macOS and Windows × Python 3.11–3.14, before publication
  (`devtools/conda-build/README.md`). The 0.12.0 gate additionally rejects
  source-shadowed/inconsistent or incomplete Ackredit imports, then runs unchanged
  acquisition/attribution tests and the public saved-reader workflow outside both
  checkouts. Public Pytest/Receptor tooling is installed with Conda; no runtime
  source/pip overlay substitutes for the artifact. Ackredit is pinned to public
  0.9.0/py_0 with its qualified SHA-256; a different digest or staging import fails.
  The preliminary 0.12.0/py_0 file passed all 12 installed lanes, 36 integration tests
  and the public workflow per lane. The producer/archive/matrix and independent
  clean Linux pip-check receipt is
  `devtools/conda-build/receipts/sabueso_0.12.0_staged_2026-10-03.json` (#110).
- **Required Ackredit integration.** `tests/core/test_attribution_offline.py` exercises
  automatic per-result attachment without a collector,
  per-result/workflow reuse, exact support scope, real provider failure, saved readers,
  context isolation and genuine fresh-process absence. All runtime CI lanes
  obtain the required provider from public Conda; dedicated receiving lanes pin
  Ackredit 0.9.0/py_0 on Python 3.11–3.14. No source overlay or Requires-Python
  override remains. The generic preflight's unpublished-provider safeguards are
  retained through synthetic negative rehearsals, independently of current delivery.
  Dedicated lanes run unchanged integration tests and the public workflow outside
  the checkout using installed code and public fixtures. The delivered portable
  minimum is `ackredit>=0.9.0` (ackredit#22/#75/#80).
  Fresh Linux receiving environments at Python 3.11–3.14 run the 36 unchanged
  attribution/acquisition cases, public workflow and pip check with the planned
  exact public core builds. Their artifact/source/installed-byte and origin receipt
  is `devtools/conda-build/receipts/ackredit_0.9.0_public_2026-10-03.json`.
  The consumer is a local wheel with all source modules/resources checked against
  its commit; these are not Sabueso's staged Conda installed-package gates.
  `test_source_acquisition_offline.py` checks automatic card/resolution/one-call
  packet traces, final refresh pins, original versions/hashes, fixtures, archive
  replay/reuse, evaluated-empty access, HTTP absence, missing fixtures, timeouts,
  partial batches, retries, provider/pin-recording failure, separate nested collectors,
  custom-client coverage and saved readers without new credit. Dedicated lanes copy
  these unchanged tests alongside packet-attribution tests outside both checkouts.
  `test_rcsb_acquisition_offline.py` adds native entry revisions (including zero
  minor versions), source citations, differing citation forms, single/batch archive
  reuse, empty/unavailable/unqueried/failure outcomes, chunking, fallbacks, partial
  completed credit, retries and saved readers. CI and the installed matrix copy and
  run it against the public Ackredit floor. The RCSB extension supersedes `py_0`
  with the qualified `7739317`/`py_1` archive: all 12 installed lanes and clean
  public installation pass 56 cases and the three-packet workflow. Publication,
  unchanged promotion, public origins/bytes/API and identical-tag Zenodo are recorded
  in `devtools/conda-build/receipts/sabueso_0.12.0_public_2026-10-04.json`.
  `dependency_preflight.py --release` now passes the adopted public closure;
  stale floors, omitted public pins and future unpublished providers still fail.
  Ackredit #81 tracks the earlier editable Git-version mismatch. The current
  0.9.0-based editable satisfies the floor and the primary environment passes pip
  check; all workspace packages remain editable.

## Unreleased traceability and extraction guards

`test_chembl_acquisition_offline.py` verifies paginated/chunked access, native releases,
original document citations, archive reuse/replay, retries, partial received-page credit,
fixtures, empty answers and failures. `test_rule_literature_extraction_offline.py`
verifies exact namespaces/token boundaries, Unicode offsets, repeated occurrence
support, original rule acquisition, input identity, saved attribution and provider
failure. Both run unchanged outside the checkout in installed-provider CI lanes.

`test_literature_intake_offline.py` adds original support/receipt replay, inert
store and card readers, saved historical pins, refresh without rerunning extraction,
explicit missing-sidecar gaps, alternative fragments, empty fragment scope, provider
failure, exact subject/refused inconsistent closure and terms-profile boundaries.
It also runs unchanged in installed-provider lanes and future staged artifact gates.

`test_pubchem_acquisition_offline.py` covers compound/structure/BioAssay traces,
native per-assay revisions (including zero), caps/chunks, original PubMed pointers,
depositor context, POST-body identity, archive reuse/replay, retries, evaluated-empty
access, rejected inputs, missing fixtures, offline unqueried access and partial
received-row credit after later failures. Public fixture cards, refresh, saved
readers, nested collectors, custom-client gaps and provider failure are exercised.
These tests also run unchanged outside the checkout with public Ackredit 0.9.0.

`test_bindingdb_acquisition_offline.py` covers REST/fixture/mirror queries, native
response/manifest identities, version and cutoff bases, caps/order, DOI/PubMed
forms and host citation preservation, archive reuse/replay, retries, decoded-empty
responses, missing fixtures, offline-unqueried access, original failures and partial
received-data credit. Mirror corruption, public card storage/refresh, nested
collectors, inert readers, provider failure and custom-client gaps are exercised.
The #114 regressions distinguish source-declared empty strings, unexpected status,
malformed/unexpected payloads, default shared-transport retries, archived empty
replay, fixture absence and card-level not-found outcomes without failure warnings.
These tests run unchanged in installed-provider and future staged gates.

`test_disease_explanation_offline.py` checks the five-source public disease group,
selected annotation members, multi-hop MedGen/MONDO support, hierarchy steps,
exact historical card/item pins, missing support, selection/qualifier alternatives,
ungrouped/conflicting identity and unqueried context, inert attribution and argument
validation. Versioned grouping guards (#115) reverse relationship insertion order,
retain converging/conflicting/unfinished MedGen branches, direct naming conflicts,
source/version differences, qualifier alternatives and all hierarchy paths. Explicit
`@1` reproduces the historical lookup/partial explanation at the unchanged card pin;
default `@2` never chooses an ambiguous target. These tests also run unchanged
outside the checkout in installed-provider CI and future staged gates.

`test_knowledge_state_explanation_offline.py` checks exact row/classification
parity, selected and competing support, conflicts, UniProt absence/relationship
coverage, unqueried curation, empty/failure/cut/partial reports, area-specific
Europe PMC counts, original report locators and historical item pins. Missing
field/relationship/conflict support stays partial rather than hiding behind a
derived absence. Original UniProt versions survive reversed support order (#116).
Selectors are digested; readers stay inert. The tests run unchanged outside the
checkout with the public provider and in future staged installed-package gates.

`test_bioactivity_explanation_offline.py` checks public TcTIM/HsTIM group/class
parity, exact source versions, coarser stated precision with units, declared copies,
assay/precision/connectivity selectors, copy-only voters, group disagreement,
cross-group discordance, direct-assay filtering and non-default quantity thresholds.
Ranges, single-point concentrations, unknown units, not-determined measurements,
ambiguity/candidate support, consistency flags, stored identity locators, missing
lineage, historical pins, ArgDigest and inert detached readers have regressions.
The #117 guards cover missing activity-only originals, successful exact pointers,
assay fallback and later statement resolution, both current and historical.
Diagnostic completeness changes neither groups/classes nor original copy support;
readers remain inert, and later acquisition cannot resolve an older pinned card.
The file runs unchanged with public Ackredit outside the checkout in installed
CI and future staged gates. No new source fixture or stored card field is introduced.

`test_ligand_explanation_offline.py` checks public TcTIM/HsTIM native site/crossing
parity, distinct protein/molecule pins, source-stated identity and actual class/name
choices, quantity thresholds, numbering/absent-annotation distinctions and
instance-level spanning. Relevance statements, selected/competing field support,
missing assertions/conflict support, duplicate deck members, historical card/deck
reads, exact selectors and detached inert readers have regressions. The existing
ligand count correction (#118) checks distinct groups across matched molecule/parent
items, declared copies, statement restatements, same-source independence, ambiguity,
discordance, copy-only fallback and assay filtering. Versioned current/legacy counts,
comparisons, exact counted ids, historical source support and ArgDigest have guards.
The file runs unchanged
outside the checkout with public Ackredit and in future staged installed gates.

`test_chemical_identity_acquisition_offline.py` covers CCD batches and both UniChem
lookup methods: normalized iterable queries, POST/wire/decoded identities, original
times and archive references, retries, empty/missing-fixture/offline/failure outcomes,
received subsets before later failures, native source forms and citation roles.
Threaded capture context, molecular resolution, ligand-deck input/result pins,
detached readers, unknown versions, provider/pin failures and custom gaps have guards.
The file runs unchanged in public-provider CI and future staged installed gates.

`test_pdbe_kb_acquisition_offline.py` covers both aggregate queries, native structural
scope and record/count bases, raw return parity, citation roles, original archive
times/wire identities, retries, empty/HTTP-not-found outcomes, unavailable and malformed
fixtures, unqueried offline access, processing failures and concurrent capture.
Card/refresh pins, stored-reader inactivity, provider failure and custom-client gaps
have guards. The file runs unchanged in public-provider CI and future staged gates.

`test_alphafold_acquisition_offline.py` covers model-list queries, native per-record
versions/identifiers, unknown latest versions, historical-version/URL/provider
declarations and citation roles. Original archive times/wire identities, retries,
empty/absent/unavailable/unqueried outcomes, unexpected envelopes, partial lists,
raw return parity, card/refresh pins, saved-reader inactivity, provider failure,
custom gaps and concurrent capture have guards. The file runs unchanged with the
public Ackredit floor in installed-provider CI and future staged gates.

`test_interpro_acquisition_offline.py` covers native family-site residue queries,
signature/member/position context, header/fixture releases (including zero/unknown),
resource-description roles, original archive time/wire/header reuse, transport retries,
empty bodies/objects/HTTP 204, ambiguous absence, HTTP 404 and original failures.
Missing/malformed fixtures, unexpected/partial signature shapes, raw parity,
card/refresh pins, inert saved readers, provider failure, custom-client gaps and
concurrent capture have guards. The file runs unchanged with the public Ackredit
floor in installed-provider CI and future staged gates.

Local diagnostic wheels additionally pass
`devtools/conda-build/check_local_wheel.py <exact-wheel>` before installation (#113):
module/resource bytes and membership must match the source, excluding generated
`_version.py`. The negative regression rejects stale, missing and ghost modules.
Clean local wheel receiving tests are diagnostic evidence, not public Conda delivery.

## Fixtures

- Fixtures are frozen public responses, saved as the source returns them (trimmed only
  when stated).
- Each set is declared in `temp_data/NOTICE.md`: source, what it holds, retrieval date
  and licence. A test checks the declaration.
- No private or pilot data, ever.
- Refetching a fixture can change counts in other tests. Update them as findings, not
  silently.

## Local checks and CI checkpoints

Select checks by the actual changed surface. Run every selected command on its
own and read its exit status. A short documentation or research-evidence commit
does not require the entire offline scientific suite. A change to public or
numerical behavior needs targeted regressions; run the full offline suite at
the next unskipped code checkpoint and inspect the CI run for that exact head.
If a changed area is not covered by a targeted test, add or identify a
meaningful guard before claiming it validated.

Use the relevant commands below:

```bash
ruff format --check .
ruff check .
python -m pytest -m "not online" --receptor=llm
python tools/card_shape.py
python tools/source_registry.py --check
python tools/validate_schema.py
python devtools/moli_governance.py
python devtools/dependency_preflight.py
```

- Python code or tests: Ruff format/check and the affected pytest selectors;
  run the full offline suite before an ordinary code checkpoint is declared
  complete. Source, schema and quantity changes also need their specific
  guards and scientific regression cases.
- Source registry or generated source terms: `tools/source_registry.py --check`.
  Card-shape and schema changes: `tools/card_shape.py` and
  `tools/validate_schema.py`, plus the relevant tests.
- `AGENTS.md`, `MOLI_GUIDE.md` or governance files: `devtools/moli_governance.py`.
  Dependency metadata, Conda environments, recipes or CI acquisition:
  `devtools/dependency_preflight.py` and the relevant package/CI checks.
- Documentation and recorded evidence: validate changed links, examples and
  generated content as applicable; use the docs build below for `docs/` or
  docstring changes. Do not claim a scientific equivalence or package result
  merely because a document check passed.

Keep several exploratory commits local when remote visibility is unnecessary.
For now, `[skip ci]` is limited to authorized direct documentation/evidence
pushes whose applicable local checks pass and whose changes cannot affect
runtime behavior, test inputs, package contents or publication. Code changes
use an ordinary push; Sabueso has no accepted recovery route for skipped code
pushes. Do not use the marker on a PR head with required checks, release
candidate or publication route. A skipped run is not passing evidence.

When `docs/` or a docstring changes, also build the documentation, failing on any
warning. Use the environment of `devtools/conda-envs/docs_env.yaml`, with the checkout
installed:

```bash
sphinx-build -W --keep-going -b html docs <output directory>
```

The API reference renders module docstrings, so a malformed RST list in a docstring
fails this build.

- Run each selected gate on its own and read its result.
- Never pipe a gate through `tail` or `grep`, and never chain a commit after a command
  whose own exit code does not reflect the gate. Both have let a failure through before.
- After an unskipped push, verify CI by the exact commit SHA. Preserve local
  check results and mark deferred remote checks as pending until they run.

## Quality rules for knowledge

- Every selected field has at least one entry in `source_assertion_ids`, and every
  referenced id exists in the card's `source_assertion_store`.
- Relationships cite SourceAssertions present on the card.
- Quantities are stored as `{value, unit}` and sealed. The seal is verified on load.
- Derived knowledge carries its rule. A test fixes each rule's observable behaviour.
