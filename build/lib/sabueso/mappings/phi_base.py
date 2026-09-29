"""PHI-base curation sessions → ``annotations.pathogen_phenotypes`` (uibcdf/sabueso#83).

One item per phenotype annotation whose pathogen genotype includes an allele of the
card's gene: what the curators state happens to the pathogen, alone or on its host.

- ``annotation_type``: PHI-base's (``pathogen_host_interaction_phenotype``,
  ``pathogen_phenotype`` or ``gene_for_gene_phenotype``).
- ``phenotype``: the PHIPO term. ``extensions`` keep its qualifiers as stated
  (``infective_ability`` → "reduced virulence", ``infects_tissue``, a chemical…).
  ``high_level_terms`` are PHI-base's own summary ("Reduced virulence", "Lethal").
- ``genotype``: every allele of the genotype, this gene's and any other's. A phenotype
  of a double mutant is never read as the single gene's.
- ``pathogen`` and ``host`` (taxon and strain), the ``diseases`` curated for the same
  pathogen–host pair, ``conditions``, the ``method`` (PHI-base's ``evidence_code``,
  verbatim), ``phi_ids``, the
  ``publication`` and the curator's comment, verbatim.

Nothing is classified: "lethal" or "reduced virulence" is PHI-base's statement about a
mutant in an experiment, kept with its genotype, host and publication.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.snapshot import canonical_json
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "PHI-base"
FIELD = "annotations.pathogen_phenotypes"
PHENOTYPE_TYPES = (
    "pathogen_host_interaction_phenotype",
    "pathogen_phenotype",
    "gene_for_gene_phenotype",
)


def _publication(ref: str | None) -> str | None:
    if not ref:
        return None
    prefix, _, value = ref.partition(":")
    return f"pubmed:{value}" if prefix.upper() == "PMID" else ref


def _organism(session: Dict[str, Any], genotype_id: str | None) -> Dict[str, Any]:
    genotype = (session.get("genotypes") or {}).get(genotype_id or "") or {}
    taxon = genotype.get("organism_taxonid")
    name = ((session.get("organisms") or {}).get(str(taxon)) or {}).get("full_name")
    return {
        k: v
        for k, v in (
            ("taxon_id", taxon),
            ("name", name),
            ("strain", genotype.get("organism_strain")),
        )
        if v not in (None, "")
    }


def _alleles(session: Dict[str, Any], genotype_id: str) -> List[Dict[str, Any]]:
    genotype = (session.get("genotypes") or {}).get(genotype_id) or {}
    alleles = session.get("alleles") or {}
    genes = session.get("genes") or {}
    out = []
    for locus in genotype.get("loci") or []:
        for entry in locus:
            allele = alleles.get(entry.get("id")) or {}
            gene = genes.get(allele.get("gene") or "") or {}
            item = {
                "gene": (gene.get("uniprot_data") or {}).get("uniprot_id")
                or gene.get("uniquename"),
                "allele": allele.get("name"),
                "allele_type": allele.get("allele_type"),
                "expression": entry.get("expression"),
            }
            out.append({k: v for k, v in item.items() if v not in (None, "")})
    return out


def _item(
    session: Dict[str, Any], annotation: Dict[str, Any], accession: str
) -> Dict[str, Any] | None:
    metagenotypes = session.get("metagenotypes") or {}
    host_id = None
    if annotation.get("metagenotype"):
        meta = metagenotypes.get(annotation["metagenotype"]) or {}
        pathogen_id, host_id = meta.get("pathogen_genotype"), meta.get("host_genotype")
    else:
        pathogen_id = annotation.get("genotype")
    if not pathogen_id:
        return None
    genotype = _alleles(session, pathogen_id)
    if accession not in {a.get("gene") for a in genotype}:
        return None
    diseases = sorted(
        {
            a["term"]
            for a in session.get("annotations") or []
            if a.get("type") == "disease_name"
            and a.get("term")
            and a.get("metagenotype") == annotation.get("metagenotype")
            and annotation.get("metagenotype")
        }
    )
    item = {
        "annotation_type": annotation.get("type"),
        "phenotype": annotation.get("term"),
        "extensions": [
            {
                k: v
                for k, v in (
                    ("relation", e.get("relation")),
                    ("term", e.get("rangeValue")),
                    ("label", e.get("rangeDisplayName")),
                )
                if v not in (None, "")
            }
            for e in annotation.get("extension") or []
        ],
        "high_level_terms": list(annotation.get("high_level_terms") or []),
        "genotype": genotype,
        "pathogen": _organism(session, pathogen_id),
        "host": _organism(session, host_id) if host_id else None,
        "diseases": diseases,
        "conditions": list(annotation.get("conditions") or []),
        # PHI-base's "evidence_code" states how the phenotype was observed (e.g. "Cell
        # growth assay"); "evidence" is Nextia's term, so it is kept as the method.
        "method": annotation.get("evidence_code"),
        "phi_ids": list(annotation.get("phi4_id") or []),
        "publication": _publication(annotation.get("publication")),
        "curator_comment": annotation.get("submitter_comment"),
    }
    return {k: v for k, v in item.items() if v not in (None, "", [], {})}


def map_phenotypes(
    sessions: List[Dict[str, Any]],
    accession: str,
    retrieved_at: str,
    version: str | None,
) -> Dict[str, Any]:
    """The phenotype items PHI-base states for the gene, with one SourceAssertion each."""
    items: List[tuple] = []
    for session in sessions:
        for annotation in session.get("annotations") or []:
            if annotation.get("type") not in PHENOTYPE_TYPES:
                continue
            item = _item(session, annotation, accession)
            if item is not None:
                record = (item.get("phi_ids") or [f"session:{session.get('session')}"])[
                    0
                ]
                items.append((item, record))
    items.sort(key=lambda pair: canonical_json(pair[0]))
    assertions = []
    for item, record in items:
        assertion = make_source_assertion(
            FIELD,
            item,
            SOURCE,
            record,
            retrieved_at,
            subject_ref=f"uniprot:{accession}",
        )
        if version is not None:
            assertion["source"]["version"] = str(version)
        assertions.append(assertion)
    fields = {FIELD: [item for item, _ in items]} if items else {}
    return {
        "fields": fields,
        "source_assertions": assertions,
        "field_source_assertions": {FIELD: [a["id"] for a in assertions]}
        if assertions
        else {},
        "relationships": [],
    }
