"""Choose original protein-context predicates without changing prior formats."""


def presentation(view):
    if (
        view._explorer.mode == "saved"
        or view._explorer._session.get("format") == "sabueso.card_exploration@33"
    ):
        from ._protein_context_history_v1 import exploration as original

        return original
    from . import card_protein_context_exploration as live

    return live


def selection(view):
    if (
        view._explorer.mode == "saved"
        or view._explorer._session.get("format") == "sabueso.card_exploration@33"
    ):
        from ._protein_context_history_v1 import selection as original

        return original
    from . import card_protein_context_selection_v1 as live

    return live


def historical_save_notice(view):
    """Preserve SDK239's recorded action text while exposing current API capabilities."""
    session = view._explorer._session
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
