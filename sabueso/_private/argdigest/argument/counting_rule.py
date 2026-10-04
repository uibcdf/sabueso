from sabueso._private.argdigest._shared import refuse


def digest_counting_rule(counting_rule, caller=None):
    """Select a versioned ligand counter without changing measurement identity."""
    if isinstance(counting_rule, str) and counting_rule in {
        "ligand_measurement_count@1",
        "ligand_measurement_count@2",
    }:
        return counting_rule
    raise refuse(
        "counting_rule",
        counting_rule,
        caller,
        'expected "ligand_measurement_count@1" or "ligand_measurement_count@2"',
    )
