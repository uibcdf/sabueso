from sabueso._private.argdigest._shared import refuse


def digest_query(query, caller=None):
    """An EntityQuery, or a non-empty identifier or name to resolve."""
    from sabueso.resolver import EntityQuery

    if isinstance(query, EntityQuery):
        return query
    if isinstance(query, str) and query.strip():
        return query.strip()
    raise refuse(
        "query", query, caller, "expected a non-empty string or an EntityQuery"
    )
