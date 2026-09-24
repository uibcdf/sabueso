from argdigest import Domain


def _members():
    """The options of the card tools ``sabueso.resolve`` routes to, read from their
    signatures so the two cannot drift apart."""
    import inspect

    from sabueso.tools.card.protein import resolve_protein_card
    from sabueso.tools.card.small_molecule import resolve_molecule_card

    names = set()
    for tool in (resolve_protein_card, resolve_molecule_card):
        names |= set(inspect.signature(inspect.unwrap(tool)).parameters)
    return tuple(sorted(names - {"query", "identifier", "skip_digestion"}))


domain = Domain(
    name="card_options",
    members=_members,
    description="options of resolve_protein_card and resolve_molecule_card",
)
