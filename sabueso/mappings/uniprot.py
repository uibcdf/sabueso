"""UniProt → ProteinCard mappings (minimal)."""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.quantities import LENGTH_UNIT, quantity_node
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.core.structures import coverage

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

# Positional feature types → canonical field paths. Natural variants (observed in a
# population) and mutagenesis (an experiment the authors performed) stay apart: they are
# different kinds of statement about a position (uibcdf/sabueso#33).
_FEATURES = {
    "Binding site": "features_positional.binding_site",
    "Active site": "features_positional.active_site",
    "Modified residue": "features_positional.modified_residue",
    "Glycosylation": "features_positional.glycosylation",
    "Disulfide bond": "features_positional.disulfide_bond",
    "Natural variant": "features_positional.natural_variant",
    "Mutagenesis": "features_positional.mutagenesis",
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


def _disease(comment: Dict[str, Any]) -> Dict[str, Any] | None:
    """A UniProt DISEASE comment as stated: the disease entry, and UniProt's note on how
    this protein is involved (uibcdf/sabueso#39)."""
    disease = comment.get("disease") or {}
    if not disease.get("diseaseId"):
        return None
    item: Dict[str, Any] = {"name": disease["diseaseId"]}
    for key, source_key in (
        ("accession", "diseaseAccession"),
        ("acronym", "acronym"),
        ("description", "description"),
    ):
        if disease.get(source_key):
            item[key] = disease[source_key]
    xref = disease.get("diseaseCrossReference") or {}
    if xref.get("database") and xref.get("id"):
        item["cross_references"] = [{"database": xref["database"], "id": xref["id"]}]
    notes = [
        t["value"] for t in get_in(comment, ["note", "texts"]) or [] if t.get("value")
    ]
    if notes:
        item["note"] = " ".join(notes)
    return item


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


# Classification cross-references -> namespace of the classified_in object.
# Gene3D ids are CATH superfamilies; SUPFAM ids are SUPERFAMILY models of SCOP superfamilies.
_CLASSIFICATIONS = {
    "InterPro": "interpro",
    "Pfam": "pfam",
    "Gene3D": "cath",
    "SUPFAM": "supfam",
    "PANTHER": "panther",
    "PROSITE": "prosite",
    "CDD": "cdd",
}

_GO_ASPECTS = {
    "C": "cellular_component",
    "F": "molecular_function",
    "P": "biological_process",
}


def publication_ref(citation: Dict[str, Any]) -> str | None:
    """``pubmed:<id>``, else ``doi:<doi>``, else UniProt's own citation id."""
    xrefs = {
        x.get("database"): x.get("id")
        for x in citation.get("citationCrossReferences") or []
    }
    if xrefs.get("PubMed"):
        return f"pubmed:{xrefs['PubMed']}"
    if xrefs.get("DOI"):
        return f"doi:{xrefs['DOI']}"
    if citation.get("id"):
        return f"uniprot.citation:{citation['id']}"
    return None


def _reference_relationships(
    uniprot_json: Dict[str, Any], primary: str, retrieved_at: str
) -> tuple:
    """The publications a UniProt entry cites, as ``described_in`` relationships
    (uibcdf/sabueso#41). Qualifiers keep the publication record and what UniProt cites it
    for (``scope``, e.g. ``HOMODIMERIZATION``); the assertion keeps the reference
    verbatim. Sequence submissions are kept too, typed as such."""
    assertions: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    for reference in uniprot_json.get("references") or []:
        citation = reference.get("citation") or {}
        object_ref = publication_ref(citation)
        if object_ref is None:
            continue
        xrefs = {
            x.get("database"): x.get("id")
            for x in citation.get("citationCrossReferences") or []
        }
        assertion = make_source_assertion(
            "relationships.described_in",
            {"object_ref": object_ref, "reference": reference},
            "UniProt",
            primary,
            retrieved_at,
        )
        assertions.append(assertion)
        authors = citation.get("authors") or []
        relationships.append(
            make_relationship(
                f"uniprot:{primary}",
                "described_in",
                object_ref,
                qualifiers={
                    "citation_type": citation.get("citationType"),
                    "title": citation.get("title"),
                    "journal": citation.get("journal"),
                    "year": citation.get("publicationDate"),
                    "first_author": authors[0] if authors else None,
                    "n_authors": len(authors),
                    "pubmed": xrefs.get("PubMed"),
                    "doi": xrefs.get("DOI"),
                    "uniprot_citation": citation.get("id"),
                    "reference_number": reference.get("referenceNumber"),
                    "scope": reference.get("referencePositions") or [],
                    "comments": [
                        {"type": c.get("type"), "value": c.get("value")}
                        for c in reference.get("referenceComments") or []
                    ],
                },
                source_assertion_ids=[assertion["id"]],
            )
        )
    return assertions, relationships


def _knowledge_relationships(
    uniprot_json: Dict[str, Any], primary: str, retrieved_at: str
) -> tuple:
    """GO annotations, classifications and curated interactions stated by UniProt.

    Each becomes a typed relationship of the protein backed by a UniProt SourceAssertion
    whose asserted value keeps the source's own properties verbatim.
    """
    subject = f"uniprot:{primary}"
    assertions: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []

    def add(predicate: str, object_ref: str, stated: Dict[str, Any], qualifiers, eco):
        assertion = make_source_assertion(
            f"relationships.{predicate}",
            {"object_ref": object_ref, **stated},
            "UniProt",
            primary,
            retrieved_at,
        )
        if eco:
            assertion["source_metadata"] = {"eco": eco}
        assertions.append(assertion)
        relationships.append(
            make_relationship(
                subject,
                predicate,
                object_ref,
                qualifiers=qualifiers,
                source_assertion_ids=[assertion["id"]],
            )
        )

    for xref in uniprot_json.get("uniProtKBCrossReferences", []) or []:
        db = xref.get("database")
        props = {p.get("key"): p.get("value") for p in xref.get("properties", []) or []}
        eco = _eco(xref.get("evidences"))
        if db == "GO":
            aspect, _, term = (props.get("GoTerm") or "").partition(":")
            code, _, assigned_by = (props.get("GoEvidenceType") or "").partition(":")
            add(
                "annotated_with",
                f"go:{xref['id']}",
                {"properties": props},
                {
                    "aspect": _GO_ASPECTS.get(aspect, aspect or None),
                    "term": term or None,
                    "go_code": code or None,  # GO's own annotation code (e.g. IDA, IEA)
                    "assigned_by": assigned_by or None,
                },
                eco,
            )
        elif db in _CLASSIFICATIONS:
            add(
                "classified_in",
                f"{_CLASSIFICATIONS[db]}:{xref['id']}",
                {"properties": props},
                {
                    "classification": db,
                    "name": props.get("EntryName"),
                    "match_count": int(props["MatchStatus"])
                    if str(props.get("MatchStatus", "")).isdigit()
                    else None,
                },
                eco,
            )

    for comment in uniprot_json.get("comments", []) or []:
        if comment.get("commentType") != "INTERACTION":
            continue
        for item in comment.get("interactions", []) or []:
            one, two = item.get("interactantOne", {}), item.get("interactantTwo", {})
            partner = two.get("uniProtKBAccession")
            if not partner:
                continue
            add(
                "interacts_with",
                f"uniprot:{partner}",
                {"interaction": item},
                {
                    "partner_gene": two.get("geneName"),
                    "intact_ids": [one.get("intActId"), two.get("intActId")],
                    "experiments": item.get("numberOfExperiments"),
                    "organism_differ": item.get("organismDiffer"),
                    "curated_by": "IntAct",
                },
                None,
            )
    return assertions, relationships


def _parse_pdb_chains(chains: str) -> tuple:
    """UniProt PDB 'Chains' property, e.g. 'A/B=2-249' or 'A/B=3-18, A/B=44-100'."""
    chain_ids: set = set()
    ranges: List[List[int]] = []
    for segment in (chains or "").split(","):
        ids, _, span = segment.strip().partition("=")
        chain_ids.update(c for c in ids.split("/") if c)
        beg, _, end = span.partition("-")
        if beg.strip().isdigit() and end.strip().isdigit():
            ranges.append([int(beg), int(end)])
    return sorted(chain_ids), ranges


def _angstrom(resolution: str | None) -> float | None:
    """'2.80 A' -> 2.8; '-' (e.g. NMR) -> None."""
    try:
        return float(str(resolution).split()[0])
    except (ValueError, IndexError):
        return None


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
    diseases: List[tuple] = []
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
        elif ctype == "DISEASE":
            item = _disease(c)
            if item:
                diseases.append(
                    (
                        item,
                        _eco(get_in(c, ["disease", "evidences"]) or c.get("evidences")),
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
    assert_list("annotations.disease", diseases, fields)
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
        # Variants and mutagenesis state a substitution. UniProt may list several
        # alternative residues for one item; they are kept as stated, not split.
        substitution = f.get("alternativeSequence") or {}
        original = substitution.get("originalSequence")
        alternatives = [a for a in substitution.get("alternativeSequences") or [] if a]
        if original or alternatives:
            item["substitution"] = {
                k: v
                for k, v in (("original", original), ("alternatives", alternatives))
                if v
            }
        if f.get("featureId"):
            item["feature_id"] = f["featureId"]
        cross_references = [
            {"database": x["database"], "id": x["id"]}
            for x in f.get("featureCrossReferences") or []
            if x.get("database") and x.get("id")
        ]
        if cross_references:
            item["cross_references"] = cross_references
        # Binding sites name their ligand: "substrate", or a ChEBI id. ``label`` tells
        # apart two sites of the same ligand (e.g. two ATP sites of one protein).
        ligand = f.get("ligand") or {}
        ligand = {
            k: ligand[k] for k in ("name", "id", "label", "note") if ligand.get(k)
        }
        if ligand:
            item["ligand"] = ligand
        feature_items[fp].append((item, _eco(f.get("evidences"))))
    for fp in _FEATURES.values():
        assert_list(fp, feature_items[fp], features)

    # experimental structures (PDB cross-references) as has_structure relationships
    relationships: List[Dict[str, Any]] = []
    for xref in uniprot_json.get("uniProtKBCrossReferences", []) or []:
        if xref.get("database") != "PDB" or not primary:
            continue
        props = {p.get("key"): p.get("value") for p in xref.get("properties", []) or []}
        chain_ids, ranges = _parse_pdb_chains(props.get("Chains", ""))
        structure_ref = f"pdb:{xref['id']}"
        stated = {
            "object_ref": structure_ref,
            **{k.lower(): v for k, v in props.items()},
        }
        assertion = make_source_assertion(
            "relationships.has_structure", stated, "UniProt", record_id, retrieved_at
        )
        source_assertions.append(assertion)
        relationships.append(
            make_relationship(
                f"uniprot:{primary}",
                "has_structure",
                structure_ref,
                qualifiers={
                    "method": props.get("Method"),
                    "resolution": quantity_node(
                        _angstrom(props.get("Resolution")), LENGTH_UNIT
                    ),
                    "chains": chain_ids,
                    "ranges": ranges,
                    "coverage": coverage(ranges, sequence.get("length")),
                },
                source_assertion_ids=[assertion["id"]],
            )
        )

    # publications the entry cites
    if primary:
        extra_assertions, extra_relationships = _reference_relationships(
            uniprot_json, primary, retrieved_at
        )
        source_assertions.extend(extra_assertions)
        relationships.extend(extra_relationships)

    # GO annotations, classifications and curated interactions
    if primary:
        extra_assertions, extra_relationships = _knowledge_relationships(
            uniprot_json, primary, retrieved_at
        )
        source_assertions.extend(extra_assertions)
        relationships.extend(extra_relationships)

    return {
        "fields": fields,
        "features": features,
        "source_assertions": source_assertions,
        "field_source_assertions": field_source_assertions,
        "relationships": relationships,
    }
