"""Native aggregate support, opposing effects, exact queries and failed access."""

import copy
import gzip
import hashlib
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import retention, source_terms
from sabueso.mappings.omnipath import FLAGS, map_interactions, response_query
from sabueso.tools.db.omnipath import (
    URL,
    FixtureOmniPathClient,
    SnapshotOmniPathClient,
    get_interactions,
)

PATH = Path("temp_data/omnipath/interactions__P60174.json")
TARGET = "P60174"


def native():
    return json.loads(PATH.read_bytes())


class Client:
    def __init__(self, payload, **context):
        self.payload, self.context = payload, context

    def interactions(self, identifier):
        return {
            "record": self.payload,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def metadata():
    return {
        "source": "OmniPath",
        "kind": "interactions",
        "query": response_query(TARGET),
    }


def test_native_row_preserves_signs_consensus_support_and_original_time():
    raw = PATH.read_bytes()
    assert len(raw) == 288
    assert (
        hashlib.sha256(raw).hexdigest()
        == "6f5a542228162871e4645e3f7897eba1bc660fb4c9ffc7bf75d9f852030d4e6a"
    )
    envelope = get_interactions("p60174", client=FixtureOmniPathClient())
    before = copy.deepcopy(envelope)
    (assertion,) = map_interactions(envelope)
    row = native()[0]
    assert assertion["asserted_value"] == row
    assert row["sources"] == ["SPIKE", "SPIKE_LC"]
    assert row["references"] == "SPIKE:17959595;SPIKE_LC:17959595"
    assert row["is_inhibition"] and not row["is_stimulation"]
    assert assertion["subject_ref"].startswith("omnipath:interaction:sha256:")
    assert assertion["source"]["version"] is None and assertion["retrieved_at"] is None
    assert assertion["acquisition"] == {"method": "database"}
    assert assertion["source_metadata"]["native_row"] == row
    assert (
        "knowledge_class" not in assertion
        and "protein_ref" not in assertion["asserted_value"]
    )
    trace = envelope["acquisition_trace"]["records"]
    assert len(trace) == 1
    assert trace[0]["count"] == 1 and trace[0]["network_attempts"] == 0
    assert (
        trace[0]["snapshot_receipt"]["document_sha256"]
        == hashlib.sha256(raw).hexdigest()
    )
    assert trace[0]["retrieved_at"] is None
    assertion["asserted_value"]["sources"].clear()
    assertion["source_metadata"]["native_row"].clear()
    assert envelope == before


def test_opposing_effects_consensus_conflicts_duplicates_and_future_context_survive():
    p = native()
    p[0].update(
        is_stimulation=True, consensus_stimulation=True, consensus_inhibition=False
    )
    p[0]["future_resource_context"] = {"literal": None}
    p[0]["sources"] += ["SPIKE", "future_resource"]
    p[0]["references"] += ";future_resource:17959595"
    p += [copy.deepcopy(p[0]), copy.deepcopy(p[0])]
    p[2]["is_directed"] = False
    a = map_interactions(get_interactions(TARGET, client=Client(p)))
    assert len(a) == len({r["id"] for r in a}) == 3
    assert len({r["subject_ref"] for r in a}) == 1
    assert [r["source_metadata"]["native_row_index"] for r in a] == [0, 1, 2]
    for assertion, row in zip(a, p):
        assert assertion["asserted_value"] == row
        assert assertion["asserted_value"]["is_stimulation"]
        assert assertion["asserted_value"]["is_inhibition"]
        assert (
            "not_strict_dataset_filtered"
            in assertion["source_metadata"]["mapping_scope"]["support"]
        )
    assert a[0]["asserted_value"] == a[1]["asserted_value"]


def test_either_native_partner_and_self_interaction_are_valid_without_reordering():
    p = native()
    p[0]["source"], p[0]["target"] = p[0]["target"], p[0]["source"]
    p.append({**copy.deepcopy(p[0]), "target": TARGET})
    a = map_interactions(get_interactions(TARGET, client=Client(p)))
    assert [r["asserted_value"] for r in a] == p
    assert a[0]["subject_ref"] != a[1]["subject_ref"]


def test_identical_rows_from_distinct_queries_keep_independent_query_support():
    a = map_interactions(get_interactions(TARGET, client=Client(native())))[0]
    b = map_interactions(get_interactions("P29466", client=Client(native())))[0]
    assert a["asserted_value"] == b["asserted_value"]
    assert a["subject_ref"] == b["subject_ref"]
    assert a["id"] != b["id"]
    assert a["source_metadata"]["query"] != b["source_metadata"]["query"]


@pytest.mark.parametrize("partner", ["P601740", "P60174-2", "p60174", "TPI1"])
def test_labels_substrings_and_version_stripping_cannot_satisfy_query(partner):
    p = native()
    p[0]["target"] = partner
    p[0]["target_genesymbol"] = TARGET
    with pytest.raises(ConnectorError):
        get_interactions(TARGET, client=Client(p))


@pytest.mark.parametrize("flag", FLAGS)
@pytest.mark.parametrize("value", [None, 1, "true"])
def test_native_boolean_flags_are_not_coerced(flag, value):
    p = native()
    p[0][flag] = value
    with pytest.raises(ConnectorError):
        get_interactions(TARGET, client=Client(p))


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", ""),
        ("source", None),
        ("target", " P60174"),
        ("sources", "SPIKE"),
        ("sources", [None]),
        ("sources", [""]),
        ("references", None),
        ("references", ["SPIKE:17959595"]),
        ("references", "17959595"),
        ("extra", float("inf")),
    ],
)
def test_malformed_native_context_is_not_silently_dropped(key, value):
    p = native()
    p.append(copy.deepcopy(p[0]))
    p[1][key] = value
    with pytest.raises(ConnectorError):
        get_interactions(TARGET, client=Client(p))


@pytest.mark.parametrize(
    "payload", [None, {}, "", [None], [["Unknown argument: strict_evidences"]]]
)
def test_application_errors_and_wrong_shapes_are_not_empty_results(payload):
    with pytest.raises(ConnectorError):
        get_interactions(TARGET, client=Client(payload))


def test_native_empty_and_missing_support_are_not_negative_biological_claims():
    e = get_interactions(TARGET, client=Client([]))
    assert map_interactions(e) == []
    p = native()
    p[0].update(sources=[], references="")
    (a,) = map_interactions(get_interactions(TARGET, client=Client(p)))
    assert a["asserted_value"]["sources"] == []
    assert a["asserted_value"]["references"] == ""


@pytest.mark.parametrize(
    "identifier", ["TPI1", "P60174-2", " P60174", "P60174?x", 60174, True]
)
def test_invalid_selection_never_reaches_client_even_with_skip(identifier):
    class Forbidden:
        def interactions(self, identifier):
            pytest.fail("Invalid selection reached client")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_interactions(identifier, client=Forbidden(), skip_digestion=True)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "SIGNOR"),
        ("kind", "pathways"),
        ("version", "2026-10-06"),
        ("truncated", True),
        ("truncated", None),
        ("query", {**response_query(TARGET), "organisms": 10090}),
        ("query", {**response_query(TARGET), "organisms": 9606.0}),
        ("query", {**response_query(TARGET), "license": "ignore"}),
        ("query", {**response_query(TARGET), "resources": "SPIKE"}),
    ],
)
def test_mapper_rechecks_query_scope_without_orthology_or_license_bypass(key, value):
    e = get_interactions(TARGET, client=FixtureOmniPathClient())
    e[key] = value
    with pytest.raises(ConnectorError):
        map_interactions(e)


@pytest.mark.parametrize(
    "context",
    [
        {"version": "2026"},
        {"truncated": True},
        {"truncated": None},
        {"source": "other"},
        {"kind": "pathways"},
        {"query": {**response_query(TARGET), "license": "commercial"}},
    ],
)
def test_client_cuts_and_fabricated_revision_are_rejected(context):
    with pytest.raises(ConnectorError):
        get_interactions(TARGET, client=Client(native(), **context))


@pytest.mark.parametrize("compressed", [False, True])
def test_snapshot_original_byte_hash_time_terms_and_binding(tmp_path, compressed):
    raw = PATH.read_bytes()
    raw = gzip.compress(raw) if compressed else raw
    p = tmp_path / ("native.json.gz" if compressed else "native.json")
    p.write_bytes(raw)
    m = metadata()
    m.update(retrieved_at="2026-10-06T12:00:00+00:00", terms={"licence": "CC-BY-4.0"})
    c = SnapshotOmniPathClient(
        p, source_metadata=m, expected_sha256=hashlib.sha256(raw).hexdigest()
    )
    m["query"]["partners"] = "P29466"
    e = get_interactions(TARGET, client=c)
    assert e["record"] == native() and e["retrieved_at"] == "2026-10-06T12:00:00+00:00"
    assert e["snapshot_receipt"]["declared_terms"] == {"licence": "CC-BY-4.0"}
    assert e["snapshot_receipt"]["source_access_observed"] is False
    assert e["snapshot_receipt"]["document_sha256"] == hashlib.sha256(raw).hexdigest()
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_interactions(
            TARGET,
            client=SnapshotOmniPathClient(
                p, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "motifs"),
        ("query", response_query("P29466")),
        ("version", "2026"),
    ],
)
def test_snapshot_binding_cannot_be_replaced(tmp_path, key, value):
    p = tmp_path / "native.json"
    p.write_bytes(PATH.read_bytes())
    m = metadata()
    m[key] = value
    with pytest.raises(ConnectorError):
        get_interactions(TARGET, client=SnapshotOmniPathClient(p, source_metadata=m))


@pytest.mark.parametrize(
    "raw",
    [
        b'[{"source":"P29466","source":"P60174"}]',
        b"[NaN]",
        b"\xff",
        b"<html>blocked</html>",
    ],
)
def test_invalid_original_json_bytes_are_rejected(tmp_path, raw):
    p = tmp_path / "native.json"
    p.write_bytes(raw)
    with pytest.raises(ConnectorError):
        get_interactions(
            TARGET, client=SnapshotOmniPathClient(p, source_metadata=metadata())
        )


def test_missing_files_and_unavailable_fixture_queries_are_not_empty(tmp_path):
    for identifier, client in [
        (TARGET, FixtureOmniPathClient(tmp_path)),
        ("P29466", FixtureOmniPathClient()),
        (
            TARGET,
            SnapshotOmniPathClient(
                tmp_path / "missing.json", source_metadata=metadata()
            ),
        ),
    ]:
        with pytest.raises(ConnectorError):
            get_interactions(identifier, client=client)


@pytest.mark.parametrize("status", [404, 429, 503])
def test_http_failure_is_not_a_source_negative(monkeypatch, status):
    from sabueso.tools.db import _http

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, status, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_interactions(TARGET)


def test_http_200_application_error_has_failure_acquisition_trace(monkeypatch):
    from sabueso.tools.db import _http

    def wire(request, **kwargs):
        response = io.BytesIO(b'[["Unknown argument: strict_evidences"]]')
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = "application/json"
        return response

    monkeypatch.setattr(_http, "_urlopen", wire)
    with pytest.raises(ConnectorError) as caught:
        get_interactions(TARGET)
    assert caught.value.acquisition_trace["records"][0]["outcome"] == "failed"


def test_one_get_and_archive_replay_keep_time_support_and_resource_rights(
    monkeypatch, tmp_path
):
    from sabueso.tools.db import _http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(PATH.read_bytes())
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = "application/json"
        return response

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "omnipath.db")
    with archive.recording():
        first = get_interactions(TARGET)

    def forbidden(*args, **kwargs):
        pytest.fail("Replay performed a new request")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_interactions(TARGET)
    assert len(calls) == 1 and calls[0].startswith(URL)
    assert parse_qs(urlsplit(calls[0]).query) == {
        k: [str(v)] for k, v in response_query(TARGET).items()
    }
    assert first["record"] == second["record"] == native()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert (
        first["download_sha256"]
        == second["download_sha256"]
        == hashlib.sha256(PATH.read_bytes()).hexdigest()
    )
    assert map_interactions(first) == map_interactions(second)
    assert first["acquisition_trace"]["records"][0]["network_attempts"] == 1
    assert second["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert source_terms()["OmniPath"]["licence"] == "NOT-STATED"
    assert retention("OmniPath")["share"] == "unknown"
