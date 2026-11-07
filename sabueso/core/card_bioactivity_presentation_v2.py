"""Capability-aware actions over the unchanged original bioactivity presentation."""

from .card_bioactivity_presentation_v1 import opening as original_opening

_ORIGINAL_SAVE = (
    "Saving this bioactivity profile is unavailable until independent original saved reading is implemented. "
    "Raw Card export: explorer.access.export_card(path)."
)


def opening(view, preview):
    lines = original_opening(view, preview)
    action = (
        "Save this captured exploration with save(path); reopen it with read_exploration(path). "
        "Reading preserves the original answer, options and source context."
        if view.capabilities["save"]
        else "This view does not retain all support needed for saving; inspect capabilities or return to a retained view."
    )
    return [action if line == _ORIGINAL_SAVE else line for line in lines]
