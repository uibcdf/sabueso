"""Explicit public-source queries, independent of desktop and rendering hosts."""

from __future__ import annotations

import json
import re
import secrets

from sabueso.core.errors import ArgumentError


def _query(kind, text):
    if not isinstance(text, str) or not text.strip() or len(text) > 8192:
        raise ArgumentError("Enter an identifier or SMILES of 1–8192 characters.")
    text = text.strip()
    if kind == "uniprot":
        value = text.removeprefix("uniprot:")
        if not re.fullmatch(r"[A-Za-z0-9]+(?:-[0-9]+)?", value):
            raise ArgumentError("Enter a UniProt accession, not a protein name.")
        return f"uniprot:{value}", {}
    if kind == "pdb":
        value = text.removeprefix("pdb:")
        if not re.fullmatch(r"[A-Za-z0-9]{4}", value):
            raise ArgumentError("Enter a four-character PDB entry identifier.")
        return f"pdb:{value}", {}
    if kind == "smiles":
        return f"smiles:{text.removeprefix('smiles:')}", {"unichem": False}
    if kind == "pubchem":
        value = text.removeprefix("pubchem:")
        if not re.fullmatch(r"[1-9][0-9]{0,19}", value):
            raise ArgumentError(
                "Choose an exact positive PubChem CID of at most 20 digits."
            )
        return f"pubchem:{value}", {"unichem": False}
    if kind == "disease":
        from sabueso.tools.db.mondo import normalize

        if normalize(text) is None:
            raise ArgumentError(
                "Enter a supported disease identifier, such as MONDO:0014221."
            )
        return text, {"entity_type": "disease"}
    raise ArgumentError("Choose UniProt, PDB, SMILES or a disease identifier.")


class _Resolution:
    def __init__(self, kind, query, card, resolution):
        self.kind = kind
        self.query = query
        self.card = card
        self.revision = secrets.token_hex(16)
        self.original = resolution.to_dict()
        self.acquisition = resolution.acquisition_trace
        self.choices = {}
        from ._source_choices import declared_choices

        self.choices = {
            secrets.token_hex(16): value
            for value in declared_choices(kind, self.original)
        }

    def panel(self):
        return {
            "format": "sabueso.explorer_resolution@1",
            "revision": self.revision,
            "kind": self.kind,
            "query": self.query,
            "status": self.original["status"],
            "entity_ref": self.original["entity_ref"],
            "has_card": self.card is not None,
            "choices": [
                {"ref": ref, "entity_ref": item["entity_ref"]}
                for ref, item in self.choices.items()
            ],
            "original_text": json.dumps(
                {"resolution": self.original, "acquisition_trace": self.acquisition},
                ensure_ascii=False,
                indent=2,
            ),
        }


def _resolve(kind, query, resolver=None):
    canonical, options = _query(kind, query)
    if resolver is None:
        from sabueso import resolve

        resolver = resolve
    card, resolution = resolver(canonical, profile="identity@1", **options)
    return _Resolution(kind, canonical, card, resolution)
