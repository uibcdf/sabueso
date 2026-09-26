"""Identity hygiene for protein entries (uibcdf/sabueso#55).

Three situations look alike in sequence and must not be confused:

- **redundant entries of one protein** (a cDNA submission and a genome annotation):
  often one or two differing positions;
- **paralogs**, two genes in one genome: they can be closer in sequence than redundant
  entries are (a pair of paralogs in UniProt differs in 4 of 252 positions);
- **strain variants**: entries of the same gene in different strain genomes.

Identity therefore never comes from sequence similarity. Rule ``protein_identity_audit@1``
compares two entries of related organisms and reports one finding, never a merge:

1. entries of unrelated organisms are not compared (identical sequences in human and
   chimpanzee are two entities). Relatedness is exact when both cards carry NCBI
   Taxonomy ancestors (#67), and read from UniProt names otherwise; each finding says
   which (``organisms``: ``same_taxon``, ``ncbi_lineage`` or ``names``);
2. a **shared gene locus** (VEuPathDB, NCBI Gene) with an identical or near-identical
   sequence → ``possibly_same_as``; with another sequence → ``same_gene``: isoforms,
   fragments or alleles of one gene, which are not the same entity;
3. **distinct loci within one genome** (the same taxon, loci in the same database, none
   shared) → ``distinct_genes``: paralogs, however close their sequences;
4. otherwise, an **identical sequence** (MD5) → ``possibly_same_as``; a **near-identical**
   one (same length, at most ``MAX_DIFFERENT_FRACTION`` of positions differing, compared
   position by position) → ``possibly_same_as`` with the number of differences, for a
   person to review. Sequences of different lengths are not compared: aligning them
   belongs to MolSysMT. When both entries state loci, but in databases that do not
   overlap (NCBI Gene for one, an organism database for the other), the basis says so
   (``gene_loci: not_comparable``, with each entry's databases): the gene layer could
   not decide, and a strain variant cannot be told from a close paralog (#69).

Every finding carries its basis. ``possibly_same_as`` is a flag for review, never an
identity.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

IDENTITY_RULE = "protein_identity_audit@1"
#: At most 2% of positions may differ for a near-identical flag (5 of 252).
MAX_DIFFERENT_FRACTION = 0.02


def basis_of_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """What the audit compares, from a UniProt entry (full or search result)."""
    organism = entry.get("organism") or {}
    loci = []
    for xref in entry.get("uniProtKBCrossReferences") or []:
        if xref.get("database") == "GeneID":
            loci.append(("NCBI Gene", xref["id"]))
        elif xref.get("database") == "VEuPathDB":
            component, _, gene = xref["id"].partition(":")
            if gene:
                loci.append((component, gene))
    sequence = entry.get("sequence") or {}
    return {
        "ref": f"uniprot:{entry.get('primaryAccession')}",
        "taxon_id": organism.get("taxonId"),
        "organism": organism.get("scientificName"),
        "lineage": list(organism.get("lineage") or []),
        "gene_loci": sorted(set(loci)),
        "sequence": sequence.get("value"),
        "md5": sequence.get("md5"),
    }


def basis_of_card(card: Any) -> Dict[str, Any]:
    """What the audit compares, from a protein card."""

    def value(path: str) -> Any:
        node = card.get(path)
        return node.get("value") if isinstance(node, dict) else node

    taxonomy = value("annotations.taxonomy") or {}
    return {
        "ref": card.id,
        "taxon_id": value("annotations.taxon_id"),
        "organism": value("annotations.organism"),
        "lineage": list(value("annotations.lineage") or []),
        # NCBI Taxonomy ancestor ids, when the card has them (#67).
        "ancestor_ids": [a["tax_id"] for a in taxonomy.get("ancestors") or []]
        if taxonomy
        else None,
        "gene_loci": sorted(
            {(x["database"], x["id"]) for x in value("identifiers.gene_loci") or []}
        ),
        "sequence": value("sequence.primary"),
        "md5": None,
    }


def _related(a: Dict[str, Any], b: Dict[str, Any]) -> str | None:
    """How two organisms are related, or None: ``same_taxon``, ``ncbi_lineage`` (one
    is an ancestor of the other in NCBI Taxonomy, #67), or ``names``.

    With NCBI ancestors for both, the answer is exact and final. Otherwise UniProt
    names are read: lineages of strain-level taxa can stop above the species
    ("Trypanosoma cruzi (strain CL Brener)" lists no "Trypanosoma cruzi"), so a name
    that extends the other's name counts too.
    """
    if a["taxon_id"] is not None and a["taxon_id"] == b["taxon_id"]:
        return "same_taxon"
    if a.get("ancestor_ids") is not None and b.get("ancestor_ids") is not None:
        exact = a["taxon_id"] in b["ancestor_ids"] or b["taxon_id"] in a["ancestor_ids"]
        return "ncbi_lineage" if exact else None
    x, y = a["organism"] or "", b["organism"] or ""
    by_name = (x and (x in b["lineage"] or y.startswith(x + " "))) or (
        y and (y in a["lineage"] or x.startswith(y + " "))
    )
    return "names" if by_name else None


def _differences(x: str, y: str) -> int:
    return sum(1 for i, j in zip(x, y) if i != j)


def compare(a: Dict[str, Any], b: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The finding for two entries or cards (``basis_of_*`` output), or None."""
    relation = None if a["ref"] == b["ref"] else _related(a, b)
    if relation is None:
        return None
    finding: Dict[str, Any] = {
        "refs": [a["ref"], b["ref"]],
        "rule": IDENTITY_RULE,
        "organisms": relation,
    }
    shared = sorted(set(a["gene_loci"]) & set(b["gene_loci"]))
    same_genome = a["taxon_id"] is not None and a["taxon_id"] == b["taxon_id"]
    databases = {d for d, _ in a["gene_loci"]} & {d for d, _ in b["gene_loci"]}
    sequence: Dict[str, Any] = {}
    x, y = a.get("sequence"), b.get("sequence")
    if a.get("md5") and a.get("md5") == b.get("md5"):
        sequence = {"sequence": "identical"}
    elif x and y:
        if x == y:
            sequence = {"sequence": "identical"}
        elif len(x) == len(y):
            n = _differences(x, y)
            if n <= MAX_DIFFERENT_FRACTION * len(x):
                sequence = {
                    "sequence": "near_identical",
                    "differences": n,
                    "length": len(x),
                }
    if shared:
        # One gene: the same protein entered twice when the sequences agree; otherwise
        # isoforms, fragments or alleles of that gene, which are not the same entity.
        return {
            **finding,
            "finding": "possibly_same_as" if sequence else "same_gene",
            "basis": {
                "shared_gene_loci": [list(x) for x in shared],
                **(
                    sequence
                    or {
                        "lengths": [
                            len(a.get("sequence") or ""),
                            len(b.get("sequence") or ""),
                        ]
                    }
                ),
            },
        }
    if same_genome and databases:
        # Two loci of one genome are two genes, whatever their sequences say.
        return {
            **finding,
            "finding": "distinct_genes",
            "basis": {
                "gene_loci": [
                    [list(locus) for locus in a["gene_loci"] if locus[0] in databases],
                    [list(locus) for locus in b["gene_loci"] if locus[0] in databases],
                ],
                **sequence,
            },
        }
    if sequence:
        basis = dict(sequence)
        if a["gene_loci"] and b["gene_loci"] and not databases:
            # Both state loci, in databases that do not overlap (NCBI Gene here, an
            # organism database there): the gene layer could not decide (#69).
            basis["gene_loci"] = "not_comparable"
            basis["loci_databases"] = [
                sorted({d for d, _ in a["gene_loci"]}),
                sorted({d for d, _ in b["gene_loci"]}),
            ]
        return {**finding, "finding": "possibly_same_as", "basis": basis}
    return None


def audit(bases: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Every finding among the pairs of ``bases``, in input order."""
    items = list(bases)
    out = []
    for i, a in enumerate(items):
        for b in items[i + 1 :]:
            found = compare(a, b)
            if found:
                out.append(found)
    return out


def derivation() -> Dict[str, Any]:
    from .relationship_store import make_derivation

    return make_derivation(
        IDENTITY_RULE,
        inputs=[
            "annotations.taxon_id",
            "annotations.lineage",
            "identifiers.gene_loci",
            "sequence",
        ],
        parameters={
            "max_different_fraction": MAX_DIFFERENT_FRACTION,
            "order": [
                "unrelated organisms: not compared",
                "shared gene locus: possibly_same_as if the sequences agree, else same_gene",
                "distinct loci in one genome: distinct_genes",
                "identical or near-identical sequence: possibly_same_as",
            ],
            "sequence_comparison": "position by position, equal lengths only",
        },
    )


def pairs_to_relationships(findings: List[Dict[str, Any]]) -> List[Any]:
    """``possibly_same_as`` relationships for the findings that raise one."""
    from .relationship_store import make_relationship

    rule = derivation()
    return [
        make_relationship(
            f["refs"][0],
            "possibly_same_as",
            f["refs"][1],
            qualifiers={"basis": f["basis"]},
            derivation={**rule, "inputs": list(f["refs"])},
        )
        for f in findings
        if f["finding"] == "possibly_same_as"
    ]
