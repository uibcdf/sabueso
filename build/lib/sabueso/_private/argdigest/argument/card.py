from sabueso._private.argdigest._shared import refuse


def digest_card(card, caller=None):
    """A Card."""
    from sabueso.core.card import Card

    if isinstance(card, Card):
        return card
    raise refuse("card", card, caller, "expected a Card")
