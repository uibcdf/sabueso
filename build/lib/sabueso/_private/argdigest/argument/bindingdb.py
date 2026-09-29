from sabueso._private.argdigest._shared import options, refuse


def _cutoff(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
        return None
    return "a positive affinity cutoff in nanomolar"


def digest_bindingdb(bindingdb, caller=None):
    """BindingDB affinities enrichment: None (off) or options {cutoff} (nanomolar)."""
    if bindingdb is not None and not isinstance(bindingdb, dict):
        raise refuse(
            "bindingdb", bindingdb, caller, "expected a dict of options, or None"
        )
    return options("bindingdb", bindingdb, caller, {"cutoff": _cutoff})
