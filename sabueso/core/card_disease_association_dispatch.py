"""Select the explicit original disease presentation without changing old formats."""


def presentation(view):
    if view._explorer.mode == "saved":
        from ._disease_association_history_v1 import presentation as frozen

        return frozen
    from . import card_disease_association_presentation_v1 as live

    return live
