from sabueso._private.argdigest._shared import refuse


def digest_other(other, caller=None):
    """The Card of the protein compared with (``Card.compare_ligands``)."""
    from sabueso.core.card import Card

    if isinstance(other, Card) and other.meta.get("entity_type") in (None, "protein"):
        return other
    raise refuse("other", other, caller, "expected the Card of a protein")
