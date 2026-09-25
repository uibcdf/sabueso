"""Migrating stored cards to the current schema, honestly (uibcdf/sabueso#51).

A migration does not have to be complete, but it must say what it did not do:

- ``migrate_card(data)`` converts a stored card, step by step, to the current card
  schema. Every step appends a record to ``quality.migration``: from which version to
  which, the rule, what was converted, and the **gaps**. A gap is what a card of the
  new schema can hold but the old card cannot, because its sources were not asked for
  it then:
  - ``missing``: a fresh build with the same options would have it, e.g. UniProt's
    taxon and lineage since 0.3.2;
  - ``available``: an enrichment that did not exist when the card was built, and can be
    asked for, e.g. NCBI Taxonomy since 0.3.4.
- The original is never changed. The record keeps its snapshot id, and ``store=``
  saves the original, when it is readable, and then the migrated card, as two
  revisions of one card.
- ``refresh_card(card)`` completes the gaps by building the card again from its
  sources, with the options its enrichments record. Curations are re-applied when a
  ``CurationStore`` is given, and keep their ids. A refresh record says which gaps were
  completed and which the sources still do not state.

Within one schema line, a step only re-labels the version: additions are optional. A
step between lines (``0.3`` → ``0.4``) is a function registered in ``STEPS``. None
exists yet, and loading a card of another line is refused, with a pointer here.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Tuple

from .errors import StorageError
from .schema_version import parse, same_line

MIGRATION_RULE = "card_migration@1"

#: What each schema version added, and how a card gets it (``filled_by``):
#: ``refresh`` (a fresh build with the same options states it), ``<option>`` (an
#: enrichment to ask for), or ``curation``. Paths are field paths or relationship
#: templates.
SCHEMA_CHANGES: Dict[str, List[Dict[str, str]]] = {
    "0.3.1": [{"path": "annotations.disease", "filled_by": "refresh"}],
    "0.3.2": [
        {"path": "annotations.taxon_id", "filled_by": "refresh"},
        {"path": "annotations.lineage", "filled_by": "refresh"},
        {"path": "identifiers.gene_loci", "filled_by": "refresh"},
        {
            "path": "relationships.classified_in (orthodb, eggnog)",
            "filled_by": "refresh",
        },
        {
            "path": "relationships.has_predicted_structure",
            "filled_by": "predicted_structures",
        },
        {
            "path": "relationships.has_bioactivity.measurement.normalized_upper",
            "filled_by": "refresh",
        },
        {"path": "relationships.engages", "filled_by": "curation"},
    ],
    "0.3.3": [
        {
            "path": "relationships.has_predicted_structure.isoform",
            "filled_by": "predicted_structures",
        },
    ],
    "0.3.4": [
        {"path": "annotations.taxonomy", "filled_by": "taxonomy"},
        {"path": "relationships.has_bioactivity (BindingDB)", "filled_by": "bindingdb"},
        {
            "path": "relationships.has_bioactivity (PubChem BioAssay)",
            "filled_by": "pubchem_bioassay",
        },
        {"path": "literature.claims", "filled_by": "curation"},
        {"path": "names.synonyms", "filled_by": "refresh"},
        {"path": "names.abbreviations", "filled_by": "refresh"},
        {"path": "names.gene_names", "filled_by": "refresh"},
    ],
}

#: Steps between schema lines: ``(from line, to line) -> step(data) -> (data, notes)``,
#: where ``notes`` is ``{"converted": [...], "gaps": [...]}``. None exists yet.
STEPS: Dict[
    Tuple[str, str], Callable[[Dict[str, Any]], Tuple[Dict[str, Any], Dict[str, Any]]]
] = {}


def _line(version: Tuple[int, int, int]) -> str:
    return f"{version[0]}.{version[1]}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _has(data: Dict[str, Any], path: str) -> bool:
    """Whether a stored card holds ``path`` (a field, or a relationship template)."""
    if path.startswith("relationships."):
        predicate = path.split(".")[1].split(" ")[0]
        rels = [
            r
            for r in data.get("relationship_store") or []
            if r.get("predicate") == predicate
        ]
        if " (" in path:
            wanted = path.split("(", 1)[1].rstrip(")")
            if predicate == "classified_in":
                return any(
                    r["object_ref"].split(":")[0] in ("orthodb", "eggnog") for r in rels
                )
            return any(
                (r.get("qualifiers") or {}).get("source") == wanted for r in rels
            )
        return bool(rels)
    node: Any = data.get("sections") or {}
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            return False
        node = node[key]
    return True


def _enrichment_options(data: Dict[str, Any]) -> set:
    """The enrichment options a stored card records it was built with."""
    options = set()
    for e in (data.get("quality") or {}).get("enrichments") or []:
        source, kind = e.get("source"), e.get("data")
        options |= {
            ("AlphaFold DB", None): {"predicted_structures"},
            ("NCBI Taxonomy", None): {"taxonomy"},
            ("BindingDB", None): {"bindingdb"},
            ("PubChem BioAssay", None): {"pubchem_bioassay"},
        }.get((source, kind), set())
    return options


def within_line_gaps(
    data: Dict[str, Any], stated: str, target: str
) -> List[Dict[str, str]]:
    """The additions between two versions of one line the card does not hold."""
    have, want = parse(stated), parse(target)
    asked = _enrichment_options(data)
    gaps = []
    for version, changes in sorted(SCHEMA_CHANGES.items(), key=lambda kv: parse(kv[0])):
        if not (have < parse(version) <= want):
            continue
        for change in changes:
            if _has(data, change["path"]):
                continue
            filled_by = change["filled_by"]
            if filled_by == "curation":
                continue  # only a curator adds it; its absence is not a gap
            kind = (
                "missing"
                if filled_by == "refresh" or filled_by in asked
                else "available"
            )
            gaps.append(
                {
                    "introduced_in": version,
                    "path": change["path"],
                    "filled_by": filled_by,
                    "kind": kind,
                }
            )
    return gaps


def migrate_card(data: Dict[str, Any], store: Any = None) -> Any:
    """A card of the current schema from stored card data; see the module docstring."""
    from .card import CARD_SCHEMA_VERSION, Card
    from .quantities import seal
    from .snapshot import snapshot_id

    original = copy.deepcopy(dict(data))
    meta = original.get("meta") or {}
    stated = parse(meta.get("schema_version"))
    if stated is None:
        raise StorageError(
            f"Card {meta.get('card_id')} states no valid schema version; nothing to migrate from."
        )
    current = parse(CARD_SCHEMA_VERSION)
    if stated > current:
        raise StorageError(
            f"Card {meta.get('card_id')} has schema {meta['schema_version']}, newer than {CARD_SCHEMA_VERSION}; it cannot be migrated backwards."
        )
    records: List[Dict[str, Any]] = []
    work = copy.deepcopy(original)
    version = stated
    while not same_line(version, current):
        nxt = (
            (version[0], version[1] + 1, 0)
            if version[0] == 0
            else (version[0] + 1, 0, 0)
        )
        step = STEPS.get((_line(version), _line(nxt)))
        if step is None:
            raise StorageError(
                f"No migration from card schema line {_line(version)} to {_line(nxt)} "
                f"(card {meta.get('card_id')}); see uibcdf/sabueso#51."
            )
        work, notes = step(work)
        work.setdefault("meta", {})["schema_version"] = f"{nxt[0]}.{nxt[1]}.{nxt[2]}"
        records.append(
            {
                "from": f"{version[0]}.{version[1]}.{version[2]}",
                "to": work["meta"]["schema_version"],
                "step": "between_lines",
                **notes,
            }
        )
        version = nxt
    from_version = f"{version[0]}.{version[1]}.{version[2]}"
    if version != current:
        gaps = within_line_gaps(work, from_version, CARD_SCHEMA_VERSION)
        records.append(
            {
                "from": from_version,
                "to": CARD_SCHEMA_VERSION,
                "step": "within_line",
                "converted": [],
                "gaps": gaps,
            }
        )
    work["meta"]["schema_version"] = CARD_SCHEMA_VERSION
    stamp = {
        "rule": MIGRATION_RULE,
        "at": _now(),
        "original_schema": meta.get("schema_version"),
        "original_snapshot": snapshot_id(original),
        "steps": records,
    }
    work.setdefault("quality", {}).setdefault("migration", []).append(stamp)
    work.pop("quantities", None)
    work["quantities"] = seal(work)
    migrated = Card.from_dict(work)
    if store is not None:
        if same_line(stated, current):
            store.save(
                Card.from_dict(original),
                note=f"schema {meta.get('schema_version')}, before migration",
            )
        store.save(migrated, note=f"migrated to schema {CARD_SCHEMA_VERSION}")
    return migrated


def rebuild_options(card: Any) -> Dict[str, Any]:
    """The enrichment options a card records it was built with, to build it again."""
    options: Dict[str, Any] = {}
    structures = []
    for e in card.quality.get("enrichments") or []:
        source, kind = e.get("source"), e.get("data")
        if source == "RCSB PDB" and e.get("structure"):
            structures.append(e["structure"])
        elif source == "ChEMBL" and not kind:
            options["chembl"] = {"limit": e["limit"]} if e.get("limit") else {}
        elif source == "PDBe-KB" and kind == "ligand_sites":
            options["ligand_sites"] = True
        elif source == "PDBe-KB" and kind == "interface_residues":
            options["interfaces"] = True
        elif source == "InterPro":
            options["family_sites"] = True
        elif source == "STRING":
            options["string"] = {
                k: e[k] for k in ("required_score", "limit") if e.get(k) is not None
            }
        elif source == "AlphaFold DB":
            options["predicted_structures"] = True
        elif source == "NCBI Taxonomy":
            options["taxonomy"] = True
        elif source == "BindingDB":
            options["bindingdb"] = {}
        elif source == "PubChem BioAssay":
            options["pubchem_bioassay"] = True
    if structures:
        options["structures"] = sorted(set(structures))
    return options


def refresh_card(
    card: Any, curations: Any = None, store: Any = None, **options: Any
) -> Tuple[Any, Any]:
    """Build the card again from its sources; see the module docstring.

    ``options`` add to, or override, the options the card records (clients included).
    Returns ``(refreshed card, resolution)``.
    """
    import sabueso

    if not card.id:
        raise StorageError("A card without meta.card_id cannot be refreshed.")
    anchor = card.id.split(":", 2)[2]
    given = {**rebuild_options(card), **options}
    refreshed, resolution = sabueso.resolve(anchor, curations=curations, **given)
    if refreshed is None:
        raise StorageError(f"Refreshing {card.id} failed: {resolution.status}.")
    history = copy.deepcopy(card.quality.get("migration") or [])
    open_gaps = [
        g
        for record in history
        for step in record.get("steps", [])
        for g in step.get("gaps", [])
    ]
    data = refreshed.to_dict()
    completed = sorted({g["path"] for g in open_gaps if _has(data, g["path"])})
    record = {
        "rule": MIGRATION_RULE,
        "at": _now(),
        "refresh_of": card.pinned_ref(),
        "options": sorted(
            k for k in given if not k.endswith("_client") and k != "resolver"
        ),
        "completed": completed,
        "not_stated": sorted(
            {g["path"] for g in open_gaps if g["kind"] == "missing"} - set(completed)
        ),
    }
    refreshed.quality["migration"] = history + [record]
    if store is not None:
        store.save(refreshed, note="refreshed from the sources")
    return refreshed, resolution
