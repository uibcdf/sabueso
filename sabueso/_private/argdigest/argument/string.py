from sabueso._private.argdigest._shared import options, positive_int


def _score(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1000:
        return "expected an integer from 0 to 1000"
    return None


def digest_string(string, caller=None):
    """STRING enrichment: None (off) or options {required_score, limit}."""
    return options(
        "string", string, caller, {"required_score": _score, "limit": positive_int}
    )
