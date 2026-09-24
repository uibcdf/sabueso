```{eval-rst}
:html_theme.sidebar_secondary.remove:
```

# Sabueso

:::{figure} _static/logo.svg
:width: 50%
:align: center

From database fragments to structured molecular intelligence.


```{image} https://img.shields.io/badge/release-v0.11.2-white.svg
:target: https://github.com/uibcdf/sabueso
```
```{image} https://img.shields.io/badge/license-MIT-white.svg
:target: https://github.com/uibcdf/sabueso/blob/master/LICENSE
```
```{image} https://img.shields.io/badge/install%20with-conda-white.svg
:target: https://anaconda.org/uibcdf/sabueso
```
```{image} https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-white.svg
:target: https://www.python.org/downloads/
```
```{image} https://img.shields.io/badge/DOI-10.5281/8092688-white.svg
:target: https://zenodo.org/record/8092688
```

:::

## Install

Sabueso is distributed through the `uibcdf` conda channel. The current Sabueso has not
had a public release yet: the `sabueso` packages already on the channel (0.2.0 and
earlier, Python 3.10 or older) belong to a previous codebase, so do not install them.
Once the first release is published:

```bash
conda install -c uibcdf -c conda-forge sabueso
```

Until then, work from the repository (see `Developers`).

## Start Here

- New users: `User` section.
- Tool-oriented tutorials: `User > Tools`.
- API generated from code docstrings: `API` section.
- Development process and constraints: `Developers` section.

```{eval-rst}

.. toctree::
   :maxdepth: 2
   :hidden:

   content/about/index.md

.. toctree::
   :maxdepth: 2
   :hidden:

   content/showcase/index.md

.. toctree::
   :maxdepth: 2
   :hidden:

   content/user/index.md

.. toctree::
   :maxdepth: 2
   :hidden:

   content/developers/index.md

.. toctree::
   :maxdepth: 2
   :hidden:

   api/index.md

```
