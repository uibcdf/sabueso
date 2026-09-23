"""PubChem → SmallMoleculeCard mappings (minimal)."""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.errors import SchemaError
from sabueso.core.source_assertion_store import make_source_assertion

from .base import get_in

# PC_Compounds ``props`` entries (urn label, urn name) → PUG-REST property-table keys.
_PC_PROPERTY_KEYS = {
    ("Molecular Weight", None): "MolecularWeight",
    ("SMILES", "Connectivity"): "ConnectivitySMILES",
    ("Molecular Formula", None): "MolecularFormula",
    ("InChIKey", "Standard"): "InChIKey",
    ("InChI", "Standard"): "InChI",
    ("Log P", "XLogP3"): "XLogP",
    ("Topological", "Polar Surface Area"): "TPSA",
    ("Count", "Hydrogen Bond Donor"): "HBondDonorCount",
    ("Count", "Hydrogen Bond Acceptor"): "HBondAcceptorCount",
    ("Count", "Rotatable Bond"): "RotatableBondCount",
}

# Property-table key → canonical field path, in emission order.
_PROPERTY_FIELDS = [
    ("MolecularFormula", "properties.physchem.formula"),
    ("InChIKey", "identifiers.inchikey"),
    ("InChI", "identifiers.inchi"),
    ("XLogP", "properties.physchem.logp"),
    ("TPSA", "properties.physchem.tpsa"),
    ("HBondDonorCount", "properties.physchem.hbd"),
    ("HBondAcceptorCount", "properties.physchem.hba"),
    ("RotatableBondCount", "properties.physchem.rotatable_bonds"),
]


def _pc_compound_properties(compound: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a PC_Compounds record into property-table keys."""
    record: Dict[str, Any] = {}
    cid = get_in(compound, ["id", "id", "cid"])
    if cid is not None:
        record["CID"] = cid
    for prop in compound.get("props", []) or []:
        urn = prop.get("urn", {}) or {}
        key = _PC_PROPERTY_KEYS.get((urn.get("label"), urn.get("name")))
        value = prop.get("value", {}) or {}
        if key and value:
            record.setdefault(key, next(iter(value.values())))
    return record


def _property_record(pubchem_json: Dict[str, Any]) -> Dict[str, Any]:
    """Return the first compound as a property-table record, whatever the payload shape."""
    props = get_in(pubchem_json, ["PropertyTable", "Properties"])
    if props:
        return props[0]
    compounds = (
        pubchem_json.get("PC_Compounds") if isinstance(pubchem_json, dict) else None
    )
    if compounds:
        return _pc_compound_properties(compounds[0])
    raise SchemaError(
        "Unsupported PubChem payload: expected PropertyTable.Properties or PC_Compounds."
    )


def _as_number(value: Any) -> Any:
    """PubChem serializes some numbers as strings (e.g. molecular weight "302.4")."""
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return value
    return value


def map_compound(pubchem_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """
    Map minimal PubChem fields into canonical card fields.

    Supports the PUG-REST property-table shape (``PropertyTable.Properties[0]``) and the
    full compound record shape (``PC_Compounds[0]``). String-typed numbers are kept as the
    asserted value and normalized to numbers. Raises ``SchemaError`` for other shapes.
    """
    fields: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

    def add(fp: str, value: Any, normalized: Any = None) -> None:
        assertion = make_source_assertion(fp, value, "PubChem", record_id, retrieved_at)
        if normalized is not None and normalized != value:
            assertion["normalized_value"] = normalized
        fields[fp] = normalized if normalized is not None else value
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion["id"]]

    p0 = _property_record(pubchem_json)
    record_id = str(p0.get("CID", ""))

    mw = p0.get("MolecularWeight")
    if mw is not None:
        add("properties.physchem.molecular_weight", mw, _as_number(mw))
    smiles = (
        p0.get("CanonicalSMILES")
        or p0.get("IsomericSMILES")
        or p0.get("ConnectivitySMILES")
    )
    if smiles:
        add("identifiers.smiles", smiles)
    for key, fp in _PROPERTY_FIELDS:
        value = p0.get(key)
        if value is not None and value != "":
            add(fp, value)

    cid = p0.get("CID")
    if cid is not None:
        add("identifiers.pubchem", str(cid))

    return {
        "fields": fields,
        "source_assertions": source_assertions,
        "field_source_assertions": field_source_assertions,
    }
