from sabueso._private.argdigest._shared import refuse

CHOICES = (None, "protein", "small_molecule")


def digest_entity_type(entity_type, caller=None):
    """None (decided from the query), "protein" or "small_molecule"."""
    if entity_type in CHOICES:
        return entity_type
    raise refuse(
        "entity_type",
        entity_type,
        caller,
        'expected None, "protein" or "small_molecule"',
    )
