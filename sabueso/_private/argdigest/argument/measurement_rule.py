def digest_measurement_rule(measurement_rule, caller=None):
    """Select an implemented measurement policy without implicit version coercion."""
    from sabueso.core.measurement_correspondence import validate_measurement_rule

    return validate_measurement_rule(measurement_rule)
