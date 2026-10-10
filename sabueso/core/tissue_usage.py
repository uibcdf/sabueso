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

When the card states GTEx's terms for the tissues (``gtex=True``,
``annotations.tissue_terms``), both views add ``tissue_terms``: per tissue the pext
names, the GTEx tissue and the ontology term GTEx states for it (UBERON, or EFO for a
cell line), joined by ``gtex_tissue_key@1``. Tissues keep their own entries: two GTEx
tissues can share a term.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .relationship_store import make_derivation

RULE = "pext_at_variant@1"
REGIONS = "annotations.exon_usage_by_tissue"
VARIANTS = "annotations.population_variants"
TERMS = "annotations.tissue_terms"
TRANSCRIPTS = "identifiers.ensembl_transcripts"
DEFAULT_THRESHOLD = 0.1


def tissue_terms(card: Any) -> Dict[str, Any] | None:
    """Per tissue the card's pext names, GTEx's tissue and its ontology term
    (``gtex_tissue_key@1``); None when the card states no GTEx terms."""
    from sabueso.mappings.gtex import KEY_RULE, tissue_key

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


def variant_tissue_usage_view(
    card: Any, threshold: float = DEFAULT_THRESHOLD, *, _support=None
) -> Dict[str, Any]:
    """Each population variant with the pext of its region; see the module docstring."""
    regions = (card.get(REGIONS) or {}).get("value") or []
    variants = (card.get(VARIANTS) or {}).get("value") or []
    items: List[Dict[str, Any]] = []
    counts = {"in_region": 0, "outside_pext_regions": 0, "no_position": 0}
    for variant_index, variant in enumerate(variants):
        item = {
            k: variant[k]
            for k in ("variant_id", "hgvs_p", "transcript", "location", "not_placed")
            if k in variant
        }
        where = _position(variant.get("variant_id"))
        trace = {
            "variant_index": variant_index,
            "position": where,
            "region_index": None,
        }
        if _support is not None:
            _support.setdefault("items", []).append(trace)
        if where is None:
            item["pext"] = {"basis": "no_position"}
            counts["no_position"] += 1
            items.append(item)
            continue
        chromosome, position = where
        region_index = next(
            (
                i
                for i, r in enumerate(regions)
                if str(r.get("chromosome")) == chromosome
                and r.get("start") is not None
                and r["start"] <= position <= r["end"]
            ),
            None,
        )
        if region_index is None:
            item["pext"] = {"basis": "outside_pext_regions"}
            counts["outside_pext_regions"] += 1
            items.append(item)
            continue
        trace["region_index"] = region_index
        region = regions[region_index]
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
    out = {
        "items": items,
        "counts": counts,
        "rule": make_derivation(
            RULE,
            inputs=[f"{VARIANTS}.variant_id", REGIONS],
            parameters={"threshold": threshold, "assembly": "GRCh38"},
        ),
    }
    terms = tissue_terms(card)
    if terms is not None:
        out["tissue_terms"] = terms
    return out


ISOFORM_RULE = "isoform_exon_usage@2"
EXONS = "annotations.isoform_coding_exons"
ISOFORMS = "annotations.isoforms"
TISSUE_TEXT = "annotations.tissue_specificity"


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


def _pext_over(
    ranges: List[List[int]], regions: List[Dict[str, Any]], *, _support=None
) -> Tuple[Dict[str, float], int]:
    """Per tissue, the mean pext over the bases of ``ranges``, each base taking the
    value of the region that contains it; and how many bases had a value."""
    totals: Dict[str, float] = {}
    counted = 0
    for range_index, (start, end) in enumerate(ranges):
        for region_index, region in enumerate(regions):
            lo, hi = max(start, region["start"]), min(end, region["end"])
            if lo > hi:
                continue
            length = hi - lo + 1
            counted += length
            if _support is not None:
                _support.append(
                    {
                        "range_index": range_index,
                        "region_index": region_index,
                        "intersection": [lo, hi],
                        "bases": length,
                    }
                )
            for t in region.get("tissues") or []:
                if t.get("value") is not None:
                    totals[t["tissue"]] = totals.get(t["tissue"], 0.0) + (
                        t["value"] * length
                    )
    return (
        {t: v / counted for t, v in sorted(totals.items())} if counted else {}
    ), counted


def _summary(by_tissue: Dict[str, float], counted: int, threshold: float) -> Dict:
    top = max(by_tissue.items(), key=lambda kv: kv[1])
    return {
        "bases_with_pext": counted,
        "max": {"tissue": top[0], "value": top[1]},
        "at_or_above_threshold": sorted(
            t for t, v in by_tissue.items() if v >= threshold
        ),
        "by_tissue": by_tissue,
    }


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


def isoform_tissue_usage_view(
    card: Any, threshold: float = DEFAULT_THRESHOLD, *, _support=None
) -> Dict[str, Any]:
    """Per UniProt isoform: what UniProt states about its tissues, and where its own
    coding bases are expressed (gnomAD's pext), under ``isoform_exon_usage@2``.

    An isoform's own coding bases are the CDS bases (GRCh38) of the transcripts UniProt
    states for it that lie in no transcript UniProt states for another isoform. Their
    pext per tissue is the mean over those bases, each base taking the value of the
    pext region that contains it; bases outside every region do not count, and their
    number is reported. An isoform without own coding bases shares all its coding
    sequence with others (``no_own_coding_bases``).

    An isoform whose exons are not known says why (``identifiers.ensembl_transcripts``,
    UniProt's cross-references):
    - ``no_transcript_stated``: UniProt states no Ensembl transcript for it, so no
      source gives its genomic structure (Sabueso does not align);
    - ``transcript_not_in_gnomad``: UniProt states transcripts (listed) that gnomAD's
      release does not annotate;
    - ``transcripts_not_recorded``: the card was built before UniProt's transcripts
      were recorded (schema 0.3.10).
    Own bases are counted against the isoforms whose exons are known. When some are
    not (``isoforms_without_exons``), a base counted as own may be shared with one of
    them: ``own_bases_complete`` is then false, and so is
    ``variable_regions_complete``.

    Isoforms built by combining exons (tau) rarely own any base, so the view also gives
    the ``variable_regions``: the coding bases not every isoform includes, as runs
    included by the same isoforms, each with its pext. Constitutive bases are left out.
    """
    isoforms = (card.get(ISOFORMS) or {}).get("value") or []
    exons = (card.get(EXONS) or {}).get("value") or []
    regions = (card.get(REGIONS) or {}).get("value") or []
    names = {f"Isoform {i.get('name')}": i.get("isoform_id") for i in isoforms}
    text_decisions = [] if _support is not None else None
    texts = _uniprot_texts(card, names, _support=text_decisions)
    cds_of: Dict[str, List[List[int]]] = {}
    transcripts_of: Dict[str, List[str]] = {}
    for item in exons:
        cds_of.setdefault(item["isoform"], []).extend(item.get("cds") or [])
        transcripts_of.setdefault(item["isoform"], []).append(item["transcript"])
    stated = card.get(TRANSCRIPTS)
    stated_for: Dict[str, List[str]] = {}
    for x in (stated or {}).get("value") or []:
        if x.get("isoform"):
            stated_for.setdefault(x["isoform"], []).append(x["transcript"])
    without = [
        i.get("isoform_id") for i in isoforms if i.get("isoform_id") not in cds_of
    ]
    complete = not without
    if _support is not None:
        _support.update(cds_of=cds_of, transcripts_of=transcripts_of, items=[])
        _support["text_decisions"] = text_decisions
    items = []
    for isoform_index, isoform in enumerate(isoforms):
        iso_id = isoform.get("isoform_id")
        trace = {"isoform_index": isoform_index, "own_regions": [], "pext_inputs": []}
        if _support is not None:
            _support["items"].append(trace)
        entry = {
            "isoform": iso_id,
            "name": isoform.get("name"),
            "canonical": isoform.get("sequence_status") == "Displayed",
            "uniprot_tissue_specificity": texts.get(iso_id, []),
        }
        if iso_id not in cds_of:
            if stated is None:
                entry["pext"] = {"basis": "transcripts_not_recorded"}
            elif iso_id in stated_for:
                entry["pext"] = {"basis": "transcript_not_in_gnomad"}
                entry["transcripts"] = sorted(stated_for[iso_id])
            else:
                entry["pext"] = {"basis": "no_transcript_stated"}
            items.append(entry)
            continue
        others = [r for k, v in cds_of.items() if k != iso_id for r in v]
        own = _minus(cds_of[iso_id], others)
        trace["own_regions"] = own
        entry["transcripts"] = sorted(transcripts_of[iso_id])
        entry["own_coding_bases"] = sum(e - s + 1 for s, e in own)
        entry["own_bases_complete"] = complete
        if not own:
            entry["pext"] = {"basis": "no_own_coding_bases"}
            items.append(entry)
            continue
        by_tissue, counted = _pext_over(
            own,
            regions,
            _support=trace["pext_inputs"] if _support is not None else None,
        )
        if not counted:
            entry["pext"] = {"basis": "outside_pext_regions"}
            items.append(entry)
            continue
        entry["pext"] = {"own_regions": own, **_summary(by_tissue, counted, threshold)}
        items.append(entry)
    variable = []
    if _support is not None:
        _support["variable_regions"] = []
    for run in variable_regions(cds_of):
        inputs = [] if _support is not None else None
        by_tissue, counted = _pext_over(
            [[run["start"], run["end"]]], regions, _support=inputs
        )
        if _support is not None:
            _support["variable_regions"].append(inputs)
        variable.append(
            {
                **run,
                "pext": _summary(by_tissue, counted, threshold)
                if counted
                else {"basis": "outside_pext_regions"},
            }
        )
    out = {
        "items": items,
        "isoforms_without_exons": without,
        "variable_regions": variable,
        "variable_regions_complete": complete,
        "entry_tissue_specificity": texts.get(None, []),
        "rule": make_derivation(
            ISOFORM_RULE,
            inputs=[EXONS, REGIONS, ISOFORMS, TISSUE_TEXT, TRANSCRIPTS],
            parameters={
                "threshold": threshold,
                "assembly": "GRCh38",
                "summary": "mean pext over the isoform's own coding bases, and over "
                "each run of coding bases not every isoform includes",
            },
        ),
    }
    terms = tissue_terms(card)
    if terms is not None:
        out["tissue_terms"] = terms
    return out
