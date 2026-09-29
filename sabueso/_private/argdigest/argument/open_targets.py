from sabueso._private.argdigest._shared import options, positive_int


def digest_open_targets(open_targets, caller=None):
    """Open Targets associations: None (off) or options {limit}."""
    return options("open_targets", open_targets, caller, {"limit": positive_int})
