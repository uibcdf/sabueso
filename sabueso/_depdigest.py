"""DepDigest configuration for Sabueso (uibcdf/sabueso#46), as in MolSysMT.

Sabueso's runtime needs only the standard library and the UIBCDF support libraries.
Optional libraries are declared here and checked at call time by ``@dep_digest``, with
a catalogued ``LibraryNotFoundError`` and install hints when missing. They are never
imported when Sabueso is imported.
"""

from sabueso.core.errors import LibraryNotFoundError

LIBRARIES = {
    # Opt-in development embedding only; #368 owns the supported provider contract.
    "molsysviewer": {"type": "soft", "pypi": "molsysviewer", "conda": "molsysviewer"},
    "aiohttp": {"type": "soft", "pypi": "aiohttp", "conda": "aiohttp"},
    "PySide6": {"type": "soft", "pypi": "PySide6", "conda": "pyside6"},
    # Explicit supplied ModelCIF metadata only; never needed for Card reading.
    "gemmi": {"type": "soft", "pypi": "gemmi", "conda": "gemmi"},
    # Views as DataFrames: sabueso.to_dataframe (#46).
    "pandas": {"type": "soft", "pypi": "pandas", "conda": "pandas"},
    # Only requested for Zstandard on Python 3.11–3.13, never on import/3.14.
    "backports.zstd": {
        "type": "soft",
        "pypi": "backports.zstd",
        "conda": "backports.zstd",
    },
}

MAPPING = {}

SHOW_ALL_CAPABILITIES = True

EXCEPTION_CLASS = LibraryNotFoundError
