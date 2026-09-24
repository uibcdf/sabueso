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


# --- Curated bioactivity measurements (uibcdf/sabueso#44) ------------------------------

RELATIONS = ("=", "<", "<=", ">", ">=", "~")
TARGET_ASSIGNMENTS = {"direct": "D", "homology": "H"}
_NUMBER_AND_UNIT = re.compile(r"\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*(.*?)\s*$")


def molecule_identity(molecule: Any) -> Dict[str, Any]:
    """``{"inchikey", "records", "as_given"}`` of a molecule: the standard InChIKey it is anchored at
    and every record linked to it (ChEMBL, PubChem, PDB component, ChEBI...).

    ``molecule`` is a small-molecule Card, an identity already recorded, or an
    identifier (``chembl:``, ``pubchem:``, ``pdb.ligand:``, ``inchikey:``) that Sabueso
    resolves online.
    """
    if isinstance(molecule, dict):
        if not molecule.get("inchikey") or not isinstance(
            molecule.get("records"), list
        ):
            raise SchemaError("A molecule identity needs 'inchikey' and 'records'.")
        return {
            "inchikey": molecule["inchikey"],
            "records": sorted(molecule["records"]),
            "as_given": molecule.get("as_given"),
        }
    card = molecule
    as_given = None
    if isinstance(molecule, str):
        as_given = molecule
        from sabueso.tools.card.small_molecule import resolve_molecule_card

        card, resolution = resolve_molecule_card(molecule)
        if card is None:
            raise SchemaError(
                f"Molecule {molecule!r} did not resolve ({resolution.status})."
            )
    node = card.get("identifiers.inchikey") or {}
    if card.meta.get("entity_type") != "small_molecule" or not node.get("value"):
        raise SchemaError("Expected the card of a small molecule, with its InChIKey.")
    records = sorted({r["subject_ref"] for r in card.relationships("same_as")})
    return {"inchikey": node["value"], "records": records, "as_given": as_given}


def _measured(value: Any) -> Tuple[Dict[str, Any], Dict[str, Any], int | None]:
    """``(as written, normalized node, stated decimals in the normalized unit)`` for a
    potency (a concentration, normalized to nanomolar) or a percentage."""
    import pyunitwizard as puw

    from .quantities import CONCENTRATION_UNIT, quantity_node

    if isinstance(value, str):
        match = _NUMBER_AND_UNIT.fullmatch(value)
        if not match or not match.group(2):
            raise SchemaError(f"A measured value needs its unit: {value!r}.")
        # The number is kept as written, so its stated precision survives re-application.
        number, unit = match.group(1), match.group(2)
        written = {"value": number, "unit": unit}
        text = number
    elif (
        isinstance(value, dict)
        and isinstance(value.get("unit"), str)
        and isinstance(value.get("value"), (str, int, float))
        and not isinstance(value.get("value"), bool)
    ):
        written = {"value": value["value"], "unit": value["unit"]}
        raw = value["value"]
        text = raw if isinstance(raw, str) else repr(raw)
    elif puw.is_quantity(value):
        v, u = puw.get_value_and_unit(value)
        written, text = {"value": float(v), "unit": str(u)}, repr(float(v))
    else:
        raise SchemaError(f"A measured value needs its unit, not {value!r}.")
    unit = "percent" if written["unit"].strip() in ("%", "percent") else written["unit"]
    try:
        q = puw.quantity(float(written["value"]), unit, form="pint")
    except Exception:
        raise SchemaError(f"Unknown unit {written['unit']!r}.") from None
    for target in (CONCENTRATION_UNIT, "percent"):
        try:
            number = converted(float(puw.convert(q, to_unit=target, to_type="value")))
            factor = float(
                puw.convert(
                    puw.quantity(1.0, unit, form="pint"),
                    to_unit=target,
                    to_type="value",
                )
            )
        except Exception:
            continue
        decimals = _decimals(text)
        power = math.log10(factor) if factor > 0 else float("nan")
        decimals = (
            decimals - round(power)
            if decimals is not None and abs(power - round(power)) < 1e-9
            else None
        )
        return written, quantity_node(number, target), decimals
    raise SchemaError(
        f"{written['unit']!r} is neither a concentration nor a percentage."
    )


def _agrees(a: float, b: float, decimals: int | None) -> bool:
    if decimals is None:
        return math.isclose(a, b, rel_tol=1e-9)
    return abs(a - b) <= 0.5 * 10.0**-decimals + 1e-9


def add_literature_bioactivity(
    card: Any,
    molecule: Any,
    measurement_type: str,
    value: Any,
    publication: str,
    curator: str,
    target_assignment: str,
    relation: str = "=",
    assay_description: str | None = None,
    locator: str | None = None,
    quote: str | None = None,
    eco_code: str | None = None,
    curated_at: str | None = None,
) -> Dict[str, Any]:
    """Record a bioactivity a publication reports, and compare it with ChEMBL.

    The measurement becomes a ``has_bioactivity`` relationship of its own (its
    ``activity_id`` is ``curated:<digest>``), carrying the molecule's identity. It is
    compared with the ChEMBL measurements of the same publication (by PubMed id or DOI),
    the same molecule (any of its records) and the same type: a value agreeing at the
    precision it was stated with corroborates; none agreeing differs; none to compare
    with is new. Nothing is overridden.
    """
    from .relationship_store import make_relationship

    subject = _subject(card)
    curated_at = curated_at or datetime.now(timezone.utc).date().isoformat()
    identity = molecule_identity(molecule)
    written, normalized, decimals = _measured(value)
    # What the curator states: the molecule as given and its InChIKey. The records
    # UniChem links belong to the card's glossary, not to the statement (#52).
    asserted = {
        "molecule": {
            "inchikey": identity["inchikey"],
            "as_given": identity["as_given"],
        },
        "measurement": {"type": measurement_type, "relation": relation, **written},
        "target_assignment": target_assignment,
        "assay_description": assay_description,
    }
    field_path = "relationships.has_bioactivity"
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
        decimals=decimals,
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

    records = identity["records"]
    shown = next(
        (
            r
            for namespace in ("chembl:", "pdb.ligand:", "pubchem:")
            for r in records
            if r.startswith(namespace)
        ),
        f"inchikey:{identity['inchikey']}",
    )
    kind, _, number = publication.partition(":")
    document = {
        "id": None,
        "year": None,
        "journal": None,
        "pubmed": number if kind == "pubmed" else None,
        "doi": number if kind == "doi" else None,
        "title": None,
    }
    relationship = make_relationship(
        subject,
        "has_bioactivity",
        shown,
        qualifiers={
            "activity_id": "curated:" + assertion["id"].rsplit("_", 1)[-1],
            "parent_molecule": shown,
            "molecule_ref": f"inchikey:{identity['inchikey']}",
            "measurement": {
                "type": measurement_type,
                "relation": relation,
                "value": float(written["value"]),
                "units": written["unit"],
                "normalized": normalized,
                "pchembl": None,
                "curated": True,
            },
            "assay": {
                "id": None,
                "description": assay_description,
                "relationship_type": TARGET_ASSIGNMENTS[target_assignment],
                "organism": None,
                "curated": True,
            },
            "document": document,
        },
        source_assertion_ids=[assertion["id"]],
    )

    same = []
    for rel in card.relationships("has_bioactivity"):
        q = rel.get("qualifiers", {})
        if (q.get("assay") or {}).get("curated"):
            continue
        doc = q.get("document") or {}
        if not (
            (document["pubmed"] and doc.get("pubmed") == document["pubmed"])
            or (
                document["doi"]
                and (doc.get("doi") or "").lower() == document["doi"].lower()
            )
        ):
            continue
        refs = {rel["object_ref"], q.get("parent_molecule")}
        if (
            not refs & set(records)
            or (q.get("measurement") or {}).get("type") != measurement_type
        ):
            continue
        same.append(rel)
    agreeing = [
        rel
        for rel in same
        if ((rel["qualifiers"]["measurement"].get("relation") or "=") == relation)
        and (rel["qualifiers"]["measurement"].get("normalized") or {}).get("unit")
        == normalized["unit"]
        and _agrees(
            float(rel["qualifiers"]["measurement"]["normalized"]["value"]),
            float(normalized["value"]),
            decimals,
        )
    ]
    card.source_assertion_store.add(assertion)
    card.relationship_store.add(relationship)
    card.register_identity(
        f"inchikey:{identity['inchikey']}",
        records,
        "small_molecule",
        {"by": "curation", "at": curated_at},
    )
    compared = [r["id"] for r in same]
    if not same:
        outcome = "new"
    elif agreeing:
        outcome = "corroborates"
    else:
        outcome = "differs"
        card.quality.setdefault("conflicts", []).append(
            {
                "field": field_path,
                "type": "curated_difference",
                "relationship_id": relationship["id"],
                "values": [r["qualifiers"]["measurement"]["normalized"] for r in same]
                + [normalized],
                "relationship_ids": [compared, [relationship["id"]]],
            }
        )
    record = {
        **base,
        "relationship_id": relationship["id"],
        "outcome": outcome,
        "compared_with": compared,
    }
    card.quality.setdefault("curation", []).append(record)
    return record
