from sabueso._private.argdigest._shared import refuse


def digest_expand_occurrences(expand_occurrences, caller=None):
    """Declaration expansion requires an explicit boolean."""
    if type(expand_occurrences) is bool:
        return expand_occurrences
    raise refuse("expand_occurrences", expand_occurrences, caller, "expected a boolean")
