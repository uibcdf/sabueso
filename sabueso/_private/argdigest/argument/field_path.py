from sabueso._private.argdigest._shared import refuse


def digest_field_path(field_path, caller=None):
    """A card field that takes curated literature assertions (``curation``)."""
    from sabueso.core.curation import CURATABLE_FIELDS

    if field_path in CURATABLE_FIELDS:
        return field_path
    raise refuse(
        "field_path",
        field_path,
        caller,
        f"expected one of the curatable fields {sorted(CURATABLE_FIELDS)}",
    )
