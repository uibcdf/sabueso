# Development environments

The runtime authority is `pyproject.toml`. The environment files provision public
Conda dependencies, including **Ackredit >=0.9.0**, the first published portable
`ackredit.attribution@1` contract. Its exact public build 0.9.0/py_0 is pinned by
the installed-package gate; no provider source overlay is needed in CI.

Create and activate the chosen development/test/docs environment, then install
Sabueso from the repository root:

```bash
python -m pip install --no-deps --editable .
```

In the maintainer's `molsyssuite@uibcdf_3.14` workspace, all installed local
MolSysSuite packages remain editable. Clean qualification environments use the
public distributions and the candidate artifact.

Every runtime CI lane obtains the required provider from the public Conda channel.
Dedicated receiving lanes exercise its first published API on Python 3.11–3.14
outside both checkouts. `python devtools/dependency_preflight.py --release` verifies
that metadata, recipe, environments and exact public build pins agree. Public
provider delivery is recorded under Sabueso #108 and Ackredit #22/#75/#80.
