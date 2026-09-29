from sabueso._private.argdigest._shared import refuse


def digest_curations(curations, caller=None):
    """None, a CurationStore, or the path of one (a str or path-like)."""
    import os

    from sabueso.core.curation_store import CurationStore

    if curations is None or isinstance(curations, CurationStore):
        return curations
    if isinstance(curations, (str, os.PathLike)) and str(curations):
        return CurationStore(curations)
    raise refuse(
        "curations", curations, caller, "expected a CurationStore, a path, or None"
    )
