"""Finite follow-up queries from original declarations, never identity selection.

These buttons start a separate source query. The original ambiguity, source
bases, duplicate occurrences and unsupported references remain in the report.
"""

import re
from copy import deepcopy

PROTEIN = "sabueso:protein:uniprot:"


def _protein(record):
    if not isinstance(record, dict):
        return None
    ref = record.get("entity_ref")
    if not isinstance(ref, str) or not ref.startswith(PROTEIN):
        return None
    query = ref.removeprefix(PROTEIN)
    if not re.fullmatch(r"[A-Za-z0-9]+(?:-[0-9]+)?", query):
        return None
    return dict(entity_ref=ref, query=query, kind="uniprot", basis=deepcopy(record))


def declared_choices(kind, original):
    """Only routes with an exact supported source reference and original basis."""
    result = []
    if kind == "pdb":
        for record in original.get("related", []):
            choice = _protein(record)
            if choice is not None:
                result.append(choice)
    elif kind == "uniprot" and original.get("status") in ("ambiguous", "resolved"):
        records = original.get(
            "candidates" if original["status"] == "ambiguous" else "alternatives", []
        )
        for record in records:
            choice = _protein(record)
            if choice is not None:
                result.append(choice)
    elif kind == "disease" and original.get("status") == "obsolete":
        from ._record_queries import reference_query

        for record in original.get("candidates", []):
            if not isinstance(record, dict):
                continue
            destination = reference_query(record.get("entity_ref"))
            if destination is not None and destination["kind"] == "disease":
                result.append(
                    {
                        **destination,
                        "entity_ref": record["entity_ref"],
                        "basis": deepcopy(record),
                    }
                )
    elif kind == "smiles" and original.get("status") == "ambiguous":
        decision = original.get("decision", {})
        candidates = (
            decision.get("candidates", []) if isinstance(decision, dict) else []
        )
        if isinstance(candidates, list):
            for ref in candidates:
                # The 20-digit bound is an application input limit, not a claim
                # that a syntactically admitted CID exists in PubChem.
                if isinstance(ref, str) and re.fullmatch(
                    r"pubchem:[1-9][0-9]{0,19}", ref
                ):
                    result.append(
                        dict(
                            entity_ref=ref,
                            query=ref.split(":")[1],
                            kind="pubchem",
                            basis=ref,
                        )
                    )
    return result


def choice_details(resolution):
    """Current bounded UI descriptions; original reports stay byte-identical."""
    from sabueso.core.card_exploration_render import preview

    details = {}
    for index, (ref, choice) in enumerate(resolution.choices.items()):
        if index == 32:
            break
        context = []
        if choice["kind"] == "pubchem":
            title = "PubChem candidate record"
            structure = resolution.original.get("decision", {}).get("structure", {})
            if isinstance(structure, dict) and "retrieved_at" in structure:
                context.append(
                    "Source observation: " + preview(structure["retrieved_at"], 240)
                )
        elif choice["kind"] == "disease":
            title = "MONDO-declared replacement or consideration"
            basis = choice["basis"].get("basis", {})
            if isinstance(basis, dict):
                context.extend(
                    key.replace("_", " ") + ": " + preview(basis[key], 120)
                    for key in ("stated_by", "replaced_by", "consider")
                    if key in basis
                )
        elif resolution.kind == "pdb":
            title = "Source-declared related protein"
            context.append("Declared in the original PDB record")
        else:
            title = "UniProt source candidate or alternative"
            basis = choice["basis"].get("basis")
            if isinstance(basis, dict):
                for key, label in (
                    ("organism_name", "Organism"),
                    ("reviewed", "Reviewed"),
                    ("length", "Recorded length"),
                ):
                    if key in basis:
                        context.append(label + ": " + preview(basis[key], 120))
        details[ref] = {"title": title, "context": context}
    return details
