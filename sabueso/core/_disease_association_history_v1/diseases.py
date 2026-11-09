"""Frozen SDK227 flat disease statements, without disease grouping."""

from typing import Any, Callable, Dict, List

CLINVAR_PLACEHOLDERS = {
    "MEDGEN:C3661900": "not provided",
    "MEDGEN:CN169374": "not specified",
}


def disease_statements(
    get: Callable[[str], Any], relationships: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Every statement naming a disease: ``{refs, curies, unmapped, source, kind, ...}``.

    ``get(path)`` returns a field's value; ``relationships`` are the card's."""
    from .normalization import normalize

    out: List[Dict[str, Any]] = []

    def add(refs: List[str], **statement: Any) -> None:
        curies = [normalize(r) for r in refs]
        out.append(
            {
                "refs": refs,
                "curies": [c for c in curies if c],
                "unmapped": [r for r, c in zip(refs, curies) if not c],
                **{k: v for k, v in statement.items() if v is not None},
            }
        )

    for rel in relationships:
        if rel.get("predicate") != "associated_with":
            continue
        q = rel.get("qualifiers") or {}
        add(
            [rel["object_ref"]],
            source=q.get("source"),
            kind="association",
            channel=q.get("channel"),
            name=q.get("disease_name"),
            relationship_id=rel.get("id"),
        )
    for item in get("annotations.disease") or []:
        for xref in item.get("cross_references") or []:
            if xref.get("database") == "MIM" and xref.get("id"):
                add(
                    [f"omim:{xref['id']}"],
                    source="UniProt",
                    kind="uniprot_disease",
                    name=item.get("name"),
                    accession=item.get("accession"),
                )
    for variant in get("annotations.clinical_variants") or []:
        for index, condition in enumerate(variant.get("conditions") or []):
            add(
                list(condition.get("xrefs") or []),
                source="ClinVar",
                kind="clinvar_condition",
                name=condition.get("name"),
                variant=variant.get("accession"),
                condition=index,
            )
    return out


def _card_statements(card: Any) -> List[Dict[str, Any]]:
    def get(path: str) -> Any:
        node = card.get(path)
        return node.get("value") if isinstance(node, dict) else None

    return disease_statements(get, card.relationships())
