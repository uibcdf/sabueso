"""PubChem database tools (minimal)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from urllib.parse import quote
from urllib.request import urlopen

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.pubchem import map_compound


def load_json(path: str | Path) -> Dict[str, Any]:
    """Load PubChem JSON from a local file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def create_compound_card_from_json(pubchem_json: Dict[str, Any], retrieved_at: str) -> Any:
    """Create a SmallMolecule Card from PubChem JSON (offline)."""
    mapping = map_compound(pubchem_json, retrieved_at=retrieved_at)
    return build_card_from_mapping(mapping, meta={"entity_type": "small_molecule"})


def create_compound_card_from_file(path: str | Path, retrieved_at: str) -> Any:
    """Create a SmallMolecule Card from a PubChem JSON file."""
    return create_compound_card_from_json(load_json(path), retrieved_at=retrieved_at)


def fetch_pubchem_json(cid: str) -> Dict[str, Any]:
    """Fetch PubChem JSON online by CID (property table)."""
    props = "MolecularWeight,MolecularFormula,CanonicalSMILES,ConnectivitySMILES,InChIKey"
    props_enc = quote(props, safe=",")
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/{props_enc}/JSON"
    with urlopen(url) as resp:  # nosec - expected trusted endpoint
        return json.loads(resp.read().decode("utf-8"))


def create_compound_card_online(cid: str, retrieved_at: str) -> Any:
    """Create a SmallMolecule Card by CID using online fetch."""
    data = fetch_pubchem_json(cid)
    return create_compound_card_from_json(data, retrieved_at=retrieved_at)
