from sabueso._private.argdigest._shared import refuse


def digest_uncertainty(uncertainty, caller=None):
    """None, or a dict stating an uncertainty; its parts are checked where it is recorded."""
    if uncertainty is None or isinstance(uncertainty, dict):
        return uncertainty
    raise refuse(
        "uncertainty",
        uncertainty,
        caller,
        "expected a dict such as {'kind': 'sd', 'value': '3 nM'}, or None",
    )
