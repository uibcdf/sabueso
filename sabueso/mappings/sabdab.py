"""SAbDab antibody instances → ``annotations.antibody_complexes`` (#83).

One item per SAbDab antibody instance with an antigen that is this protein, as SAbDab
states it: the structure and model, the heavy and light chains (PDB chain, chain type,
V gene subgroup; a nanobody has no light chain), the chains of this protein among the
antigens, and every antigen SAbDab assigns to the antibody (name, type, PDB entity and
chain), so that a complex with other proteins shows them.

**Joined only through stated identity.** An antigen is this protein when it is a
protein or peptide chain that UniProt states is this protein in that PDB entry (the
entry's PDB cross-reference, ``Chains=A/B=…``). The antigen names SAbDab writes are
never used to join, and a hapten, sugar or ion (SAbDab gives it the chain of the
polymer it is attached to) never makes a protein an antigen.

**What "antigen" means here** is SAbDab's assignment in the structure: the chains it
finds bound to the antibody. In a complex several proteins can be antigens of one
antibody (a Fab bound to an arrestin–receptor complex lists both); it is not a
statement that the antibody recognises each of them.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.source_assertion_store import make_source_assertion

from .skempi import chains_of

SOURCE = "SAbDab"
FIELD = "annotations.antibody_complexes"
PROTEIN_TYPES = ("PROTEIN", "PEPTIDE")


def _chain(stated: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not stated:
        return None
    item = {
        "chain": stated.get("PDB auth_asym_id"),
        "entity": stated.get("PDB entity"),
        "type": stated.get("chain type"),
        "v_gene_subgroup": stated.get("V gene subgroup"),
    }
    return {k: v for k, v in item.items() if v not in (None, "")}


def map_complexes(
    record: Dict[str, List[Dict[str, Any]]],
    accession: str,
    entry: Dict[str, Any],
    retrieved_at: str,
    version: str | None,
) -> Dict[str, Any]:
    items, assertions = [], []
    for pdb_id in sorted(record):
        mine = chains_of(entry, pdb_id)
        for n, instance in enumerate(record[pdb_id]):
            antigens = instance.get("antigen_instances") or []
            this = sorted(
                {
                    a.get("PDB auth_asym_id")
                    for a in antigens
                    if a.get("entity type") in PROTEIN_TYPES
                    and a.get("PDB auth_asym_id") in mine
                }
            )
            if not this:
                continue
            item = {
                "structure": f"pdb:{pdb_id}",
                "model": instance.get("model"),
                "heavy_chain": _chain(instance.get("heavy chain")),
                "light_chain": _chain(instance.get("light chain")),
                "antigen_chains": this,
                "antigens": [
                    {
                        k: v
                        for k, v in {
                            "name": a.get("antigen name"),
                            "type": a.get("entity type"),
                            "entity": a.get("PDB entity"),
                            "chain": a.get("PDB auth_asym_id"),
                            "this_protein": a.get("entity type") in PROTEIN_TYPES
                            and a.get("PDB auth_asym_id") in mine,
                        }.items()
                        if v not in (None, "")
                    }
                    for a in antigens
                ],
            }
            item = {k: v for k, v in item.items() if v not in (None, "", [])}
            assertion = make_source_assertion(
                FIELD,
                item,
                SOURCE,
                f"{pdb_id}:{n}",
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
