"""TCDB literal accession selection, unbound rows and native export provenance."""

import copy
import gzip
import hashlib
import io
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import source_terms
from sabueso.mappings.tcdb import (
    URL,
    map_assignments,
    parse_assignments,
    response_query,
)
from sabueso.tools.db.tcdb import FixtureTCDBClient, SnapshotTCDBClient, get_assignments

PATH = Path("temp_data/tcdb/accession_assignments.tsv")


class Client:
    def __init__(self, record, **context):
        self.record, self.context = record, context

    def assignments(self, identifier):
        return {
            "record": self.record,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def read(text, identifier="Q39253", **context):
    return get_assignments(identifier, client=Client(text, **context))


def metadata(identifier="Q39253"):
    return {
        "source": "TCDB",
        "kind": "accession_assignments",
        "query": response_query(identifier),
    }


def test_native_export_preserves_full_table_blank_ids_and_six_component_system():
    raw = PATH.read_bytes()
    assert len(raw) == 486702
    assert (
        hashlib.sha256(raw).hexdigest()
        == "c59e2b2c5293e0f33e75bcc0bf89e0eb6988be54fb7f2121935749bda3feef8a"
    )
    e = get_assignments("Q39253", client=FixtureTCDBClient())
    before = copy.deepcopy(e)
    a = map_assignments(e)
    assert e["record"].encode() == raw and e["truncated"] is False
    assert [s["asserted_value"]["tc_system"] for s in a] == [
        "2.A.19.2.3",
        "1.A.1.9.2.3",
    ]
    assert [s["source_metadata"]["native_row"]["line"] for s in a] == [3138, 23892]
    assert all(s["subject_ref"] == "tcdb:accession:Q39253" for s in a)
    for s in a:
        assert s["source"]["version"] is s["retrieved_at"] is None
        assert s["source_metadata"]["received_export_count"] == 24956
        assert s["source_metadata"]["received_unbound_count"] == 13
        assert set(s["asserted_value"]) == {"accession_literal", "tc_system"}
        assert (
            "namespace_unspecified" in s["source_metadata"]["mapping_scope"]["identity"]
        )
    rows = parse_assignments(e["record"])
    assert rows[0]["fields"] == ["A0CIB0", "1.A.17.1.13"]
    assert sum(not r["fields"][0] for r in rows) == 13
    trace = e["acquisition_trace"]["records"][0]
    assert trace["count"] == 2 and trace["received_export_count"] == 24956
    assert trace["received_unbound_count"] == 13 and trace["network_attempts"] == 0
    assert trace["access"] == "supplied_file" and trace["retrieved_at"] is None
    assert any(b["id"] == "url:https://tcdb.org/" for b in trace["bibliography"])
    assert source_terms()["TCDB"]["licence"] == "NOT-STATED"
    a[0]["asserted_value"].clear()
    a[1]["source_metadata"]["native_row"]["fields"].clear()
    assert e == before


def test_versioned_non_uniprot_identifiers_and_case_are_exact_without_namespace_guess():
    e = get_assignments("ATE86338.1", client=FixtureTCDBClient())
    a = map_assignments(e)
    assert [s["asserted_value"]["tc_system"] for s in a] == [
        "1.M.1.3.37",
        "1.M.1.4.1.1",
    ]
    assert all(s["subject_ref"] == "tcdb:accession:ATE86338.1" for s in a)
    lower = map_assignments(get_assignments("q15049", client=FixtureTCDBClient()))
    assert (
        len(lower) == 1 and lower[0]["asserted_value"]["accession_literal"] == "q15049"
    )
    assert not map_assignments(get_assignments("Q15049", client=FixtureTCDBClient()))
    assert not map_assignments(get_assignments("ATE86338", client=FixtureTCDBClient()))


def test_native_identical_pairs_keep_independent_occurrence_ids():
    a = map_assignments(get_assignments("OLS27678", client=FixtureTCDBClient()))
    assert len(a) == 2 and a[0]["asserted_value"] == a[1]["asserted_value"]
    assert a[0]["id"] != a[1]["id"]
    assert (
        a[0]["source_metadata"]["native_row"]["line"]
        != a[1]["source_metadata"]["native_row"]["line"]
    )


def test_not_listed_selection_is_distinct_from_unavailable_or_empty_export():
    e = get_assignments("P60174", client=FixtureTCDBClient())
    assert map_assignments(e) == [] and e["record"] == PATH.read_text()
    trace = e["acquisition_trace"]["records"][0]
    assert trace["outcome"] == "not_found" and trace["received_export_count"] == 24956
    assert trace["truncated"] is False
    with pytest.raises(ConnectorError):
        read("")


def test_independent_multiple_assignments_blank_rows_and_line_endings_survive():
    text = "Query.1\t1.A.1.1.1\r\n\t9.A.22.1.8\r\nQuery.1\t2.A.2.2.2\r\nother\t1.A.1.1.1\r\nQuery.1\t1.A.1.1.1\r\n"
    e = read(text, "Query.1")
    a = map_assignments(e)
    assert e["record"] == text and len(a) == 3
    assert [s["source_metadata"]["native_row"]["line"] for s in a] == [1, 3, 5]
    assert len({s["id"] for s in a}) == 3
    assert all(s["source_metadata"]["received_unbound_count"] == 1 for s in a)


def test_full_export_hash_distinguishes_changed_support_outside_selection():
    a = map_assignments(read("Q39253\t1.A.1.1.1\nother\t2.A.2.2.2\n"))[0]
    b = map_assignments(read("Q39253\t1.A.1.1.1\nother\t3.A.3.3.3\n"))[0]
    assert a["asserted_value"] == b["asserted_value"] and a["id"] != b["id"]


@pytest.mark.parametrize(
    "text",
    [
        None,
        [],
        {},
        "",
        "\n",
        "<html>blocked</html>",
        "No results",
        "accession\ttc_id\n",
        "Q39253\t1.A.1.1.1\textra\n",
        "Q39253\t\n",
        "Q39253\t1.A.1\n",
        "Q39253\t1.A.1.1.1.1.1\n",
        " Q39253\t1.A.1.1.1\n",
        "Q39253\t1.A.1.1.1 \n",
        "Q39253\t1.A.1.1.1\nmalformed\n",
        "Q39253\t1.A.1.1.1\nunsafe/id\t2.A.2.2.2\n",
    ],
)
def test_non_native_error_header_or_malformed_late_rows_fail_before_selection(text):
    with pytest.raises(ConnectorError):
        read(text)


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        "",
        1,
        True,
        "Q39253/",
        "Q39253?",
        "Q39253 other",
        "Q39253:UniProt",
        "Q39253\nother",
        "A" * 129,
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_invalid_query_never_reaches_client(identifier, skip):
    class Forbidden:
        def assignments(self, identifier):
            pytest.fail("Invalid request reached client")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_assignments(identifier, client=Forbidden(), skip_digestion=skip)


@pytest.mark.parametrize(
    "context",
    [
        {"source": "other"},
        {"kind": "sequences"},
        {"version": "20261006"},
        {"query": response_query("q39253")},
        {"query": {"accession_literal": "Q39253"}},
        {"truncated": True},
        {"truncated": None},
    ],
)
def test_custom_client_cannot_override_source_query_revision_or_cut(context):
    with pytest.raises(ConnectorError):
        read("Q39253\t1.A.1.1.1\n", **context)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "sequences"),
        ("version", "20261006"),
        ("truncated", None),
        ("query", {"accession_literal": "Q39253"}),
        ("query", {"accession_literal": "Q39253", "export": "other"}),
    ],
)
def test_mapping_requires_original_source_and_explicit_export_query(key, value):
    e = read("Q39253\t1.A.1.1.1\n")
    e[key] = value
    with pytest.raises(ConnectorError):
        map_assignments(e)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_native_snapshot_keeps_original_bytes_case_time_and_terms(
    tmp_path, compressed
):
    raw = PATH.read_bytes()
    raw = gzip.compress(raw) if compressed else raw
    p = tmp_path / ("native.tsv.gz" if compressed else "native.tsv")
    p.write_bytes(raw)
    m = metadata()
    m.update(retrieved_at="2026-10-07T12:00:00+00:00", terms={"licence": "NOT-STATED"})
    client = SnapshotTCDBClient(
        p, source_metadata=m, expected_sha256=hashlib.sha256(raw).hexdigest().upper()
    )
    m["query"]["accession_literal"] = "other"
    e = get_assignments("Q39253", client=client)
    assert (
        e["record"] == PATH.read_text()
        and e["retrieved_at"] == "2026-10-07T12:00:00+00:00"
    )
    receipt = e["snapshot_receipt"]
    assert receipt["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["native_format"].startswith("TCDB_headerless")
    assert receipt["declared_terms"] == {"licence": "NOT-STATED"}
    assert receipt["source_access_observed"] is False
    assert map_assignments(e)[0]["source_metadata"]["snapshot_receipt"] == receipt
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_assignments(
            "Q39253",
            client=SnapshotTCDBClient(
                p, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "sequences"),
        ("version", "20261006"),
        ("query", response_query("q39253")),
        ("query", {**response_query("Q39253"), "taxon": 9606}),
    ],
)
def test_supplied_scope_cannot_change_source_kind_exact_case_export_or_revision(
    key, value
):
    m = metadata()
    m[key] = value
    with pytest.raises(ConnectorError):
        get_assignments("Q39253", client=SnapshotTCDBClient(PATH, source_metadata=m))


@pytest.mark.parametrize(
    "raw,compressed",
    [
        (b"\xff", False),
        (b"<html>failed</html>", False),
        (b"", False),
        (b"not gzip", True),
        (gzip.compress(b"Q39253\t1.A.1.1.1\n")[:-4], True),
    ],
)
def test_failed_encoding_or_compression_never_becomes_not_listed(
    tmp_path, raw, compressed
):
    p = tmp_path / ("native.tsv.gz" if compressed else "native.tsv")
    p.write_bytes(raw)
    with pytest.raises(ConnectorError):
        get_assignments(
            "Q39253", client=SnapshotTCDBClient(p, source_metadata=metadata())
        )


def test_missing_fixture_and_snapshot_are_not_not_listed(tmp_path):
    for c in [
        FixtureTCDBClient(tmp_path),
        SnapshotTCDBClient(tmp_path / "missing.tsv", source_metadata=metadata()),
    ]:
        with pytest.raises(ConnectorError):
            get_assignments("Q39253", client=c)


def test_failed_http_is_not_a_native_export_or_absence(monkeypatch):
    from sabueso.tools.db import _http

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 404, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_assignments("Q39253")


def test_one_export_get_and_archive_replay_never_fetch_sequence_or_family(
    monkeypatch, tmp_path
):
    from sabueso.tools.db import _http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        r = io.BytesIO(PATH.read_bytes())
        r.status = 200
        r.headers = Message()
        r.headers["Content-Type"] = "text/plain"
        return r

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "tcdb.db")
    with archive.recording():
        first = get_assignments("Q39253")

    def forbidden(*args, **kwargs):
        pytest.fail("Replay fetched a linked record")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_assignments("Q39253")
    assert calls == [URL]
    assert first["record"] == second["record"] == PATH.read_text()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert (
        first["download_sha256"]
        == second["download_sha256"]
        == hashlib.sha256(PATH.read_bytes()).hexdigest()
    )
    assert map_assignments(first) == map_assignments(second)
    assert second["acquisition_trace"]["records"][0]["network_attempts"] == 0
