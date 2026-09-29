"""gnomAD variants → ``annotations.population_variants`` (#83).

One item per gnomAD variant with a protein change (``hgvsp``): its id
(chromosome-position-ref-alt, GRCh38), consequence, transcript, HGVS, flags, and the
allele count, allele number and frequency in exomes and genomes, as gnomAD states them.
Variants without a protein change are left out and counted by the caller.

A variant is placed in UniProt numbering only through an Ensembl transcript the UniProt
entry states for its canonical isoform, and a matching residue (``_hgvs.place``).
gnomAD's transcript ids carry no version, so the residue check is the guard against a
changed sequence.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.source_assertion_store import make_source_assertion

from ._hgvs import place

SOURCE = "gnomAD"
FIELD = "annotations.population_variants"


def _frequencies(block: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not block:
        return None
    return {k: block.get(k) for k in ("ac", "an", "af")}


def map_variants(
    variants: List[Dict[str, Any]],
    accession: str,
    context: Dict[str, Any],
    retrieved_at: str,
    version: str | None,
) -> Dict[str, Any]:
    items, assertions = [], []
    for variant in variants:
        if not variant.get("hgvsp"):
            continue
        item = {
            "variant_id": variant.get("variant_id"),
            "consequence": variant.get("consequence"),
            "transcript": variant.get("transcript_id"),
            "hgvs_c": variant.get("hgvsc"),
            "hgvs_p": variant.get("hgvsp"),
            "flags": variant.get("flags") or [],
            "exome": _frequencies(variant.get("exome")),
            "genome": _frequencies(variant.get("genome")),
        }
        placed = place(
            item["hgvs_p"],
            item["transcript"],
            context["canonical"],
            context["sequence"],
            context["isoform_of"],
            context["maps"],
        )
        item.update(placed)
        item["numbering"] = "uniprot" if "location" in placed else item["transcript"]
        item = {k: v for k, v in item.items() if v not in (None, "", [])}
        assertion = make_source_assertion(
            FIELD,
            item,
            SOURCE,
            f"{variant.get('variant_id')}:{variant.get('transcript_id')}",
            retrieved_at,
            subject_ref=f"uniprot:{accession}",
        )
        if version is not None:
            assertion["source"]["version"] = str(version)
        items.append(item)
        assertions.append(assertion)
    return {
        "fields": {FIELD: items} if items else {},
        "source_assertions": assertions,
        "field_source_assertions": {FIELD: [a["id"] for a in assertions]}
        if assertions
        else {},
        "relationships": [],
    }
