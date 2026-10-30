from sabueso._private.argdigest._shared import refuse


def digest_expand_operations(expand_operations, caller=None):
    """Expansion must be a deliberate boolean, never truth-value coercion."""
    if type(expand_operations) is bool:
        return expand_operations
    raise refuse("expand_operations", expand_operations, caller, "expected a boolean")
