"""Curated literature assertions on existing card fields (uibcdf/sabueso#41, part 2).

A person, or later an agent, reads a publication and records what it states as a
SourceAssertion: ``source.type = "literature"``, the publication as the record
(``pubmed:<id>`` or ``doi:<doi>``), and the curation in ``source_metadata.curation``
(curator, date, locator, optional short quote). Sabueso does not read the paper. It
checks the claim's shape against the field, stores it, and compares it mechanically
with what other sources state:

- a **scalar** field (``properties.physchem.*``) is resolved again from all its
  assertions. "Literature" is not in any priority list, so a curated value is selected
  only when nothing else states the field;
- a **list** field compares items by an identity (``ITEM_IDENTITY``), for example
  position and substitution for a mutagenesis. An item with the same identity and the
  same content corroborates; the same identity with a different content **differs**.
  Sabueso cannot tell whether "abolishes homodimer" and "Loss of dimerization" mean the
  same thing, so a difference is flagged for a reader, never judged a contradiction;
- free-text lists (``annotations.function``, ``subunit``...) have no identity: the item
  is added and marked ``not_compared``.

Nothing is discarded or overridden. Every outcome is recorded in
``quality.curation``; a difference also goes to ``quality.conflicts`` and raises
``CuratedDisagreementWarning``. How a curated assertion bears on a project's hypotheses
is Nextia Evidence, not Sabueso's (SourceAssertion ≠ Evidence).
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Tuple

from .errors import SchemaError
from .quantities import FIELD_UNITS, converted, is_quantity_node
from .source_assertion_store import (
    assertion_value,
    generate_source_assertion_id,
    make_source_assertion,
)

LITERATURE = "Literature"

SCALAR_FIELDS = frozenset(
    {
        "properties.physchem.aromatic_rings",
        "properties.physchem.formula",
        "properties.physchem.hba",
        "properties.physchem.hbd",
        "properties.physchem.logp",
        "properties.physchem.molecular_weight",
        "properties.physchem.molecule_type",
        "properties.physchem.rotatable_bonds",
        "properties.physchem.tpsa",
    }
)


def _positions(item: Dict[str, Any]) -> Tuple[int, ...]:
    sequence = (item.get("location") or {}).get("sequence") or {}
    spans = sequence.get("fragments") or [
        {"start": sequence.get("start"), "end": sequence.get("end")}
    ]
    return tuple(
        sorted(
            {
                p
                for s in spans
                if s.get("start") is not None
                for p in range(s["start"], (s.get("end") or s["start"]) + 1)
            }
        )
    )


def _substitution(item: Dict[str, Any]) -> tuple:
    s = item.get("substitution") or {}
    return (s.get("original"), tuple(s.get("alternatives") or []))


#: How two items of a list field are recognised as the same item. None: free text,
#: which cannot be compared without reading it.
ITEM_IDENTITY: Dict[str, Callable[[Any], Any] | None] = {
    "features_positional.mutagenesis": lambda i: (_positions(i), _substitution(i)),
    "features_positional.natural_variant": lambda i: (_positions(i), _substitution(i)),
    "features_positional.binding_site": lambda i: (
        _positions(i),
        ((i.get("ligand") or {}).get("name") or "").lower(),
    ),
    "features_positional.active_site": _positions,
    "features_positional.disulfide_bond": _positions,
    "features_positional.glycosylation": _positions,
    "features_positional.modified_residue": _positions,
    "annotations.disease": lambda i: i.get("accession") or i.get("name", "").lower(),
    "annotations.catalytic_activity": lambda i: i.get("rhea_id") or i.get("reaction"),
    "annotations.subcellular_location": lambda i: (i.get("location") or "").lower(),
    "annotations.function": None,
    "annotations.pathway": None,
    "annotations.subunit": None,
    "annotations.ptm": None,
    "annotations.polymorphism": None,
    "annotations.tissue_specificity": None,
}
LIST_FIELDS = frozenset(ITEM_IDENTITY)
CURATABLE_FIELDS = SCALAR_FIELDS | LIST_FIELDS

#: Predicates a curated assertion may state. Not identity links (same_as...), not
#: has_structure (the PDB states structures), not described_in (citing is not a claim),
#: and not has_bioactivity yet: telling a curated measurement from the ChEMBL record of
#: the same paper needs its own design (uibcdf/sabueso#44).
CURATABLE_PREDICATES = frozenset(
    {
        "interacts_with",
        "functionally_associated_with",
        "annotated_with",
        "classified_in",
        "has_ligand_site",
        "has_interface_with",
    }
)

#: Keys an item must state, per list field (beyond a location for positional fields).
REQUIRED_KEYS = {
    "features_positional.mutagenesis": ("substitution", "description"),
    "features_positional.natural_variant": ("substitution",),
    "annotations.disease": ("name",),
    "annotations.catalytic_activity": ("reaction",),
    "annotations.subcellular_location": ("location",),
}


def _key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)


def _subject(card: Any) -> str:
    card_id = card.meta.get("card_id") or ""
    entity_type = card.meta.get("entity_type") or ""
    prefix = f"sabueso:{entity_type}:"
    if not card_id.startswith(prefix):
        raise SchemaError("A curated assertion needs a card with a stable card_id.")
    return card_id[len(prefix) :]


def _sequence_id(subject: str) -> str | None:
    namespace, _, record = subject.partition(":")
    return f"UniProt:{record}" if namespace == "uniprot" else None


def _item(field_path: str, value: Any, subject: str) -> Any:
    """The item as it will be stored, or SchemaError if its shape does not fit."""
    if ITEM_IDENTITY[field_path] is None:
        if not isinstance(value, str) or not value.strip():
            raise SchemaError(f"{field_path} takes a non-empty text.")
        return value.strip()
    if not isinstance(value, dict):
        raise SchemaError(f"{field_path} takes a dict item.")
    item = dict(value)
    if field_path.startswith("features_positional."):
        if "location" not in item:
            # Shorthand: {"start": 105} or {"start": 12, "end": 14}, in the card's
            # UniProt numbering.
            if not isinstance(item.get("start"), int):
                raise SchemaError(
                    f"{field_path} needs a location, or 'start' in UniProt numbering."
                )
            start = item.pop("start")
            end = item.pop("end", start)
            item["location"] = {
                "kind": "sequence",
                "sequence": {
                    "sequence_id": _sequence_id(subject),
                    "start": start,
                    "end": end,
                    "indexing": "1-based",
                },
            }
        if not _positions(item):
            raise SchemaError(f"{field_path} needs at least one sequence position.")
    missing = [k for k in REQUIRED_KEYS.get(field_path, ()) if not item.get(k)]
    if missing:
        raise SchemaError(f"{field_path} items need {missing}.")
    return item


def _decimals(text: str) -> int | None:
    match = re.match(r"\s*[-+]?(\d+)(?:\.(\d+))?(?![\d.eE])", text)
    if match is None:
        return None
    return len(match.group(2) or "")


def _scalar(field_path: str, value: Any) -> Tuple[Any, Any, int | None]:
    """``(asserted, normalized, stated decimals in the field's unit)``.

    A quantity field takes a quantity in any PyUnitWizard form, never a bare number. It
    is converted explicitly to the field's negotiated unit. The value is kept as written
    (a string stays verbatim), and its stated precision is carried into the field's
    unit: "0.9 kDa" states hundreds of daltons, "824.97 Da" hundredths.
    """
    unit = FIELD_UNITS.get(field_path)
    if unit is None:
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            raise SchemaError(f"{field_path} takes a number or a text.")
        return value, value, None
    import pyunitwizard as puw

    if is_quantity_node(value):
        q = puw.quantity(float(value["value"]), value["unit"], form="pint")
        asserted, text = dict(value), repr(value["value"])
    elif isinstance(value, str) or puw.is_quantity(value):
        try:
            q = puw.convert(value, to_form="pint")
        except Exception:
            raise SchemaError(
                f"{field_path} takes a quantity, not {value!r}."
            ) from None
        if isinstance(value, str):
            asserted, text = value, value
        else:
            stated_value, stated_unit = puw.get_value_and_unit(q)
            asserted = {"value": float(stated_value), "unit": str(stated_unit)}
            text = repr(float(stated_value))
    else:
        raise SchemaError(
            f"{field_path} is a quantity in {unit}: give its unit, not a bare number."
        )
    try:
        number = converted(float(puw.convert(q, to_unit=unit, to_type="value")))
        factor = float(
            puw.convert(
                puw.quantity(1.0, str(puw.get_unit(q)), form="pint"),
                to_unit=unit,
                to_type="value",
            )
        )
    except Exception:
        raise SchemaError(f"{field_path} must be convertible to {unit}.") from None
    decimals = _decimals(text)
    power = math.log10(factor) if factor > 0 else float("nan")
    if decimals is not None and abs(power - round(power)) < 1e-9:
        decimals -= round(power)
    else:
        decimals = None  # not a decimal scale change: compare exactly
    return asserted, number, decimals


def _field_assertions(card: Any, field_path: str) -> List[Dict]:
    """Every assertion about the field. A card's field assertions are all about its
    entity, whatever record they came from (a small molecule's ChEMBL and PubChem
    records): the aggregator admits no other."""
    return [
        a
        for a in card.source_assertion_store.to_list()
        if a.get("field_path") == field_path
    ]


def _replace(records: List[Dict], field_path: str, new: Dict | None) -> List[Dict]:
    kept = [r for r in records if r.get("field") != field_path]
    return kept + ([new] if new else [])


def add_literature_assertion(
    card: Any,
    field_path: str,
    value: Any,
    publication: str,
    curator: str,
    locator: str | None = None,
    quote: str | None = None,
    method: str | None = None,
    eco_code: str | None = None,
    curated_at: str | None = None,
) -> Dict[str, Any]:
    """Record what ``publication`` states about ``field_path``; see the module docstring.

    Returns the curation record also appended to ``card.quality["curation"]``:
    ``{"field", "publication", "source_assertion_id", "outcome", "compared_with"}`` where
    ``outcome`` is ``new``, ``corroborates``, ``differs``, ``not_comparable`` or
    ``not_compared``.
    """
    if field_path not in CURATABLE_FIELDS:
        raise SchemaError(f"{field_path} cannot take curated literature assertions.")
    subject = _subject(card)
    curated_at = curated_at or datetime.now(timezone.utc).date().isoformat()

    decimals = None
    if field_path in SCALAR_FIELDS:
        asserted, normalized, decimals = _scalar(field_path, value)
    else:
        asserted = normalized = _item(field_path, value, subject)

    assertion = _literature_assertion(
        field_path,
        asserted,
        publication,
        subject,
        curator,
        locator,
        quote,
        eco_code,
        curated_at,
        method=method,
        decimals=decimals,
    )
    if normalized != asserted:
        assertion["normalized_value"] = normalized
    if card.source_assertion_store.get(assertion["id"]) is not None:
        previous = next(
            (
                r
                for r in card.quality.get("curation", [])
                if r["source_assertion_id"] == assertion["id"]
            ),
            None,
        )
        # The same statement, already recorded.
        return previous or {
            "field": field_path,
            "publication": publication,
            "source_assertion_id": assertion["id"],
            "outcome": "already_recorded",
            "compared_with": [],
        }
    others = _field_assertions(card, field_path)
    card.source_assertion_store.add(assertion)

    if field_path in SCALAR_FIELDS:
        record = _resolve_scalar(card, field_path, assertion, others)
    else:
        record = _add_item(card, field_path, assertion, others)
    record = {
        "field": field_path,
        "publication": publication,
        "source_assertion_id": assertion["id"],
        **record,
    }
    card.quality.setdefault("curation", []).append(record)
    return record


def _resolve_scalar(card, field_path, assertion, others) -> Dict[str, Any]:
    from sabueso.resolver import load_selection_rules, resolve_field

    rules = card.selection_rules or load_selection_rules()
    result = resolve_field(field_path, others + [assertion], rules)
    card.set(
        field_path,
        result.get("selected_value"),
        result.get("source_assertion_ids", []),
    )
    conflict, alternatives = result.get("conflict"), result.get("alternatives")
    card.quality["conflicts"] = _replace(
        card.quality.get("conflicts", []),
        field_path,
        {"field": field_path, **conflict} if conflict else None,
    )
    card.quality["alternatives"] = _replace(
        card.quality.get("alternatives", []),
        field_path,
        {"field": field_path, **alternatives} if alternatives else None,
    )
    for key in ("conflicts", "alternatives"):
        if not card.quality[key]:
            del card.quality[key]
    compared = [a["id"] for a in others]
    by_id = {a["id"]: a for a in others}
    # The assertions stating the curated value: its conflict group, or the selected
    # support when there is no conflict.
    groups = (conflict or {}).get("source_assertion_ids") or []
    mine = next((g for g in groups if assertion["id"] in g), None)
    if mine is None and assertion["id"] in result.get("source_assertion_ids", []):
        mine = result["source_assertion_ids"]
    agreeing = [i for i in mine or [] if i != assertion["id"] and i in by_id]
    if not others:
        outcome = "new"
    elif any(_is_database(by_id[i]) for i in agreeing):
        outcome = "corroborates"  # another source states the same value
    elif mine is not None and conflict:
        outcome = "differs"
    elif agreeing:
        outcome = "corroborates"  # only other curated assertions agree
    elif alternatives:
        outcome = "not_comparable"  # e.g. another or an unstated method
    else:
        outcome = "differs"
    return {"outcome": outcome, "compared_with": compared}


def _is_database(assertion: Dict[str, Any]) -> bool:
    return (assertion.get("source") or {}).get("type") != "literature"


def _add_item(card, field_path, assertion, others) -> Dict[str, Any]:
    item = assertion_value(assertion)
    node = card.get(field_path) or {"value": [], "source_assertion_ids": []}
    items = list(node.get("value") or [])
    if _key(item) not in {_key(i) for i in items}:
        items.append(item)
    card.set(
        field_path,
        items,
        list(node.get("source_assertion_ids") or []) + [assertion["id"]],
    )
    identity = ITEM_IDENTITY[field_path]
    if identity is None:
        return {"outcome": "not_compared", "compared_with": []}
    same = [a for a in others if identity(assertion_value(a)) == identity(item)]
    if not same:
        return {"outcome": "new", "compared_with": []}
    compared = [a["id"] for a in same]
    if any(_key(assertion_value(a)) == _key(item) for a in same):
        return {"outcome": "corroborates", "compared_with": compared}
    card.quality.setdefault("conflicts", []).append(
        {
            "field": field_path,
            "type": "curated_difference",
            "values": [assertion_value(a) for a in same] + [item],
            "source_assertion_ids": [[a["id"]] for a in same] + [[assertion["id"]]],
        }
    )
    return {"outcome": "differs", "compared_with": compared}


def _literature_assertion(
    field_path,
    asserted,
    publication,
    subject,
    curator,
    locator,
    quote,
    eco_code,
    curated_at,
    method=None,
    decimals=None,
):
    assertion = make_source_assertion(
        field_path,
        asserted,
        LITERATURE,
        publication,
        curated_at,
        source_type="literature",
        subject_ref=subject,
    )
    # Two statements of the same value in two places of a paper are two assertions.
    assertion["id"] = generate_source_assertion_id(
        LITERATURE, publication, field_path, {"value": asserted, "locator": locator}
    )
    curation = {"curator": curator, "curated_at": curated_at, "locator": locator}
    if quote:
        curation["quote"] = quote
    metadata: Dict[str, Any] = {"curation": curation}
    if method:
        metadata["method"] = method
    if decimals is not None:
        metadata["stated_decimals"] = decimals  # in the field's unit
    if eco_code:
        metadata["eco"] = [{"code": eco_code, "source": "Literature"}]
    assertion["source_metadata"] = metadata
    return assertion


def add_literature_relationship(
    card: Any,
    predicate: str,
    object_ref: str,
    qualifiers: Dict[str, Any] | None,
    publication: str,
    curator: str,
    locator: str | None = None,
    quote: str | None = None,
    eco_code: str | None = None,
    curated_at: str | None = None,
) -> Dict[str, Any]:
    """Record a relationship a publication states (``CURATABLE_PREDICATES``).

    The relationship merges with the same relationship stated by other sources (same
    subject, predicate and object). Qualifiers the curated assertion states differently
    become ``qualifier_conflicts`` on the relationship, and the outcome is ``differs``;
    nothing is overridden. Outcomes and records as in ``add_literature_assertion``.
    """
    from .relationship_store import make_relationship

    if predicate not in CURATABLE_PREDICATES:
        raise SchemaError(f"{predicate} cannot take curated literature assertions.")
    subject = _subject(card)
    curated_at = curated_at or datetime.now(timezone.utc).date().isoformat()
    qualifiers = dict(qualifiers or {})
    field_path = f"relationships.{predicate}"
    assertion = _literature_assertion(
        field_path,
        {"object_ref": object_ref, "qualifiers": qualifiers},
        publication,
        subject,
        curator,
        locator,
        quote,
        eco_code,
        curated_at,
    )
    base = {
        "field": field_path,
        "publication": publication,
        "source_assertion_id": assertion["id"],
    }
    if card.source_assertion_store.get(assertion["id"]) is not None:
        previous = next(
            (
                r
                for r in card.quality.get("curation", [])
                if r["source_assertion_id"] == assertion["id"]
            ),
            None,
        )
        return previous or {**base, "outcome": "already_recorded", "compared_with": []}

    relationship = make_relationship(
        subject,
        predicate,
        object_ref,
        qualifiers,
        source_assertion_ids=[assertion["id"]],
    )
    existing = card.relationship_store.get(relationship["id"])
    before = json.loads(_key((existing or {}).get("qualifier_conflicts") or {}))
    compared = list((existing or {}).get("source_assertion_ids") or [])
    card.source_assertion_store.add(assertion)
    card.relationship_store.add(relationship)
    stored = card.relationship_store.get(relationship["id"])
    after = stored.get("qualifier_conflicts") or {}
    differing = {
        k: v for k, v in after.items() if k in qualifiers and v != before.get(k)
    }
    if existing is None:
        outcome = "new"
    elif differing:
        outcome = "differs"
        card.quality.setdefault("conflicts", []).append(
            {
                "field": field_path,
                "type": "curated_difference",
                "relationship_id": relationship["id"],
                "qualifiers": differing,
                "source_assertion_ids": [compared, [assertion["id"]]],
            }
        )
    else:
        outcome = "corroborates"
    record = {
        **base,
        "relationship_id": relationship["id"],
        "outcome": outcome,
        "compared_with": compared,
    }
    card.quality.setdefault("curation", []).append(record)
    return record
