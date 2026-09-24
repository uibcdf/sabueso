from sabueso._private.argdigest._shared import refuse


def digest_policy(policy, caller=None):
    """None (no preference) or one of the resolver's named preference policies."""
    from sabueso.resolver.entity_resolver import POLICIES

    if policy is None or policy in POLICIES:
        return policy
    raise refuse("policy", policy, caller, f"expected None or one of {list(POLICIES)}")
