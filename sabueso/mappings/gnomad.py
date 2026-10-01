"""gnomAD variants → ``annotations.population_variants`` (#83).

One item per gnomAD variant with a protein change (``hgvsp``): its id
(chromosome-position-ref-alt, GRCh38), consequence, transcript, HGVS, flags, and the
allele count, allele number and frequency in exomes and genomes, as gnomAD states them.
Variants without a protein change are left out and counted by the caller.

gnomAD is asked twice (#85): for the gene, where it states each variant's consequence
on the one transcript it ranks most severe, and for each Ensembl transcript the UniProt
entry states for its canonical isoform, where it states the consequence on that
transcript, with its version (``merged``). A variant keeps:

- its consequence on the canonical transcript, when gnomAD states a protein change there;
  it is then read in UniProt numbering as stated (the residue must still match);
- otherwise its consequence on the other transcript, placed as ``_hgvs.place`` does
  (through UniProt's isoform map, or not placed). When gnomAD states that the variant
  changes no residue of the canonical transcript (it is intronic or in a UTR there),
  the item records that consequence (``canonical_consequence``) and is not placed
  (``not_coding_on_canonical``): the same DNA change can shift a residue on one isoform
  and none on the other, so the isoform map is not applied to it.
- a change the isoform map would place, and the transcript query does not state (it
  lies in an intron of the canonical transcript, beyond the query's margin, or outside
  it), is asked of gnomAD variant by variant (#102): a protein change on the canonical
  transcript is read as stated, a non-coding consequence there gives
  ``not_coding_on_canonical``, and none at all ``no_consequence_on_canonical``. PKM's
  M1 exon and KRAS's exon 4A are such exons: identical residues flank the segment
  UniProt marks as different, so the isoform map placed changes the canonical protein
  never carries.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from sabueso.core.source_assertion_store import make_source_assertion

from ._hgvs import place

SOURCE = "gnomAD"
FIELD = "annotations.population_variants"


def _frequencies(block: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not block:
        return None
    return {k: block.get(k) for k in ("ac", "an", "af")}


def merged(
    gene_variants: List[Dict[str, Any]],
    canonical_records: List[Dict[str, Any]],
    consequences: Dict[str, List[Dict[str, Any]]] | None = None,
    canonical_transcripts: Iterable[str] = (),
) -> Tuple[List[Dict[str, Any]], int]:
    """The variants to keep (see the module docstring), and how many of the variants
    gnomAD states change no residue of any transcript it names.

    ``consequences`` are what gnomAD states, variant by variant, on every transcript,
    for the changes the isoform map would otherwise place: their consequence on a
    canonical transcript is used the same way, and a variant with none there is
    marked ``no_canonical_consequence``."""
    canonical_set = set(canonical_transcripts)
    on_canonical: Dict[str, Dict[str, Any]] = {}
    for record in canonical_records:
        for variant in record.get("variants") or []:
            kept = on_canonical.get(variant["variant_id"])
            if kept is None or (variant.get("hgvsp") and not kept.get("hgvsp")):
                on_canonical[variant["variant_id"]] = variant
    out, seen = [], set()
    for variant in gene_variants:
        stated = on_canonical.get(variant["variant_id"])
        if stated is not None and stated.get("hgvsp"):
            out.append(stated)
        elif (
            variant.get("hgvsp")
            and stated is None
            and consequences
            and (variant["variant_id"] in consequences)
        ):
            variant = _from_consequences(
                variant, consequences[variant["variant_id"]], canonical_set
            )
            out.append(variant)
        elif variant.get("hgvsp"):
            if stated is not None:
                variant = {
                    **variant,
                    "canonical_consequence": {
                        "transcript": stated.get("transcript_id"),
                        "transcript_version": stated.get("transcript_version"),
                        "consequence": stated.get("consequence"),
                        "hgvs_c": stated.get("hgvsc"),
                    },
                }
            out.append(variant)
        else:
            continue
        seen.add(variant["variant_id"])
    for variant_id, stated in on_canonical.items():
        if stated.get("hgvsp") and variant_id not in seen:
            out.append(stated)
            seen.add(variant_id)
    every = {v["variant_id"] for v in gene_variants} | set(on_canonical)
    return out, len(every) - len(out)


def _from_consequences(
    variant: Dict[str, Any],
    stated: List[Dict[str, Any]],
    canonical: set,
) -> Dict[str, Any]:
    """A gene variant read with what gnomAD states on the canonical transcript."""
    on_canonical = [c for c in stated if c.get("transcript_id") in canonical]
    coding = next((c for c in on_canonical if c.get("hgvsp")), None)
    if coding is not None:
        return {
            **variant,
            "transcript_id": coding.get("transcript_id"),
            "transcript_version": coding.get("transcript_version"),
            "hgvsp": coding.get("hgvsp"),
            "hgvsc": coding.get("hgvsc"),
            "consequence": coding.get("major_consequence"),
        }
    if on_canonical:
        c = on_canonical[0]
        return {
            **variant,
            "canonical_consequence": {
                "transcript": c.get("transcript_id"),
                "transcript_version": c.get("transcript_version"),
                "consequence": c.get("major_consequence"),
                "hgvs_c": c.get("hgvsc"),
            },
        }
    return {**variant, "no_canonical_consequence": True}


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
            "transcript_version": variant.get("transcript_version"),
            "hgvs_c": variant.get("hgvsc"),
            "hgvs_p": variant.get("hgvsp"),
            "flags": variant.get("flags") or [],
            "exome": _frequencies(variant.get("exome")),
            "genome": _frequencies(variant.get("genome")),
        }
        if variant.get("no_canonical_consequence"):
            placed = {"not_placed": "no_consequence_on_canonical"}
        elif variant.get("canonical_consequence"):
            item["canonical_consequence"] = {
                k: v for k, v in variant["canonical_consequence"].items() if v
            }
            placed = {"not_placed": "not_coding_on_canonical"}
        else:
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


PEXT_FIELD = "annotations.exon_usage_by_tissue"


def map_pext(
    record: Dict[str, Any],
    accession: str,
    retrieved_at: str,
    version: str | None,
) -> Dict[str, Any]:
    """gnomAD's pext of a gene → ``annotations.exon_usage_by_tissue`` (#102).

    One item per coding region gnomAD states: the gene, the region in GRCh38, the mean
    over tissues, and per GTEx v10 tissue the share of the gene's expression that
    includes the region, as stated. Nothing is placed in UniProt numbering here: a
    variant's genomic position meets its region in the view (``pext_at_variant@1``).
    """
    gene = record.get("gene") or {}
    items, assertions = [], []
    for region in (record.get("pext") or {}).get("regions") or []:
        item = {
            "gene": gene.get("gene_id"),
            "assembly": "GRCh38",
            "chromosome": gene.get("chrom"),
            "start": region.get("start"),
            "end": region.get("stop"),
            "mean": region.get("mean"),
            "tissues": [
                {"tissue": t.get("tissue"), "value": t.get("value")}
                for t in region.get("tissues") or []
            ],
        }
        assertion = make_source_assertion(
            PEXT_FIELD,
            item,
            SOURCE,
            f"pext:{gene.get('gene_id')}:{region.get('start')}-{region.get('stop')}",
            retrieved_at,
            subject_ref=f"uniprot:{accession}",
        )
        if version is not None:
            assertion["source"]["version"] = str(version)
        items.append(item)
        assertions.append(assertion)
    return {
        "fields": {PEXT_FIELD: items} if items else {},
        "source_assertions": assertions,
        "field_source_assertions": {PEXT_FIELD: [a["id"] for a in assertions]}
        if assertions
        else {},
        "relationships": [],
    }
