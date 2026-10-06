"""Project native ChEMBL reference pointers without consulting their targets."""

from copy import deepcopy
from urllib.parse import urlsplit

from .snapshot import canonical_json, digest

_FIELDS = (
    "drugind_id",
    "molecule_chembl_id",
    "parent_molecule_chembl_id",
    "efo_id",
    "mesh_id",
    "indication_refs",
)


def reference_rows(records):
    """Keep native row identity and reference forms, including malformed forms."""
    return [
        {key: deepcopy(row[key]) for key in _FIELDS if key in row}
        for row in records
        if isinstance(row, dict)
    ]


def citations(context):
    """Return incomplete citations, explicit gaps and all observed occurrences.

    Native grouped identifiers remain grouped. A URL is a source-stated pointer,
    not an observed target request, a publication identity or a permission grant.
    """
    items, gaps, occurrences = {}, [], []
    for observation_index, observation in enumerate(context["observations"]):
        for row_position, row in enumerate(observation["rows"]):
            location = {
                "observation_index": observation_index,
                "row_position": row_position,
                "drugind_id": deepcopy(row.get("drugind_id")),
            }
            references = row.get("indication_refs")
            if not isinstance(references, list) or not references:
                gaps.append(
                    {
                        **location,
                        "reason": "indication_references_not_stated"
                        if references is None or references == []
                        else "indication_references_malformed",
                    }
                )
                continue
            for reference_position, reference in enumerate(references):
                occurrence = {
                    **location,
                    "reference_position": reference_position,
                    "native_reference": deepcopy(reference),
                }
                if not isinstance(reference, dict):
                    gaps.append(
                        {**occurrence, "reason": "indication_reference_malformed"}
                    )
                    continue
                missing = [
                    key
                    for key in ("ref_type", "ref_id", "ref_url")
                    if not isinstance(reference.get(key), str)
                    or not reference[key].strip()
                ]
                url = reference.get("ref_url")
                valid_url = False
                if isinstance(url, str):
                    try:
                        parsed = urlsplit(url)
                        valid_url = parsed.scheme in {"https", "http"} and bool(
                            parsed.netloc
                        )
                    except ValueError:
                        pass
                if missing:
                    gaps.append(
                        {
                            **occurrence,
                            "reason": "indication_reference_fields_not_stated",
                            "fields": missing,
                        }
                    )
                if url is not None and not valid_url:
                    gaps.append(
                        {
                            **occurrence,
                            "reason": "indication_reference_url_not_supported",
                        }
                    )
                if "ref_id" in missing and not valid_url:
                    gaps.append(
                        {
                            **occurrence,
                            "reason": "indication_reference_pointer_unusable",
                        }
                    )
                    continue
                identifier = "sabueso:chembl-indication-reference:" + digest(
                    canonical_json(reference)
                )
                item = {
                    "id": identifier,
                    "type": "web" if valid_url else "other",
                    "note": "Reference declared by ChEMBL; target not consulted by this operation. Native reference: "
                    + canonical_json(reference),
                }
                if valid_url:
                    item["url"] = url
                if identifier not in items:
                    items[identifier] = item
                    gaps.append(
                        {
                            "citation_id": identifier,
                            "reason": "indication_reference_metadata_not_stated",
                            "fields": ["title", "authors", "year"],
                        }
                    )
                occurrences.append({**occurrence, "citation_id": identifier})
    gaps.append("indication_reference_targets_not_queried")
    return list(items.values()), gaps, occurrences
