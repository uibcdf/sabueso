from sabueso._private.argdigest._shared import refuse


def digest_predicate(predicate, caller=None):
    """A relationship predicate that takes curated literature assertions."""
    from sabueso.core.curation import CURATABLE_PREDICATES

    if predicate in CURATABLE_PREDICATES:
        return predicate
    raise refuse(
        "predicate",
        predicate,
        caller,
        f"expected one of {sorted(CURATABLE_PREDICATES)}",
    )
