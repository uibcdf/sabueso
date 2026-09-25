"""BindingDB affinities → ``has_bioactivity`` relationships (uibcdf/sabueso#66).

One relationship per BindingDB record, from the protein to ``bindingdb:<monomer id>``,
with the same qualifier layout as ChEMBL measurements, so views read both alike:

- ``activity_id`` is ``bindingdb:<digest>`` of what the record states (the service
  gives no record id), and ``source`` is ``"BindingDB"``;
- the relation written in the value (``">1.00e+5"``) is split out, and the value as
  written is kept in ``stated_value``, so that its precision is known;
- ``molecule_ref`` is the InChIKey anchor when UniChem resolves the monomer; the
  identity is returned for the card's glossary, never computed from the SMILES;
- the target is the UniProt entry BindingDB states, so the assignment is direct (``D``).
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List

from sabueso.core.quantities import normalized_measurement
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "BindingDB"
_VALUE = re.compile(
    r"\s*(<=|>=|<|>|~|=)?\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*$"
)
#: UniChem short names → Sabueso namespaces, for the records a monomer is linked to.
NAMESPACES = {
    "chembl": "chembl",
    "pubchem": "pubchem",
    "bindingdb": "bindingdb",
    "pdb": "pdb.ligand",
}


def parse_affinity(text: Any) -> tuple:
    """``(relation, value, stated text)`` of a BindingDB affinity, or Nones."""
    match = _VALUE.fullmatch(str(text or ""))
    if not match:
        return None, None, None
    relation, number = match.group(1) or "=", match.group(2)
    return relation, float(number), number


def molecule_identity(
    compound: Dict[str, Any] | None, monomer: str
) -> Dict[str, Any] | None:
    """``{"anchor", "records"}`` from a UniChem compound, or None when unresolved."""
    if not compound or not compound.get("standardInchiKey"):
        return None
    records = {f"bindingdb:{monomer}"}
    for s in compound.get("sources") or []:
        namespace = NAMESPACES.get(s.get("shortName"))
        if namespace and s.get("compoundId"):
            records.add(f"{namespace}:{s['compoundId']}")
    return {
        "anchor": f"inchikey:{compound['standardInchiKey']}",
        "records": sorted(records),
    }


def map_affinities(
    response: Dict[str, Any],
    accession: str,
    retrieved_at: str,
    identities: Dict[str, Dict[str, Any] | None] | None = None,
) -> Dict[str, Any]:
    identities = identities or {}
    source_assertions: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    for record in response.get("record") or []:
        monomer = str(record.get("monomerid") or "")
        if not monomer:
            continue
        relation, value, stated = parse_affinity(record.get("affinity"))
        statement = json.dumps(
            [
                monomer,
                record.get("pmid"),
                record.get("doi"),
                record.get("affinity_type"),
                record.get("affinity"),
            ],
            sort_keys=True,
        )
        activity_id = "bindingdb:" + hashlib.sha256(statement.encode()).hexdigest()[:16]
        object_ref = f"bindingdb:{monomer}"
        assertion = make_source_assertion(
            "relationships.has_bioactivity",
            {"object_ref": object_ref, "record": record},
            SOURCE,
            accession,
            retrieved_at,
            subject_ref=f"uniprot:{accession}",
        )
        source_assertions.append(assertion)
        identity = identities.get(monomer)
        pmid, doi = record.get("pmid"), record.get("doi")
        relationships.append(
            make_relationship(
                f"uniprot:{accession}",
                "has_bioactivity",
                object_ref,
                qualifiers={
                    "activity_id": activity_id,
                    "source": SOURCE,
                    "molecule_ref": identity["anchor"] if identity else None,
                    "measurement": {
                        "type": record.get("affinity_type"),
                        "relation": relation,
                        "value": value,
                        "units": "nM",
                        "stated_value": stated,
                        "normalized": normalized_measurement(value, "nM"),
                        "pchembl": None,
                    },
                    "assay": {
                        "id": None,
                        "description": None,
                        "relationship_type": "D",
                        "organism": None,
                        "source": SOURCE,
                    },
                    "document": {
                        "id": None,
                        "year": None,
                        "journal": None,
                        "pubmed": str(pmid) if pmid else None,
                        "doi": str(doi) if doi else None,
                        "title": None,
                    },
                },
                source_assertion_ids=[assertion["id"]],
            )
        )
    return {
        "fields": {},
        "source_assertions": source_assertions,
        "field_source_assertions": {},
        "relationships": relationships,
    }
