"""SDK230 tissue constants, intervals and retained text, scoped helpers only."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .rules import make_derivation

REGIONS = "annotations.exon_usage_by_tissue"

VARIANTS = "annotations.population_variants"

TERMS = "annotations.tissue_terms"

TRANSCRIPTS = "identifiers.ensembl_transcripts"

ISOFORMS = "annotations.isoforms"

EXONS = "annotations.isoform_coding_exons"

TISSUE_TEXT = "annotations.tissue_specificity"


def tissue_terms(card: Any) -> Dict[str, Any] | None:
    """Per tissue the card's pext names, GTEx's tissue and its ontology term
    (``gtex_tissue_key@1``); None when the card states no GTEx terms."""
    from .terms import KEY_RULE, tissue_key

    stated = (card.get(TERMS) or {}).get("value")
    if not stated:
        return None
    by_key = {tissue_key(t.get("gtex_id") or ""): t for t in stated}
    named = sorted(
        {
            t.get("tissue")
            for r in (card.get(REGIONS) or {}).get("value") or []
            for t in r.get("tissues") or []
            if t.get("tissue")
        }
    )
    return {
        "terms": {
            key: {
                k: by_key[key][k]
                for k in ("gtex_id", "name", "ontology_id")
                if k in by_key[key]
            }
            for key in named
            if key in by_key
        },
        "tissues_without_term": [key for key in named if key not in by_key],
        "rule": make_derivation(KEY_RULE, inputs=[f"{REGIONS}.tissues", TERMS]),
    }


def _position(variant_id: str | None) -> Tuple[str, int] | None:
    parts = str(variant_id or "").split("-")
    if len(parts) < 2 or not parts[1].isdigit():
        return None
    return parts[0], int(parts[1])


def _merge(ranges: List[List[int]]) -> List[List[int]]:
    out: List[List[int]] = []
    for start, end in sorted(ranges):
        if out and start <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return out


def _minus(ranges: List[List[int]], others: List[List[int]]) -> List[List[int]]:
    """The bases of ``ranges`` in none of ``others`` (closed intervals)."""
    out = []
    for start, end in _merge(ranges):
        pieces = [[start, end]]
        for o_start, o_end in _merge(others):
            next_pieces = []
            for p_start, p_end in pieces:
                if o_end < p_start or o_start > p_end:
                    next_pieces.append([p_start, p_end])
                    continue
                if p_start < o_start:
                    next_pieces.append([p_start, o_start - 1])
                if o_end < p_end:
                    next_pieces.append([o_end + 1, p_end])
            pieces = next_pieces
        out.extend(pieces)
    return out


def _uniprot_texts(
    card: Any, names: Dict[str, str], *, _support=None
) -> Dict[str, List[Dict]]:
    """UniProt's tissue-specificity statements restricted to an isoform, by isoform
    id; the ones without restriction under ``None``."""
    by_isoform: Dict[Any, List[Dict]] = {}
    for sa in card.source_assertion_store.find_by_field(TISSUE_TEXT):
        metadata = sa.get("source_metadata") or {}
        molecule = metadata.get("molecule")
        isoform = names.get(molecule) if molecule else None
        if _support is not None:
            _support.append(
                {
                    "source_assertion_id": sa["id"],
                    "molecule": molecule,
                    "isoform": isoform,
                    "status": "excluded"
                    if molecule and isoform is None
                    else "included",
                    "basis": "unknown_isoform_molecule"
                    if molecule and isoform is None
                    else "exact_isoform_name"
                    if molecule
                    else "entry_scope",
                }
            )
        if molecule and isoform is None:
            continue  # restricted to something other than a known isoform
        by_isoform.setdefault(isoform, []).append(
            {
                "text": sa.get("asserted_value"),
                "molecule": molecule,
                "evidence": metadata.get("eco"),
                "source_assertion_id": sa.get("id"),
            }
        )
    return by_isoform


def variable_regions(cds_of: Dict[str, List[List[int]]]) -> List[Dict[str, Any]]:
    """The coding bases not every isoform includes, as runs of bases included by the
    same isoforms: ``[{start, end, isoforms}]``. Isoforms with transcripts only."""
    if len(cds_of) < 2:
        return []
    merged = {k: _merge(v) for k, v in cds_of.items()}
    points = sorted({p for v in merged.values() for s, e in v for p in (s, e + 1)})
    runs: List[Dict[str, Any]] = []
    for start, nxt in zip(points, points[1:]):
        end = nxt - 1
        holders = sorted(
            k for k, v in merged.items() if any(s <= start and end <= e for s, e in v)
        )
        if not holders or len(holders) == len(merged):
            continue
        if runs and runs[-1]["isoforms"] == holders and runs[-1]["end"] == start - 1:
            runs[-1]["end"] = end
        else:
            runs.append({"start": start, "end": end, "isoforms": holders})
    return runs
