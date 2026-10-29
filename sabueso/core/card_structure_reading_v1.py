"""Current delivery of original regional outputs, without scientific reevaluation.

Keep this named presentation policy stable. Locations address the exact registered
inventory item and its original relationship; labels never identify another row.
This context is not inserted into the scientific wire or historical source data.
"""

from copy import deepcopy
from itertools import islice

RULE = "structure_region_reading@1"
SCOPE = (
    "The original native result for this exact declaration and regional request. "
    "Per-chain counts summarize its recorded missing-position lists; they do not "
    "recompute coordinates or establish absent source knowledge. Author numbering "
    "retains its original chain scope. Assembly composition does not establish "
    "chain/contact membership, physical identity or biological relevance."
)


def reading(access, result, key, *, chain_limit=None):
    """Detached compact context; None without an original regional request."""
    region = result.options.get("region")
    if region is None:
        return None
    row = result.wire["items"][key]

    def field(name, *children):
        if name not in row:
            return None
        return access._location(result.location("items", key, name, *children))

    coordinate = row.get("coordinate_scope")
    coordinate = coordinate if isinstance(coordinate, dict) else {}
    reference = coordinate.get("reference") or {}
    missing = row.get("missing_in_region")
    numbering = row.get("author_numbering")
    chains = []
    if isinstance(missing, dict):
        items = missing.items()
        if chain_limit is not None:
            items = islice(items, chain_limit)
        for chain, positions in items:
            chains.append(
                {
                    "chain": chain,
                    "missing_count": len(positions)
                    if isinstance(positions, list)
                    else None,
                    "missing_positions_location": field("missing_in_region", chain),
                    "numbering_location": field("author_numbering", chain)
                    if isinstance(numbering, dict) and chain in numbering
                    else None,
                }
            )
    source = result.wire["support"][key]["relationship_location"]
    parent, _ = access._resolve(source)
    qualifiers = parent.get("qualifiers")
    present = isinstance(qualifiers, dict) and "assemblies" in qualifiers
    assemblies = qualifiers["assemblies"] if present else None
    assembly_state = (
        "unrecognized_parent_shape"
        if not isinstance(qualifiers, dict)
        else "not_retained"
        if not present
        else "retained_null"
        if assemblies is None
        else "unrecognized_shape"
        if not isinstance(assemblies, list)
        else "retained_empty"
        if not assemblies
        else "retained"
    )
    assembly_location = (
        access._location(
            {
                **source,
                "segments": [
                    *source["segments"],
                    {"type": "Key", "value": "qualifiers"},
                    {"type": "Key", "value": "assemblies"},
                ],
            }
        )
        if present
        else None
    )
    return {
        "rule": RULE,
        "scope": SCOPE,
        "result_ref": result.result_ref,
        "relationship_ref": key,
        "item_location": access._location(result.location("items", key)),
        "source_relationship_location": access._location(source),
        "region": deepcopy(region),
        "sequence_ref": reference.get("sequence_ref"),
        "coordinate_basis": {
            "rule": coordinate.get("rule"),
            "status": coordinate.get("status", "not_retained"),
            "reason": coordinate.get("reason"),
            "structure_reference_revision": coordinate.get(
                "structure_reference_revision", "not_retained"
            ),
            "location": field("coordinate_scope"),
        },
        "status": "recorded" if isinstance(missing, dict) else "not_computed",
        "complete_chains": deepcopy(row.get("complete_chains")),
        "chains": chains,
        "chain_count": len(missing) if isinstance(missing, dict) else None,
        "chains_complete": isinstance(missing, dict) and len(chains) == len(missing),
        "missing_in_region_location": field("missing_in_region"),
        "numbering_location": field("author_numbering"),
        "assembly_context": {"state": assembly_state, "location": assembly_location},
    }
