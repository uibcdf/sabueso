from sabueso._private.argdigest._shared import refuse


def digest_view(view, caller=None):
    """A card view with a table form (``sabueso.core.tables.TABLES``)."""
    from sabueso.core.tables import TABLES

    if view in TABLES:
        return view
    raise refuse("view", view, caller, f"expected one of {sorted(TABLES)}")
