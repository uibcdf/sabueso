"""SmallMoleculeCards anchored at the standard InChIKey (uibcdf/sabueso#25).

A small molecule is identified by its standard InChIKey: its card id is
``sabueso:small_molecule:inchikey:<key>``. The ChEMBL molecules and PDB chemical
components with that key, and the records UniChem lists for it, are linked to the anchor
with ``same_as`` relationships, each supported by the source that states it
(``sabueso.mappings.molecule_identity``). Only assertions about those records feed the
card's fields (``entity_subjects`` guard).

- ``build_molecule_cards`` builds the cards from records already retrieved. It is shared by
  single-molecule resolution and by the ligand deck of a protein card.
- ``resolve_molecule_card`` resolves one identifier (``chembl:<id>``,
  ``pdb.ligand:<code>`` or ``inchikey:<key>``) and builds the card of its molecule.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card, make_card_id
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.core.merge import merge_mapping_results
from sabueso.mappings.molecule_identity import (
    anchor_ref,
    is_standard_inchikey,
    linked_records,
    map_ccd_identity,
    map_chembl_identity,
    map_unichem_identity,
)
from sabueso.resolver.entity_resolver import EntityResolution

IDENTITY_RULE = "standard_inchikey_anchor"


def molecule_ref(inchikey: str) -> str:
    """Card id of the small molecule with this standard InChIKey."""
    return make_card_id("small_molecule", anchor_ref(inchikey))


def build_molecule_cards(
    chembl: Dict[str, Any] | None = None,
    ccd: Dict[str, Any] | None = None,
    unichem: Iterable[Dict[str, Any]] = (),
) -> Tuple[Dict[str, Card], List[Dict[str, Any]]]:
    """One SmallMoleculeCard per standard InChIKey, from retrieved records.

    ``chembl`` is a ``molecules`` response, ``ccd`` a ``components`` response and
    ``unichem`` a sequence of ``compound`` responses. Returns ``(cards, unanchored)``:
    cards keyed by InChIKey, and the records that have no standard InChIKey.
    """
    groups: Dict[str, List[Dict[str, Any]]] = {}
    unanchored: List[Dict[str, Any]] = []
    for cid, record in sorted(((chembl or {}).get("molecules") or {}).items()):
        mapping, key = map_chembl_identity(
            record, chembl.get("retrieved_at", ""), chembl.get("version")
        )
        if key:
            groups.setdefault(key, []).append(mapping)
        else:
            unanchored.append(
                {"ref": f"chembl:{cid}", "reason": "no_standard_inchikey"}
            )
    for code, record in sorted(((ccd or {}).get("components") or {}).items()):
        mapping, key = map_ccd_identity(record, ccd.get("retrieved_at", ""))
        if key:
            groups.setdefault(key, []).append(mapping)
        else:
            unanchored.append(
                {"ref": f"pdb.ligand:{code}", "reason": "no_standard_inchikey"}
            )
    for response in unichem:
        mapping, key = map_unichem_identity(
            response["compound"], response.get("retrieved_at", "")
        )
        if key:
            groups.setdefault(key, []).append(mapping)

    cards: Dict[str, Card] = {}
    for key, mappings in sorted(groups.items()):
        merged = merge_mapping_results(mappings)
        subjects = {anchor_ref(key)} | {
            rel["subject_ref"]
            for rel in merged["relationships"]
            if rel["predicate"] == "same_as" and rel["object_ref"] == anchor_ref(key)
        }
        cards[key] = build_card_from_mapping(
            merged,
            meta={"entity_type": "small_molecule"},
            card_id=molecule_ref(key),
            entity_subjects=subjects,
        )
    return cards, unanchored


def _parse(identifier: str) -> Tuple[str | None, str]:
    value = identifier.strip()
    namespace, _, record = value.partition(":")
    if record and namespace.lower() in ("chembl", "pdb.ligand", "inchikey"):
        namespace = namespace.lower()
        return namespace, record if namespace == "inchikey" else record.upper()
    if value.upper().startswith("CHEMBL"):
        return "chembl", value.upper()
    if is_standard_inchikey(value):
        return "inchikey", value
    return None, value


def _clients(chembl_client, ccd_client, unichem_client):
    if chembl_client is None:
        from sabueso.tools.db.chembl import OnlineChEMBLClient

        chembl_client = OnlineChEMBLClient()
    if ccd_client is None:
        from sabueso.tools.db.pdb_ccd import OnlineCCDClient

        ccd_client = OnlineCCDClient()
    if unichem_client is None:
        from sabueso.tools.db.unichem import OnlineUniChemClient

        unichem_client = OnlineUniChemClient()
    return chembl_client, ccd_client, unichem_client


def resolve_molecule_card(
    identifier: str,
    chembl_client: Any | None = None,
    ccd_client: Any | None = None,
    unichem: bool = True,
    unichem_client: Any | None = None,
) -> Tuple[Card | None, EntityResolution]:
    """Resolve a small-molecule identifier and build the card of its molecule.

    The anchor InChIKey comes from the record named by ``identifier`` (or is the
    identifier itself). With ``unichem`` (default), UniChem adds the records other
    resources hold for that structure, and the ChEMBL molecules and PDB components it
    lists are retrieved too. A failure of that expansion never prevents the card; it is
    recorded in ``quality.enrichments``. ``inchikey:`` identifiers need UniChem.
    """
    namespace, record = _parse(identifier)
    decision: Dict[str, Any] = {"query": identifier, "rules": [], "sources": []}

    def outcome(status: str, rule: str) -> Tuple[None, EntityResolution]:
        decision["rules"].append(rule)
        return None, EntityResolution(status=status, decision=decision)

    if namespace is None:
        return outcome("unsupported", "unsupported_identifier")
    if namespace == "inchikey" and not is_standard_inchikey(record):
        return outcome("unsupported", "not_a_standard_inchikey")
    if namespace == "inchikey" and not unichem:
        return outcome("unsupported", "inchikey_requires_unichem")
    chembl_client, ccd_client, unichem_client = _clients(
        chembl_client, ccd_client, unichem_client
    )

    chembl_ids = [record] if namespace == "chembl" else []
    codes = [record] if namespace == "pdb.ligand" else []
    chembl = ccd = None
    key = record if namespace == "inchikey" else None
    enrichments: List[Dict[str, Any]] = []
    try:
        if chembl_ids:
            chembl = chembl_client.molecules(chembl_ids)
            decision["sources"].append({"name": "ChEMBL", "records": chembl_ids})
            if not chembl["molecules"]:
                return outcome("not_found", "record_not_found")
        if codes:
            ccd = ccd_client.components(codes)
            decision["sources"].append({"name": "PDB CCD", "records": codes})
            if not ccd["components"]:
                return outcome("not_found", "record_not_found")
    except ConnectorError as exc:
        decision["detail"] = str(exc)
        return outcome("error", "source_error")

    if key is None:
        cards, unanchored = build_molecule_cards(chembl, ccd)
        if not cards:
            return outcome("unsupported", "no_standard_inchikey")
        (key,) = cards

    unichem_responses: List[Dict[str, Any]] = []
    if unichem:
        try:
            response = unichem_client.compound(key)
        except RecordNotFoundError:
            if namespace == "inchikey":
                return outcome("not_found", "unichem_not_found")
            enrichments.append({"source": "UniChem", "status": "not_found"})
        except ConnectorError as exc:
            if namespace == "inchikey":
                decision["detail"] = str(exc)
                return outcome("error", "source_error")
            enrichments.append(
                {"source": "UniChem", "status": "error", "detail": str(exc)}
            )
        else:
            unichem_responses.append(response)
            linked = linked_records(response["compound"])
            enrichments.append(
                {
                    "source": "UniChem",
                    "status": "added",
                    "uci": response["compound"].get("uci"),
                    "linked": linked,
                }
            )
            decision["sources"].append({"name": "UniChem", "records": [key]})
            chembl, ccd = _expand(
                chembl_client, ccd_client, chembl, ccd, linked, enrichments
            )

    cards, unanchored = build_molecule_cards(chembl, ccd, unichem_responses)
    card = cards.get(key)
    if card is None:
        return outcome("not_found", "no_record_for_inchikey")
    decision["rules"].append(IDENTITY_RULE)
    decision["discrepancies"] = [
        {"ref": rel["subject_ref"], "inchikey": other}
        for other, other_card in cards.items()
        if other != key
        for rel in other_card.relationships("same_as")
    ] + unanchored
    if enrichments:
        card.quality["enrichments"] = enrichments
    resolution = EntityResolution(
        status="resolved",
        entity_ref=molecule_ref(key),
        identity_links=card.relationships("same_as"),
        decision=decision,
    )
    card.quality["entity_resolution"] = {
        "status": resolution.status,
        "entity_ref": resolution.entity_ref,
        "decision": decision,
    }
    return card, resolution


def _expand(chembl_client, ccd_client, chembl, ccd, linked, enrichments):
    """Retrieve the ChEMBL molecules and PDB components that UniChem links."""
    have_chembl = set(((chembl or {}).get("molecules") or {}).keys())
    have_codes = set(((ccd or {}).get("components") or {}).keys())
    wanted_chembl = sorted(set(linked["chembl"]) | have_chembl)
    wanted_codes = sorted(set(linked["pdb.ligand"]) | have_codes)
    for name, client_call, wanted, have in (
        ("ChEMBL", chembl_client.molecules, wanted_chembl, have_chembl),
        ("PDB CCD", ccd_client.components, wanted_codes, have_codes),
    ):
        if not wanted or set(wanted) == have:
            continue
        try:
            response = client_call(wanted)
        except ConnectorError as exc:
            enrichments.append({"source": name, "status": "error", "detail": str(exc)})
            continue
        field = "molecules" if name == "ChEMBL" else "components"
        found = response.get(field) or {}
        enrichments.append(
            {
                "source": name,
                "status": "added" if found else "not_found",
                "records": sorted(found),
                "missing": response.get("missing", []),
            }
        )
        previous = chembl if name == "ChEMBL" else ccd
        merged = {**response, field: {**((previous or {}).get(field) or {}), **found}}
        if name == "ChEMBL":
            chembl = merged
        else:
            ccd = merged
    return chembl, ccd
