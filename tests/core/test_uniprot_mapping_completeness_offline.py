"""UniProt mapping must not silently drop annotated content (uibcdf/sabueso#13)."""

import json
from pathlib import Path

import pytest

from sabueso.mappings.uniprot import map_protein
from sabueso.tools.db.uniprot import create_protein_card_from_file

FIXTURES = ["P52789", "P35372", "A0A140VJM9", "P60174", "P52270"]


def _raw(accession):
    return json.loads(Path(f"temp_data/{accession}.json").read_text(encoding="utf-8"))


def _comments(raw, comment_type):
    return [c for c in raw.get("comments", []) if c.get("commentType") == comment_type]


@pytest.mark.parametrize("accession", FIXTURES)
def test_uniprot_comments_and_sequence_are_mapped(accession):
    raw = _raw(accession)
    fields = map_protein(raw, retrieved_at="2026-02-01")["fields"]

    reactions = _comments(raw, "CATALYTIC ACTIVITY")
    assert len(fields.get("annotations.catalytic_activity", [])) == len(reactions)

    locations = [
        s
        for c in _comments(raw, "SUBCELLULAR LOCATION")
        for s in c.get("subcellularLocations", [])
    ]
    assert len(fields.get("annotations.subcellular_location", [])) == len(locations)

    sequence = raw["sequence"]
    assert fields["sequence.primary"] == sequence["value"]
    assert fields["sequence.length"] == sequence["length"] == len(sequence["value"])
    assert fields["sequence.molecular_weight"] == sequence["molWeight"]
    assert fields["sequence.checksums"] == {
        "crc64": sequence["crc64"],
        "md5": sequence["md5"],
    }


@pytest.mark.parametrize("accession", FIXTURES)
def test_uniprot_eco_qualifiers_are_kept_as_source_metadata(accession):
    raw = _raw(accession)
    mapping = map_protein(raw, retrieved_at="2026-02-01")
    with_eco = [
        a
        for a in mapping["source_assertions"]
        if a.get("source_metadata", {}).get("eco")
    ]

    mapped_types = {
        "FUNCTION",
        "PATHWAY",
        "SUBUNIT",
        "TISSUE SPECIFICITY",
        "PTM",
        "POLYMORPHISM",
    }
    qualified_mapped_texts = sum(
        1
        for c in raw.get("comments", [])
        if c.get("commentType") in mapped_types
        for t in c.get("texts", []) or []
        if t.get("value") and t.get("evidences")
    )
    text_fields = {
        "annotations.function",
        "annotations.pathway",
        "annotations.subunit",
        "annotations.tissue_specificity",
        "annotations.ptm",
        "annotations.polymorphism",
    }
    assert (
        sum(1 for a in with_eco if a["field_path"] in text_fields)
        == qualified_mapped_texts
    )
    for assertion in with_eco:
        for item in assertion["source_metadata"]["eco"]:
            assert item["code"].startswith("ECO:")


def test_human_tim_reactions_and_location():
    card = create_protein_card_from_file(
        "temp_data/P60174.json", retrieved_at="2026-02-01"
    )

    reactions = card.get("annotations.catalytic_activity")["value"]
    assert {(r["ec_number"], r["rhea_id"]) for r in reactions} == {
        ("5.3.1.1", "RHEA:18585"),
        ("4.2.3.3", "RHEA:17937"),
    }
    assert card.get("annotations.subcellular_location")["value"] == [
        {"location": "Cytoplasm"}
    ]
    assert card.get("sequence.length")["value"] == 249

    tim = next(
        card.source_assertion_store.get(sa_id)
        for sa_id in card.get("annotations.catalytic_activity")["source_assertion_ids"]
        if card.source_assertion_store.get(sa_id)["asserted_value"]["ec_number"]
        == "5.3.1.1"
    )
    assert any(
        e["code"] == "ECO:0000269" and e.get("source") == "PubMed"
        for e in tim["source_metadata"]["eco"]
    )


def test_trypanosoma_cruzi_tim_is_glycosomal():
    card = create_protein_card_from_file(
        "temp_data/P52270.json", retrieved_at="2026-02-01"
    )

    assert card.get("annotations.organism")["value"] == "Trypanosoma cruzi"
    assert card.get("annotations.subcellular_location")["value"] == [
        {"location": "Glycosome"}
    ]
    assert [
        r["ec_number"] for r in card.get("annotations.catalytic_activity")["value"]
    ] == ["5.3.1.1"]
    assert card.get("sequence.length")["value"] == 251


def test_isoform_restricted_location_keeps_its_molecule():
    fields = map_protein(_raw("P35372"), retrieved_at="2026-02-01")["fields"]
    restricted = [
        loc for loc in fields["annotations.subcellular_location"] if "molecule" in loc
    ]
    assert restricted == [{"location": "Cytoplasm", "molecule": "Isoform 12"}]
