"""Choose original sequence-change predicates without changing prior formats."""


def presentation(view):
    if (
        view._explorer.mode == "saved"
        or view._explorer._session.get("format") == "sabueso.card_exploration@31"
    ):
        from ._sequence_change_history_v1 import exploration as original

        return original
    from . import card_sequence_change_exploration as live

    return live


def selection(view):
    if (
        view._explorer.mode == "saved"
        or view._explorer._session.get("format") == "sabueso.card_exploration@31"
    ):
        from ._sequence_change_history_v1 import selection as original

        return original
    from . import card_sequence_change_selection_v1 as live

    return live
