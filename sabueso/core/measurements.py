"""One measurement stated by several sources (uibcdf/sabueso#66, rule
``measurement_identity@1``; design in devguide/archive/measurement_identity.md).

Every source record stays a ``has_bioactivity`` relationship with its own context. This
module groups the records that state one measurement, so that views count
measurements, not records, and a copy never reads as a confirmation:

1. **Provenance.** A record that states it copies another (``copy_of``: the source and
   the original's activity id, or its assay id) is grouped with it. This is exact. A
   copy whose original is not on the card is listed as a pointer to follow (#68).
2. **Statement.** Records of different sources are grouped when they share:

   - the publication (PubMed id or DOI);
   - the molecule, through the card's glossary of entities (identities stated by
     sources, e.g. UniChem);
   - the measurement type and relation;
   - a value that agrees at the coarser of the two stated precisions, in the
     normalized unit.

   This is a derived judgement, recomputed whenever the card changes.
3. **Ambiguity.** A record with several candidates in another source is not grouped,
   and neither is a group that would hold two records of one source. Both are
   reported; nothing is chosen silently.
4. **Review.** Records of two sources with the same publication, type and exact value
   but different molecules are not grouped. They are listed with a reason:
   ``stereo_differs`` (the same connectivity, the first InChIKey block, with another
   stereochemistry), ``molecule_differs``, or ``molecule_unresolved`` (a molecule one
   source cannot anchor). The sources may attribute one measurement to different
   compounds. Censored values (``>``, ``<``) are not listed, because many compounds of
   one paper share them.

Records of one source are never grouped with each other: a source that states a value
twice (ChEMBL's Kd and ED50 of the same experiment) keeps both, as it states them.
"""

from __future__ import annotations

import hashlib
import re
from itertools import combinations
from typing import Any, Dict, List, Tuple

MEASUREMENT_RULE = "measurement_identity@1"
_NUMBER = re.compile(r"\s*[-+]?(\d*)(?:\.(\d*))?(?:[eE]([-+]?\d+))?\s*$")


def record_source(q: Dict[str, Any]) -> str:
    if q.get("source"):
        return q["source"]
    return "curation" if (q.get("assay") or {}).get("curated") else "ChEMBL"


def _publications(q: Dict[str, Any]) -> set:
    doc = q.get("document") or {}
    out = set()
    if doc.get("pubmed"):
        out.add(("pubmed", str(doc["pubmed"])))
    if doc.get("doi"):
        out.add(("doi", str(doc["doi"]).lower()))
    return out


def half_unit(m: Dict[str, Any]) -> float | None:
    """Half a unit of the last stated digit, in the measurement's normalized unit."""
    from .quantities import normalized_measurement

    value = m.get("value")
    if value is None:
        return None
    text = m.get("stated_value") or repr(float(value))
    match = _NUMBER.fullmatch(str(text))
    if not match:
        return None
    decimals = len(match.group(2) or "")
    exponent = int(match.group(3) or 0)
    step = 10.0 ** (exponent - decimals)
    scale = normalized_measurement(1.0, m.get("units"))
    return None if scale is None else 0.5 * step * float(scale["value"])


def _agree(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    na, nb = a.get("normalized") or {}, b.get("normalized") or {}
    if not na or not nb or na.get("unit") != nb.get("unit"):
        return False
    ha, hb = half_unit(a), half_unit(b)
    tolerance = max(h for h in (ha, hb, 0.0) if h is not None)
    return abs(float(na["value"]) - float(nb["value"])) <= tolerance + 1e-9


def _blocks(keys: set) -> set:
    """First InChIKey blocks (connectivity) of the anchored molecules."""
    return {k[9:23] for k in keys if k.startswith("inchikey:")}


def _relations_match(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    """Equal relations; a declared copy that states none (PubChem's table) matches any."""
    if a["relation"] == b["relation"]:
        return True
    return any(i["copy_of"] and i["relation"] is None for i in (a, b))


def _molecules(card: Any) -> Dict[str, str]:
    """Record → entity key, from the card's glossary."""
    from .entities import build_entities

    out = {}
    for key, entry in build_entities(card).items():
        for record in entry.get("records") or []:
            out[record] = key
        out[key] = key
    return out


def measurement_groups(card: Any) -> Dict[str, Any]:
    """``{"rule", "groups", "ambiguous", "unresolved_copies", "review", "group_of"}``;
    see the module docstring. ``unresolved_copies`` are declared copies whose original
    is not on the card: pointers to follow (#68).

    ``group_of`` maps every relationship id to its group id; a record stated by one
    source only is its own group.
    """
    from .relationship_store import make_derivation

    rels = card.relationships("has_bioactivity")
    molecule = _molecules(card)

    def molecules_of(rel: Dict[str, Any]) -> set:
        q = rel.get("qualifiers") or {}
        refs = {rel["object_ref"], q.get("parent_molecule"), q.get("molecule_ref")}
        return {molecule.get(r, r) for r in refs if r}

    info = {}
    for rel in rels:
        q = rel.get("qualifiers") or {}
        m = q.get("measurement") or {}
        info[rel["id"]] = {
            "source": record_source(q),
            "publications": _publications(q),
            "molecules": molecules_of(rel),
            "type": m.get("type"),
            # A declared copy that states no relation keeps None: it imposes nothing.
            "relation": m.get("relation") or (None if q.get("copy_of") else "="),
            "measurement": m,
            "activity_id": q.get("activity_id"),
            "assay": (q.get("assay") or {}).get("id"),
            "copy_of": q.get("copy_of"),
        }

    edges: List[Tuple[str, str, str]] = []
    ambiguous: List[Dict[str, Any]] = []
    unresolved_copies: List[Dict[str, Any]] = []
    review: List[Dict[str, Any]] = []
    # 1. Provenance: exact. A copy names its original record, or the original's assay
    #    (PubChem names the ChEMBL assay it copied); within that assay, the molecule and
    #    the type select the record, and the value when several remain.
    by_source_activity = {
        (i["source"], i["activity_id"]): rid for rid, i in info.items()
    }
    for rid, i in info.items():
        copy = i["copy_of"] or {}
        if not copy:
            continue
        original = by_source_activity.get((copy.get("source"), copy.get("activity_id")))
        if original and original != rid:
            edges.append((rid, original, "provenance"))
            continue
        if not copy.get("assay"):
            continue
        in_assay = [
            o
            for o, j in info.items()
            if j["source"] == copy.get("source")
            and j["assay"] == copy["assay"]
            and (not i["type"] or not j["type"] or i["type"] == j["type"])
        ]
        found = [o for o in in_assay if info[o]["molecules"] & i["molecules"]]
        stereo = False
        if not found:
            # The copy's compound can be standardised differently (stereochemistry or
            # salt lost): the same connectivity, within the named assay.
            blocks = _blocks(i["molecules"])
            found = [o for o in in_assay if _blocks(info[o]["molecules"]) & blocks]
            stereo = bool(found)
        if len(found) > 1:
            found = [
                o for o in found if _agree(i["measurement"], info[o]["measurement"])
            ]
        if len(found) == 1:
            edges.append((rid, found[0], "provenance"))
            if stereo:
                review.append(
                    {
                        "records": sorted([rid, found[0]]),
                        "sources": sorted({i["source"], info[found[0]]["source"]}),
                        "reason": "stereo_differs",
                        "molecules": sorted(
                            i["molecules"] | info[found[0]]["molecules"]
                        ),
                        "note": "declared copy, grouped by provenance",
                    }
                )
        elif found:
            ambiguous.append(
                {
                    "record": rid,
                    "source": copy.get("source"),
                    "candidates": sorted(found),
                }
            )
        else:
            unresolved_copies.append(
                {
                    "record": rid,
                    "copy_of": copy,
                    "reason": "molecule_not_found_in_assay"
                    if in_assay
                    else "original_not_on_card",
                }
            )
    copied = {a for a, _, kind in edges if kind == "provenance"}
    # 2. Statement: candidates bucketed by publication and type.
    buckets: Dict[tuple, List[str]] = {}
    for rid, i in info.items():
        if rid in copied:
            continue  # already joined to its original by provenance
        for pub in i["publications"]:
            buckets.setdefault((pub, i["type"]), []).append(rid)
    candidates: Dict[tuple, set] = {}
    for members in buckets.values():
        for a, b in combinations(sorted(set(members)), 2):
            ia, ib = info[a], info[b]
            if ia["source"] == ib["source"]:
                continue
            if not _relations_match(ia, ib):
                continue
            if not _agree(ia["measurement"], ib["measurement"]):
                continue
            if ia["molecules"] & ib["molecules"]:
                candidates.setdefault((a, ib["source"]), set()).add(b)
                candidates.setdefault((b, ia["source"]), set()).add(a)
            elif ia["relation"] == "=":
                # Same paper, type and exact value, different or unknown molecule: the
                # sources may attribute one measurement to different compounds. Never
                # grouped; reported for a reader.
                keys = [
                    {k for k in i["molecules"] if k.startswith("inchikey:")}
                    for i in (ia, ib)
                ]
                if not all(keys):
                    reason = "molecule_unresolved"
                elif {k[9:23] for k in keys[0]} & {k[9:23] for k in keys[1]}:
                    # Same connectivity (first InChIKey block), other stereochemistry.
                    reason = "stereo_differs"
                else:
                    reason = "molecule_differs"
                review.append(
                    {
                        "records": sorted([a, b]),
                        "sources": sorted({ia["source"], ib["source"]}),
                        "reason": reason,
                        "molecules": sorted(ia["molecules"] | ib["molecules"]),
                    }
                )
    for (rid, other_source), found in sorted(candidates.items()):
        if len(found) > 1:
            ambiguous.append(
                {"record": rid, "source": other_source, "candidates": sorted(found)}
            )
    blocked = {(a["record"], c) for a in ambiguous for c in a["candidates"]}
    for (rid, _), found in sorted(candidates.items()):
        for other in found:
            if (
                rid < other
                and (rid, other) not in blocked
                and (other, rid) not in blocked
            ):
                edges.append((rid, other, "statement"))

    parent = {rid: rid for rid in info}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    basis: Dict[frozenset, set] = {}
    for a, b, kind in edges:
        parent[find(a)] = find(b)
    members: Dict[str, List[str]] = {}
    for rid in info:
        members.setdefault(find(rid), []).append(rid)
    for a, b, kind in edges:
        basis.setdefault(find(a), set()).add(kind)

    groups, group_of = [], {}
    for root, rids in members.items():
        sources = [info[r]["source"] for r in rids]
        if len(rids) > 1 and len(set(sources)) < len(sources):
            # Two records of one source would be merged: not the same measurement.
            ambiguous.append(
                {"records": sorted(rids), "reason": "same_source_in_group"}
            )
            for r in rids:
                group_of[r] = r
            continue
        if len(rids) == 1:
            group_of[rids[0]] = rids[0]
            continue
        gid = "MG_" + hashlib.sha256("|".join(sorted(rids)).encode()).hexdigest()[:16]
        for r in rids:
            group_of[r] = gid
        groups.append(
            {
                "id": gid,
                "records": sorted(rids),
                "sources": sorted(set(sources)),
                "basis": sorted(basis.get(root, set())),
            }
        )
    return {
        "rule": make_derivation(
            MEASUREMENT_RULE,
            inputs=["has_bioactivity"],
            parameters={
                "provenance": "copy_of (source, activity_id)",
                "statement": [
                    "publication",
                    "molecule (glossary)",
                    "type",
                    "relation",
                    "value at the coarser stated precision",
                ],
                "same_source": "never grouped",
            },
        ),
        "groups": sorted(groups, key=lambda g: g["id"]),
        "ambiguous": ambiguous,
        # A copy grouped afterwards by statement identity is resolved after all.
        "unresolved_copies": [
            u for u in unresolved_copies if group_of.get(u["record"]) == u["record"]
        ],
        "review": sorted(
            {tuple(r["records"]): r for r in review}.values(),
            key=lambda r: r["records"],
        ),
        "group_of": group_of,
    }
