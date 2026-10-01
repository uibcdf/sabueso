"""Where a variant matters: the tissues whose expression includes its position (#102).

gnomAD states, per coding region of a gene, the pext: the share of the gene's expression
in each GTEx v10 tissue that comes from transcripts including the region
(``annotations.exon_usage_by_tissue``). gnomAD states each population variant's genomic
position (``variant_id``, GRCh38). The view joins the two under the rule
``pext_at_variant@1``:

- a variant takes the pext of the region that contains its position (the first base of
  ``chromosome-position-ref-alt``), on the same chromosome and assembly;
- a variant outside every region is ``outside_pext_regions``: gnomAD states pext for
  coding regions only, so this is not "not expressed";
- per variant: the region, the mean over tissues, the value in each tissue, the tissue
  with the highest value, and the tissues at or above ``threshold`` (0.1 by default, a
  parameter of the rule, not a statement of any source).

The values are gnomAD's; nothing is stored. They come from isoform quantifications of
adult post-mortem tissues (RSEM), as gnomAD warns: a region absent from every GTEx
tissue may be developmental or annotated in error, and a low value is not proof that
the change is harmless.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .relationship_store import make_derivation

RULE = "pext_at_variant@1"
REGIONS = "annotations.exon_usage_by_tissue"
VARIANTS = "annotations.population_variants"
DEFAULT_THRESHOLD = 0.1


def _position(variant_id: str | None) -> Tuple[str, int] | None:
    parts = str(variant_id or "").split("-")
    if len(parts) < 2 or not parts[1].isdigit():
        return None
    return parts[0], int(parts[1])


def variant_tissue_usage_view(
    card: Any, threshold: float = DEFAULT_THRESHOLD
) -> Dict[str, Any]:
    """Each population variant with the pext of its region; see the module docstring."""
    regions = (card.get(REGIONS) or {}).get("value") or []
    variants = (card.get(VARIANTS) or {}).get("value") or []
    items: List[Dict[str, Any]] = []
    counts = {"in_region": 0, "outside_pext_regions": 0, "no_position": 0}
    for variant in variants:
        item = {
            k: variant[k]
            for k in ("variant_id", "hgvs_p", "transcript", "location", "not_placed")
            if k in variant
        }
        where = _position(variant.get("variant_id"))
        if where is None:
            item["pext"] = {"basis": "no_position"}
            counts["no_position"] += 1
            items.append(item)
            continue
        chromosome, position = where
        region = next(
            (
                r
                for r in regions
                if str(r.get("chromosome")) == chromosome
                and r.get("start") is not None
                and r["start"] <= position <= r["end"]
            ),
            None,
        )
        if region is None:
            item["pext"] = {"basis": "outside_pext_regions"}
            counts["outside_pext_regions"] += 1
            items.append(item)
            continue
        by_tissue = {t["tissue"]: t["value"] for t in region.get("tissues") or []}
        top = max(by_tissue.items(), key=lambda kv: kv[1]) if by_tissue else None
        item["pext"] = {
            "region": {"start": region["start"], "end": region["end"]},
            "mean": region.get("mean"),
            "max": {"tissue": top[0], "value": top[1]} if top else None,
            "at_or_above_threshold": sorted(
                t for t, v in by_tissue.items() if v is not None and v >= threshold
            ),
            "by_tissue": by_tissue,
        }
        counts["in_region"] += 1
        items.append(item)
    return {
        "items": items,
        "counts": counts,
        "rule": make_derivation(
            RULE,
            inputs=[f"{VARIANTS}.variant_id", REGIONS],
            parameters={"threshold": threshold, "assembly": "GRCh38"},
        ),
    }
