# Conda publication routes

Sabueso builds one `noarch: python` artifact for Python 3.11–3.14.
The recipe freezes the exact Conda version into the ephemeral build source;
the repository's dynamic `versioningit` configuration remains unchanged.
The build workflow accepts either a reviewed direct release or an immutable
staging candidate, as selected in `release_plan.toml`.

Before a release, update the plan to the proposed three-part version and
record the route, reason, reviewer, and required exact-commit workflows.
Sabueso's full matrix (`ci.yml`: Ruff and the offline suite on Python 3.11–3.14)
and the MOLI governance check (`moli-governance.yml`) are required. Run them at the final candidate SHA. A direct route is appropriate
only when no pre-public installed-artifact or coupled-consumer gate is needed;
the registry must confirm that the version is unoccupied. A staged route is
required for a new interpreter, dependency, packaging contract, or other
change that needs clean installed-package evidence before public visibility.

Before any candidate build, `python devtools/dependency_preflight.py --release` must pass. It is a
read-only check that the recipe, every environment installing the runtime, and the
exact public builds pinned by the staged-package test agree with `pyproject.toml`
(`devtools/dependency_routes.toml`, #76). CI's quality job runs the development check
without `--release`, allowing only explicitly inventoried required source candidates
while reporting their release blockers.

**Immutable coordinates (#78).**
- A Conda file coordinate (`uibcdf/sabueso/<version>/noarch/<filename>`) is never
  overwritten, under any label, even with the same bytes.
- Before a staged upload, `release_route.py coordinate` refuses a coordinate the
  registry already holds. A corrected build needs a new build number or version. The
  direct route refuses any existing file of the version.
- After promotion, `release_route.py poststate` queries the registry read-only, with
  bounded retries. The exact coordinate must carry the `main` label and the tested
  SHA-256. The result is kept as a receipt (`sabueso-conda-poststate-*`).
- A red poststate is diagnosed with read-only queries, never with another upload or
  promotion.

For the staged route, dispatch
`.github/workflows/build_and_upload_conda_packages.yaml` with the exact
`candidate_sha`, `version`, and `build_number` (normally zero). It uploads
only to `uibcdf/label/staging` and retains the route and producer receipts.
Then dispatch `.github/workflows/test_staged_conda_package.yaml` with the
same coordinates and successful staging run ID. Before any installation, it downloads
the exact staged file and inspects it (`verify_staged_install.py archive`, #77): its
digest against the producer receipts, the version it embeds (`info/index.json`,
`_version.py` and the `dist-info` metadata), and the package-critical resources
(`REQUIRED_RESOURCES`: the packaged selection rules and enrichment profiles). This is
the only claimed public route (the `noarch` conda package); Sabueso publishes no wheel. The gate checks artifact
digest, source channel, public dependency provenance, package version, and
an API smoke test (a card whose quantities are sealed by `to_dict()` and verified by
`from_dict()`) in clean Linux, macOS Apple Silicon (arm64) and Windows
environments for Python 3.11–3.14, with the
public SMonitor, PyUnitWizard and DepDigest builds.
The installed check also rejects an Ackredit import from a source checkout,
inconsistent provider metadata or missing portable capture/reader APIs. Each
installed lane then runs the unchanged acquisition/packet-attribution regressions
and public offline workflow outside both checkouts, using only copied public
fixtures and the installed provider/consumer. Pytest and published Pytest Receptor
are gate tooling; no runtime source overlay or pip replacement is installed.
Do not publish a stable GitHub Release until every cell passes.

For a staged release, the release event verifies the plan and does not
rebuild. Dispatch `.github/workflows/promote_conda_package.yaml` only after
the stable GitHub Release exists, using the independently verified digest.
It promotes the exact staged file to the public channel and checks the public
record. For a direct route, the release event builds and uploads once to
`main`, then independently checks the public file's digest.

This mechanism mirrors PyUnitWizard's (uibcdf/pyunitwizard), as MOLI's distribution
policy expects of every component (uibcdf/sabueso#34). The local verification build
described in `meta.yaml` (`SABUESO_CONDA_VERSION=X.Y.Z conda build ...`) is never
uploaded.

Before documenting any installation route, verify a clean installation from the public
channel; staging and source tests alone are not publication.

## Card schema at release

The release notes state the card schema the release writes. If the release publishes a
card schema no earlier release published, add its frozen card before tagging:
`temp_data/frozen_cards/schema_<version>__<public accession>.json`. Build it with
the candidate's package: `SABUESO_CONDA_VERSION=X.Y.Z conda build devtools/conda-build
--no-anaconda-upload --output-folder <tmp>`, install it in a clean environment, and
write the card from the fixtures there
(see `devguide/SCHEMA.md`, "Versioning policy", and uibcdf/sabueso#42). From then on,
that schema's recorded shape is fixed.

## Delivered required provider

Ackredit 0.9.0/py_0 is public, carrying the first published portable attribution
contract (#108; ackredit#22/#75/#80). Metadata, recipe and environments require
`ackredit>=0.9.0`; CI uses public Conda without a source overlay. The installed-file
matrix pins the public build and rejects any other archive digest:
`37661090f6ad19a74b8155d8a4d4b4a068c9099f4ceba0743b3abfe887e97fe1`.
The public bytes match the previously independently verified staging file.

Provider installed run 37152044426 covers Linux/macOS arm64 × Python 3.11–3.14;
promotion 37152421084 preserves the archive. Independent receiving compatibility
on all four Linux minors passes the 36 tests, public workflow and pip check with
Sabueso's planned exact public core pins. Staging/public receiving receipts remain
separate from Sabueso's actual Conda candidate qualification. `dependency_preflight.py
--release` passes the adopted closure; it retains generic future-provider guards.
The primary workspace keeps editable packages; provider #81 owns its Git-derived
version mismatch with the published minimum.

## Prepared 0.12.0 scope (#110)

`release_plan.toml` selects 0.12.0 and the staged route;
`release_notes_0.12.0.md` contains the reusable draft. The preliminary local
Conda candidate at `01d5bf2` passes installed checks on all four Linux minors
and supplies `schema_0.3.11__P60174.json` from its clean Python 3.14.7 install.
The local artifact/hash, source, public pins, regressions and schema-freeze receipt
are in `receipts/sabueso_0.12.0_local_schema_freeze_2026-10-03.json`.
No staging or publication receipt is claimed by this local qualification.

The preparation includes the exact qualified builder
`8da628d9b393e184c3bf3722708b19dcfbf7ef0a`, retaining upload, immutable coordinate,
producer-receipt and promotion contracts. Provider #46/#47 and the MolSysSuite #78
handoff supply environment-aware compilation qualification; this pin adoption is
not an actual Sabueso staged-build receipt.

Before selecting the final candidate:

1. Provider delivery is verified and adopted: minimum 0.9.0, public build/hash,
   compatible public core pins and no source overlay. Re-run
   `dependency_preflight.py --release` before every build/installed/promotion route.
2. Build a local, unpublished candidate Conda file and install it in a separate
   clean environment. Generate the 0.3.11 frozen public card from that installed
   code, record its candidate/fixture/version/licence receipt in `temp_data/NOTICE.md`,
   and commit it. Do not freeze a card from the editable workspace.
3. Review the final notes and `CITATION.cff`, which follows the planned version
   and retains the concept/historical DOIs. Its optional publication date stays
   unset while qualifying the candidate; the release and archive record the actual
   publication date.
   Run local gates, inspect exact final-SHA CI/governance and confirm the registry
   coordinate before dispatching the staged build.
4. Inspect the staged archive and complete Linux/macOS/Windows × Python 3.11–3.14
   installed gates, including required-provider regressions.
5. Then publish the stable GitHub release, promote the tested file, verify a clean
   public install and archive the identical tag on Zenodo.

Broader source/result coverage, undeclared bibliography and Recorda integration
remain issue-backed work with explicit release limits. This bounded scope retains
the required traceability target without asserting full pipeline provenance.
