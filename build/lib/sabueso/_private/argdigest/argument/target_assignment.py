from sabueso._private.argdigest._shared import refuse


def digest_target_assignment(target_assignment, caller=None):
    """Measured on this protein ("direct") or on an ortholog ("homology")."""
    from sabueso.core.curation import TARGET_ASSIGNMENTS

    if target_assignment in TARGET_ASSIGNMENTS:
        return target_assignment
    raise refuse(
        "target_assignment",
        target_assignment,
        caller,
        f"expected one of {sorted(TARGET_ASSIGNMENTS)}",
    )
