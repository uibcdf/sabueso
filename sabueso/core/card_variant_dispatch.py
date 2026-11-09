"""Select original variant presentation without changing older saved formats."""


def presentation(view):
    if (
        view._explorer.mode == "saved"
        or view._explorer._session.get("format") == "sabueso.card_exploration@29"
    ):
        from ._variant_history_v1 import presentation as frozen

        return frozen
    from . import card_variant_presentation_v1 as live

    return live
