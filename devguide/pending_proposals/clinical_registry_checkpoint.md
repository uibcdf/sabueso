---
summary: Local clinical registry/reference qualification and reproducible resumption.
issue: uibcdf/sabueso#108
status: open
opened: 2026-10-06
closed:
verification: local_runtime_tested
area: [source_access, attribution, bibliography]
blocked_by: []
supersedes: []
related: [uibcdf/sabueso#112, uibcdf/sabueso#127, uibcdf/sabueso#128]
---

# Clinical registry and bibliography checkpoint

Updated 2026-10-06. This is the latest bounded local slice; the published release
remains 0.13.0. The diagnostic receipts below were produced locally from
`c1bab2d` plus uncommitted changes. Those changes are included in the maintainer-
authorized implementation checkpoint; current remote verification is recorded
in `CHECKPOINT.md`. Historical wheel versions/hashes remain unchanged.
The [resume section](../CHECKPOINT.md#resume-here) and
[immediate roadmap](../ROADMAP.md#immediate-resumption-sequence) own current priorities.

## Implemented scope

- `core/clinicaltrials_acquisition.py` observes built-in study/reference operations
  under `clinicaltrials_registry_observation@1`: native logical/normalized queries,
  version/page/entry scope, decoded hashes, all continuation pages, original times,
  reuse, empty/unavailable and partial/failure outcomes.
- `tools/db/clinicaltrials.py` fixes omitted pagination, malformed responses interpreted
  as absence, unavailable fixtures, contradictory duplicate NCT records and consumed
  generators (#127). `get_study_references` and online/fixture `study_references`
  ask for reference modules independently of the frozen clinical card fields.
- `core/clinicaltrials_bibliography.py`, source acquisition and attribution bibliography
  preserve registry records plus native PMID/citation/retraction/see-also/IPD pointers,
  differing forms and exact occurrences. Roles distinguish registry records from
  source-cited references. Linked targets are not followed; free citations are not
  parsed into identity, author, title, date or DOI metadata.
- Explicit Europe PMC queries contribute their own original metadata and complete
  returned personal/collective authors. `article_metadata.py` fixes the collective
  author projection (#128). Scientific clinical SourceAssertions, raw successful
  records and frozen schema 0.3.12 remain unchanged.
- Public fixtures: native NCT00123916 references and separate metadata for native
  PMID 18585495, 26323937 and 19753491, all declared in `temp_data/NOTICE.md` with
  wire identities and version/permission bases. No full text or participant data.
- CI and staged installed gates copy/run the clinical registry test unchanged;
  existing article-metadata gates include collective-author regressions.

## Qualification receipts

Primary Python: `/home/diego/Myopt/miniconda3/envs/molsyssuite@uibcdf_3.14/bin/python`
(3.14.7). All 14 workspace distributions were verified editable, importing their
local checkouts outside the repository. Runtime/distribution Sabueso versions agree.

The 178 targeted clinical/source-envelope/article/fixture cases pass in 19.52 seconds
through `--receptor=llm`. Ruff check passes. Schema alignment and recorded card shape
pass at 0.3.12; registry/generated resources, local governance, dependency preflight
and workflow YAML/copy/execution binding checks pass. Original disease `@1`–`@5`
bundles read with installed code without source access, derivation, admission,
receipt modification or new credit.

Diagnostic local wheel:
`/tmp/sabueso-clinicaltrials-wheel/sabueso-0.13.0+1.gc1bab2d.dirty-py3-none-any.whl`.
SHA-256: `c4e2d66047e40822ac480b5d5f3c64b1dd2ca1a96a51d7a413624be41b0f3e76`.
Size: 626999 bytes. All 393 non-version Python/JSON package files match checkout
and installed bytes. Nineteen test modules are copied unchanged outside the checkout.
Installed receiving environment: `/tmp/sabueso-state-122-installed-v2`, with public
Ackredit 0.9.0, PyUnitWizard 0.27.0 and pytest-receptor 1.2.0. Imports resolve to its
site-packages; its `pip check` passes. This is local Linux/Python 3.14 qualification,
not remote CI or the staged Conda OS/minor matrix.

Final full offline gate passes **2272 cases**, with 26 online cases deselected,
in 693.93 seconds. Six expected fixture-failure/truncation warnings remain.
Ruff format/check pass (712 formatted files); warning-fatal Sphinx passes. The
20 local checkpoint/roadmap/index links and anchors resolve, and the exact user-guide
registry/article workflow executes against the declared public fixtures.

The first installed 19-module run passed 546 cases and failed four (456.05 seconds):
the temporary client lacked the four new fixtures and the licensing document needed
by an added licensing test. The package itself already matched the exact wheel.
Copying the complete declared public fixture tree and licensing document corrected
this setup. The unchanged five-module clinical/source-envelope/article/fixture gate
then passed **178 cases in 19.50 seconds**, including all four previously failing
cases, with public Ackredit 0.9.0. The other 546 results and the corrected affected
gate provide the receiving coverage; the entire 19-module gate was not repeated.
Future requalification must copy all current fixtures, not reuse an older client
subset. CI uses the complete fixture tree and the staged gate copies it.

## Shared environment discrepancy

The current primary-environment `pip check` fails, superseding earlier passing
receipts. These installed external requirements are currently inconsistent:

- `packmol-memgen 2026.3.25` and `proprep 1.0.0` need missing `pdb2pqr`.
- `ndfes`, `fetkutils` and `edgembar` 3.6.5 require `numpy<2`; installed is 2.4.6.
- `proprep 1.0.0` requires `numpy>=1.26,<2` and `biopython>=1.83,<1.86`;
  installed Biopython is 1.88.

All 14 workspace editable imports still pass. No shared package versions were
changed to resolve unrelated tool requirements; diagnose their owning distribution
and compatibility separately. The clean receiving environment passes its own check.

## Resume constraints and remaining work

Routine development checks use the receptor and the declared shared Python:

```bash
python -m pytest tests/core/test_clinicaltrials_acquisition_offline.py tests/core/test_clinical_offline.py tests/core/test_source_access_offline.py tests/core/test_article_metadata_offline.py tests/core/test_fixture_licensing_offline.py -m "not online" --receptor=llm
python -m pytest -m "not online" --receptor=llm
```

For installed requalification, the durable copy/execution recipes are in
`.github/workflows/ci.yml` and `.github/workflows/test_staged_conda_package.yaml`.
Use their outside-checkout client layout and public-provider floor; a new release
must follow `devtools/conda-build/README.md`, not substitute this diagnostic wheel
for its exact staged Conda artifact. Run applicable schema, registry, formatting,
governance, dependency and documentation gates separately as listed in `../TESTS.md`.

Do not replace accumulated local code or genuine historical receipts. `/tmp`
environments/artifacts may disappear; code, tests, public fixture declarations,
checks and this receipt are the durable requalification route. Use the environment
and gates in `../TESTS.md`; qualification must use installed imports outside the
checkout with the public Ackredit minimum. Rebuild a diagnostic artifact if needed
and compare package bytes before making an installed-code claim.

Owner issues #127/#128 have final local implementation/test receipts and still need delivered-code
verification; keep them open until delivery. #108/#112 cover the wider remaining
work. Recorded receipts: [client integrity #127](https://github.com/uibcdf/sabueso/issues/127#issuecomment-6012209247),
[collective authors #128](https://github.com/uibcdf/sabueso/issues/128#issuecomment-6012209679),
[traceability #108](https://github.com/uibcdf/sabueso/issues/108#issuecomment-6012210029)
and [roadmap/resumption #112](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6012210391).
Source-level observation does not automatically revise the saved disease
example: its current manifest stays `@5`. The next integration needs explicit NCT/
PMID scope, a versioned example and original sidecars through readers/reacquisition.
Broader bibliography, fine terms filtering, non-protein packet contracts and shared
MOLI/Recorda guarantees remain separate work; see the immediate roadmap.
