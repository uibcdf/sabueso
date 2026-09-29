"""Deprecated: RCSB access is ``sabueso.tools.db.rcsb`` (uibcdf/sabueso#49).

Experimental structures are not Cards in Sabueso: they are ``has_structure``
relationships of protein entities, shown through ``Card.structures()`` and enriched from
RCSB polymer-entity data (``sabueso.mappings.rcsb_structures``, ``resolve_protein_card``).
The former PDB-entry cards (``create_structure_card_*``) were removed in
uibcdf/sabueso#21 because they were structure cards typed as proteins.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from urllib.request import urlopen


def load_json(path: str | Path) -> Dict[str, Any]:
    """Load PDB JSON from a local file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fetch_pdb_json(pdb_id: str) -> Dict[str, Any]:
    """Deprecated: use ``sabueso.tools.db.rcsb.get_entry(pdb_id)`` (#49).

    Returns the RCSB REST core entry, as before; ``get_entry`` returns the GraphQL entry
    Sabueso maps, in a provenance envelope.
    """
    from sabueso._private.smonitor.outcomes import report_deprecated

    report_deprecated(
        "sabueso.tools.db.pdb.fetch_pdb_json", "sabueso.tools.db.rcsb.get_entry(pdb_id)"
    )
    url = f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"
    with urlopen(url, timeout=30) as resp:  # nosec - expected trusted endpoint
        return json.loads(resp.read().decode("utf-8"))
