from sabueso._private.argdigest._shared import options


def _channels(value):
    from sabueso.tools.db.diseases import CHANNELS

    if (
        isinstance(value, (list, tuple))
        and value
        and all(isinstance(c, str) and c in CHANNELS for c in value)
        and len(set(value)) == len(value)
    ):
        return None
    return f"expected distinct channels among {', '.join(CHANNELS)}"


def digest_diseases(diseases, caller=None):
    """DISEASES enrichment: None (off) or options {channels}."""
    return options("diseases", diseases, caller, {"channels": _channels})
