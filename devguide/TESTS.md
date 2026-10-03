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
  (`devtools/conda-build/README.md`). The prepared 0.12.0 gate additionally rejects
  source-shadowed/inconsistent or incomplete Ackredit imports, then runs unchanged
  acquisition/attribution tests and the public saved-reader workflow outside both
  checkouts. Public Pytest/Receptor tooling is installed with Conda; no runtime
  source/pip overlay substitutes for the artifact. Provider public pins remain
  pending, so this prepared matrix is not an installed-file success receipt (#110).
- **Required Ackredit integration.** `tests/core/test_attribution_offline.py` exercises
  automatic per-result attachment without a collector,
  per-result/workflow reuse, exact support scope, real provider failure, saved readers,
  context isolation and genuine fresh-process absence. CI installs a tracked full
  source commit in every runtime lane, without skipping provider tests. Python
  3.11–3.14 use normal source installs under the provider's corrected interpreter
  contract (ackredit#80), without metadata overrides. The source candidate is not
  a public-channel installation claim. The preflight rejects required source
  candidates whose interpreter range excludes a supported Sabueso minor or whose
  workflow installation bypasses Requires-Python.
  Dedicated provider lanes run the unchanged integration tests and public workflow
  outside both checkouts, using installed consumer/provider code and public fixtures.
  The portable contract is accepted for prepared 0.9.0; source-installed CI and
  independent exact-staging-file receiving proof remain distinct from public delivery.
  Fresh Linux receiving environments at Python 3.11–3.14 run the 36 unchanged
  attribution/acquisition cases, public workflow and pip check with the planned
  exact public core builds. Their artifact/source/installed-byte and origin receipt
  is `devtools/conda-build/receipts/ackredit_0.9.0_staging_2026-10-03.json`.
  The consumer is a local wheel with all source modules/resources checked against
  its commit; these are not Sabueso's staged Conda installed-package gates.
  `test_source_acquisition_offline.py` checks automatic card/resolution/one-call
  packet traces, final refresh pins, original versions/hashes, fixtures, archive
  replay/reuse, evaluated-empty access, HTTP absence, missing fixtures, timeouts,
  partial batches, retries, provider/pin-recording failure, separate nested collectors,
  custom-client coverage and saved readers without new credit. Dedicated lanes copy
  these unchanged tests alongside packet-attribution tests outside both checkouts.
  `dependency_preflight.py
  --release` blocks build, staged installation and promotion until the stable
  provider API and public dependency closure are verified (#108, ackredit#22/#75).

## Fixtures

- Fixtures are frozen public responses, saved as the source returns them (trimmed only
  when stated).
- Each set is declared in `temp_data/NOTICE.md`: source, what it holds, retrieval date
  and licence. A test checks the declaration.
- No private or pilot data, ever.
- Refetching a fixture can change counts in other tests. Update them as findings, not
  silently.

## Local gates before a commit

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

When `docs/` or a docstring changes, also build the documentation, failing on any
warning. Use the environment of `devtools/conda-envs/docs_env.yaml`, with the checkout
installed:

```bash
sphinx-build -W --keep-going -b html docs <output directory>
```

The API reference renders module docstrings, so a malformed RST list in a docstring
fails this build.

- Run each gate on its own and read its result.
- Never pipe a gate through `tail` or `grep`, and never chain a commit after a command
  whose own exit code does not reflect the gate. Both have let a failure through before.
- After pushing, verify CI by the commit SHA.

## Quality rules for knowledge

- Every selected field has at least one entry in `source_assertion_ids`, and every
  referenced id exists in the card's `source_assertion_store`.
- Relationships cite SourceAssertions present on the card.
- Quantities are stored as `{value, unit}` and sealed. The seal is verified on load.
- Derived knowledge carries its rule. A test fixes each rule's observable behaviour.
