from sabueso._private.argdigest._shared import refuse


def digest_grouping_rule(grouping_rule, caller=None):
    """Select an implemented disease grouping rule without inferring a version."""
    if isinstance(grouping_rule, str) and grouping_rule in {
        "disease_grouping@1",
        "disease_grouping@2",
    }:
        return grouping_rule
    raise refuse(
        "grouping_rule",
        grouping_rule,
        caller,
        'expected "disease_grouping@1" or "disease_grouping@2"',
    )
