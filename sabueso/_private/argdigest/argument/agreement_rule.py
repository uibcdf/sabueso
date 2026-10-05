from sabueso._private.argdigest._shared import refuse


def digest_agreement_rule(agreement_rule, caller=None):
    """Select an implemented interface comparison without guessing a version."""
    if isinstance(agreement_rule, str) and agreement_rule in {
        "interface_site_agreement@1",
        "interface_site_agreement@2",
    }:
        return agreement_rule
    raise refuse(
        "agreement_rule",
        agreement_rule,
        caller,
        'expected "interface_site_agreement@1" or "interface_site_agreement@2"',
    )
