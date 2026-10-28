from sabueso._private.argdigest._shared import refuse


def digest_relationship_id(relationship_id, caller=None):
    """None or a nonempty exact stored relationship identifier, without coercion."""
    if relationship_id is None or (
        isinstance(relationship_id, str) and relationship_id.strip()
    ):
        return relationship_id
    raise refuse(
        "relationship_id",
        relationship_id,
        caller,
        "expected None or a nonempty exact relationship id",
    )
