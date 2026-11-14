"""Explicit fresh record queries from exact native retained link rows.

This is acquisition admission, not retained destination resolution or an identity
rule. It never follows a name, arbitrary field value, pinned revision or URL.
"""

from __future__ import annotations

import re

from sabueso.core.errors import ArgumentError


def reference_query(reference):
    """Finite unambiguous record namespaces; no implicit identifier conversion."""
    if not isinstance(reference, str) or len(reference) > 8192:
        return None
    # A fresh source query cannot reproduce a pinned Card/item revision.
    if "@" in reference or "#" in reference:
        return None
    value = reference
    if value.startswith("sabueso:protein:uniprot:"):
        value = value.removeprefix("sabueso:protein:")
    elif value.startswith("sabueso:disease:mondo:"):
        value = value.removeprefix("sabueso:disease:")
    elif value.startswith("sabueso:"):
        return None
    if re.fullmatch(r"uniprot:[A-Za-z0-9]+(?:-[0-9]+)?", value):
        return {"kind": "uniprot", "query": value}
    if re.fullmatch(r"pdb:[A-Za-z0-9]{4}", value):
        return {"kind": "pdb", "query": value}
    if re.fullmatch(r"pdb\.ligand:[A-Za-z0-9]{1,5}", value):
        return {"kind": "pdb_ligand", "query": value}
    if re.fullmatch(r"pubchem:[1-9][0-9]{0,19}", value):
        return {"kind": "pubchem", "query": value}
    if re.fullmatch(r"(?:mondo:)?MONDO:[0-9]{7}", value):
        return {"kind": "disease", "query": value}
    # In particular, a bare chembl namespace can denote a molecule, target or
    # assay. Its spelling alone must not route a protein target as a compound.
    return None


def item_query(view, item):
    """Only native subject/object/entity links, not lookalike Card extensions."""
    if view.schema.get("kind") != "link" or item.kind != "link":
        return None
    cells = item.cells
    if not {"role", "target_ref"} <= cells.keys():
        return None
    role, reference = cells["role"].value, cells["target_ref"].value
    if role not in ("subject", "object", "entity"):
        return None
    destination = reference_query(reference)
    if destination is None:
        return None
    return {**destination, "reference": reference, "role": role}


def current_item_query(session, item_ref):
    """Recheck the current Card/Deck page; the caller supplies no target string."""
    from ._deck_session import _DeckSession
    from ._session import PAGE_SIZE, _Session

    reading = session.card_session if isinstance(session, _DeckSession) else session
    if not isinstance(reading, _Session) or not isinstance(item_ref, str):
        raise ArgumentError("Choose a referenced record from a retained Card reading.")
    visible = reading.current.items()[reading.offset : reading.offset + PAGE_SIZE]
    item = next((item for item in visible if item.item_ref == item_ref), None)
    destination = item_query(reading.current, item) if item is not None else None
    if destination is None:
        raise ArgumentError("Choose a supported record link from the current page.")
    return destination
