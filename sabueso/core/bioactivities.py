"""Protein–molecule bioactivities: derived activity classes and the card view.

A ProteinCard carries measured bioactivities as ``has_bioactivity`` Relationships, one per
source measurement (uibcdf/sabueso#23, ``devguide/pending_proposals/chembl_bioactivities.md``).
This module reads them. The activity class of a measurement ("active", "weak", ...) and the
test concentration of a single-point measurement are derived knowledge. They are computed
here, from the stated rule and thresholds, and never stored as SourceAssertions.

Rule ``bioactivity_class@1``, on a potency expressed in µM:

- a potency measure (IC50, Ki, Kd, ...) with relation ``=`` is "active" up to
  ``active_max_uM``, "weak" up to ``weak_max_uM`` and "inactive" beyond;
- an upper bound (``<``, ``<=``) is "active" or "weak" when the bound falls in those bands,
  and "inconclusive" otherwise;
- a lower bound (``>``, ``>=``) is "inactive" when it reaches ``weak_max_uM``, and
  "inconclusive" otherwise;
- a single-point % inhibition reads as an IC50 bound: an inhibition of at least
  ``single_point_min_percent`` at concentration c means IC50 <= c, and less than that
  means IC50 > c. This assumes a standard dose response. c comes from the assay
  description, and a measurement without c is "inconclusive";
- "Not Determined" measurements are "not_determined", and ChEMBL "Not Active" or
  "Inactive" comments are "inactive";
- other measurement types are "unclassified".

By default, only assays whose target assignment is direct (ChEMBL relationship type
``D``) are included. Homology-assigned measurements (``H``: measured on an ortholog) and
other assignments are excluded, and the exclusion is reported, never silent.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

BIOACTIVITY_CLASS_RULE = "bioactivity_class@1"
BIOACTIVITY_THRESHOLDS: Dict[str, Any] = {
    "active_max_uM": 10.0,
    "weak_max_uM": 100.0,
    "single_point_min_percent": 50.0,
}
POTENCY_TYPES = frozenset(
    {"IC50", "Ki", "Kd", "EC50", "ED50", "AC50", "XC50", "Potency", "Kb"}
)
SINGLE_POINT_TYPES = frozenset({"Inhibition"})
CLASS_ORDER = (
    "active",
    "weak",
    "inactive",
    "inconclusive",
    "not_determined",
    "unclassified",
)
DIRECT_ASSIGNMENT = "D"
UNITS_TO_UM = {"pM": 1e-6, "nM": 1e-3, "uM": 1.0, "µM": 1.0, "mM": 1e3, "M": 1e6}
TEST_CONCENTRATION = re.compile(
    r"\bat\s+(?:a\s+concentration\s+of\s+)?(\d+(?:\.\d+)?|\.\d+)\s*(pM|nM|uM|µM|mM|M)\b"
)
NOT_DETERMINED = {"not determined", "nd", "not tested"}
INACTIVE_COMMENTS = {"not active", "inactive"}


def single_point_concentration_uM(description: str | None) -> float | None:
    """Single-point test concentration stated in an assay description, in µM."""
    match = TEST_CONCENTRATION.search(description or "")
    if not match:
        return None
    return float(match.group(1)) * UNITS_TO_UM[match.group(2)]


def _band(value_uM: float, t: Dict[str, Any]) -> str:
    if value_uM <= t["active_max_uM"]:
        return "active"
    if value_uM <= t["weak_max_uM"]:
        return "weak"
    return "inactive"


def _bounded(relation: str, value_uM: float, t: Dict[str, Any]) -> str:
    if relation in ("=", "~"):
        return _band(value_uM, t)
    if relation in ("<", "<="):
        band = _band(value_uM, t)
        return band if band != "inactive" else "inconclusive"
    if relation in (">", ">="):
        return "inactive" if value_uM >= t["weak_max_uM"] else "inconclusive"
    return "inconclusive"


def classify_measurement(
    measurement: Dict[str, Any],
    assay_description: str | None = None,
    thresholds: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """``{"class", "basis", "test_concentration_uM"?}`` for one measurement."""
    t = {**BIOACTIVITY_THRESHOLDS, **(thresholds or {})}
    kind = measurement.get("type")
    value = measurement.get("value")
    relation = measurement.get("relation") or "="
    comment = (measurement.get("activity_comment") or "").strip().lower()
    if value is None:
        if comment in NOT_DETERMINED:
            return {"class": "not_determined", "basis": "activity_comment"}
        if comment in INACTIVE_COMMENTS:
            return {"class": "inactive", "basis": "activity_comment"}
        return {"class": "inconclusive", "basis": "no_value"}
    if kind in POTENCY_TYPES:
        factor = UNITS_TO_UM.get(measurement.get("units") or "")
        if factor is None:
            return {"class": "inconclusive", "basis": "unknown_units"}
        return {"class": _bounded(relation, value * factor, t), "basis": "potency"}
    if kind in SINGLE_POINT_TYPES and measurement.get("units") == "%":
        concentration = single_point_concentration_uM(assay_description)
        if concentration is None:
            return {"class": "inconclusive", "basis": "single_point_no_concentration"}
        if relation in ("<", "<=") and value >= t["single_point_min_percent"]:
            return {
                "class": "inconclusive",
                "basis": "single_point",
                "test_concentration_uM": concentration,
            }
        ic50_relation = "<=" if value >= t["single_point_min_percent"] else ">"
        return {
            "class": _bounded(ic50_relation, concentration, t),
            "basis": "single_point",
            "test_concentration_uM": concentration,
        }
    return {"class": "unclassified", "basis": "measurement_type"}


def bioactivity_derivation(thresholds: Dict[str, Any] | None = None) -> Dict[str, Any]:
    from .relationship_store import make_derivation

    return make_derivation(
        BIOACTIVITY_CLASS_RULE,
        inputs=["has_bioactivity.measurement", "has_bioactivity.assay.description"],
        parameters={
            **BIOACTIVITY_THRESHOLDS,
            **(thresholds or {}),
            "potency_types": sorted(POTENCY_TYPES),
            "single_point_types": sorted(SINGLE_POINT_TYPES),
            "test_concentration": "assay description text",
        },
    )


def _flags(q: Dict[str, Any]) -> List[str]:
    m, assay = q.get("measurement", {}), q.get("assay", {})
    flags = []
    if m.get("data_validity_comment"):
        flags.append(f"data_validity:{m['data_validity_comment']}")
    if m.get("potential_duplicate"):
        flags.append("potential_duplicate")
    if assay.get("relationship_type") is None:
        flags.append("missing_assay_metadata")
    if "unknown origin" in (assay.get("description") or "").lower():
        flags.append("assay_organism_unknown_origin")
    if assay.get("variant_mutation"):
        flags.append(f"variant:{assay['variant_mutation']}")
    return flags


def _stated_smiles(card: Any, rel: Dict[str, Any]) -> str | None:
    """SMILES of the tested molecule as stated in the supporting activity record."""
    for sa_id in rel.get("source_assertion_ids", []):
        sa = card.source_assertion_store.get(sa_id) or {}
        activity = (sa.get("asserted_value") or {}).get("activity")
        if isinstance(activity, dict) and activity.get("canonical_smiles"):
            return activity["canonical_smiles"]
    return None


def bioactivities_view(
    card: Any,
    include_indirect: bool = False,
    thresholds: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Molecule-centric summary of the card's ``has_bioactivity`` relationships.

    Returns ``{"items", "excluded", "documents", "scope", "classification"}``. ``items`` has one
    entry per parent molecule, holding all its measurements and its strongest class.
    Measurements from assays that were not assigned directly to the target are excluded
    unless ``include_indirect``, and they are listed in ``excluded``.
    """
    molecules: Dict[str, Dict[str, Any]] = {}
    excluded: List[Dict[str, Any]] = []
    documents: Dict[str, int] = {}
    for rel in card.relationships(predicate="has_bioactivity"):
        q = rel.get("qualifiers", {})
        m, assay, doc = (
            q.get("measurement", {}),
            q.get("assay", {}),
            q.get("document", {}),
        )
        assignment = assay.get("relationship_type")
        if not include_indirect and assignment != DIRECT_ASSIGNMENT:
            excluded.append(
                {
                    "activity_id": q.get("activity_id"),
                    "molecule_ref": rel["object_ref"],
                    "assay": assay.get("id"),
                    "reason": f"target_assignment:{assignment}",
                    "assay_organism": assay.get("organism"),
                }
            )
            continue
        derived = classify_measurement(m, assay.get("description"), thresholds)
        measurement = {
            "relationship_id": rel["id"],
            "activity_id": q.get("activity_id"),
            "molecule_ref": rel["object_ref"],
            "type": m.get("type"),
            "relation": m.get("relation"),
            "value": m.get("value"),
            "units": m.get("units"),
            "pchembl": m.get("pchembl"),
            **derived,
            "assay": assay.get("id"),
            "assay_organism": assay.get("organism"),
            "target_assignment": assignment,
            "document": doc.get("id"),
            "year": doc.get("year"),
            "flags": _flags(q),
        }
        if doc.get("id"):
            documents[doc["id"]] = documents.get(doc["id"], 0) + 1
        key = q.get("parent_molecule") or rel["object_ref"]
        entry = molecules.setdefault(
            key,
            {
                "molecule_ref": key,
                "tested_forms": set(),
                "name": None,
                "smiles": None,
                "measurements": [],
            },
        )
        entry["tested_forms"].add(rel["object_ref"])
        if entry["smiles"] is None or rel["object_ref"] == key:  # prefer the parent
            entry["name"] = q.get("molecule_name") or entry["name"]
            entry["smiles"] = _stated_smiles(card, rel) or entry["smiles"]
        entry["measurements"].append(measurement)

    items = []
    for entry in molecules.values():
        measurements = sorted(
            entry["measurements"], key=lambda x: x["activity_id"] or 0
        )
        classes: Dict[str, int] = {}
        for x in measurements:
            classes[x["class"]] = classes.get(x["class"], 0) + 1
        pchembls = [x["pchembl"] for x in measurements if x["pchembl"] is not None]
        items.append(
            {
                "molecule_ref": entry["molecule_ref"],
                "tested_forms": sorted(entry["tested_forms"]),
                "name": entry["name"],
                "smiles": entry["smiles"],
                "class": min(classes, key=CLASS_ORDER.index),
                "classes": classes,
                "discordant": bool({"active", "weak"} & classes.keys())
                and "inactive" in classes,
                "best_pchembl": max(pchembls) if pchembls else None,
                "documents": sorted(
                    {x["document"] for x in measurements if x["document"]}
                ),
                "measurements": measurements,
            }
        )
    items.sort(
        key=lambda i: (
            CLASS_ORDER.index(i["class"]),
            -(i["best_pchembl"] or 0.0),
            i["molecule_ref"],
        )
    )
    return {
        "items": items,
        "excluded": sorted(excluded, key=lambda x: x["activity_id"] or 0),
        "documents": dict(sorted(documents.items(), key=lambda kv: (-kv[1], kv[0]))),
        "scope": {
            "target_assignment": "any" if include_indirect else DIRECT_ASSIGNMENT
        },
        "classification": bioactivity_derivation(thresholds),
    }
