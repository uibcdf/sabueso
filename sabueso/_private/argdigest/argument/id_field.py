from sabueso._private.argdigest._shared import field_path, refuse


def digest_id_field(id_field, caller=None):
    """None (the card id) or the field path whose value labels each stored row."""
    if id_field is None:
        return None
    if not isinstance(id_field, str):
        raise refuse("id_field", id_field, caller, "expected a field path or None")
    return field_path("id_field", id_field, caller)
