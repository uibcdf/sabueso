"""Choose original protein-context predicates without changing prior formats."""


def presentation(view):
    result = view._selection._scientific
    if (
        result is not None
        and result.wire.get("context", {}).get("adapter")
        == "protein_knowledge_comparison_exploration@1"
    ):
        if view._explorer._session.get("format") == "sabueso.card_exploration@35":
            from ._knowledge_comparison_history_v1 import exploration as comparison

            return comparison
        from . import card_knowledge_comparison_exploration as comparison

        return comparison
    if view._explorer.mode == "saved" or view._explorer._session.get("format") in (
        "sabueso.card_exploration@33",
        "sabueso.card_exploration@35",
    ):
        from ._protein_context_history_v1 import exploration as original

        return original
    from . import card_protein_context_exploration as live

    return live


def selection(view):
    if view._explorer.mode == "saved" or view._explorer._session.get("format") in (
        "sabueso.card_exploration@33",
        "sabueso.card_exploration@35",
    ):
        from ._protein_context_history_v1 import selection as original

        return original
    from . import card_protein_context_selection_v1 as live

    return live


def historical_save_notice(view):
    """Preserve SDK239's recorded action text while exposing current API capabilities."""
    session = view._explorer._session
    if session.get("format") == "sabueso.card_exploration@35":
        return any(
            original._selection._scientific is not None
            and original._selection._scientific.wire.get("context", {}).get("adapter")
            == "protein_knowledge_comparison_exploration@1"
            and original._selection._scientific.wire.get("native_payload", {})
            .get("rule", {})
            .get("sabueso_version")
            == "0.14.0+243.gf6d8e4a"
            for original in session["views"].values()
        )
    if session.get("format") != "sabueso.card_exploration@33":
        return False
    for original in session["views"].values():
        result = original._selection._scientific
        if (
            result is not None
            and result.wire.get("context", {}).get("adapter")
            == "protein_context_exploration@1"
        ):
            rule = result.wire.get("native_payload", {}).get("rule", {})
            if (
                rule.get("rule") == "protein_context_projection@1"
                and rule.get("sabueso_version") == "0.14.0+239.g738a422"
            ):
                return True
    return False
