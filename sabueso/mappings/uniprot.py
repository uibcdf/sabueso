"""UniProt → ProteinCard mappings (minimal)."""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.source_assertion_store import make_source_assertion

from .base import get_in

# Free-text comment types → canonical field paths.
_TEXT_COMMENTS = {
    "FUNCTION": "annotations.function",
    "PATHWAY": "annotations.pathway",
    "SUBUNIT": "annotations.subunit",
    "TISSUE SPECIFICITY": "annotations.tissue_specificity",
    "PTM": "annotations.ptm",
    "POLYMORPHISM": "annotations.polymorphism",
}

# Positional feature types → canonical field paths.
_FEATURES = {
    "Binding site": "features_positional.binding_site",
    "Active site": "features_positional.active_site",
    "Modified residue": "features_positional.modified_residue",
    "Glycosylation": "features_positional.glycosylation",
    "Disulfide bond": "features_positional.disulfide_bond",
}


def _eco(evidences: List[Dict[str, Any]] | None) -> List[Dict[str, str]]:
    """UniProt evidence qualifiers as ECO codes with their cited source, if any."""
    out: List[Dict[str, str]] = []
    for ev in evidences or []:
        code = ev.get("evidenceCode")
        if not code:
            continue
        item = {"code": code}
        if ev.get("source"):
            item["source"] = ev["source"]
        if ev.get("id"):
            item["id"] = ev["id"]
        out.append(item)
    return out


def _reaction(reaction: Dict[str, Any], molecule: str | None) -> Dict[str, Any]:
    rhea = [
        x.get("id")
        for x in reaction.get("reactionCrossReferences", []) or []
        if x.get("database") == "Rhea"
    ]
    item = {
        "reaction": reaction.get("name"),
        "ec_number": reaction.get("ecNumber"),
        "rhea_id": rhea[0] if rhea else None,
    }
    if molecule:
        item["molecule"] = molecule  # isoform/chain the comment is restricted to
    return item


def _subcellular_location(
    entry: Dict[str, Any], molecule: str | None
) -> Dict[str, Any] | None:
    location = get_in(entry, ["location", "value"])
    if not location:
        return None
    item: Dict[str, Any] = {"location": location}
    for key in ("topology", "orientation"):
        value = get_in(entry, [key, "value"])
        if value:
            item[key] = value
    if molecule:
        item["molecule"] = molecule  # isoform/chain the comment is restricted to
    return item


def map_protein(uniprot_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """Map UniProt payload data into canonical Sabueso structures.

    Returns a dictionary with canonical mappings, including:
    - ``fields``: ``field_path -> value``
    - ``features``: ``feature_field_path -> list[feature]``
    - ``source_assertions`` and ``field_source_assertions`` links for provenance

    UniProt evidence qualifiers are kept on each SourceAssertion as
    ``source_metadata["eco"]`` (ECO code plus cited source), never as project Evidence.
    """
    fields: Dict[str, Any] = {}
    features: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

    primary = uniprot_json.get("primaryAccession")
    record_id = primary or ""

    def assert_value(
        fp: str, value: Any, metadata: Dict[str, Any] | None = None
    ) -> None:
        assertion = make_source_assertion(fp, value, "UniProt", record_id, retrieved_at)
        if metadata:
            assertion["source_metadata"] = metadata
        source_assertions.append(assertion)
        field_source_assertions.setdefault(fp, []).append(assertion["id"])

    def assert_list(fp: str, items: List[tuple], target: Dict[str, Any]) -> None:
        """Record a list-valued field; ``items`` holds ``(value, eco)`` pairs."""
        if not items:
            return
        target[fp] = [value for value, _ in items]
        for value, eco in items:
            assert_value(fp, value, {"eco": eco} if eco else None)

    # identifiers and names
    if primary:
        fields["identifiers.uniprot"] = primary
        assert_value("identifiers.uniprot", primary)
    name = get_in(
        uniprot_json, ["proteinDescription", "recommendedName", "fullName", "value"]
    )
    if name:
        fields["names.canonical_name"] = name
        assert_value("names.canonical_name", name)

    # comments
    comments = uniprot_json.get("comments", []) or []
    text_items: Dict[str, List[tuple]] = {fp: [] for fp in _TEXT_COMMENTS.values()}
    reactions: List[tuple] = []
    locations: List[tuple] = []
    for c in comments:
        ctype = c.get("commentType")
        if ctype in _TEXT_COMMENTS:
            for t in c.get("texts", []) or []:
                if t.get("value"):
                    text_items[_TEXT_COMMENTS[ctype]].append(
                        (t["value"], _eco(t.get("evidences")))
                    )
        elif ctype == "CATALYTIC ACTIVITY" and c.get("reaction"):
            reactions.append(
                (
                    _reaction(c["reaction"], c.get("molecule")),
                    _eco(c["reaction"].get("evidences")),
                )
            )
        elif ctype == "SUBCELLULAR LOCATION":
            for entry in c.get("subcellularLocations", []) or []:
                item = _subcellular_location(entry, c.get("molecule"))
                if item:
                    locations.append(
                        (item, _eco(get_in(entry, ["location", "evidences"])))
                    )

    assert_list("annotations.function", text_items["annotations.function"], fields)
    assert_list("annotations.catalytic_activity", reactions, fields)
    assert_list("annotations.pathway", text_items["annotations.pathway"], fields)
    assert_list("annotations.subunit", text_items["annotations.subunit"], fields)
    assert_list("annotations.subcellular_location", locations, fields)
    for fp in (
        "annotations.tissue_specificity",
        "annotations.ptm",
        "annotations.polymorphism",
    ):
        assert_list(fp, text_items[fp], fields)

    # organism
    org_name = get_in(uniprot_json, ["organism", "scientificName"])
    if org_name:
        fields["annotations.organism"] = org_name
        assert_value("annotations.organism", org_name)

    # sequence
    sequence = uniprot_json.get("sequence", {}) or {}
    if sequence.get("value"):
        seq_version = get_in(uniprot_json, ["entryAudit", "sequenceVersion"])
        fields["sequence.primary"] = sequence["value"]
        assert_value(
            "sequence.primary",
            sequence["value"],
            {"sequence_version": seq_version} if seq_version is not None else None,
        )
        if sequence.get("length") is not None:
            fields["sequence.length"] = sequence["length"]
            assert_value("sequence.length", sequence["length"])
        if sequence.get("molWeight") is not None:
            fields["sequence.molecular_weight"] = sequence["molWeight"]
            assert_value(
                "sequence.molecular_weight", sequence["molWeight"], {"unit": "Da"}
            )
        checksums = {k: sequence[k] for k in ("crc64", "md5") if sequence.get(k)}
        if checksums:
            fields["sequence.checksums"] = checksums
            assert_value("sequence.checksums", checksums)

    # positional features
    feature_items: Dict[str, List[tuple]] = {fp: [] for fp in _FEATURES.values()}
    for f in uniprot_json.get("features", []) or []:
        fp = _FEATURES.get(f.get("type"))
        if not fp:
            continue
        loc = f.get("location", {}) or {}
        start = get_in(loc, ["start", "value"])
        end = get_in(loc, ["end", "value"])
        if start is None:
            continue
        item = {
            "location": {
                "kind": "sequence",
                "sequence": {
                    "sequence_id": f"UniProt:{primary}" if primary else None,
                    "start": start,
                    "end": end if end is not None else start,
                    "indexing": "1-based",
                },
            },
            "description": f.get("description") or "",
        }
        feature_items[fp].append((item, _eco(f.get("evidences"))))
    for fp in _FEATURES.values():
        assert_list(fp, feature_items[fp], features)

    return {
        "fields": fields,
        "features": features,
        "source_assertions": source_assertions,
        "field_source_assertions": field_source_assertions,
    }
