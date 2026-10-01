from sabueso._private.argdigest._shared import options, positive_int

REL_TYPES = ("1:1", "1:n", "m:1", "m:n")


def _rel_type(value):
    return None if value in REL_TYPES else f"one of {list(REL_TYPES)}"


def _taxa(value):
    if (
        isinstance(value, (list, tuple))
        and value
        and all(isinstance(t, int) and not isinstance(t, bool) for t in value)
    ):
        return None
    return "a non-empty list of NCBI taxon ids (integers)"


def digest_oma(oma, caller=None):
    """OMA orthologs: None (off) or options {limit, rel_type, taxa}."""
    return options(
        "oma",
        oma,
        caller,
        {"limit": positive_int, "rel_type": _rel_type, "taxa": _taxa},
    )
