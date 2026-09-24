from sabueso._private.argdigest._shared import boolean


def digest_skip_digestion(skip_digestion, caller=None):
    """The bypass flag itself, as in the sibling components: only True or False."""
    return boolean("skip_digestion", skip_digestion, caller)
