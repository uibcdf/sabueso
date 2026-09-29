"""Placing a protein change stated on a transcript in the card's UniProt numbering.

Shared by the variant sources (ClinVar, gnomAD; #83). A change is placed only when two
things hold. First, its transcript is one the UniProt entry states for its canonical
isoform. Second, the residue the change names is the residue of the UniProt sequence at
that position. Otherwise ``not_placed`` says why: ``no_protein_change``,
``transcript_not_canonical`` or ``residue_mismatch``. Nothing is placed by similarity.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable

THREE = {
    "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D", "Cys": "C", "Gln": "Q",
    "Glu": "E", "Gly": "G", "His": "H", "Ile": "I", "Leu": "L", "Lys": "K",
    "Met": "M", "Phe": "F", "Pro": "P", "Ser": "S", "Thr": "T", "Trp": "W",
    "Tyr": "Y", "Val": "V", "Sec": "U", "Pyl": "O", "Ter": "*",
}  # fmt: skip
PROTEIN = re.compile(r"p\.([A-Z][a-z]{2})(\d+)(.*)")


def _change(rest: str) -> str | None:
    """The one-letter result of a simple change, or the stated suffix otherwise."""
    if rest in THREE:
        return THREE[rest]
    if rest == "=":
        return "="
    return rest or None


def place(
    hgvs_p: str | None,
    transcript: str | None,
    canonical: Iterable[str],
    sequence: str | None,
) -> Dict[str, Any]:
    """``{"location", "substitution"}`` in UniProt numbering, or ``{"not_placed"}``."""
    if not hgvs_p:
        return {"not_placed": "no_protein_change"}
    if transcript not in set(canonical):
        return {"not_placed": "transcript_not_canonical"}
    match = PROTEIN.match(hgvs_p)
    residue = THREE.get(match.group(1)) if match else None
    position = int(match.group(2)) if match else None
    if (
        residue is None
        or not sequence
        or not 0 < position <= len(sequence)
        or sequence[position - 1] != residue
    ):
        return {"not_placed": "residue_mismatch"}
    return {
        "location": {"start": position, "end": position},
        "substitution": {"original": residue, "change": _change(match.group(3))},
    }
