from sabueso._private.argdigest._shared import refuse


def digest_detail(detail, caller=None):
    """A packet's level of detail: ``"full"`` or ``"index"`` (#88)."""
    from sabueso.core.packets import DETAILS

    if detail in DETAILS:
        return detail
    raise refuse("detail", detail, caller, f"expected one of {', '.join(DETAILS)}")
