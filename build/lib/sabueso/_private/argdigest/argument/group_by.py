from sabueso._private.argdigest._shared import refuse


def digest_group_by(group_by, caller=None):
    """None (every state key), or a non-empty sequence of distinct keys of
    ``sabueso.core.structures.GROUP_KEYS``."""
    from sabueso.core.structures import GROUP_KEYS

    if group_by is None:
        return None
    if isinstance(group_by, str):
        group_by = (group_by,)
    if (
        isinstance(group_by, (list, tuple))
        and group_by
        and all(isinstance(k, str) and k in GROUP_KEYS for k in group_by)
        and len(set(group_by)) == len(group_by)
    ):
        return tuple(group_by)
    raise refuse(
        "group_by",
        group_by,
        caller,
        f"expected None or distinct keys among {', '.join(GROUP_KEYS)}",
    )
