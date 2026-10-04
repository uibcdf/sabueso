import os

from sabueso._private.argdigest._shared import refuse


def digest_extractions(extractions, caller=None):
    """An ExtractionStore, its path, or None."""
    from sabueso.core.extraction_store import ExtractionStore

    if extractions is None or isinstance(extractions, ExtractionStore):
        return extractions
    if isinstance(extractions, (str, os.PathLike)) and str(extractions):
        return ExtractionStore(extractions)
    raise refuse(
        "extractions",
        extractions,
        caller,
        "expected an ExtractionStore, a path, or None",
    )
