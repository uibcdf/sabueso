def digest_target_scope_rule(target_scope_rule, caller=None):
    """Select an implemented target-selection interpretation without coercion."""
    from sabueso.core.bioactivity_target_scope import validate_target_scope_rule

    return validate_target_scope_rule(target_scope_rule)
