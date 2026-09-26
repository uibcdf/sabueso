"""Card views as flat rows, and as DataFrames (uibcdf/sabueso#46).

``card.table(name, **options)`` runs a view and returns a list of flat records with
stable column names, one per structure, measurement, molecule, ligand, interface
partner, publication or entity. Quantities stay quantities (MOLI quantity integrity
policy): a column never holds bare numbers with the unit in its name. Lists become
``"; "``-joined text so every cell is one value.

``to_dataframe(rows, units=None)`` needs pandas, an optional dependency (DepDigest):

- by default, quantity cells stay quantities, each with its unit;
- ``units={"normalized": "nanomolar"}`` asks for numbers in a named unit: the column is
  converted explicitly, renamed ``"normalized [nanomolar]"``, and the unit is recorded
  in ``df.attrs["units"]``.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from depdigest import dep_digest

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import SchemaError


def _join(values: Any) -> str:
    if not values:
        return ""
    if isinstance(values, (list, tuple, set)):
        return "; ".join(str(v) for v in values)
    return str(values)


def _structures(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "structure_ref": s["structure_ref"],
            "method": s["method"],
            "resolution": s["resolution"],
            "coverage": s["coverage"],
            "coverage_class": s["coverage_class"],
            "chains": _join(s["chains"]),
            "sources": _join(s["sources"]),
            "released": s.get("released"),
            "r_free": s.get("r_free"),
            "sequence_state": s["state"]["sequence"],
            "substitutions": _join(s.get("substitutions")),
            "author_substitutions": _join(s.get("author_substitutions")),
            "modified_residues": _join(s.get("modified_residues")),
            "ligand_state": s["state"]["ligands"],
            "ligands_of_interest": _join(s.get("ligands_of_interest")),
            "oligomer": s["state"]["oligomer"],
            "oligomer_basis": s.get("oligomer_basis"),
            "oligomer_disagreement": s.get("oligomer_disagreement"),
            "in_complex": s["state"]["in_complex"],
            "expression_host": _join(s.get("expression_host")),
            "missing_in_region": _join(
                [
                    f"{chain}: {','.join(str(p) for p in gaps)}"
                    for chain, gaps in (s.get("missing_in_region") or {}).items()
                    if gaps
                ]
            ),
            "complete_chains": _join(s.get("complete_chains")),
        }
        for s in view["items"]
    ]


def _uncertainty_columns(u: Dict[str, Any] | None) -> Dict[str, Any]:
    """A stated uncertainty as flat cells (#37): its kind, a half-width or the ends of an
    interval (quantities), its level and its number of replicates."""
    u = u or {}
    return {
        "uncertainty_kind": u.get("kind"),
        "uncertainty_half_width": u.get("half_width"),
        "uncertainty_lower": u.get("lower"),
        "uncertainty_upper": u.get("upper"),
        "uncertainty_level": u.get("level"),
        "uncertainty_n": u.get("n"),
    }


def _bioactivities(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for item in view["items"]:
        for m in item["measurements"]:
            rows.append(
                {
                    "molecule_ref": item["molecule_ref"],
                    "label": item["label"],
                    "activity_id": m["activity_id"],
                    "type": m["type"],
                    "relation": m["relation"],
                    "value": m["value"],
                    "units": m["units"],
                    "normalized": m["normalized"],
                    "normalized_upper": m["normalized_upper"],
                    **_uncertainty_columns(m["uncertainty"]),
                    "pchembl": m["pchembl"],
                    "class": m["class"],
                    "basis": m["basis"],
                    "test_concentration": m.get("test_concentration"),
                    "curated": m["curated"],
                    "source": m["source"],
                    "group": m["group"],
                    "copy": m["copy"],
                    "target_assignment": m["target_assignment"],
                    "assay": m["assay"],
                    "document": m["document"],
                    "year": m["year"],
                    "flags": _join(m["flags"]),
                }
            )
    return rows


def _ligands(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for item in view["items"]:
        bio = item.get("bioactivity") or {}
        rows.append(
            {
                "molecule_ref": item["molecule_ref"],
                "label": item["label"],
                "label_source": item["label_source"],
                "class": bio.get("class"),
                "best_pchembl": bio.get("best_pchembl"),
                "measurements": bio.get("measurements", 0),
                "excluded_measurements": item["excluded_measurements"],
                "structures": len(item["structures"]),
                "structures_of_interest": _join(item["structures_of_interest"]),
                "observed_in": _join(item["observed_in"]),
                "records": _join(item["records"]),
            }
        )
    return rows


def _ligand_sites(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "ligand_ref": item["ligand_ref"],
            "name": item["name"],
            "positions": _join(item["positions"]),
            "n_positions": len(item["positions"]),
            "site_class": item["site_class"],
            "spans_chains": None
            if item["spans_chains"] is None
            else _join(item["spans_chains"]),
            "structures": len(item["structures"]),
        }
        for item in view["items"]
    ]


def _interfaces(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "partner_ref": i["partner_ref"],
            "partner_name": i["partner_name"],
            "partner_type": i["partner_type"],
            "class": i["class"],
            "n_positions": len(i["positions"]),
            "structures": len(i["structures"]),
            "sources": _join(i["sources"]),
        }
        for i in view["interfaces"]
    ]


def _literature(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "publication_ref": p["publication_ref"],
            "year": p["year"],
            "title": p["title"],
            "journal": p["journal"],
            "cited_for": _join([s for c in p["cited_by"] for s in c["scope"]]),
            "primary_citation_of": _join(p["primary_citation_of"]),
            "supports": len(p["supports"]),
            "curated": len(p["curated"]),
            "measurements": p["measurements"],
        }
        for p in view["publications"]
    ]


def _entities(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "entity_ref": key,
            "entity_type": e["entity_type"],
            "anchor": e["anchor"],
            "names": _join(e["names"]),
            "records": _join(e["records"]),
            "appears_in": _join(e["appears_in"]),
            "identity": (e.get("identity") or {}).get("by"),
        }
        for key, e in view.items()
    ]


def _claims(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "topic": c["topic"],
            "text": c["text"],
            "about": _join(c["about"]),
            "publication": c["publication"],
            "locator": c["locator"],
            "curator": c["curator"],
            "outcome": c["outcome"],
        }
        for c in view["items"]
    ]


def _predicted_structures(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "model_ref": i["model_ref"],
            "model_version": i["model_version"],
            "tool": i["tool"],
            "mean_plddt": i["mean_plddt"],
            "fraction_very_high": (i["plddt_fractions"] or {}).get("very_high"),
            "range": "-".join(str(x) for x in i["range"] or [] if x is not None),
            "isoform": i["isoform"],
            "coverage": i["coverage"],
            "sequence_matches": i["sequence_matches"],
        }
        for i in view["items"]
    ]


def _knowledge_state(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "area": r["area"],
            "source": r["source"],
            "release": r["release"],
            "state": r["state"],
            "count": r["count"],
            "basis": "; ".join(f"{k}={v}" for k, v in sorted(r["basis"].items())),
        }
        for r in view["rows"]
    ]


#: name -> (card view method, rows of its output)
TABLES: Dict[str, tuple] = {
    "structures": ("structures", _structures),
    "bioactivities": ("bioactivities", _bioactivities),
    "ligands": ("ligands", _ligands),
    "ligand_sites": ("ligand_sites", _ligand_sites),
    "interfaces": ("oligomer", _interfaces),
    "literature": ("literature", _literature),
    "entities": ("entities", _entities),
    "knowledge_state": ("knowledge_state", _knowledge_state),
    "predicted_structures": ("predicted_structures", _predicted_structures),
    "claims": ("claims", _claims),
}


def card_table(card: Any, view: str, **options: Any) -> List[Dict[str, Any]]:
    view_name, to_rows = TABLES[view]
    method: Callable[..., Any] = getattr(card, view_name)
    return to_rows(method(**options))


@dep_digest("pandas")
@arg_digest()
def to_dataframe(
    rows: List[Dict[str, Any]],
    units: Dict[str, str] | None = None,
    skip_digestion: bool = False,
):
    """A pandas DataFrame of table rows; see the module docstring for ``units``."""
    import pandas as pd
    import pyunitwizard as puw

    df = pd.DataFrame(rows)
    df.attrs["units"] = {}
    for column, unit in (units or {}).items():
        if column not in df.columns:
            raise KeyError(f"No column {column!r} to express in {unit}.")
        values = []
        for q in df[column]:
            if q is None:
                values.append(None)
                continue
            try:
                values.append(float(puw.get_value(puw.convert(q, to_unit=unit))))
            except Exception:
                # A column can hold several kinds, e.g. potencies (nanomolar) and
                # single-point inhibitions (percent). Converting some rows and blanking
                # the rest would lose data silently: filter the rows first.
                found = sorted(
                    {str(puw.get_unit(v)) for v in df[column] if v is not None}
                )
                raise SchemaError(
                    f"Column {column!r} holds quantities in {found}; they cannot all "
                    f"be expressed in {unit}. Select the rows of one kind first."
                ) from None
        target = f"{column} [{unit}]"
        df[column] = values
        df = df.rename(columns={column: target})
        df.attrs["units"][target] = unit
    return df
