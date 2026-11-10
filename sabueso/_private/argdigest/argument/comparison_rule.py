from sabueso._private.argdigest._shared import refuse


def digest_comparison_rule(comparison_rule, caller=None):
    """Choose a named knowledge comparison without changing the default."""
    if isinstance(comparison_rule, str) and comparison_rule in (
        "card_knowledge_diff@1",
        "card_knowledge_diff@2",
    ):
        return comparison_rule
    raise refuse(
        "comparison_rule",
        comparison_rule,
        caller,
        'expected "card_knowledge_diff@1" or "card_knowledge_diff@2"',
    )
