def digest_generation_rule(generation_rule, caller=None):
    """Select an implemented assembly rule without guessing a version."""
    from sabueso.core.assembly_requests import generation_rule as validate

    return validate(generation_rule)
