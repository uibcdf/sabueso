"""Where two proteins' sequences differ, position by position (#103).

Rule ``equal_length_positions@1``: two stated sequences of the same length are compared
position by position, and the positions where the residues differ are listed. Nothing
is aligned: sequences of different lengths are not compared (``different_lengths``),
because placing one in the other's numbering would need an alignment, and Sabueso does
not align. The comparison says nothing about identity: two related entries (a reference
entry and a genome-strain entry, ``clustered_with``) stay two entities.
"""

from __future__ import annotations

from typing import Any, Dict

from .relationship_store import make_derivation

RULE = "equal_length_positions@1"
SEQUENCE = "sequence.primary"


def sequence_differences_view(card: Any, other: Any) -> Dict[str, Any]:
    """The positions where ``card``'s and ``other``'s sequences differ; see the module
    docstring."""
    a = (card.get(SEQUENCE) or {}).get("value") or ""
    b = (other.get(SEQUENCE) or {}).get("value") or ""
    out: Dict[str, Any] = {
        "cards": [card.id, other.id],
        "lengths": [len(a), len(b)],
        "rule": make_derivation(RULE, inputs=[SEQUENCE]),
    }
    if not a or not b:
        out["basis"] = "sequence_not_stated"
    elif len(a) != len(b):
        out["basis"] = "different_lengths"
    else:
        out["differences"] = [
            {"position": i + 1, "residues": [x, y]}
            for i, (x, y) in enumerate(zip(a, b))
            if x != y
        ]
        out["identical"] = not out["differences"]
    return out
