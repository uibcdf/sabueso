"""Native association subjects, page boundaries, qualified inputs and replay."""

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
from sabueso.core.terms import source_terms
from sabueso.mappings.monarch import map_associations, response_query
from sabueso.tools.db.monarch import (
    URL,
    FixtureMonarchClient,
    SnapshotMonarchClient,
    get_associations,
)

PATH = Path("temp_data/monarch/associations__HGNC_12009__limit2__offset0.json")
TARGET = "HGNC:12009"


def native():
    return json.loads(PATH.read_bytes())


class Client:
    def __init__(self, record, **context):
        self.record, self.context = record, context

    def associations(self, identifier, limit, offset):
        return {
            "record": self.record,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def read(record, **context):
    return get_associations(TARGET, limit=2, client=Client(record, **context))


def metadata():
    return {
        "source": "Monarch",
        "kind": "associations",
        "query": response_query(TARGET, 2, 0),
    }


def test_native_partial_page_keeps_gene_relationships_and_all_original_support():
    raw = PATH.read_bytes()
    assert len(raw) == 5205
    assert (
        hashlib.sha256(raw).hexdigest()
        == "0456c3b120f0922eab4a0508f4169ac253ba973a5191bce625da65cc2607e858"
    )
    e = get_associations(TARGET, limit=2, client=FixtureMonarchClient())
    before = copy.deepcopy(e)
    a = map_associations(e)
    assert len(a) == len({s["id"] for s in a}) == 2
    assert e["record"] == native() and e["truncated"] is True
    for s, row in zip(a, native()["items"]):
        assert s["asserted_value"] == s["source_metadata"]["native_association"] == row
        assert s["subject_ref"] == "monarch:association:" + row["id"]
        assert row["subject"] == TARGET and row["original_subject"] == "NCBIGene:7167"
        assert row["subject_category"] == "biolink:Gene"
        assert row["predicate"] == "biolink:interacts_with"
        assert row["primary_knowledge_source"] == "infores:biogrid"
        assert row["aggregator_knowledge_source"] == ["infores:monarchinitiative"]
        assert row["has_evidence"] == ["ECO:0000172"] and row["evidence_count"] == 2
        assert row["publications"] == ["PMID:26344197"] and row["negated"] is None
        assert s["source"]["version"] is s["retrieved_at"] is None
        assert s["acquisition"] == {"method": "database"}
        assert "protein_ref" not in row and "evidence_class" not in row
        assert s["source_metadata"]["page"] == {
            "limit": 2,
            "offset": 0,
            "total": 232,
            "returned": 2,
            "partial": True,
        }
    trace = e["acquisition_trace"]["records"]
    assert len(trace) == 1 and trace[0]["count"] == 2
    assert trace[0]["network_attempts"] == 0 and trace[0]["truncated"] is True
    assert (
        trace[0]["snapshot_receipt"]["document_sha256"]
        == hashlib.sha256(raw).hexdigest()
    )
    a[0]["asserted_value"]["has_evidence"].clear()
    a[0]["source_metadata"]["native_association"].clear()
    assert e == before


def test_disease_category_negation_null_missing_and_qualifiers_remain_independent():
    p = native()
    p["items"][0].update(
        object="MONDO:0000001",
        object_category="biolink:Disease",
        negated=True,
        qualifiers=["native:qualifier"],
        knowledge_level="future_level",
        agent_type="future_agent",
        has_count=0,
        has_total=0,
    )
    p["items"][1].pop("negated")
    p["items"][1].update(
        primary_knowledge_source=None,
        aggregator_knowledge_source=[],
        publications=[],
        has_evidence=None,
        future_context={"literal": None},
    )
    a = map_associations(read(p))
    assert len(a) == 2 and a[0]["asserted_value"]["negated"] is True
    assert a[0]["asserted_value"]["has_count"] == 0
    assert "negated" not in a[1]["asserted_value"]
    assert a[1]["asserted_value"]["has_evidence"] is None
    assert a[0]["asserted_value"]["knowledge_level"] == "future_level"
    assert [s["asserted_value"] for s in a] == p["items"]


def test_duplicate_ids_and_conflicting_assertions_are_not_overwritten():
    p = native()
    p["items"][1] = copy.deepcopy(p["items"][0])
    a = map_associations(read(p))
    assert a[0]["id"] != a[1]["id"] and a[0]["subject_ref"] == a[1]["subject_ref"]
    p["items"][1].update(negated=True, predicate="biolink:causes")
    b = map_associations(read(p))
    assert len(b) == 2 and b[0]["asserted_value"]["negated"] is None
    assert b[1]["asserted_value"]["negated"] is True


def test_full_empty_and_out_of_range_pages_have_distinct_coverage():
    p = native()
    p["total"] = 2
    assert read(p)["truncated"] is False
    p.update(items=[], total=0)
    e = read(p)
    assert e["truncated"] is False and map_associations(e) == []
    p.update(offset=500, total=232)
    e = get_associations(TARGET, limit=2, offset=500, client=Client(p))
    assert e["truncated"] is True and map_associations(e) == []
    assert e["record"]["total"] == 232


def test_manual_offset_and_distinct_pages_preserve_query_support():
    p = native()
    p["offset"] = 2
    a = map_associations(read(native()))
    b = map_associations(get_associations(TARGET, limit=2, offset=2, client=Client(p)))
    assert a[0]["asserted_value"] == b[0]["asserted_value"]
    assert a[0]["id"] != b[0]["id"]
    assert b[0]["source_metadata"]["page"]["offset"] == 2


@pytest.mark.parametrize(
    "subject", ["HGNC:120090", "HGNC:12009.1", "NCBIGene:7167", "hgnc:12009"]
)
def test_ancestors_labels_and_aliases_do_not_bind_direct_subject(subject):
    p = native()
    p["items"][0]["subject"] = subject
    p["items"][0].update(subject_label=TARGET, subject_closure=[TARGET])
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize(
    "key,value",
    [
        ("id", None),
        ("subject", ""),
        ("object", {}),
        ("predicate", "interacts_with"),
        ("knowledge_level", None),
        ("agent_type", None),
        ("negated", "false"),
        ("negated", 0),
        ("primary_knowledge_source", []),
        ("publications", "PMID:26344197"),
        ("has_evidence", [None]),
        ("qualifiers", {}),
        ("aggregator_knowledge_source", [""]),
        ("subject_taxon", 9606),
        ("evidence_count", -1),
        ("has_count", True),
        ("has_total", 1.5),
        ("future_context", float("inf")),
    ],
)
def test_invalid_native_context_is_rejected_before_mapping(key, value):
    p = native()
    p["items"][1][key] = value
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize(
    "key,value",
    [
        ("limit", 3),
        ("limit", True),
        ("offset", 2),
        ("offset", 0.0),
        ("total", -1),
        ("total", 1),
        ("total", None),
        ("items", {}),
        ("items", [None]),
    ],
)
def test_page_counts_and_requested_scope_cannot_be_guessed(key, value):
    p = native()
    p[key] = value
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize(
    "payload", [None, {}, {"detail": "blocked"}, {"items": []}, [["error"]]]
)
def test_missing_application_or_non_native_payload_is_not_an_empty_page(payload):
    with pytest.raises(ConnectorError):
        read(payload)


def test_empty_page_before_declared_total_is_inconsistent():
    p = native()
    p["items"] = []
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize(
    "arguments",
    [
        {"identifier": "TPI1"},
        {"identifier": "HGNC:12009?x"},
        {"identifier": "HGNC:12009/"},
        {"limit": 0},
        {"limit": 501},
        {"limit": True},
        {"limit": 2.0},
        {"offset": -1},
        {"offset": True},
        {"offset": 0.0},
    ],
)
def test_invalid_request_never_reaches_client_even_with_skip(arguments):
    class Forbidden:
        def associations(self, *args):
            pytest.fail("Invalid request reached client")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_associations(
            **{"identifier": TARGET, "limit": 2, **arguments},
            client=Forbidden(),
            skip_digestion=True,
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "entity"),
        ("version", "0.1.0"),
        ("truncated", False),
        ("truncated", None),
        ("query", {**response_query(TARGET, 2, 0), "direct": "false"}),
    ],
)
def test_mapping_refuses_wrong_source_revision_cut_or_ancestor_scope(key, value):
    e = read(native())
    e[key] = value
    with pytest.raises(ConnectorError):
        map_associations(e)


@pytest.mark.parametrize(
    "context",
    [
        {"version": "0.1.0"},
        {"truncated": False},
        {"truncated": None},
        {"query": response_query("HGNC:3465", 2, 0)},
        {"query": {**response_query(TARGET, 2, 0), "limit": 2.0}},
    ],
)
def test_client_revision_or_coverage_cannot_override_native_scope(context):
    with pytest.raises(ConnectorError):
        read(native(), **context)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_json_gzip_keep_original_hash_time_terms_and_no_access_credit(
    tmp_path, compressed
):
    raw = PATH.read_bytes()
    raw = gzip.compress(raw) if compressed else raw
    p = tmp_path / ("native.json.gz" if compressed else "native.json")
    p.write_bytes(raw)
    m = metadata()
    m.update(retrieved_at="2026-10-07T12:00:00+00:00", terms={"licence": "MIT"})
    c = SnapshotMonarchClient(
        p, source_metadata=m, expected_sha256=hashlib.sha256(raw).hexdigest()
    )
    m["query"]["subject"] = "HGNC:3465"
    e = get_associations(TARGET, limit=2, client=c)
    assert e["record"] == native() and e["retrieved_at"] == "2026-10-07T12:00:00+00:00"
    assert e["snapshot_receipt"]["declared_terms"] == {"licence": "MIT"}
    assert e["snapshot_receipt"]["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert e["snapshot_receipt"]["source_access_observed"] is False
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_associations(
            TARGET,
            limit=2,
            client=SnapshotMonarchClient(
                p, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "entity"),
        ("version", "2026"),
        ("query", response_query(TARGET, 2, 2)),
    ],
)
def test_snapshot_scope_is_exact(tmp_path, key, value):
    p = tmp_path / "native.json"
    p.write_bytes(PATH.read_bytes())
    m = metadata()
    m[key] = value
    with pytest.raises(ConnectorError):
        get_associations(
            TARGET, limit=2, client=SnapshotMonarchClient(p, source_metadata=m)
        )


@pytest.mark.parametrize(
    "raw",
    [b'{"items":[],"items":[]}', b'{"extra":NaN}', b"\xff", b"<html>blocked</html>"],
)
def test_invalid_original_json_bytes_fail_explicitly(tmp_path, raw):
    p = tmp_path / "native.json"
    p.write_bytes(raw)
    with pytest.raises(ConnectorError):
        get_associations(
            TARGET, limit=2, client=SnapshotMonarchClient(p, source_metadata=metadata())
        )


def test_missing_snapshot_fixture_and_unavailable_page_are_not_empty(tmp_path):
    for c, limit in [
        (FixtureMonarchClient(tmp_path), 2),
        (FixtureMonarchClient(), 20),
        (
            SnapshotMonarchClient(
                tmp_path / "missing.json", source_metadata=metadata()
            ),
            2,
        ),
    ]:
        with pytest.raises(ConnectorError):
            get_associations(TARGET, limit=limit, client=c)


@pytest.mark.parametrize("status", [404, 429, 503])
def test_http_failure_is_not_a_native_negative(monkeypatch, status):
    from sabueso.tools.db import _http

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, status, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_associations(TARGET, limit=2)


def test_one_get_replay_keeps_original_time_and_never_follows_pages_or_support(
    monkeypatch, tmp_path
):
    from sabueso.tools.db import _http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        r = io.BytesIO(PATH.read_bytes())
        r.status = 200
        r.headers = Message()
        r.headers["Content-Type"] = "application/json"
        return r

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "monarch.db")
    with archive.recording():
        first = get_associations(TARGET, limit=2)

    def forbidden(*args, **kwargs):
        pytest.fail("Replay followed a page or publication")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_associations(TARGET, limit=2)
    assert len(calls) == 1 and calls[0].startswith(URL)
    assert parse_qs(urlsplit(calls[0]).query) == {
        k: [str(v)] for k, v in response_query(TARGET, 2, 0).items()
    }
    assert (
        first["record"] == second["record"] == native()
        and first["retrieved_at"] == second["retrieved_at"]
    )
    assert (
        first["download_sha256"]
        == second["download_sha256"]
        == hashlib.sha256(PATH.read_bytes()).hexdigest()
    )
    assert map_associations(first) == map_associations(second)
    assert first["acquisition_trace"]["records"][0]["network_attempts"] == 1
    assert second["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert source_terms()["Monarch"]["licence"] == "NOT-STATED"
