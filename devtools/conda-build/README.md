# Sabueso conda package

Sabueso is distributed through the `uibcdf` conda channel (uibcdf/sabueso#34). The recipe
follows the UIBCDF support libraries: `noarch: python`, with the version frozen from the
X.Y.Z release tag (`freeze_project_version.py`), because conda-build runs on a copy of the
repository.

## Build locally

```bash
conda env create -n sabueso-build -f devtools/conda-envs/build_env.yaml
conda activate sabueso-build
SABUESO_CONDA_VERSION=X.Y.Z conda build devtools/conda-build -c uibcdf -c conda-forge \
    --no-anaconda-upload --output-folder /tmp/sabueso-conda
```

On a tagged commit, `GIT_DESCRIBE_TAG` provides the version and `SABUESO_CONDA_VERSION`
is not needed. The recipe's test imports Sabueso and checks that the installed version
equals the package version.

## Before the first public release

- **Version above 0.2.0.** The `uibcdf` channel already holds `sabueso` 0.0.1–0.2.0
  (2019–2023, Python 3.10 or older, platform-specific builds) from a previous codebase.
  The first release of the current Sabueso must sort after them, so that a pinned or
  unpinned install cannot confuse the two.
- **Publication.** Uploading needs the channel token secret and a release workflow. The
  UIBCDF libraries use `uibcdf/action-build-and-upload-conda-packages`; which staging and
  promotion routes a direct MOLI component adopts is open in uibcdf/moli#7.
- MOLI's release-version, badge and Zenodo policies apply from that release on.
