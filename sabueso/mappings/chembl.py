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

# ChEMBL molecule record -> (field path, location in the record, source metadata).
# ``method`` names what the value depends on, as ChEMBL states it: different sources' logP
# or rotatable-bond values are different quantities, compared only within one method
# (uibcdf/sabueso#10). Numbers ChEMBL serialises as strings get a numeric
# ``normalized_value``; the asserted value keeps the source's own text and precision.
_MOLECULE_FIELDS = [
    ("identifiers.chembl", ["molecule_chembl_id"], None),
    ("names.canonical_name", ["pref_name"], None),
    ("properties.physchem.molecule_type", ["molecule_type"], None),
    ("properties.physchem.formula", ["molecule_properties", "full_molformula"], None),
    ("properties.physchem.logp", ["molecule_properties", "alogp"], {"method": "ALogP"}),
    ("properties.physchem.hbd", ["molecule_properties", "hbd"], None),
    ("properties.physchem.hba", ["molecule_properties", "hba"], None),
    ("properties.physchem.tpsa", ["molecule_properties", "psa"], None),
    (
        "properties.physchem.rotatable_bonds",
        ["molecule_properties", "rtb"],
        {"method": "chembl:rtb"},
    ),
    (
        "properties.physchem.aromatic_rings",
        ["molecule_properties", "aromatic_rings"],
        None,
    ),
    # The weight of the structure the record describes, salts included. ``mw_freebase`` is
    # the parent's weight: another structure, with its own InChIKey and card.
    (
        "properties.physchem.molecular_weight",
        ["molecule_properties", "full_mwt"],
        {"unit": "Da"},
    ),
    (
        "identifiers.smiles",
        ["molecule_structures", "canonical_smiles"],
        {"representation": "isomeric"},
    ),
    ("identifiers.inchi", ["molecule_structures", "standard_inchi"], None),
    ("identifiers.inchikey", ["molecule_structures", "standard_inchi_key"], None),
]
_NUMERIC = {
    "properties.physchem.logp",
    "properties.physchem.hbd",
    "properties.physchem.hba",
    "properties.physchem.tpsa",
    "properties.physchem.rotatable_bonds",
    "properties.physchem.aromatic_rings",
    "properties.physchem.molecular_weight",
}


def map_molecule(chembl_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """Map a ChEMBL molecule record into canonical card fields."""
    fields: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}
    chembl_id = chembl_json.get("molecule_chembl_id") or ""

    for fp, path, metadata in _MOLECULE_FIELDS:
        value = get_in(chembl_json, path)
        if value is None or value == "":
            continue
        assertion = make_source_assertion(fp, value, "ChEMBL", chembl_id, retrieved_at)
        normalized = _number(value) if fp in _NUMERIC else None
        if normalized is not None and normalized != value:
            assertion["normalized_value"] = normalized
        if metadata:
            assertion["source_metadata"] = dict(metadata)
        fields[fp] = assertion.get("normalized_value", value)
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
