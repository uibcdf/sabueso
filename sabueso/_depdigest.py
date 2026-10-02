"""DepDigest configuration for Sabueso (uibcdf/sabueso#46), as in MolSysMT.

Sabueso's runtime needs only the standard library and the UIBCDF support libraries.
Optional libraries are declared here and checked at call time by ``@dep_digest``, with
a catalogued ``LibraryNotFoundError`` and install hints when missing. They are never
imported when Sabueso is imported.
"""

from sabueso.core.errors import LibraryNotFoundError

LIBRARIES = {
    # Opt-in packet attribution; source pilot, public extra pending (#108).
    "ackredit": {"type": "soft", "pypi": "ackredit", "conda": "ackredit"},
    # Views as DataFrames: sabueso.to_dataframe (#46).
    "pandas": {"type": "soft", "pypi": "pandas", "conda": "pandas"},
}

MAPPING = {}

SHOW_ALL_CAPABILITIES = True

EXCEPTION_CLASS = LibraryNotFoundError
