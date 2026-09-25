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
- ``ligand_deck`` builds the deck of the molecules a protein card refers to; cross it with
  the protein through ``Card.ligands(deck)``.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from smonitor import signal

from sabueso._private.argdigest import arg_digest
from sabueso._private.smonitor.outcomes import report_outcomes, report_unanchored
from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card, make_card_id
from sabueso.core.deck import Deck
from sabueso.core.errors import ConnectorError, RecordNotFoundError, SchemaError
from sabueso.core.merge import merge_mapping_results
from sabueso.mappings.molecule_identity import (
    anchor_ref,
    is_standard_inchikey,
    linked_records,
    map_ccd_identity,
    map_chembl_identity,
    map_pubchem_identity,
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
    pubchem: Dict[str, Any] | None = None,
) -> Tuple[Dict[str, Card], List[Dict[str, Any]]]:
    """One SmallMoleculeCard per standard InChIKey, from retrieved records.

    ``chembl`` is a ``molecules`` response, ``ccd`` a ``components`` response,
    ``unichem`` a sequence of ``compound`` responses and ``pubchem``
    ``{"retrieved_at", "compounds": {cid: record}}``. Returns ``(cards, unanchored)``:
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
    for cid, record in sorted(((pubchem or {}).get("compounds") or {}).items()):
        mapping, key = map_pubchem_identity(record, pubchem.get("retrieved_at", ""))
        if key:
            groups.setdefault(key, []).append(mapping)
        else:
            unanchored.append(
                {"ref": f"pubchem:{cid}", "reason": "no_standard_inchikey"}
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


def single_molecule_card(**records: Any) -> Card:
    """The one card of a molecule built from records of one or more sources.

    Raises ``SchemaError`` when a record has no standard InChIKey, or when the records
    describe more than one molecule: a small molecule card is never built without its
    identity anchor, and never from records that are not the same structure.
    """
    cards, unanchored = build_molecule_cards(**records)
    if unanchored:
        raise SchemaError(
            f"{[u['ref'] for u in unanchored]} have no standard InChIKey: a small "
            "molecule card needs one as its identity anchor"
        )
    if len(cards) != 1:
        raise SchemaError(
            f"The records describe {len(cards)} molecules ({sorted(cards)}), not one"
        )
    return next(iter(cards.values()))


def _parse(identifier: str) -> Tuple[str | None, str]:
    value = identifier.strip()
    namespace, _, record = value.partition(":")
    if record and namespace.lower() == "pubchem":
        # A PubChem CID only with its prefix: a bare number could be anything.
        return (
            ("pubchem", record.strip()) if record.strip().isdigit() else (None, value)
        )
    if record and namespace.lower() in ("chembl", "pdb.ligand", "inchikey"):
        namespace = namespace.lower()
        return namespace, record if namespace == "inchikey" else record.upper()
    if value.upper().startswith("CHEMBL"):
        return "chembl", value.upper()
    if is_standard_inchikey(value):
        return "inchikey", value
    return None, value


def _pubchem_client(pubchem_client):
    if pubchem_client is None:
        from sabueso.tools.db.pubchem import OnlinePubChemClient

        pubchem_client = OnlinePubChemClient()
    return pubchem_client


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


@signal(tags=["api", "small_molecule"])
@arg_digest()
def resolve_molecule_card(
    identifier: str,
    chembl_client: Any | None = None,
    ccd_client: Any | None = None,
    unichem: bool = True,
    unichem_client: Any | None = None,
    pubchem: bool = False,
    pubchem_client: Any | None = None,
    skip_digestion: bool = False,
) -> Tuple[Card | None, EntityResolution]:
    """Resolve a small-molecule identifier and build the card of its molecule.

    ``identifier`` is ``chembl:<id>`` (or a bare ChEMBL id), ``pdb.ligand:<code>``,
    ``pubchem:<cid>`` or ``inchikey:<key>`` (or a bare standard InChIKey). With
    ``pubchem=True``, the PubChem compounds UniChem links are retrieved too; a
    ``pubchem:`` identifier always brings its own compound.

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
    chembl = ccd = compounds = None
    if namespace == "pubchem" or pubchem:
        pubchem_client = _pubchem_client(pubchem_client)
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
        if namespace == "pubchem":
            try:
                response = pubchem_client.compound(record)
            except RecordNotFoundError:
                return outcome("not_found", "record_not_found")
            decision["sources"].append({"name": "PubChem", "records": [record]})
            compounds = {
                "retrieved_at": response["retrieved_at"],
                "compounds": {record: response["record"]},
            }
    except ConnectorError as exc:
        decision["detail"] = str(exc)
        return outcome("error", "source_error")

    if key is None:
        cards, unanchored = build_molecule_cards(chembl, ccd, pubchem=compounds)
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
            if pubchem:
                compounds = _expand_pubchem(
                    pubchem_client, compounds, linked, enrichments
                )

    cards, unanchored = build_molecule_cards(
        chembl, ccd, unichem_responses, pubchem=compounds
    )
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
        report_outcomes(enrichments, subject=molecule_ref(key))
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


def _expand_pubchem(pubchem_client, pubchem, linked, enrichments):
    """Retrieve the PubChem compounds UniChem links (``pubchem=True``)."""
    have = set(((pubchem or {}).get("compounds") or {}).keys())
    wanted = [cid for cid in linked.get("pubchem", []) if cid not in have]
    if not wanted:
        return pubchem
    pubchem = pubchem or {"retrieved_at": None, "compounds": {}}
    found, missing = [], []
    for cid in wanted:
        try:
            response = pubchem_client.compound(cid)
        except RecordNotFoundError:
            missing.append(cid)
            continue
        except ConnectorError as exc:
            enrichments.append(
                {"source": "PubChem", "status": "error", "detail": str(exc)}
            )
            return pubchem
        pubchem["compounds"][cid] = response["record"]
        pubchem["retrieved_at"] = pubchem["retrieved_at"] or response["retrieved_at"]
        found.append(cid)
    enrichments.append(
        {
            "source": "PubChem",
            "status": "added" if found else "not_found",
            "records": sorted(found),
            "missing": missing,
        }
    )
    return pubchem


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


STRUCTURE_LIGAND_MODES = ("of_interest", "all")


def _parent_id(rel: Dict[str, Any]) -> str:
    ref = rel["qualifiers"].get("parent_molecule") or rel["object_ref"]
    return ref.split(":", 1)[1]


def _protein_molecule_records(protein_card: Card, structure_ligands: str | None):
    """ChEMBL parent ids, PDB component codes, and the structure ligands left out."""
    if structure_ligands not in (*STRUCTURE_LIGAND_MODES, None, False):
        raise ValueError(
            f"structure_ligands must be one of {STRUCTURE_LIGAND_MODES} or None"
        )
    chembl_ids = sorted(
        {_parent_id(rel) for rel in protein_card.relationships("has_bioactivity")}
    )
    seen: Dict[str, Dict[str, Any]] = {}
    for rel in protein_card.relationships("has_structure"):
        for ligand in rel.get("qualifiers", {}).get("ligands") or []:
            if not ligand.get("comp_id"):
                continue
            entry = seen.setdefault(
                ligand["comp_id"], {"structures": set(), "flags": set()}
            )
            entry["structures"].add(rel["object_ref"])
            entry["flags"].add(ligand.get("subject_of_investigation"))
    # Ligands PDBe-KB reports in structures the card has not fetched: the PDB flag is
    # unknown for them unless a fetched structure states it.
    for rel in protein_card.relationships("has_ligand_site"):
        code = rel["object_ref"].split(":", 1)[1]
        if code not in seen:
            seen[code] = {
                "structures": set(rel["qualifiers"].get("structures") or []),
                "flags": {None},
            }
    if not structure_ligands:
        return chembl_ids, [], []
    codes, excluded = [], []
    for code, entry in sorted(seen.items()):
        if structure_ligands == "all" or True in entry["flags"]:
            codes.append(code)
            continue
        excluded.append(
            {
                "ref": f"pdb.ligand:{code}",
                "structures": sorted(entry["structures"]),
                "reason": "not_subject_of_investigation"
                if False in entry["flags"]
                else "subject_of_investigation_unknown",
            }
        )
    return chembl_ids, codes, excluded


def _notes(structure_ligands: str | None) -> List[str]:
    if structure_ligands == "of_interest":
        return [
            "Structure ligands: only those the PDB declares subject of investigation. "
            "A ligand left out is not declared of interest, which does not assert that "
            "it is irrelevant (uibcdf/sabueso#25, item 3)."
        ]
    if structure_ligands == "all":
        return [
            "Structure ligands: all, including those not declared subject of "
            "investigation (often crystallisation additives or ions)."
        ]
    return []


@signal(tags=["api", "small_molecule", "deck"])
@arg_digest()
def ligand_deck(
    protein_card: Card,
    structure_ligands: str | None = "of_interest",
    chembl_client: Any | None = None,
    ccd_client: Any | None = None,
    unichem: bool = False,
    unichem_client: Any | None = None,
    skip_digestion: bool = False,
) -> Deck:
    """Deck of the small molecules a protein card refers to, anchored at the InChIKey.

    Molecules come from the card's ``has_bioactivity`` relationships (ChEMBL parent
    molecules) and from the ligands of its structures (PDB chemical components):

    - ``"of_interest"`` (default): only ligands the PDB declares subject of investigation
      in at least one structure (by the depositor, or by RCSB for older entries). The
      others, mostly additives and ions, are listed in
      ``deck.meta["excluded_structure_ligands"]`` with the reason;
    - ``"all"``: every structure ligand;
    - ``None``: no structure ligands.

    Every source outcome and every record without a standard InChIKey are recorded in
    ``deck.meta``. UniChem is off by default because it takes one request per molecule.
    """
    chembl_ids, codes, excluded_ligands = _protein_molecule_records(
        protein_card, structure_ligands
    )
    chembl_client, ccd_client, unichem_client = _clients(
        chembl_client, ccd_client, unichem_client if unichem else None
    )
    sources: List[Dict[str, Any]] = []
    chembl = ccd = None
    for name, call, requested, field in (
        ("ChEMBL", chembl_client.molecules, chembl_ids, "molecules"),
        ("PDB CCD", ccd_client.components, codes, "components"),
    ):
        if not requested:
            continue
        try:
            response = call(requested)
        except ConnectorError as exc:
            sources.append(
                {"source": name, "status": "error", "requested": len(requested),
                 "detail": str(exc)}
            )  # fmt: skip
            continue
        sources.append(
            {
                "source": name,
                "status": "added",
                "requested": len(requested),
                "found": len(response.get(field) or {}),
                "missing": response.get("missing", []),
            }
        )
        if name == "ChEMBL":
            chembl = response
        else:
            ccd = response

    cards, unanchored = build_molecule_cards(chembl, ccd)
    if unichem and cards:
        responses, not_found, errors = [], [], []
        for key in cards:
            try:
                responses.append(unichem_client.compound(key))
            except RecordNotFoundError:
                not_found.append(key)
            except ConnectorError as exc:
                errors.append({"inchikey": key, "detail": str(exc)})
        sources.append(
            {
                "source": "UniChem",
                "status": "added" if responses else "not_found",
                "found": len(responses),
                "not_found": not_found,
                "errors": errors,
            }
        )
        cards, unanchored = build_molecule_cards(chembl, ccd, responses)

    report_outcomes(sources, subject=protein_card.id or "the protein card")
    report_unanchored(unanchored, subject=protein_card.id or "the protein card")
    return Deck(
        [cards[key] for key in sorted(cards)],
        meta={
            # Why each card is here (#58): a ligand of this protein, anchored by rule.
            "membership": {
                cards[key].id: {"ligand_of": protein_card.id, "rule": IDENTITY_RULE}
                for key in sorted(cards)
            },
            "kind": "protein_ligands",
            "protein": protein_card.id,
            "identity_rule": IDENTITY_RULE,
            "sources": sources,
            "unanchored": unanchored,
            "structure_ligands": structure_ligands or None,
            "excluded_structure_ligands": excluded_ligands,
            "notes": _notes(structure_ligands),
        },
    )
