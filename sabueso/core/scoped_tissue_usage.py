"""Versioned genomic scope and per-tissue coverage, without acquisition (#138).

A base contributes once only when all covering records state the same finite pext
for that tissue. Missing values and disagreements are counted separately. A mean
uses only that tissue's resolved bases, never bases of an unmeasured tissue.
"""

from collections import defaultdict
from math import isfinite

from .relationship_store import make_derivation
from .tissue_usage import (
    EXONS,
    ISOFORMS,
    REGIONS,
    TISSUE_TEXT,
    TRANSCRIPTS,
    VARIANTS,
    _merge,
    _minus,
    _position,
    _uniprot_texts,
    tissue_terms,
    variable_regions,
)

VARIANT_RULE = "pext_at_variant@2"
ISOFORM_RULE = "isoform_exon_usage@3"


def check_arguments(threshold, usage_rule, *, kind):
    from sabueso._private.argdigest._shared import refuse
    from sabueso._private.argdigest.argument.threshold import digest_threshold
    from sabueso._private.argdigest.argument.usage_rule import digest_usage_rule

    caller = f"sabueso.core.card.{kind}_tissue_usage"
    digest_threshold(threshold, caller=caller)
    digest_usage_rule(usage_rule, caller=caller)
    allowed = (
        {"pext_at_variant@1", VARIANT_RULE}
        if kind == "variant"
        else {"isoform_exon_usage@2", ISOFORM_RULE}
    )
    if usage_rule not in allowed:
        raise refuse(
            "usage_rule", usage_rule, caller, f"expected one of {sorted(allowed)}"
        )


def _values(card, path):
    return (card.get(path) or {}).get("value") or []


def _axis(row):
    assembly, chromosome = row.get("assembly"), row.get("chromosome")
    if not isinstance(assembly, str) or not assembly or chromosome in (None, ""):
        return None
    return assembly, str(chromosome)


def _interval(start, end):
    return (
        isinstance(start, int)
        and not isinstance(start, bool)
        and isinstance(end, int)
        and not isinstance(end, bool)
        and 1 <= start <= end
    )


def _variant_scope(card, variant, position):
    """Use a row's explicit assembly or matching selected assertion metadata.

    Historical dataset/version labels alone cannot prove a coordinate scope. The
    current gnomAD mapping preserves its requested assembly as acquisition context,
    explicitly distinct from a native response echo or independently verified release.
    """
    if not position:
        return {"status": "no_position", "basis": "variant_id_first_genomic_base"}
    assemblies = set()
    refs = []
    if isinstance(variant.get("assembly"), str) and variant["assembly"]:
        assemblies.add(variant["assembly"])
    node = card.get(VARIANTS) or {}
    for assertion_id in node.get("source_assertion_ids") or []:
        assertion = card.source_assertion_store.get(assertion_id)
        if not assertion or assertion.get("field_path") != VARIANTS:
            continue
        value = assertion.get("asserted_value")
        if value != variant and value != node.get("value"):
            continue
        scope = (assertion.get("source_metadata") or {}).get("coordinate_scope") or {}
        assembly = scope.get("assembly")
        if isinstance(assembly, str) and assembly:
            assemblies.add(assembly)
            refs.append(assertion_id)
    status = (
        "confirmed"
        if len(assemblies) == 1
        else "incompatible"
        if assemblies
        else "missing"
    )
    return {
        "status": status,
        "assembly": next(iter(assemblies)) if len(assemblies) == 1 else None,
        "assembly_candidates": sorted(assemblies),
        "chromosome": position[0],
        "position": position[1],
        "source_assertion_ids": refs,
        "basis": "explicit_record_or_selected_assertion_coordinate_context",
        "native_release_identity": "not_independently_verified",
    }


def _eligible_regions(regions, axis):
    eligible, excluded = [], []
    for i, region in enumerate(regions):
        candidate = _axis(region)
        reason = (
            "genomic_scope_missing"
            if candidate is None
            else "incompatible_genomic_scope"
            if candidate != axis
            else "invalid_genomic_interval"
            if not _interval(region.get("start"), region.get("end"))
            else None
        )
        if reason:
            excluded.append({"region_index": i, "reason": reason})
        else:
            eligible.append((i, region))
    return eligible, excluded


def _no_eligible_basis(excluded):
    for reason in (
        "genomic_scope_missing",
        "incompatible_genomic_scope",
        "invalid_genomic_interval",
    ):
        if any(row["reason"] == reason for row in excluded):
            return reason
    return "outside_pext_regions"


def _transcript_matches(stated, row):
    transcript = row.get("transcript")
    if not stated or not transcript or stated.split(".")[0] != transcript.split(".")[0]:
        return False
    version = row.get("transcript_version")
    if "." in transcript:
        suffix = transcript.rsplit(".", 1)[1]
        if version is not None and str(version) != suffix:
            return False
        version = suffix
    return "." not in stated or (
        version is not None and stated.rsplit(".", 1)[1] == str(version)
    )


def _tissue_value(region, tissue):
    values = [
        t.get("value") for t in region.get("tissues") or [] if t.get("tissue") == tissue
    ]
    valid = [
        v
        for v in values
        if isinstance(v, (int, float))
        and not isinstance(v, bool)
        and 0 <= v <= 1
        and isfinite(v)
    ]
    if len(set(valid)) > 1:
        return "conflicting", None
    if not values or len(valid) != len(values):
        return "missing", None
    return "resolved", valid[0]


def _coverage(ranges, eligible, threshold, *, _support=None):
    """Partition closed intervals; never sum overlapping record lengths."""
    names = sorted(
        {
            t["tissue"]
            for _, r in eligible
            for t in r.get("tissues") or []
            if isinstance(t.get("tissue"), str) and t["tissue"]
        }
    )
    coverage = {
        t: {
            "bases_with_value": 0,
            "bases_missing_value": 0,
            "bases_conflicting_value": 0,
        }
        for t in names
    }
    totals = dict.fromkeys(names, 0.0)
    covered, overlap_bases = 0, 0
    segments = []
    for start, end in _merge(ranges):
        cuts = {start, end + 1}
        for _, region in eligible:
            lo, hi = max(start, region["start"]), min(end, region["end"])
            if lo <= hi:
                cuts.update((lo, hi + 1))
        points = sorted(cuts)
        for lo, nxt in zip(points, points[1:]):
            hi, length = nxt - 1, nxt - lo
            records = [
                (i, r) for i, r in eligible if r["start"] <= lo and hi <= r["end"]
            ]
            if records:
                covered += length
            if len(records) > 1:
                overlap_bases += length
            decisions = {}
            for tissue in names:
                states = [_tissue_value(r, tissue) for _, r in records]
                stated = {v for status, v in states if status == "resolved"}
                status = (
                    "conflicting"
                    if len(stated) > 1 or any(s == "conflicting" for s, _ in states)
                    else "missing"
                    if not states or any(s == "missing" for s, _ in states)
                    else "resolved"
                )
                key = {
                    "resolved": "bases_with_value",
                    "missing": "bases_missing_value",
                    "conflicting": "bases_conflicting_value",
                }[status]
                coverage[tissue][key] += length
                value = next(iter(stated)) if status == "resolved" else None
                if value is not None:
                    totals[tissue] += value * length
                decisions[tissue] = {"status": status, "value": value}
            segments.append(
                {
                    "intersection": [lo, hi],
                    "bases": length,
                    "region_indices": [i for i, _ in records],
                    "tissues": decisions,
                }
            )
    total_bases = sum(e - s + 1 for s, e in _merge(ranges))
    by_tissue = {
        t: totals[t] / c["bases_with_value"] if c["bases_with_value"] else None
        for t, c in coverage.items()
    }
    for c in coverage.values():
        c["complete"] = c["bases_with_value"] == total_bases
    known = {t: v for t, v in by_tissue.items() if v is not None}
    top = max(known.items(), key=lambda kv: kv[1]) if known else None
    if _support is not None:
        _support.extend(segments)
    return {
        "basis": "resolved_tissue_values"
        if known
        else "outside_pext_regions"
        if not covered
        else "no_resolved_tissue_values",
        "bases_with_pext": covered,
        "bases_without_pext": total_bases - covered,
        "overlapping_bases": overlap_bases,
        "coverage_by_tissue": coverage,
        "by_tissue": by_tissue,
        "max": {"tissue": top[0], "value": top[1]} if top else None,
        "at_or_above_threshold": sorted(t for t, v in known.items() if v >= threshold),
        "denominator": "resolved_bases_per_tissue",
        "overlap_policy": "all_covering_records_must_state_the_same_value",
    }


def _out(card, view, rule, inputs, threshold):
    view["rule"] = make_derivation(
        rule,
        inputs=inputs,
        parameters={
            "threshold": threshold,
            "coordinate_policy": "explicit_equal_assembly_and_chromosome",
            "overlap_policy": "all_covering_records_must_state_the_same_value",
            "denominator": "resolved_bases_per_tissue",
        },
    )
    terms = tissue_terms(card)
    if terms is not None:
        view["tissue_terms"] = terms
    return view


def variant_view(card, threshold, *, _support=None):
    regions = _values(card, REGIONS)
    items, counts = [], defaultdict(int)
    for index, variant in enumerate(_values(card, VARIANTS)):
        position = _position(variant.get("variant_id"))
        if position and (not position[0] or position[1] < 1):
            position = None
        scope = _variant_scope(card, variant, position)
        trace = {
            "variant_index": index,
            "coordinate_scope": scope,
            "segments": [],
            "excluded_regions": [],
        }
        item = {
            k: variant[k]
            for k in ("variant_id", "hgvs_p", "transcript", "location", "not_placed")
            if k in variant
        }
        item["coordinate_scope"] = scope
        if scope["status"] != "confirmed":
            basis = (
                "no_position"
                if scope["status"] == "no_position"
                else "genomic_scope_missing"
                if scope["status"] == "missing"
                else "incompatible_genomic_scope"
            )
            item["pext"] = {"basis": basis}
        else:
            eligible, excluded = _eligible_regions(
                regions, (scope["assembly"], scope["chromosome"])
            )
            trace["excluded_regions"] = excluded
            # A variant summarizes its first genomic base; no protein-location join.
            item["pext"] = _coverage(
                [[position[1], position[1]]],
                eligible,
                threshold,
                _support=trace["segments"],
            )
            if not eligible and regions:
                item["pext"]["basis"] = _no_eligible_basis(excluded)
            # Only a single unambiguous stated region contributes its source mean.
            indices = trace["segments"][0]["region_indices"]
            if len(indices) == 1:
                row = regions[indices[0]]
                item["pext"]["region"] = {"start": row["start"], "end": row["end"]}
                item["pext"]["mean"] = row.get("mean")
        counts[item["pext"]["basis"]] += 1
        items.append(item)
        if _support is not None:
            _support.setdefault("items", []).append(trace)
    return _out(
        card,
        {"items": items, "counts": dict(counts)},
        VARIANT_RULE,
        [VARIANTS, REGIONS],
        threshold,
    )


def isoform_view(card, threshold, *, _support=None):
    isoforms, exons, regions, transcripts = (
        _values(card, p) for p in (ISOFORMS, EXONS, REGIONS, TRANSCRIPTS)
    )
    ids = {i.get("isoform_id") for i in isoforms}
    names = {f"Isoform {i.get('name')}": i.get("isoform_id") for i in isoforms}
    decisions = []
    texts = _uniprot_texts(card, names, _support=decisions)
    cds, txs, axes, excluded = {}, defaultdict(list), set(), []
    invalid_isoforms = set()
    stated_for = defaultdict(list)
    for row in transcripts:
        if row.get("isoform") in ids:
            stated_for[row["isoform"]].append(row.get("transcript"))
    for index, row in enumerate(exons):
        iso_id, axis = row.get("isoform"), _axis(row)
        tx = row.get("transcript")
        # Versioned source identities remain visible; unequal explicit versions are
        # incompatible, rather than being silently stripped for correspondence.
        matching = [t for t in stated_for[iso_id] if _transcript_matches(t, row)]
        reason = (
            "isoform_not_on_card"
            if iso_id not in ids
            else "transcript_link_not_stated"
            if not matching
            else "genomic_scope_missing"
            if axis is None
            else "invalid_genomic_interval"
            if not row.get("cds")
            or any(len(r) != 2 or not _interval(*r) for r in row["cds"])
            else None
        )
        if reason:
            excluded.append({"exon_index": index, "reason": reason, "isoform": iso_id})
            if iso_id in ids:
                invalid_isoforms.add(iso_id)
            continue
        axes.add(axis)
        cds.setdefault(iso_id, []).extend(row["cds"])
        txs[iso_id].append(tx)
    for iso_id in invalid_isoforms:
        cds.pop(iso_id, None)
    compatible = len(axes) <= 1
    axis = next(iter(axes)) if len(axes) == 1 else None
    without = [i.get("isoform_id") for i in isoforms if i.get("isoform_id") not in cds]
    missing_transcripts = {
        iso_id: [
            t
            for t in stated
            if not any(
                row.get("isoform") == iso_id
                and _transcript_matches(t, row)
                and i not in {r["exon_index"] for r in excluded}
                for i, row in enumerate(exons)
            )
        ]
        for iso_id, stated in stated_for.items()
    }
    missing_transcripts = {k: v for k, v in missing_transcripts.items() if v}
    complete = not without and not missing_transcripts and compatible
    eligible, rejected = _eligible_regions(regions, axis) if axis else ([], [])
    trace = {
        "items": [],
        "variable_regions": [],
        "text_decisions": decisions,
        "excluded_exons": excluded,
        "excluded_regions": rejected,
        "cds_of": cds,
        "axis": axis,
    }
    items = []
    for index, isoform in enumerate(isoforms):
        iso_id = isoform.get("isoform_id")
        item = {
            "isoform": iso_id,
            "name": isoform.get("name"),
            "canonical": isoform.get("sequence_status") == "Displayed",
            "uniprot_tissue_specificity": texts.get(iso_id, []),
        }
        inputs = {"isoform_index": index, "own_regions": [], "segments": []}
        if not compatible:
            item["pext"] = {"basis": "incompatible_genomic_scope"}
        elif iso_id not in cds:
            basis = (
                "unsupported_coding_exons"
                if iso_id in invalid_isoforms
                else "transcripts_not_recorded"
                if card.get(TRANSCRIPTS) is None
                else "transcript_not_in_gnomad"
                if stated_for[iso_id]
                else "no_transcript_stated"
            )
            item["pext"] = {"basis": basis}
            if stated_for[iso_id]:
                item["transcripts"] = sorted(stated_for[iso_id])
        else:
            own = _minus(
                cds[iso_id], [r for k, rows in cds.items() if k != iso_id for r in rows]
            )
            inputs["own_regions"] = own
            item.update(
                transcripts=sorted(txs[iso_id]),
                own_coding_bases=sum(e - s + 1 for s, e in own),
                own_bases_complete=complete,
            )
            if own:
                item["pext"] = {
                    "own_regions": own,
                    **_coverage(own, eligible, threshold, _support=inputs["segments"]),
                }
                if not eligible and regions:
                    item["pext"]["basis"] = _no_eligible_basis(rejected)
            else:
                item["pext"] = {"basis": "no_own_coding_bases"}
        items.append(item)
        trace["items"].append(inputs)
    variable = []
    if compatible:
        for run in variable_regions(cds):
            segments = []
            pext = _coverage(
                [[run["start"], run["end"]]], eligible, threshold, _support=segments
            )
            if not eligible and regions:
                pext["basis"] = _no_eligible_basis(rejected)
            variable.append({**run, "pext": pext})
            trace["variable_regions"].append(segments)
    if _support is not None:
        _support.update(trace)
    return _out(
        card,
        {
            "items": items,
            "isoforms_without_exons": without,
            "transcripts_without_coding_exons": missing_transcripts,
            "variable_regions": variable,
            "variable_regions_complete": complete,
            "entry_tissue_specificity": texts.get(None, []),
            "coordinate_scope": {
                "status": "incompatible"
                if not compatible
                else "confirmed"
                if axis
                else "missing",
                "assembly": axis[0] if axis else None,
                "chromosome": axis[1] if axis else None,
            },
            "excluded_coding_exons": excluded,
            "excluded_pext_regions": rejected,
        },
        ISOFORM_RULE,
        [EXONS, REGIONS, ISOFORMS, TISSUE_TEXT, TRANSCRIPTS],
        threshold,
    )
