from sabueso._private.argdigest._shared import options, positive_int


def digest_gpcrdb(gpcrdb, caller=None):
    """GPCRdb: None (off) or options {limit}."""
    return options("gpcrdb", gpcrdb, caller, {"limit": positive_int})
