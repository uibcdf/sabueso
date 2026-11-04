def digest_classification_rule(classification_rule, caller=None):
    """Select an explicit implemented activity policy without coercion."""
    from sabueso.core.bioactivity_class_v4 import classification_rule as validate

    return validate(classification_rule)
