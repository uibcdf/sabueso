from sabueso._private.argdigest._shared import refuse


def digest_mode(mode, caller=None):
    if mode in ("full", "minimal"):
        return mode
    raise refuse("mode", mode, caller, "expected 'full' or 'minimal'")
