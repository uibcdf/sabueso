from argdigest import Domain


def _members():
    """The options of the card views ``Card.table`` runs, read from their signatures."""
    import inspect

    from sabueso.core.card import Card
    from sabueso.core.tables import TABLES

    names = set()
    for view_name, _ in TABLES.values():
        method = inspect.unwrap(getattr(Card, view_name))
        names |= set(inspect.signature(method).parameters)
    return tuple(sorted(names - {"self", "skip_digestion"}))


domain = Domain(
    name="view_options",
    members=_members,
    description="options of the card views behind Card.table",
)
