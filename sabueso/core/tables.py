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
        }
        for s in view["items"]
    ]


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
                    "pchembl": m["pchembl"],
                    "class": m["class"],
                    "basis": m["basis"],
                    "test_concentration": m.get("test_concentration"),
                    "curated": m["curated"],
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


#: name -> (card view method, rows of its output)
TABLES: Dict[str, tuple] = {
    "structures": ("structures", _structures),
    "bioactivities": ("bioactivities", _bioactivities),
    "ligands": ("ligands", _ligands),
    "ligand_sites": ("ligand_sites", _ligand_sites),
    "interfaces": ("oligomer", _interfaces),
    "literature": ("literature", _literature),
    "entities": ("entities", _entities),
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
