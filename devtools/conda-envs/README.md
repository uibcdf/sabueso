# Development environments and the required Ackredit source candidate

The runtime authority is `pyproject.toml`. Ackredit is required, but the portable
capture API has no stable public-channel build yet (ackredit#22/#75). These environment
files provision the available Conda dependencies. They are not complete until the
required provider is installed from the full commit recorded in
`../dependency_routes.toml`:

```bash
git clone https://github.com/uibcdf/ackredit.git /tmp/sabueso-ackredit-source
git -C /tmp/sabueso-ackredit-source checkout e4a006a6931f3fb5f97be5b09767c144dfb35662
python -m pip install --no-deps --no-build-isolation /tmp/sabueso-ackredit-source
python -m pip install --no-deps --editable .
```

Run these commands in the activated development/test/docs environment, from the
Sabueso root. The candidate declares Python 3.11–3.14 under
[ackredit#80](https://github.com/uibcdf/ackredit/issues/80). Every source CI lane uses
normal installation; no Requires-Python override is needed. Source installation
evidence remains separate from a released public build and its clean installation.

All runtime CI lanes install the pinned provider and test the real API. The dependency
preflight validates the source overlay and reports the unresolved release blocker.
`python devtools/dependency_preflight.py --release` fails until a stable provider
version, exact public build pins, and normal clean installs on Python 3.11–3.14 are
verified. This is development provisioning, not a public installation route.
