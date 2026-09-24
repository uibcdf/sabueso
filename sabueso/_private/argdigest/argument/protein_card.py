from sabueso._private.argdigest._shared import refuse


def digest_protein_card(protein_card, caller=None):
    """A Card of a protein entity."""
    from sabueso.core.card import Card

    if isinstance(protein_card, Card) and (
        protein_card.meta.get("entity_type") in (None, "protein")
    ):
        return protein_card
    raise refuse("protein_card", protein_card, caller, "expected the Card of a protein")
