from sabueso._private.argdigest._shared import refuse


def digest_relation(relation, caller=None):
    """How the value relates to the measurement: =, <, <=, >, >= or ~."""
    from sabueso.core.curation import RELATIONS

    if relation in RELATIONS:
        return relation
    raise refuse("relation", relation, caller, f"expected one of {list(RELATIONS)}")
