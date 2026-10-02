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
`temp_data/frozen_cards/schema_<version>__P52270.json`. Build it with the candidate's
package: `SABUESO_CONDA_VERSION=X.Y.Z conda build devtools/conda-build
--no-anaconda-upload --output-folder <tmp>`, install it in a clean environment, and
write the card from the fixtures there
(see `devguide/SCHEMA.md`, "Versioning policy", and uibcdf/sabueso#42). From then on,
that schema's recorded shape is fixed.

## Unreleased required dependency gate

The development line now requires Ackredit for automatic packet attribution (#108).
Its portable API has no verified stable public build across Python 3.11–3.14 yet
(ackredit#22/#75/#80). Build, staged installed-package and promotion workflows run
`python devtools/dependency_preflight.py --release` and stop while this dependency
is declared unpublished in `devtools/dependency_routes.toml`. Do not infer public
closure from the source CI candidate or its experimental 3.14 metadata override.
Once the provider publishes, set the actual API floor and exact public build pins,
verify normal clean installs on all supported interpreters, and remove the tracked
source overlay and blocker together. The published 0.11.0 route is unchanged.
