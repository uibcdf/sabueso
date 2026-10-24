"""Frozen pre-context projection from 40eb9c2 for packet mappings @6/@7/@8."""

from typing import Any, Dict


def predicted_structures_view(card: Any) -> Dict[str, Any]:
    """The card's predicted models (``has_predicted_structure``, #57), never mixed with
    experimental structures.

    Each item: the model reference, version and tool, the mean pLDDT and its bands, the
    UniProt range it covers and its coverage of the sequence, and whether the modelled
    sequence is the entry's current one. A model of an isoform names it (``isoform``) and
    has no coverage of the entry.
    """
    length = (card.get("sequence.length") or {}).get("value")
    items = []
    for rel in card.relationships(predicate="has_predicted_structure"):
        q = rel.get("qualifiers") or {}
        start, end = (list(q.get("range") or []) + [None, None])[:2]
        items.append(
            {
                "model_ref": rel["object_ref"],
                "model_version": q.get("model_version"),
                "tool": q.get("tool"),
                "mean_plddt": q.get("mean_plddt"),
                "plddt_fractions": q.get("plddt_fractions"),
                "range": q.get("range"),
                "isoform": q.get("isoform"),
                "coverage": round((end - start + 1) / length, 3)
                if length and start and end and not q.get("isoform")
                else None,
                "sequence_matches": q.get("sequence_matches"),
            }
        )
    return {"items": sorted(items, key=lambda i: i["model_ref"])}
