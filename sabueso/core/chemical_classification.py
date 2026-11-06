"""Source-bound chemical classes and roles; no pharmacological inference."""

from .card_capture import _capture_cards
from .chemical_classification_v1 import interpret


def chemical_classification(card):
    """Read original field membership with complete support and explicit gaps."""
    captures, inputs = _capture_cards(card, ())
    return interpret(captures[inputs[0]])
