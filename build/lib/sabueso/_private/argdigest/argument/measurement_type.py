from sabueso._private.argdigest._shared import refuse


def digest_measurement_type(measurement_type, caller=None):
    """The measurement type as the publication names it: IC50, Ki, Inhibition..."""
    if isinstance(measurement_type, str) and measurement_type.strip():
        return measurement_type.strip()
    raise refuse(
        "measurement_type", measurement_type, caller, "expected a measurement type"
    )
