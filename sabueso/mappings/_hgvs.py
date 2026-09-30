"""Placing a protein change stated on a transcript in the card's UniProt numbering.

Shared by the variant sources (ClinVar, gnomAD; #83). Every step rests on a statement:

1. **The canonical isoform.** A change on a transcript the UniProt entry states for its
   canonical isoform is read in UniProt numbering as it is.
2. **Another isoform** (rule ``uniprot_isoform_map@1``). UniProt states which isoform
   each transcript encodes (Ensembl and RefSeq cross-references), and how each isoform
   differs from the canonical sequence (its alternative sequences, ``VSP_``). Applying
   those edits gives a map from the isoform's positions to the canonical ones. A
   position inside a replaced or inserted segment has no canonical counterpart
   (``isoform_specific_position``). Nothing is aligned or matched by similarity.
3. **The residue.** The residue the change names must be the residue of the UniProt
   sequence at the placed position (``residue_mismatch`` otherwise).

Otherwise ``not_placed`` says why:
- ``no_protein_change``;
- ``unparsed_protein_change``, for a notation other than one residue's change (e.g.
  a multi-residue delins);
- ``transcript_not_canonical``, for a transcript UniProt maps to no isoform with a
  map;
- ``stop_codon``, for a change at the stop codon, one past the sequence;
- ``isoform_specific_position`` or ``residue_mismatch``.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

ISOFORM_RULE = "uniprot_isoform_map@1"
THREE = {
    "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D", "Cys": "C", "Gln": "Q",
    "Glu": "E", "Gly": "G", "His": "H", "Ile": "I", "Leu": "L", "Lys": "K",
    "Met": "M", "Phe": "F", "Pro": "P", "Ser": "S", "Thr": "T", "Trp": "W",
    "Tyr": "Y", "Val": "V", "Sec": "U", "Pyl": "O", "Ter": "*",
}  # fmt: skip
PROTEIN = re.compile(r"p\.([A-Z][a-z]{2})(\d+)(.*)")


def isoform_map(length: int, edits: List[Tuple[int, int, str]]) -> Dict[int, int]:
    """Isoform position → canonical position, from the isoform's stated edits.

    ``edits`` are ``(start, end, replacement)`` in canonical numbering; an empty
    replacement is a deletion ("Missing"). Positions of a replacement have no canonical
    counterpart and are left out of the map.
    """
    mapping: Dict[int, int] = {}
    edits = sorted(edits)
    iso = 0
    canonical = 1
    for start, end, replacement in edits:
        while canonical < start:
            iso += 1
            mapping[iso] = canonical
            canonical += 1
        iso += len(replacement)  # isoform-specific residues
        canonical = end + 1
    while canonical <= length:
        iso += 1
        mapping[iso] = canonical
        canonical += 1
    return mapping


def transcript_context(entry: Dict[str, Any]) -> Dict[str, Any]:
    """What a UniProt entry states about its transcripts and isoforms:
    ``{"canonical": {transcript}, "isoform_of": {transcript: isoform},
    "maps": {isoform: {isoform position: canonical position}}, "sequence"}``.
    Ensembl transcripts are keyed without version (gnomAD states none); RefSeq
    transcripts with their version (ClinVar states it)."""
    sequence = (entry.get("sequence") or {}).get("value") or ""
    isoforms, displayed = {}, None
    for comment in entry.get("comments") or []:
        if comment.get("commentType") != "ALTERNATIVE PRODUCTS":
            continue
        for isoform in comment.get("isoforms") or []:
            ids = isoform.get("isoformIds") or []
            if not ids:
                continue
            if isoform.get("isoformSequenceStatus") == "Displayed":
                displayed = ids[0]
            isoforms[ids[0]] = list(isoform.get("sequenceIds") or [])
    segments = {}
    for feature in entry.get("features") or []:
        if feature.get("type") != "Alternative sequence" or not feature.get(
            "featureId"
        ):
            continue
        location = feature.get("location") or {}
        alternatives = (feature.get("alternativeSequence") or {}).get(
            "alternativeSequences"
        ) or [""]
        segments[feature["featureId"]] = (
            (location.get("start") or {}).get("value"),
            (location.get("end") or {}).get("value"),
            alternatives[0],
        )
    maps = {}
    for isoform, vsps in isoforms.items():
        if isoform == displayed or not vsps:
            continue
        edits = [segments[v] for v in vsps if v in segments]
        if len(edits) == len(vsps) and all(s and e for s, e, _ in edits):
            maps[isoform] = isoform_map(len(sequence), edits)
    canonical, isoform_of = set(), {}
    for xref in entry.get("uniProtKBCrossReferences") or []:
        database = xref.get("database")
        if database == "Ensembl":
            transcripts = [xref["id"].split(".")[0]]
        elif database == "RefSeq":
            transcripts = [
                p["value"]
                for p in xref.get("properties") or []
                if p.get("key") == "NucleotideSequenceId" and p.get("value")
            ]
        else:
            continue
        isoform = xref.get("isoformId")
        for transcript in transcripts:
            # A cross-reference without an isoform is the canonical one only in an
            # entry that describes no isoforms; in one that does, UniProt names the
            # isoform of each transcript it matched, and states none for a transcript
            # that encodes another sequence (CD44: ENST00000442151, 294 residues).
            if isoform == displayed or (isoform is None and displayed is None):
                canonical.add(transcript)
            elif isoform is not None:
                isoform_of[transcript] = isoform
    return {
        "canonical": canonical,
        "isoform_of": isoform_of,
        "maps": maps,
        "sequence": sequence,
    }


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
    isoform_of: Dict[str, str] | None = None,
    maps: Dict[str, Dict[int, int]] | None = None,
) -> Dict[str, Any]:
    """``{"location", "substitution"[, "placed_via"]}`` in UniProt numbering, or
    ``{"not_placed"}``; see the module docstring."""
    if not hgvs_p:
        return {"not_placed": "no_protein_change"}
    match = PROTEIN.match(hgvs_p)
    residue = THREE.get(match.group(1)) if match else None
    if residue is None:
        return {"not_placed": "unparsed_protein_change"}
    stated = int(match.group(2))
    via = None
    if transcript in set(canonical):
        position = stated
    else:
        isoform = (isoform_of or {}).get(transcript)
        position_map = (maps or {}).get(isoform)
        if position_map is None:
            return {"not_placed": "transcript_not_canonical"}
        position = position_map.get(stated)
        if position is None:
            return {"not_placed": "isoform_specific_position"}
        via = {"rule": ISOFORM_RULE, "isoform": isoform, "isoform_position": stated}
    if residue == "*" and sequence and position == len(sequence) + 1:
        return {"not_placed": "stop_codon"}
    if (
        not sequence
        or not 0 < position <= len(sequence)
        or sequence[position - 1] != residue
    ):
        return {"not_placed": "residue_mismatch"}
    placed = {
        "location": {"start": position, "end": position},
        "substitution": {"original": residue, "change": _change(match.group(3))},
    }
    if via is not None:
        placed["placed_via"] = via
    return placed
