"""Clinical presentation after independent original saved reading is admitted."""

from ._clinical_history_v1.presentation import HEADERS as HEADERS
from ._clinical_history_v1.presentation import context_opening as context_opening
from ._clinical_history_v1.presentation import display_row as display_row
from ._clinical_history_v1.presentation import opening as original_opening


def opening(view, preview):
    lines = original_opening(view, preview)
    lines[-1] = (
        "Save this exploration to preserve its original clinical knowledge, source roles, "
        "requests and navigation. Saved scientific selection reopens retained requests; "
        "literal source reading uses retained data without consulting a source."
    )
    return lines
