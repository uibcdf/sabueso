"""Native identity, sequence scope, source subsets and supplied-file access."""

import copy
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso.core.errors import ConnectorError
from sabueso.mappings.disprot import map_disorder_regions, validate_records
from sabueso.tools.db.disprot import (
    FixtureDisProtClient,
    OnlineDisProtClient,
    SnapshotDisProtClient,
    get_records,
)


def native():
    return json.loads(Path("temp_data/disprot/records__P37840.json").read_text())


def test_native_fixture_retains_subset_and_distinct_source_sequence():
    envelope = get_records("P37840", client=FixtureDisProtClient())
    assert envelope["truncated"] is True
    record = envelope["record"]["data"][0]
    assert len(record["regions"]) == 22 and record["regions_counter"] == 40
    before = copy.deepcopy(envelope)
    assertions = map_disorder_regions(envelope)
    assert assertions and envelope == before
    for assertion in assertions:
        value = assertion["asserted_value"]
        assert value["term_id"] == "IDPO:0000002"
        assert value["location"]["sequence"]["sequence_id"] == "DisProt:DP00070"
        assert assertion["subject_ref"] == "uniprot:P37840"
        assert assertion["source_metadata"]["native_region"]["reference_id"]
        assert assertion["acquisition"] == {"method": "database"}
    (access,) = envelope["acquisition_trace"]["records"]
    assert access["access"] == "supplied_file" and access["network_attempts"] == 0
    assert access["retrieved_at"] is None and access["source_version"]["value"] is None
    assert (
        "underlying_disorder_publication_metadata_not_fetched"
        in access["bibliography_gaps"]
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(size=2),
        lambda p: p["data"].append(copy.deepcopy(p["data"][0])),
        lambda p: p["data"][0].update(acc="P99999"),
        lambda p: p["data"][0].update(length=139),
        lambda p: p["data"][0]["regions"][0].update(start=0),
        lambda p: p["data"][0]["regions"][0].update(end=True),
        lambda p: p["data"][0]["regions"][0].update(version=True),
        lambda p: p["data"][0]["regions"][0].update(term_is_obsolete="false"),
        lambda p: p["data"][0]["regions"].append(
            copy.deepcopy(p["data"][0]["regions"][0])
        ),
    ],
)
def test_unrelated_capped_and_malformed_answers_are_refused(change):
    payload = native()
    change(payload)
    with pytest.raises(ConnectorError):
        validate_records(payload, "P37840")


def test_unknown_term_is_not_turned_into_disorder():
    envelope = get_records("P37840", client=FixtureDisProtClient())
    for record in envelope["record"]["data"]:
        for region in record["regions"]:
            region["term_id"] = "IDPO:unknown"
    assert map_disorder_regions(envelope) == []


def test_mapping_refuses_another_source_and_preserves_zero_revision():
    envelope = get_records("P37840", client=FixtureDisProtClient())
    for region in envelope["record"]["data"][0]["regions"]:
        region["version"] = 0
    assert all(a["source"]["version"] == "0" for a in map_disorder_regions(envelope))
    envelope["source"] = "Another source"
    with pytest.raises(ConnectorError):
        map_disorder_regions(envelope)


def test_explicit_snapshot_binding_and_digest(tmp_path):
    path = tmp_path / "source.json"
    path.write_text(json.dumps(native()), encoding="utf-8")
    metadata = {
        "source": "DisProt",
        "kind": "records",
        "query": {"accession": "P37840"},
        "retrieved_at": "2020-01-01",
    }
    client = SnapshotDisProtClient(path, source_metadata=metadata)
    result = get_records("P37840", client=client)
    assert result["retrieved_at"] == "2020-01-01"
    metadata["query"] = {"accession": "P99999"}
    with pytest.raises(ConnectorError, match="do not match"):
        get_records("P37840", client=client)
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_records(
            "P37840",
            client=SnapshotDisProtClient(
                path, source_metadata=metadata, expected_sha256="0" * 64
            ),
        )


def test_empty_answer_and_unavailable_fixture_differ(tmp_path):
    directory = tmp_path / "disprot"
    directory.mkdir()
    (directory / "records__P37840.json").write_text(
        '{"data":[],"size":0}', encoding="utf-8"
    )
    result = get_records("P37840", client=FixtureDisProtClient(tmp_path))
    assert result["acquisition_trace"]["records"][0]["outcome"] == "empty"
    with pytest.raises(ConnectorError) as unavailable:
        get_records("P37840", client=FixtureDisProtClient(tmp_path / "absent"))
    assert unavailable.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


def test_online_transport_native_scope_and_preaccess_validation(monkeypatch):
    from sabueso.tools.db import disprot

    calls = []

    def download(url, **options):
        calls.append((url, options))
        return io.BytesIO(json.dumps(native()).encode())

    monkeypatch.setattr(disprot, "urlopen", download)
    result = get_records("p37840", client=OnlineDisProtClient(timeout=3))
    assert result["query"] == {"accession": "P37840"}
    assert calls[0] == (
        disprot.URL + "?acc=P37840",
        {"timeout": 3, "expect_json": True},
    )
    with pytest.raises(ConnectorError):
        get_records("protein name", client=OnlineDisProtClient())
    assert len(calls) == 1


def test_archive_replay_keeps_original_time_and_source_scope(tmp_path, monkeypatch):
    from sabueso import RetrievalArchive
    from sabueso.tools.db import _http

    class Response(io.BytesIO):
        status = 200
        headers = Message()

    monkeypatch.setattr(
        _http,
        "_urlopen",
        lambda request, timeout: Response(json.dumps(native()).encode()),
    )
    archive = RetrievalArchive(tmp_path / "disprot.db")
    with archive.recording():
        original = get_records("P37840")

    def forbidden(*args, **kwargs):
        raise AssertionError("Replay must not query the source")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        replay = get_records("P37840")
    assert replay["record"] == original["record"]
    assert replay["retrieved_at"] == original["retrieved_at"]
    assert replay["truncated"] is True
    assert map_disorder_regions(replay) == map_disorder_regions(original)
    (access,) = replay["acquisition_trace"]["records"]
    assert access["network_attempts"] == 0
    assert access["outcome"] == "received"


def test_missing_api_route_is_failure_not_biological_absence(monkeypatch):
    from sabueso.tools.db import _http

    def missing(request, timeout):
        raise HTTPError(request.full_url, 404, "API route missing", Message(), None)

    monkeypatch.setattr(_http, "_urlopen", missing)
    with pytest.raises(ConnectorError) as failed:
        get_records("P37840")
    (access,) = failed.value.acquisition_trace["records"]
    assert access["outcome"] == "failed"
