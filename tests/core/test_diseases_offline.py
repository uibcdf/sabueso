"""DISEASES: human gene–disease associations, one per channel (#82).

Fixtures: the filtered rows of HsTIM's Ensembl protein ENSP00000229270 (files of
2026-09-18 and 2026-09-20), and the UniProt entries of HsTIM (P60174) and TcTIM
(P52270).
"""

import io

import pytest

import sabueso
from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
from sabueso.core.errors import ArgumentError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import diseases as diseases_db
from sabueso.tools.db.diseases import (
    FixtureDISEASESClient,
    OnlineDISEASESClient,
    parse_channel,
)


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(FixtureUniProtClient("temp_data"))


def _card(resolver, accession="P60174", **options):
    card, _ = sabueso.resolve(
        accession,
        resolver=resolver,
        diseases_client=FixtureDISEASESClient("temp_data"),
        **options,
    )
    return card


def _associations(card):
    return {
        (r["object_ref"], r["qualifiers"]["channel"]): r
        for r in card.relationships("associated_with")
    }


def test_curated_associations_come_with_their_resource_and_confidence(resolver):
    found = _associations(_card(resolver, diseases={}))
    assert set(found) == {
        ("doid:DOID:0050884", "knowledge"),
        ("doid:DOID:589", "knowledge"),
    }
    deficiency = found[("doid:DOID:0050884", "knowledge")]["qualifiers"]
    assert deficiency["disease_name"] == "Triosephosphate isomerase deficiency"
    assert (deficiency["source_database"], deficiency["confidence"]) == (
        "MedlinePlus",
        5.0,
    )
    # Joined through the Ensembl protein UniProt cross-references, never by name.
    assert deficiency["via_protein"] == "ensembl:ENSP00000229270"
    assert deficiency["uniprot_isoform"] == "P60174-3"
    assert deficiency["basis"] == "uniprot_ensembl_xref"


def test_text_mining_is_added_only_when_asked_and_kept_apart(resolver):
    card = _card(resolver, diseases={"channels": ["knowledge", "textmining"]})
    found = _associations(card)
    # The same disease, curated and text-mined: two statements, never merged.
    assert ("doid:DOID:0050884", "knowledge") in found
    assert ("doid:DOID:0050884", "textmining") in found
    # Text mining links names: the human gene is co-mentioned with giardiasis, whose
    # parasite has its own triosephosphate isomerase.
    giardiasis = found[("doid:DOID:10718", "textmining")]["qualifiers"]
    assert set(giardiasis) >= {"z_score", "confidence"}
    assert ("doid:DOID:10718", "textmining") not in _associations(
        _card(resolver, diseases={})
    )


def test_a_non_human_protein_is_not_queried_never_not_stated(resolver):
    card = _card(resolver, "P52270", diseases={})
    (row,) = [
        r
        for r in card.knowledge_state()["rows"]
        if (r["area"], r["source"]) == ("relationships.associated_with", "DISEASES")
    ]
    assert row["state"] == "not_queried"
    assert row["basis"] == {"detail": "DISEASES covers Homo sapiens genes only"}
    assert card.relationships("associated_with") == []


def test_a_failed_download_is_unavailable(resolver):
    with pytest.warns(EnrichmentFailedWarning):
        card, _ = sabueso.resolve(
            "P60174",
            resolver=resolver,
            diseases={},
            diseases_client=FixtureDISEASESClient(
                "temp_data", failing={"ENSP00000229270"}
            ),
        )
    states = {
        (r["area"], r["source"]): r["state"] for r in card.knowledge_state()["rows"]
    }
    assert states[("relationships.associated_with", "DISEASES")] == "unavailable"


def test_unknown_channels_are_refused(resolver):
    with pytest.raises(ArgumentError):
        _card(resolver, diseases={"channels": ["guesswork"]})


def test_rows_of_each_channel_are_parsed_by_their_columns():
    text = (
        "ENSP1\tG\tDOID:1\tD\tTIGA\tMeanRankScore = 29\t0.897\n"
        "18S_rRNA\t18S_rRNA\tDOID:2\tE\tTIGA\tx\t1\n"
    )
    rows = parse_channel(text, "experiments")
    assert list(rows) == ["ENSP1"]  # non-protein entities are left out
    assert rows["ENSP1"][0]["source_score"] == "MeanRankScore = 29"


class _Response(io.BytesIO):
    headers = {"Last-Modified": "Fri, 18 Sep 2026 20:10:21 GMT"}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_the_online_client_versions_by_date_and_caches_only_where_told(
    tmp_path, monkeypatch
):
    body = b"ENSP1\tG\tDOID:1\tD\tMedlinePlus\tCURATED\t5\n"
    monkeypatch.setattr(diseases_db, "_MEMORY", {})
    monkeypatch.setattr(
        diseases_db, "urlopen", lambda request, timeout: _Response(body)
    )
    monkeypatch.delenv("SABUESO_CACHE_DIR", raising=False)
    response = OnlineDISEASESClient().associations(["ENSP1.4", "ENSP2"], ["knowledge"])
    assert response["version"] == {"knowledge": "2026-09-18"}
    assert response["record"]["knowledge"][0]["disease"] == "DOID:1"
    assert response["missing"] == ["ENSP2"]
    monkeypatch.setattr(diseases_db, "_MEMORY", {})
    OnlineDISEASESClient(cache_dir=tmp_path).associations(["ENSP1"], ["knowledge"])
    assert [p.name for p in (tmp_path / "diseases").iterdir()] == [
        "knowledge_2026-09-18.json"
    ]


# --- Open Targets ----------------------------------------------------------------------


def _open_targets(resolver, accession="P60174", **options):
    from sabueso.tools.db.open_targets import FixtureOpenTargetsClient

    card, _ = sabueso.resolve(
        accession,
        resolver=resolver,
        open_targets=options.pop("open_targets", {}),
        open_targets_client=FixtureOpenTargetsClient("temp_data"),
        diseases={},
        diseases_client=FixtureDISEASESClient("temp_data"),
        **options,
    )
    return card


def test_open_targets_scores_are_kept_as_stated_and_the_cut_reported(resolver):
    from sabueso._private.smonitor.warnings import EnrichmentTruncatedWarning

    with pytest.warns(EnrichmentTruncatedWarning):  # 20 saved rows of 483
        card = _open_targets(resolver)
    found = {
        (r["object_ref"], r["qualifiers"]["source"]): r["qualifiers"]
        for r in card.relationships("associated_with")
    }
    deficiency = found[("mondo:MONDO:0014221", "Open Targets")]
    assert deficiency["rank"] == 1
    assert round(deficiency["score"], 3) == 0.783
    assert {d["datatype"] for d in deficiency["datatype_scores"]} == {
        "literature",
        "genetic_association",
        "genetic_literature",
    }
    assert (deficiency["via_gene"], deficiency["gene_lists_protein"]) == (
        "ensembl:ENSG00000111669",
        True,
    )
    # DISEASES states the same disease under another ontology: never merged.
    assert ("doid:DOID:0050884", "DISEASES") in found


def test_open_targets_needs_both_sources_to_state_the_link(resolver, monkeypatch):
    from sabueso.tools.db.open_targets import FixtureOpenTargetsClient

    original = FixtureOpenTargetsClient.associations

    def other_products(self, gene, limit=100):
        response = original(self, gene, limit)
        response["record"]["target"]["proteinIds"] = [{"id": "Q00000"}]
        return response

    monkeypatch.setattr(FixtureOpenTargetsClient, "associations", other_products)
    card = _open_targets(resolver)
    sources = {r["qualifiers"]["source"] for r in card.relationships("associated_with")}
    assert sources == {"DISEASES"}
    (record,) = [
        e for e in card.quality["enrichments"] if e["source"] == "Open Targets"
    ]
    assert record["status"] == "not_found"
    assert "does not list P60174" in record["detail"]


def test_open_targets_does_not_cover_a_parasite_protein(resolver):
    card = _open_targets(resolver, "P52270")
    rows = {
        (r["area"], r["source"]): r
        for r in card.knowledge_state()["rows"]
        if r["area"] == "relationships.associated_with"
    }
    assert rows[("relationships.associated_with", "Open Targets")]["state"] == (
        "not_queried"
    )
