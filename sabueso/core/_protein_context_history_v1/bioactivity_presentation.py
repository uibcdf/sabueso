"""Original SDK239 bioactivity action notice within the pending protein session.

The archived notice is presentation history, not the current save capability.
"""

from ..card_bioactivity_presentation_v1 import opening as original_opening

_ORIGINAL_SAVE = (
    "Saving this bioactivity profile is unavailable until independent original saved reading is implemented. "
    "Raw Card export: explorer.access.export_card(path)."
)


def opening(view, preview):
    return [
        "This view does not retain all support needed for saving; inspect capabilities or return to a retained view."
        if line == _ORIGINAL_SAVE
        else line
        for line in original_opening(view, preview)
    ]
