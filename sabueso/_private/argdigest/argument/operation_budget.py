def digest_operation_budget(operation_budget, caller=None):
    """Positive operation receiving budget, or explicit None for no ceiling."""
    from sabueso.core.assembly_requests import budget

    return budget(operation_budget)
