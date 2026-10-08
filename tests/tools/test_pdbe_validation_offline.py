"""Native validation metrics retain structure scope, population gaps and access history."""

import copy
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ConnectorError
from sabueso.mappings.pdbe_validation import (
    map_global_percentiles,
    validate_percentiles,
)
from sabueso.tools.db.pdbe_validation import (
    FixturePDBeValidationClient,
    get_global_percentiles,
)

PATH = Path("temp_data/pdbe_validation/global_percentiles__1hti.json")


def native():
    return json.loads(PATH.read_text(encoding="utf-8"))


def metric(payload):
    return payload["1hti"]["clashscore"]


class Client:
    def __init__(self, payload):
        self.payload = payload

    def global_percentiles(self, identifier):
        return {"record": self.payload, "retrieved_at": "2026-01-01", "version": None}


@pytest.mark.parametrize("identifier, count", [("1HTI", 3), ("1CBS", 5)])
def test_native_metrics_are_structure_bound_and_detached(identifier, count):
    envelope = get_global_percentiles(identifier, client=FixturePDBeValidationClient())
    before = copy.deepcopy(envelope)
    assertions = map_global_percentiles(envelope)
    assert len(assertions) == count and envelope == before
    assert envelope["version"] is None and envelope["truncated"] is False
    for assertion in assertions:
        value = assertion["asserted_value"]
        assert assertion["subject_ref"] == "pdb:" + identifier
        assert value["pdb_id"] == identifier
        assert (
            value["native_values"]
            == envelope["record"][identifier.lower()][value["metric"]]
        )
        assert assertion["source"]["name"] == "PDBe Validation"
        assert assertion["source"]["version"] is None
        assert (
            assertion["field_path"] == "structures.validation.pdbe_global_percentiles"
        )
        assert "evidence_class" not in value and "knowledge_class" not in value
        assert (
            assertion["source_metadata"]["comparison_population"]
            == "counts_and_revision_not_stated"
        )
    (access,) = envelope["acquisition_trace"]["records"]
    assert access["source"] == "PDBe Validation" and access["count"] == count
    assert access["access"] == "supplied_file" and access["network_attempts"] == 0
    assert access["retrieved_at"] is None and access["source_version"]["value"] is None
    assert (
        "validation_pipeline_and_comparison_population_revisions_not_stated"
        in access["bibliography_gaps"]
    )
    assertions[0]["asserted_value"]["native_values"]["rawvalue"] = 999
    assertions[0]["source_metadata"]["snapshot_receipt"].clear()
    assert envelope == before


def test_zero_outliers_and_perfect_percentiles_do_not_mean_missing():
    envelope = get_global_percentiles("1cbs", client=FixturePDBeValidationClient())
    values = {
        a["asserted_value"]["metric"]: a["asserted_value"]["native_values"]
        for a in map_global_percentiles(envelope)
    }
    assert values["percent-RSRZ-outliers"] == {
        "rawvalue": 0.0,
        "absolute": 100.0,
        "relative": 100.0,
    }
    assert values["DCC_Rfree"]["rawvalue"] == 0.1871
    tim = get_global_percentiles("1hti", client=FixturePDBeValidationClient())
    assert "percent-RSRZ-outliers" not in tim["record"]["1hti"]
    assert len(map_global_percentiles(tim)) == 3  # Missing metrics are not filled in.


def test_unknown_metric_optional_relative_and_extra_native_context_survive():
    payload = native()
    payload["1hti"]["future-provider-metric"] = {
        "rawvalue": -7.0,
        "absolute": 0,
        "method": "literal native context",
    }
    del metric(payload)["relative"]
    envelope = get_global_percentiles("1hti", client=Client(payload))
    values = {
        a["asserted_value"]["metric"]: a["asserted_value"]["native_values"]
        for a in map_global_percentiles(envelope)
    }
    assert values == payload["1hti"] and "relative" not in values["clashscore"]
    assert values["future-provider-metric"]["rawvalue"] == -7.0
    assert (
        envelope["acquisition_trace"]["records"] == []
    )  # Custom access is unobserved.


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.clear(),
        lambda p: p.update(other={}),
        lambda p: p.update({"1hti": None}),
        lambda p: p.update({"1hti": []}),
        lambda p: p["1hti"].update({"": metric(p)}),
        lambda p: p["1hti"].update({"clashscore": None}),
        lambda p: metric(p).pop("rawvalue"),
        lambda p: metric(p).pop("absolute"),
        lambda p: metric(p).update(rawvalue=None),
        lambda p: metric(p).update(rawvalue=True),
        lambda p: metric(p).update(rawvalue="14.12"),
        lambda p: metric(p).update(rawvalue=float("nan")),
        lambda p: metric(p).update(absolute=-0.1),
        lambda p: metric(p).update(absolute=100.1),
        lambda p: metric(p).update(absolute=True),
        lambda p: metric(p).update(absolute=None),
        lambda p: metric(p).update(relative=-1),
        lambda p: metric(p).update(relative=101),
        lambda p: metric(p).update(relative=None),
        lambda p: metric(p).update(relative=True),
        lambda p: metric(p).update(relative=float("inf")),
        lambda p: metric(p).update(context=float("nan")),
    ],
)
def test_invalid_identity_values_or_percentiles_never_become_claims(change):
    payload = native()
    change(payload)
    with pytest.raises(ConnectorError):
        get_global_percentiles("1hti", client=Client(payload))
    with pytest.raises(ConnectorError):
        validate_percentiles(payload, "1hti")


@pytest.mark.parametrize(
    "identifier", ["../1hti", "pdb:1hti", "1hti/extra", "pdb_00001hti", "", None]
)
def test_invalid_pdb_identity_is_refused_before_access(identifier):
    class Forbidden:
        def global_percentiles(self, identifier):
            raise AssertionError("Invalid IDs must not access a source")

    with pytest.raises(Exception) as caught:
        get_global_percentiles(identifier, client=Forbidden())
    assert not isinstance(caught.value, AssertionError)


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(source="Other"),
        lambda e: e.update(kind="per_residue"),
        lambda e: e.update(query={"pdb_id": "2hti"}),
        lambda e: e.update(version="2.10.9"),
        lambda e: e.update(truncated=True),
    ],
)
def test_wrong_subject_source_revision_or_scope_is_refused(change):
    envelope = get_global_percentiles("1hti", client=FixturePDBeValidationClient())
    change(envelope)
    with pytest.raises(ConnectorError):
        map_global_percentiles(envelope)


class Response(io.BytesIO):
    status = 200

    def __init__(self, raw):
        super().__init__(raw)
        self.headers = Message()
        self.headers["Content-Type"] = "application/json"


def test_explicit_empty_metrics_are_distinct_from_missing_fixture(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    monkeypatch.setattr(
        _http, "_urlopen", lambda request, timeout: Response(b'{"1hti":{}}')
    )
    envelope = get_global_percentiles("1hti")
    assert envelope["acquisition_trace"]["records"][0]["outcome"] == "empty"
    assert map_global_percentiles(envelope) == [] and envelope["truncated"] is False
    with pytest.raises(ConnectorError) as missing:
        get_global_percentiles("1hti", client=FixturePDBeValidationClient(tmp_path))
    assert missing.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


@pytest.mark.parametrize("status", [404, 422, 503])
def test_http_failure_is_never_relabelled_source_absence(status, monkeypatch):
    from sabueso.tools.db import _http

    def failed(request, timeout):
        raise HTTPError(request.full_url, status, "API failure", Message(), None)

    monkeypatch.setattr(_http, "_urlopen", failed)
    with pytest.raises(ConnectorError) as caught:
        get_global_percentiles("1hti")
    assert caught.value.acquisition_trace["records"][0]["outcome"] == "failed"


def test_malformed_wire_duplicate_keys_and_unrelated_subject_fail(monkeypatch):
    from sabueso.tools.db import _http

    for raw in (
        b'{"1hti":{},"1hti":{}}',
        b'{"2hti":{}}',
        b'{"1hti":{"clashscore":{"rawvalue":NaN,"absolute":50}}}',
    ):
        monkeypatch.setattr(_http, "_urlopen", lambda request, timeout: Response(raw))
        with pytest.raises(ConnectorError) as caught:
            get_global_percentiles("1hti")
        assert caught.value.acquisition_trace["records"][0]["outcome"] == "failed"


def test_native_online_archive_replay_preserves_time_and_support(tmp_path, monkeypatch):
    from sabueso.tools.db import _http

    calls = []

    def download(request, timeout):
        calls.append(request.full_url)
        return Response(PATH.read_bytes())

    monkeypatch.setattr(_http, "_urlopen", download)
    archive = RetrievalArchive(tmp_path / "validation.db")
    with archive.recording():
        original = get_global_percentiles("1hti")

    def forbidden(*args, **kwargs):
        raise AssertionError("Replay must not access the network")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        replayed = get_global_percentiles("1hti")
    assert calls == [
        "https://www.ebi.ac.uk/pdbe/api/validation/global-percentiles/entry/1hti"
    ]
    assert original["retrieved_at"] == replayed["retrieved_at"]
    assert map_global_percentiles(original) == map_global_percentiles(replayed)
    assert original["acquisition_trace"]["records"][0]["network_attempts"] == 1
    assert replayed["acquisition_trace"]["records"][0]["access"] == "replay"
