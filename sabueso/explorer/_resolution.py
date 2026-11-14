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


PROTEIN_SOURCES = {
    "identity": {},
    "interpro": {"family_sites": True},
    "alphafold": {"predicted_structures": True},
}


def _protein_options(kind, source):
    """One explicit additional source route; no arbitrary resolver options."""
    if not isinstance(source, str) or source not in PROTEIN_SOURCES:
        raise ArgumentError("Choose identity, InterPro sites or AlphaFold DB models.")
    if source != "identity" and kind != "uniprot":
        raise ArgumentError("Additional protein sources require a UniProt accession.")
    return dict(PROTEIN_SOURCES[source])


def source_access_preview(resolution):
    """Bounded literal access observations, distinct from scientific coverage."""
    from sabueso.core.card_exploration_render import preview

    trace = resolution.acquisition
    records = trace.get("records", []) if isinstance(trace, dict) else []
    if not isinstance(records, list):
        records = []

    def version(record):
        value = record.get("source_version")
        if isinstance(value, dict):
            text = preview(value["value"], 100) if "value" in value else "Not retained"
            basis = (
                preview(value["basis"], 80)
                if "basis" in value
                else "Basis not retained"
            )
            return f"{text} ({basis})"
        return preview(value, 160) if "source_version" in record else "Not retained"

    return {
        "count": len(records),
        "rows": [
            {
                key: preview(record[key], 160) if key in record else "Not retained"
                for key in (
                    "source",
                    "operation",
                    "outcome",
                    "access",
                )
            }
            | {"source_version": version(record)}
            for record in records[:16]
            if isinstance(record, dict)
        ],
        "scope": "Observed source access only; inspect original coverage and quality for scientific outcomes",
    }


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


def _resolve(kind, query, resolver=None, *, protein_source="identity"):
    canonical, options = _query(kind, query)
    options.update(_protein_options(kind, protein_source))
    if resolver is None:
        from sabueso import resolve

        resolver = resolve
    card, resolution = resolver(canonical, profile="identity@1", **options)
    return _Resolution(kind, canonical, card, resolution)
