"""Native GlyGen sites retain sequence scope, categories, support and access history."""

import copy
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.mappings.glygen import map_glycosylation, map_phosphorylation
from sabueso.tools.db.glygen import FixtureGlyGenClient, get_protein

PATH = Path("temp_data/glygen/protein__P60174.json")


def native():
    return json.loads(PATH.read_bytes())


def total(payload, table="glycosylation"):
    section = next(s for s in payload["section_stats"] if s["table_id"] == table)
    return next(s for s in section["table_stats"] if s["field"] == "total")


class Client:
    def __init__(self, payload):
        self.payload = payload

    def protein(self, identifier):
        return {"record": self.payload, "retrieved_at": "2026-01-01", "version": None}


def test_native_sites_are_independent_source_sequence_assertions():
    envelope = get_protein("p60174", client=FixtureGlyGenClient())
    before = copy.deepcopy(envelope)
    glycans, phospho = map_glycosylation(envelope), map_phosphorylation(envelope)
    assert len(glycans) == 3 and len(phospho) == 13
    assert envelope == before and envelope["version"] is None
    for assertion in glycans + phospho:
        assert assertion["subject_ref"] == "uniprot:P60174"
        assert assertion["source"]["name"] == "GlyGen"
        assert assertion["source"]["version"] is None
        value, metadata = assertion["asserted_value"], assertion["source_metadata"]
        assert value["location"]["sequence"]["sequence_id"] == "GlyGen:P60174-1"
        assert value["glygen_canonical_ac"] == "P60174-1"
        assert value["evidence"] == metadata["native_annotation"]["evidence"]
        assert "evidence_class" not in value and "knowledge_class" not in value
        assert metadata["sequence"]["value"] == native()["sequence"]["sequence"]
        assert (
            metadata["native_history"][0]["description"]
            == "introduced in data release 1.8.25"
        )
    assert glycans[0]["asserted_value"]["residue"] == "Asn"
    assert glycans[0]["asserted_value"]["site_seq"] == "GWLKSNVSDAVAQSTR"
    assert "P60174-3" in glycans[0]["asserted_value"]["comment"]
    assert glycans[0]["asserted_value"]["location"]["sequence"]["start"] == 196
    assert "glytoucan_ac" not in glycans[2]["asserted_value"]
    assert len({a["id"] for a in glycans}) == 3
    assert any(
        p["database"] == "iPTMnet"
        for a in phospho
        for p in a["asserted_value"]["evidence"]
    )
    (access,) = envelope["acquisition_trace"]["records"]
    assert access["source"] == "GlyGen" and access["count"] == 1
    assert access["network_attempts"] == 0 and access["access"] == "supplied_file"
    assert access["annotation_counts"] == {"glycosylation": 3, "phosphorylation": 13}
    assert access["retrieved_at"] is None and access["source_version"]["value"] is None
    glycans[0]["asserted_value"]["evidence"].clear()
    glycans[0]["source_metadata"]["snapshot_receipt"].clear()
    assert envelope == before


@pytest.mark.parametrize(
    "category", ["predicted", "automatic_literature_mining", "future_category"]
)
def test_native_categories_and_declared_support_never_become_curated_status(category):
    payload = native()
    payload["glycosylation"][0]["site_category"] = category
    payload["glycosylation"][0]["future_field"] = {"literal": "kept"}
    assertions = map_glycosylation(get_protein("P60174", client=Client(payload)))
    assert assertions[0]["asserted_value"]["site_category"] == category
    assert assertions[0]["source_metadata"]["native_annotation"]["future_field"] == {
        "literal": "kept"
    }
    assert assertions[0]["acquisition"] == {"method": "database"}


@pytest.mark.parametrize(
    "begin,end",
    [
        (None, None),
        (0, 0),
        (-1, -1),
        (190, 200),
        (196, None),
        (None, 196),
        (250, 250),
        (200, 190),
    ],
)
def test_ambiguous_unlocated_and_inconsistent_numbering_stays_native(begin, end):
    payload = native()
    row = payload["glycosylation"][0]
    row["start_pos"], row["end_pos"] = begin, end
    assertion = map_glycosylation(get_protein("P60174", client=Client(payload)))[0]
    assert "location" not in assertion["asserted_value"]
    assert assertion["source_metadata"]["native_annotation"] == row
    assert (
        "no_single_residue"
        in assertion["source_metadata"]["mapping_scope"]["coordinates"]
    )


def test_missing_native_coordinate_keys_stay_missing_and_no_duplicate_row_is_lost():
    payload = native()
    row = payload["glycosylation"][0]
    del row["start_pos"], row["end_pos"]
    payload["glycosylation"].append(copy.deepcopy(row))
    total(payload)["count"] += 1
    assertions = map_glycosylation(get_protein("P60174", client=Client(payload)))
    assert len(assertions) == 4 and len({a["id"] for a in assertions}) == 4
    assert "start_pos" not in assertions[0]["source_metadata"]["native_annotation"]


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.clear(),
        lambda p: p.update(error_list=[]),
        lambda p: p["uniprot"].update(uniprot_canonical_ac="P37840-1"),
        lambda p: p["uniprot"].update(uniprot_canonical_ac="P60174"),
        lambda p: p["sequence"].update(sequence="AC D"),
        lambda p: p["sequence"].update(length=248),
        lambda p: p["uniprot"].update(length=True),
        lambda p: p.pop("glycosylation"),
        lambda p: p.update(phosphorylation=None),
        lambda p: total(p).update(count=4),
        lambda p: total(p, "phosphorylation").update(count=12),
        lambda p: total(p).update(count=True),
        lambda p: p["section_stats"].append(copy.deepcopy(p["section_stats"][0])),
        lambda p: p.update(section_stats=[None]),
        lambda p: p["glycosylation"].append(None),
        lambda p: p["glycosylation"][0].update(start_pos=True),
        lambda p: p["glycosylation"][0].update(end_pos="196"),
        lambda p: p["glycosylation"][0].update(site_category=None),
        lambda p: p["glycosylation"][0].update(evidence=None),
        lambda p: p["glycosylation"][0]["evidence"][0].update(id=None),
        lambda p: p["glycosylation"][0]["evidence"].append(None),
        lambda p: p.update(unknown=float("nan")),
    ],
)
def test_invalid_native_identity_shape_or_cut_tables_are_refused(change):
    payload = native()
    change(payload)
    with pytest.raises(ConnectorError):
        get_protein("P60174", client=Client(payload))


@pytest.mark.parametrize(
    "identifier", ["P60174-1", "TPIS_HUMAN", "../P60174", "P60174?x", 123]
)
def test_invalid_identifiers_are_refused_before_access(identifier):
    class NoAccess:
        def protein(self, identifier):
            pytest.fail("Invalid identifier reached the client.")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_protein(identifier, client=NoAccess())


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(source="UniProt"),
        lambda e: e.update(kind="annotations"),
        lambda e: e.update(version="1.8.25"),
        lambda e: e.update(truncated=True),
        lambda e: e["query"].update(accession="P37840"),
    ],
)
def test_mapper_refuses_wrong_source_query_revision_and_scope(change):
    envelope = get_protein("P60174", client=FixtureGlyGenClient())
    change(envelope)
    with pytest.raises(ConnectorError):
        map_glycosylation(envelope)


def test_explicit_empty_tables_are_not_missing_fixture(tmp_path):
    payload = native()
    for table in ("glycosylation", "phosphorylation"):
        payload[table] = []
        total(payload, table)["count"] = 0
    envelope = get_protein("P60174", client=Client(payload))
    assert map_glycosylation(envelope) == [] and map_phosphorylation(envelope) == []
    assert envelope["record"]["sequence"] == native()["sequence"]
    with pytest.raises(ConnectorError) as missing:
        get_protein("P60174", client=FixtureGlyGenClient(tmp_path))
    assert missing.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


@pytest.mark.parametrize("status", [404, 500])
def test_http_failure_never_becomes_source_absence(status, monkeypatch):
    import sabueso.tools.db._http as http

    monkeypatch.setattr(http, "RETRIES", 0)

    def fail(request, timeout):
        raise HTTPError(request.full_url, status, "failure", {}, None)

    monkeypatch.setattr(http, "_urlopen", fail)
    with pytest.raises(ConnectorError) as error:
        get_protein("P60174")
    (access,) = error.value.acquisition_trace["records"]
    assert access["outcome"] == "failed" and access["network_attempts"] == 1


def test_shared_online_archive_replay_keeps_original_time_and_support(
    tmp_path, monkeypatch
):
    import sabueso.tools.db._http as http

    calls = []

    class Answer(io.BytesIO):
        status = 200
        headers = Message()
        headers["Content-Type"] = "application/json"

    def wire(request, timeout):
        calls.append(request.full_url)
        return Answer(PATH.read_bytes())

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "glygen.db")
    with archive.recording():
        first = get_protein("P60174")

    def fail(*args, **kwargs):
        pytest.fail("Replay reached the network.")

    monkeypatch.setattr(http, "_urlopen", fail)
    with archive.replaying():
        second = get_protein("P60174")
    assert calls == ["https://api.glygen.org/protein/detail/P60174/"]
    assert first["retrieved_at"] == second["retrieved_at"]
    assert map_glycosylation(first) == map_glycosylation(second)
    assert map_phosphorylation(first) == map_phosphorylation(second)
    a, b = (
        first["acquisition_trace"]["records"][0],
        second["acquisition_trace"]["records"][0],
    )
    assert a["received_responses"] == 1 and a["network_attempts"] == 1
    assert b["access"] == "replay" and b["network_attempts"] == 0
    assert (
        b["received_responses"] == 1
    )  # The replayed body is received without network access.
    assert a["retrieved_at"] == b["retrieved_at"]
