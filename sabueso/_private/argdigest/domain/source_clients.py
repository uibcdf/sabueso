from argdigest import Domain


def _members():
    """``resolver`` and the ``*_client`` options of the protein card tool, read from its
    signature so the two cannot drift apart."""
    import inspect

    from sabueso.tools.card.protein import resolve_protein_card

    names = inspect.signature(inspect.unwrap(resolve_protein_card)).parameters
    return tuple(sorted(n for n in names if n == "resolver" or n.endswith("_client")))


domain = Domain(
    name="source_clients",
    members=_members,
    description="resolver and source clients of resolve_protein_card",
)
