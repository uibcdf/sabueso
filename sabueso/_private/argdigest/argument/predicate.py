from sabueso._private.argdigest._shared import STORE_QUERIES, refuse


def digest_predicate(predicate, caller=None):
    """A relationship predicate that takes curated literature assertions.

    A knowledge store query takes any predicate Sabueso states, or None (any).
    """
    if caller in STORE_QUERIES:
        from sabueso.core.relationship_store import PREDICATES

        if predicate is None or predicate in PREDICATES:
            return predicate
        raise refuse(
            "predicate", predicate, caller, f"expected one of {sorted(PREDICATES)}"
        )
    from sabueso.core.curation import CURATABLE_PREDICATES

    if predicate in CURATABLE_PREDICATES:
        return predicate
    raise refuse(
        "predicate",
        predicate,
        caller,
        f"expected one of {sorted(CURATABLE_PREDICATES)}",
    )
