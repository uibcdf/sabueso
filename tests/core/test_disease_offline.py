"""UniProt DISEASE comments in protein cards (uibcdf/sabueso#39).

Frozen UniProt entries (release 2026_03): human TIM P60174 states one disease; TcTIM
P52270 states none.
"""

import json
from pathlib import Path

from sabueso import resolve_protein_card
from sabueso.mappings.uniprot import map_protein
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

DISEASE = "annotations.disease"


def _mapped(accession):
    entry = json.loads(Path(f"temp_data/{accession}.json").read_text(encoding="utf-8"))
    return map_protein(entry, "2026-09-24")


def test_a_disease_is_kept_as_uniprot_states_it():
    (disease,) = _mapped("P60174")["fields"][DISEASE]
    assert disease["name"] == "Triosephosphate isomerase deficiency"
    assert disease["accession"] == "DI-02390"
    assert disease["acronym"] == "TPID"
    assert disease["description"].startswith("An autosomal recessive multisystem")
    assert disease["cross_references"] == [{"database": "MIM", "id": "615512"}]
    assert disease["note"] == (
        "The disease is caused by variants affecting the gene represented in this entry"
    )


def test_each_disease_has_a_source_assertion_with_its_evidence():
    mapped = _mapped("P60174")
    (sa_id,) = mapped["field_source_assertions"][DISEASE]
    (assertion,) = [a for a in mapped["source_assertions"] if a["id"] == sa_id]
    assert assertion["source"]["name"] == "UniProt"
    pubmed = [
        e["id"]
        for e in assertion["source_metadata"]["eco"]
        if e.get("source") == "PubMed"
    ]
    assert pubmed == ["2876430", "8503454", "8571957", "9338582"]


def test_a_protein_without_a_disease_comment_has_no_disease_field():
    assert DISEASE not in _mapped("P52270")["fields"]


def test_the_disease_reaches_the_resolved_card():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    card, _ = resolve_protein_card("P60174", resolver)
    node = card.get(DISEASE)
    assert [d["accession"] for d in node["value"]] == ["DI-02390"]
    assert len(node["source_assertion_ids"]) == 1
