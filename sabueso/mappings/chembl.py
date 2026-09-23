"""ChEMBL mappings: molecule records (SmallMoleculeCard) and target bioactivities.

``map_bioactivities`` turns the activity records of a ChEMBL target into
``has_bioactivity`` relationships of the protein entity to the tested molecule
(``chembl:<molecule_chembl_id>``), one per activity record (uibcdf/sabueso#23). Each one is
backed by two ChEMBL SourceAssertions, with the ChEMBL release in ``source.version``: the
activity record, kept verbatim, and the record of its assay (target-assignment confidence,
assay organism), which is stated once per assay and shared by its activities. Qualifiers keep what ChEMBL states (numbers
as numbers); any reading of them as active or inactive is derived later, in
``sabueso.core.bioactivities``.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

from .base import get_in


def map_molecule(chembl_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """
    Map minimal ChEMBL molecule fields into canonical card fields.

    Expected (if present):
      - molecule_chembl_id
      - molecule_properties.alogp
      - molecule_structures.canonical_smiles
    """
    fields: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

    chembl_id = chembl_json.get("molecule_chembl_id")
    if chembl_id:
        fp = "identifiers.chembl"
        fields[fp] = chembl_id
        assertion = make_source_assertion(
            fp, chembl_id, "ChEMBL", chembl_id, retrieved_at
        )
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion["id"]]

    pref_name = chembl_json.get("pref_name")
    if pref_name:
        fp = "names.canonical_name"
        fields[fp] = pref_name
        assertion = make_source_assertion(
            fp, pref_name, "ChEMBL", chembl_id or "", retrieved_at
        )
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion["id"]]

    molecule_type = chembl_json.get("molecule_type")
    if molecule_type:
        fp = "properties.physchem.molecule_type"
        fields[fp] = molecule_type
        assertion = make_source_assertion(
            fp, molecule_type, "ChEMBL", chembl_id or "", retrieved_at
        )
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion["id"]]

    alogp = get_in(chembl_json, ["molecule_properties", "alogp"])
    if alogp is not None:
        fp = "properties.physchem.logp"
        fields[fp] = alogp
        assertion = make_source_assertion(
            fp, alogp, "ChEMBL", chembl_id or "", retrieved_at
        )
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion["id"]]

    hbd = get_in(chembl_json, ["molecule_properties", "hbd"])
    if hbd is not None:
        fp = "properties.physchem.hbd"
        fields[fp] = hbd
        assertion = make_source_assertion(
            fp, hbd, "ChEMBL", chembl_id or "", retrieved_at
        )
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion["id"]]

    hba = get_in(chembl_json, ["molecule_properties", "hba"])
    if hba is not None:
        fp = "properties.physchem.hba"
        fields[fp] = hba
        assertion = make_source_assertion(
            fp, hba, "ChEMBL", chembl_id or "", retrieved_at
        )
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion["id"]]

    psa = get_in(chembl_json, ["molecule_properties", "psa"])
    if psa is not None:
        fp = "properties.physchem.tpsa"
        fields[fp] = psa
        assertion = make_source_assertion(
            fp, psa, "ChEMBL", chembl_id or "", retrieved_at
        )
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion["id"]]

    rtb = get_in(chembl_json, ["molecule_properties", "rtb"])
    if rtb is not None:
        fp = "properties.physchem.rotatable_bonds"
        fields[fp] = rtb
        assertion = make_source_assertion(
            fp, rtb, "ChEMBL", chembl_id or "", retrieved_at
        )
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion["id"]]

    arom = get_in(chembl_json, ["molecule_properties", "aromatic_rings"])
    if arom is not None:
        fp = "properties.physchem.aromatic_rings"
        fields[fp] = arom
        assertion = make_source_assertion(
            fp, arom, "ChEMBL", chembl_id or "", retrieved_at
        )
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion["id"]]

    mw_freebase = get_in(chembl_json, ["molecule_properties", "mw_freebase"])
    if mw_freebase is not None:
        fp = "properties.physchem.molecular_weight"
        fields[fp] = mw_freebase
        assertion = make_source_assertion(
            fp, mw_freebase, "ChEMBL", chembl_id or "", retrieved_at
        )
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion["id"]]

    smiles = get_in(chembl_json, ["molecule_structures", "canonical_smiles"])
    if smiles:
        fp = "identifiers.smiles"
        fields[fp] = smiles
        assertion = make_source_assertion(
            fp, smiles, "ChEMBL", chembl_id or "", retrieved_at
        )
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion["id"]]

    inchi = get_in(chembl_json, ["molecule_structures", "standard_inchi"])
    if inchi:
        fp = "identifiers.inchi"
        fields[fp] = inchi
        assertion = make_source_assertion(
            fp, inchi, "ChEMBL", chembl_id or "", retrieved_at
        )
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion["id"]]

    inchikey = get_in(chembl_json, ["molecule_structures", "standard_inchi_key"])
    if inchikey:
        fp = "identifiers.inchikey"
        fields[fp] = inchikey
        assertion = make_source_assertion(
            fp, inchikey, "ChEMBL", chembl_id or "", retrieved_at
        )
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion["id"]]

    return {
        "fields": fields,
        "source_assertions": source_assertions,
        "field_source_assertions": field_source_assertions,
    }


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def map_bioactivities(
    response: Dict[str, Any], subject_accession: str, retrieved_at: str
) -> Dict[str, Any]:
    """Map a target bioactivity response (``tools.db.chembl``) for a protein entity."""
    version = response.get("version")
    assays = response.get("assays", {}) or {}
    source_assertions: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    assay_assertions: Dict[str, Dict[str, Any]] = {}

    def assertion(field_path: str, value: Any, record_id: str) -> Dict[str, Any]:
        sa = make_source_assertion(field_path, value, "ChEMBL", record_id, retrieved_at)
        if version:
            sa["source"]["version"] = version
        source_assertions.append(sa)
        return sa

    for activity in response.get("activities", []) or []:
        molecule = activity.get("molecule_chembl_id")
        if not molecule:
            continue
        object_ref = f"chembl:{molecule}"
        assay_id = activity.get("assay_chembl_id")
        assay = assays.get(assay_id) or {}
        support = [
            assertion(
                "relationships.has_bioactivity",
                {"object_ref": object_ref, "activity": activity},
                activity.get("target_chembl_id") or "",
            )["id"]
        ]
        if assay:
            if assay_id not in assay_assertions:
                assay_assertions[assay_id] = assertion(
                    "relationships.has_bioactivity.assay", assay, assay_id
                )
            support.append(assay_assertions[assay_id]["id"])
        parent = activity.get("parent_molecule_chembl_id")
        relationships.append(
            make_relationship(
                f"uniprot:{subject_accession}",
                "has_bioactivity",
                object_ref,
                qualifiers={
                    "activity_id": activity.get("activity_id"),
                    "target": activity.get("target_chembl_id"),
                    "molecule_name": activity.get("molecule_pref_name"),
                    "parent_molecule": f"chembl:{parent}" if parent else None,
                    "measurement": {
                        "type": activity.get("standard_type"),
                        "relation": activity.get("standard_relation"),
                        "value": _number(activity.get("standard_value")),
                        "upper_value": _number(activity.get("standard_upper_value")),
                        "units": activity.get("standard_units"),
                        "text_value": activity.get("standard_text_value"),
                        "pchembl": _number(activity.get("pchembl_value")),
                        "activity_comment": activity.get("activity_comment"),
                        "data_validity_comment": activity.get("data_validity_comment"),
                        "potential_duplicate": bool(
                            activity.get("potential_duplicate")
                        ),
                        "action_type": activity.get("action_type"),
                    },
                    "assay": {
                        "id": activity.get("assay_chembl_id"),
                        "type": activity.get("assay_type"),
                        "description": activity.get("assay_description"),
                        "organism": assay.get("assay_organism"),
                        "tax_id": assay.get("assay_tax_id"),
                        "confidence_score": assay.get("confidence_score"),
                        "relationship_type": assay.get("relationship_type"),
                        "variant_mutation": activity.get("assay_variant_mutation"),
                    },
                    "document": {
                        "id": activity.get("document_chembl_id"),
                        "year": activity.get("document_year"),
                        "journal": activity.get("document_journal"),
                    },
                },
                source_assertion_ids=support,
            )
        )
    return {
        "fields": {},
        "source_assertions": source_assertions,
        "field_source_assertions": {},
        "relationships": relationships,
    }
