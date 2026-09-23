"""Small-molecule identity: source records linked to their standard InChIKey (#25).

A small molecule is anchored at its standard InChIKey (``inchikey:<key>``), the way a
protein is anchored at its UniProt accession. Every source record of the molecule is
linked to that anchor with a ``same_as`` relationship, supported by what the source
itself states:

- a ChEMBL molecule record states its standard InChIKey (``chembl:<id>``);
- a PDB chemical component states the InChIKey of its standard InChI (``pdb.ligand:<code>``);
- UniChem states which records of other resources share one standard InChI (DrugBank,
  PubChem, ChEBI, BindingDB, and the ChEMBL and PDB records again).

Only standard InChIKeys anchor a molecule. A record without one (no structure, or a
non-standard InChI) is reported as unanchored and never guessed. Two structures that
differ only in charge, isotopes or stereochemistry have different standard InChIKeys and
therefore different anchors (``devguide/pending_proposals/molecule_identity.md``).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

from .chembl import map_molecule

STANDARD_INCHIKEY = re.compile(r"^[A-Z]{14}-[A-Z]{8}SA-[A-Z]$")

# UniChem sources whose records become same_as links, and their Sabueso namespaces. The
# full UniChem source list is kept verbatim in the supporting SourceAssertion.
UNICHEM_NAMESPACES = {
    "chembl": "chembl",
    "rcsb_pdb": "pdb.ligand",
    "pdbe": "pdb.ligand",
    "pubchem": "pubchem",
    "drugbank": "drugbank",
    "chebi": "chebi",
    "bindingdb": "bindingdb",
}


def anchor_ref(inchikey: str) -> str:
    return f"inchikey:{inchikey}"


def is_standard_inchikey(value: Any) -> bool:
    return isinstance(value, str) and bool(STANDARD_INCHIKEY.match(value))


def _empty() -> Dict[str, Any]:
    return {
        "fields": {},
        "source_assertions": [],
        "field_source_assertions": {},
        "relationships": [],
    }


def _versioned(assertion: Dict[str, Any], version: str | None) -> Dict[str, Any]:
    if version:
        assertion["source"]["version"] = version
    return assertion


def map_chembl_identity(
    record: Dict[str, Any], retrieved_at: str, version: str | None = None
) -> Tuple[Dict[str, Any], str | None]:
    """ChEMBL molecule record -> (mapping, standard InChIKey or None)."""
    mapping = map_molecule(record, retrieved_at)
    chembl_id = record.get("molecule_chembl_id") or ""
    mapping.setdefault("relationships", [])
    if record.get("max_phase") is not None:
        # ChEMBL's highest development phase for any indication: 4 approved, 3-1 clinical
        # (0.5 early phase 1), -1 unknown. ChEMBL serializes it as a string.
        fp = "clinical.max_phase"
        assertion = make_source_assertion(
            fp, record["max_phase"], "ChEMBL", chembl_id, retrieved_at
        )
        try:
            assertion["normalized_value"] = float(record["max_phase"])
        except (TypeError, ValueError):
            pass
        mapping["fields"][fp] = assertion.get("normalized_value", record["max_phase"])
        mapping["source_assertions"].append(assertion)
        mapping["field_source_assertions"][fp] = [assertion["id"]]
    for assertion in mapping["source_assertions"]:
        _versioned(assertion, version)
    key = (record.get("molecule_structures") or {}).get("standard_inchi_key")
    if not is_standard_inchikey(key):
        return mapping, None
    stated = make_source_assertion(
        "relationships.same_as",
        {
            "object_ref": anchor_ref(key),
            "standard_inchi_key": key,
            "molecule_hierarchy": record.get("molecule_hierarchy"),
        },
        "ChEMBL",
        chembl_id,
        retrieved_at,
    )
    mapping["source_assertions"].append(_versioned(stated, version))
    mapping["relationships"].append(
        make_relationship(
            f"chembl:{chembl_id}",
            "same_as",
            anchor_ref(key),
            qualifiers={"name": record.get("pref_name")},
            source_assertion_ids=[stated["id"]],
        )
    )
    return mapping, key


def _formula(value: str | None) -> str | None:
    return value.replace(" ", "") if value else None


def map_ccd_identity(
    record: Dict[str, Any], retrieved_at: str
) -> Tuple[Dict[str, Any], str | None]:
    """PDB chemical component record -> (mapping, standard InChIKey or None)."""
    mapping = _empty()
    component = record.get("chem_comp") or {}
    descriptors = record.get("rcsb_chem_comp_descriptor") or {}
    code = component.get("id") or ""
    key = descriptors.get("InChIKey")
    standard = (descriptors.get("InChI") or "").startswith("InChI=1S/")
    if not (standard and is_standard_inchikey(key)):
        return mapping, None

    def field(fp: str, value: Any, normalized: Any = None) -> None:
        assertion = make_source_assertion(fp, value, "PDB CCD", code, retrieved_at)
        if normalized is not None and normalized != value:
            assertion["normalized_value"] = normalized
        mapping["fields"][fp] = normalized if normalized is not None else value
        mapping["source_assertions"].append(assertion)
        mapping["field_source_assertions"][fp] = [assertion["id"]]

    field("identifiers.inchikey", key)
    field("identifiers.inchi", descriptors["InChI"])
    if component.get("formula"):
        field(
            "properties.physchem.formula",
            component["formula"],
            _formula(component["formula"]),
        )
    stated = make_source_assertion(
        "relationships.same_as",
        {
            "object_ref": anchor_ref(key),
            "chem_comp": component,
            "descriptors": descriptors,
        },
        "PDB CCD",
        code,
        retrieved_at,
    )
    mapping["source_assertions"].append(stated)
    mapping["relationships"].append(
        make_relationship(
            f"pdb.ligand:{code}",
            "same_as",
            anchor_ref(key),
            qualifiers={
                "name": component.get("name"),
                "component_type": component.get("type"),
            },
            source_assertion_ids=[stated["id"]],
        )
    )
    return mapping, key


def _unichem_ref(source: Dict[str, Any]) -> str | None:
    namespace = UNICHEM_NAMESPACES.get(source.get("shortName") or "")
    record = str(source.get("compoundId") or "")
    if not namespace or not record:
        return None
    if namespace == "chebi":
        record = record.removeprefix("CHEBI:")
    return f"{namespace}:{record}"


def map_unichem_identity(
    compound: Dict[str, Any], retrieved_at: str
) -> Tuple[Dict[str, Any], str | None]:
    """UniChem compound -> (same_as links of its source records, standard InChIKey)."""
    mapping = _empty()
    key = compound.get("standardInchiKey")
    if not is_standard_inchikey(key):
        return mapping, None
    stated = make_source_assertion(
        "relationships.same_as",
        {"object_ref": anchor_ref(key), "sources": compound.get("sources", [])},
        "UniChem",
        str(compound.get("uci") or ""),
        retrieved_at,
    )
    mapping["source_assertions"].append(stated)
    refs = sorted({r for s in compound.get("sources", []) if (r := _unichem_ref(s))})
    mapping["relationships"] = [
        make_relationship(
            ref, "same_as", anchor_ref(key), source_assertion_ids=[stated["id"]]
        )
        for ref in refs
    ]
    return mapping, key


def linked_records(compound: Dict[str, Any]) -> Dict[str, List[str]]:
    """ChEMBL ids and PDB component codes that UniChem lists for a compound."""
    out: Dict[str, List[str]] = {"chembl": [], "pdb.ligand": []}
    for source in compound.get("sources", []):
        ref = _unichem_ref(source)
        if ref:
            namespace, record = ref.split(":", 1)
            if namespace in out and record not in out[namespace]:
                out[namespace].append(record)
    return {k: sorted(v) for k, v in out.items()}
