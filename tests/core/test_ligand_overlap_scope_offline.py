"""Coordinate admission, not numerical coincidence, controls ligand overlap."""

import socket
from copy import deepcopy

import pytest

import sabueso
from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.interpro import map_family_sites
from sabueso.mappings.uniprot import map_protein

FIELD = "features_positional.active_site"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("No source queries or sequence alignment")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def protein(*, molecule=None, modifier="EXACT", annotation=True, position=2):
    native = {
        "primaryAccession": "P52270",
        "sequence": {"value": "M" * 20, "length": 20},
        "entryAudit": {"sequenceVersion": 7},
        "features": [
            {
                "type": "Active site",
                "description": "Explicit synthetic annotation",
                "molecule": molecule,
                "location": {
                    "start": {"value": 2, "modifier": modifier},
                    "end": {"value": 4, "modifier": "EXACT"},
                },
            }
        ]
        if annotation
        else [],
    }
    card = build_card_from_mapping(
        map_protein(native, "synthetic"), meta={"entity_type": "protein"}
    )
    add_contact(card, position=position)
    return card


def add_contact(
    card, *, position=2, code="ATP", subject="uniprot:P52270", numbering="uniprot"
):
    q = {
        "numbering": numbering,
        "residues": [{"start": position, "end": position, "residue": "M"}],
    }
    a = make_source_assertion(
        "relationships.has_ligand_site",
        {"object_ref": "pdb.ligand:" + code, "qualifiers": deepcopy(q)},
        "Explicit synthetic contact source",
        code,
        "synthetic",
        subject_ref=subject,
    )
    card.source_assertion_store.add(a)
    return card.relationship_store.add(
        make_relationship(
            subject, "has_ligand_site", "pdb.ligand:" + code, deepcopy(q), [a["id"]]
        )
    )


def value_edit(card, change):
    node = card.get(FIELD)
    change(node["value"][0])
    for ref in node["source_assertion_ids"]:
        card.source_assertion_store.get(ref)["normalized_value"] = deepcopy(
            node["value"][0]
        )


def view(card):
    result = card.ligand_sites()
    return result, result["items"][0]


def test_exact_scope_and_source_bound_originals_allow_positive_and_negative_results():
    for position, expected in [
        (2, "overlaps_annotated_site"),
        (5, "no_annotated_overlap"),
    ]:
        card = protein(position=position)
        before = card.to_dict()
        result, site = view(card)
        assert site["site_class"] == expected
        assert site["comparison"]["status"] == "computed"
        assert result["classification"]["rule"] == "annotated_site_overlap@3"
        assert (
            result["annotated_sites"][0]["scope"]["sequence_revisions"]["state"]
            == "matching"
        )
        assert site["comparison"]["contact_scope"]["sequence_revision"] == "not_stated"
        assert card.to_dict() == before


@pytest.mark.parametrize("molecule", ["P52270-2", "Isoform 2", "", "UniProt:P60174"])
def test_foreign_or_unidentified_annotation_axis_is_visible_and_not_a_negative(
    molecule,
):
    card = protein(molecule=molecule)
    result, site = view(card)
    assert site["site_class"] == "comparison_not_computed"
    assert site["comparison"]["status"] == "not_computed"
    assert site["annotated_overlap"] == []
    (row,) = result["annotated_sites"]
    assert row["positions"] is None
    assert row["recorded_annotation"]["molecule"] == molecule
    assert row["scope"]["reason"] == "annotation_axis_not_canonical"
    assert row["source_assertion_id"] in card.get(FIELD)["source_assertion_ids"]


@pytest.mark.parametrize(
    "modifier", ["LESS_THAN", "GREATER_THAN", "UNKNOWN", "UNSURE", "future"]
)
def test_uncertain_bounds_are_not_closed_into_exact_overlaps(modifier):
    result, site = view(protein(modifier=modifier))
    assert site["site_class"] == "comparison_not_computed"
    assert (
        result["annotated_sites"][0]["scope"]["reason"]
        == "annotation_positions_uncertain_or_invalid"
    )


@pytest.mark.parametrize(
    "start,end", [(None, 4), (True, 4), ("2", 4), (2, 2.0), (0, 4), (4, 2), (2, 21)]
)
def test_invalid_normalized_intervals_remain_uncomputed(start, end):
    card = protein()
    value_edit(card, lambda v: v["location"]["sequence"].update(start=start, end=end))
    result, site = view(card)
    assert site["site_class"] == "comparison_not_computed"
    assert result["annotated_sites"][0]["positions"] is None


@pytest.mark.parametrize(
    "change",
    [
        "indexing",
        "axis",
        "native_molecule",
        "native_bounds",
        "native_type",
        "compound",
        "lost_native",
    ],
)
def test_native_source_scope_cannot_be_overridden_by_normalized_positions(change):
    card = protein()
    source = card.source_assertion_store.get(card.get(FIELD)["source_assertion_ids"][0])
    native = source["source_metadata"]["uniprot_feature"]
    if change == "indexing":
        value_edit(card, lambda v: v["location"]["sequence"].update(indexing="0-based"))
    elif change == "axis":
        value_edit(
            card,
            lambda v: v["location"]["sequence"].update(sequence_id="UniProt:P60174"),
        )
    elif change == "native_molecule":
        native["molecule"] = "P52270-2"
    elif change == "native_bounds":
        native["location"]["start"]["value"] = 3
    elif change == "native_type":
        native["type"] = "Binding site"
    elif change == "compound":
        native["location"]["fragments"] = [{"start": 2, "end": 4}]
    else:
        source["source_metadata"].pop("uniprot_feature")
    result, site = view(card)
    assert site["site_class"] == "comparison_not_computed"
    assert result["annotated_sites"][0]["recorded_annotation"]


@pytest.mark.parametrize(
    "change",
    [
        "missing_source",
        "foreign_subject",
        "other_field",
        "conflict",
        "revision",
        "invalid_revision",
    ],
)
def test_annotation_support_conflicts_and_revisions_block_projection(change):
    card = protein()
    node = card.get(FIELD)
    source = card.source_assertion_store.get(node["source_assertion_ids"][0])
    if change == "missing_source":
        node["source_assertion_ids"].append("SA_EXPLICIT_MISSING")
    elif change == "foreign_subject":
        source["subject_ref"] = "uniprot:P60174"
    elif change == "other_field":
        source["field_path"] = "features_positional.binding_site"
    elif change == "conflict":
        card.quality["conflicts"] = [{"field": FIELD, "explicit_synthetic": True}]
    else:
        source["source_metadata"]["sequence_version"] = (
            8 if change == "revision" else True
        )
    assert view(card)[1]["site_class"] == "comparison_not_computed"


def test_missing_sequence_revision_is_visible_not_reported_as_revision_agreement():
    card = protein()
    source = card.source_assertion_store.get(card.get(FIELD)["source_assertion_ids"][0])
    source["source_metadata"].pop("sequence_version")
    result, site = view(card)
    assert site["site_class"] == "overlaps_annotated_site"
    scope = result["annotated_sites"][0]["scope"]
    assert scope["sequence_revisions"]["state"] == "partially_stated"
    assert scope["sequence_revisions"]["unstated_source_assertion_ids"] == [
        source["id"]
    ]


@pytest.mark.parametrize(
    "change", ["identity", "sequence", "length", "support", "conflict", "revision"]
)
def test_canonical_prerequisites_require_actual_consistent_source_support(change):
    card = protein()
    if change in ("identity", "sequence", "length"):
        path = {
            "identity": "identifiers.uniprot",
            "sequence": "sequence.primary",
            "length": "sequence.length",
        }[change]
        card.get(path)["value"] = {
            "identity": "P60174",
            "sequence": "M",
            "length": True,
        }[change]
    elif change == "support":
        card.get("sequence.primary")["source_assertion_ids"] = []
    elif change == "conflict":
        card.quality["conflicts"] = [{"field": "sequence.primary.value"}]
    else:
        ref = card.get("sequence.primary")["source_assertion_ids"][0]
        card.source_assertion_store.get(ref)["source_metadata"]["sequence_version"] = (
            "7"
        )
    assert view(card)[1]["site_class"] == "comparison_not_computed"


@pytest.mark.parametrize(
    "change",
    [
        "subject",
        "numbering",
        "empty",
        "bool",
        "missing_end",
        "out_of_bounds",
        "missing_source",
        "source_subject",
        "edited_positions",
    ],
)
def test_contact_scope_must_match_canonical_axis_and_original_declaration(change):
    card = protein()
    rel = card.relationships("has_ligand_site")[0]
    if change == "subject":
        rel["subject_ref"] = "uniprot:P60174"
    elif change == "numbering":
        rel["qualifiers"]["numbering"] = "author"
    elif change == "empty":
        rel["qualifiers"]["residues"] = []
    elif change in ("bool", "missing_end", "out_of_bounds", "edited_positions"):
        residue = rel["qualifiers"]["residues"][0]
        if change == "missing_end":
            residue.pop("end")
        else:
            residue.update(
                start=True
                if change == "bool"
                else 21
                if change == "out_of_bounds"
                else 3
            )
            residue["end"] = residue["start"]
    elif change == "missing_source":
        rel["source_assertion_ids"] = ["SA_EXPLICIT_MISSING"]
    else:
        card.source_assertion_store.get(rel["source_assertion_ids"][0])[
            "subject_ref"
        ] = "uniprot:P60174"
    site = view(card)[1]
    assert site["site_class"] in ("comparison_not_computed", "numbering_not_comparable")
    assert site["positions"] is None and site["residues"] is None
    assert site["comparison"]["contact_scope"]["reason"]
    assert site["comparison"]["compared_annotation_indices"] == []
    assert site["recorded_residues"] == rel["qualifiers"].get("residues")


def test_partial_positive_survives_but_partial_negative_never_becomes_absence():
    card = protein()
    value = deepcopy(card.get(FIELD)["value"][0])
    value["description"] = "Explicit unplaced annotation"
    value["location"]["sequence"]["sequence_id"] = None
    card.get(FIELD)["value"].append(value)
    for position, expected, status in [
        (2, "overlaps_annotated_site", "partial"),
        (5, "comparison_not_computed", "not_computed"),
    ]:
        other = Card.from_dict(card.to_dict())
        other.relationship_store.store.clear()
        add_contact(other, position=position)
        result, site = view(other)
        assert site["site_class"] == expected
        assert site["comparison"]["status"] == status
        assert site["comparison"]["uncomputed_annotation_indices"]
        assert len(result["annotated_sites"]) == 2


@pytest.mark.parametrize(
    "change",
    [None, "end", "axis", "ligand", "record", "positions", "normalized_override"],
)
def test_native_pdbe_contact_requires_original_exact_axis_object_and_positions(change):
    from sabueso.mappings.pdbe_kb import map_ligand_sites

    card = protein()
    card.relationship_store.store.clear()
    mapped = map_ligand_sites(
        {
            "accession": "P52270",
            "record": {
                "data": [
                    {
                        "accession": "ATP",
                        "residues": [
                            {
                                "startIndex": 2,
                                "endIndex": 2,
                                "indexType": "UNIPROT",
                                "startCode": "M",
                                "endCode": "M",
                            }
                        ],
                    }
                ]
            },
        },
        "synthetic",
    )
    for source in mapped["source_assertions"]:
        card.source_assertion_store.add(source)
    for rel in mapped["relationships"]:
        card.relationship_store.add(rel)
    rel = card.relationships("has_ligand_site")[0]
    source = card.source_assertion_store.get(rel["source_assertion_ids"][0])
    ligand = source["asserted_value"]["ligand"]
    if change == "end":
        ligand["residues"][0].pop("endIndex")
    elif change == "axis":
        ligand["residues"][0]["indexType"] = "PDB"
    elif change == "ligand":
        ligand["accession"] = "OTHER"
    elif change == "record":
        source["source"]["record_id"] = "P60174"
    elif change == "positions":
        ligand["residues"][0].update(startIndex=3, endIndex=3)
    elif change == "normalized_override":
        source["normalized_value"] = {
            "object_ref": rel["object_ref"],
            "qualifiers": deepcopy(rel["qualifiers"]),
        }
        ligand["residues"][0]["indexType"] = "PDB"
    _, site = view(card)
    assert site["site_class"] == (
        "overlaps_annotated_site" if change is None else "comparison_not_computed"
    )
    assert site["comparison"]["contact_scope"]["status"] == (
        "comparable" if change is None else "not_computed"
    )


@pytest.mark.parametrize(
    "change", ["bare_qualifiers", "indexing", "sequence_ref", "compound"]
)
def test_contact_axis_extensions_and_unbound_qualifiers_cannot_prove_overlap(change):
    card = protein()
    rel = card.relationships("has_ligand_site")[0]
    q = rel["qualifiers"]
    source = card.source_assertion_store.get(rel["source_assertion_ids"][0])
    if change == "bare_qualifiers":
        source["asserted_value"] = deepcopy(q)
    else:
        q.update(
            {
                "indexing": {"indexing": "0-based"},
                "sequence_ref": {"sequence_ref": "uniprot:P60174"},
                "compound": {"fragments": [{"start": 2, "end": 2}]},
            }[change]
        )
        source["asserted_value"]["qualifiers"] = deepcopy(q)
    assert view(card)[1]["site_class"] == "comparison_not_computed"


def test_interpro_fragments_keep_explicit_axis_and_original_model_support():
    card = protein(annotation=False)
    mapped = map_family_sites(
        {
            "accession": "P52270",
            "version": "synthetic",
            "residues": {
                "signature": {
                    "source_database": "cdd",
                    "accession": "signature",
                    "locations": [
                        {
                            "description": "Explicit family site",
                            "fragments": [
                                {"start": 2, "end": 2, "residues": "M"},
                                {"start": 4, "end": 4, "residues": "M"},
                            ],
                        }
                    ],
                }
            },
        },
        "synthetic",
    )
    path = "features_positional.family_site"
    for source in mapped["source_assertions"]:
        card.source_assertion_store.add(source)
    card.set(path, mapped["features"][path], mapped["field_source_assertions"][path])
    result, site = view(card)
    assert result["annotated_sites"][0]["positions"] == [2, 4]
    assert site["site_class"] == "overlaps_annotated_site"
    node = card.get(path)
    node["value"][0]["location"]["sequence"]["sequence_id"] = "UniProt:P60174"
    card.source_assertion_store.get(node["source_assertion_ids"][0])[
        "asserted_value"
    ] = deepcopy(node["value"][0])
    assert view(card)[1]["site_class"] == "comparison_not_computed"


def test_stored_absence_is_distinct_from_an_unrecognized_annotation_collection():
    card = protein(annotation=False)
    assert view(card)[1]["site_class"] == "no_annotated_sites"
    card.set(FIELD, {"explicit_synthetic": "not_an_array"}, [])
    result, site = view(card)
    assert site["site_class"] == "comparison_not_computed"
    assert (
        result["annotated_sites"][0]["scope"]["reason"]
        == "unrecognized_annotation_collection"
    )


@pytest.mark.parametrize("detail", ["full", "index"])
def test_old_packet10_reading_keeps_original_projection_and_terms(
    detail, tmp_path, monkeypatch
):
    from sabueso.core.packets import KnowledgePacket, _facts, full_rules

    card = protein(molecule="P52270-2")
    current = sabueso.compose_packet(
        sabueso.KnowledgeQuery("P52270", aspects=["ligand_sites"], detail=detail), card
    )
    assert current.to_dict()["aspect_mapping"] == "packet_aspects@11"
    payload = current.to_dict()
    payload["aspect_mapping"] = "packet_aspects@10"
    if detail == "full":
        historical = _facts("ligand_sites", card, mapping="packet_aspects@10")
        assert historical["items"][0]["site_class"] == "overlaps_annotated_site"
        payload["facts"]["ligand_sites"]["subject"] = historical
    else:
        payload["facts"]["ligand_sites"]["subject"]["full_rules"] = full_rules(
            "packet_aspects@10"
        )["ligand_sites"]
    original = KnowledgePacket(payload)
    store = sabueso.KnowledgeStore(tmp_path / "old.db")
    store.save(card)
    before = original.to_dict()
    pin = store.save_packet(original, "explicit_synthetic_legacy")
    monkeypatch.setattr(
        Card,
        "ligand_sites",
        lambda *a, **k: pytest.fail("No current coordinate reader"),
    )
    restored = store.load_packet(pin)
    assert (
        restored.terms("commercial_product", store=store)["packet_rule"]
        == "packet_terms@1"
    )
    assert restored.to_dict() == before
