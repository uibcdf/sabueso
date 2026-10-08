"""Native ProBiS catalog literals, duplicate chains, unknown columns and replay."""

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
from sabueso.core.terms import retention, source_terms, verdict
from sabueso.mappings.probis import (
    ARTIFACT,
    URL,
    map_chain_catalog,
    parse_chain_catalog,
    response_query,
)
from sabueso.tools.db.probis import (
    FixtureProBiSClient,
    SnapshotProBiSClient,
    get_chain_catalog,
)

PATH = Path("temp_data/probis/nrpdb-2015-07-31.txt")
ID = "5a2q.h"
ROW = "0\t1     \t5a2q\th\t1.0\n"
NATIVE = ROW + "7\t16    \t5a2q\th\t1.0\n" + "10\t2     \t2ww9\tL\t1.0\n"


class Client:
    def __init__(self, text, **context):
        self.text, self.context = text, context

    def chain_catalog(self, identifier):
        return {
            "record": self.text,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def read(text=NATIVE, identifier=ID, **context):
    return get_chain_catalog(identifier, client=Client(text, **context))


def metadata():
    return {
        "source": "ProBiS-Database",
        "kind": "reference_chain_catalog",
        "query": response_query(ID),
    }


def test_full_original_catalog_keeps_first_row_padding_gaps_and_three_repeated_chain_rows():
    raw = PATH.read_bytes()
    assert len(raw) == 1003440
    assert (
        hashlib.sha256(raw).hexdigest()
        == "2a4f3dd8f3f186f482541c51f177899cbf3c174cc21838dd6a9b185646c12c0a"
    )
    envelope = get_chain_catalog(ID, client=FixtureProBiSClient())
    before = copy.deepcopy(envelope)
    assert envelope["record"].encode() == raw and envelope["truncated"] is False
    assert envelope["version"] is envelope["retrieved_at"] is None
    rows = parse_chain_catalog(envelope["record"])
    assert len(rows) == 42270
    assert rows[0]["fields"] == ["0", "1     ", "12as", "A", "1.0"]
    assert rows[-1]["fields"][0] == "43577"  # Native column gaps are not reconstructed.
    assertions = map_chain_catalog(envelope)
    assert len(assertions) == len({a["id"] for a in assertions}) == 3
    assert [a["source_metadata"]["native_row"]["line"] for a in assertions] == [
        25465,
        25466,
        42034,
    ]
    assert [a["asserted_value"]["column_1_literal"] for a in assertions] == [
        "25714",
        "25715",
        "43270",
    ]
    assert [a["asserted_value"]["column_2_literal"] for a in assertions] == [
        "16    ",
        "16    ",
        "1     ",
    ]
    assert all(a["asserted_value"]["native_chain_literal"] == "h" for a in assertions)
    assert all(a["subject_ref"] == "probis:catalog_chain:5a2q.h" for a in assertions)
    assert all(
        a["field_path"] == "annotations.reference_chain_listing" for a in assertions
    )
    assert all(
        a["source_metadata"]["received_export_count"] == 42270 for a in assertions
    )
    trace = envelope["acquisition_trace"]["records"][0]
    assert (
        trace["outcome"] == "received"
        and trace["count"] == 3
        and trace["network_attempts"] == 0
    )
    assert trace["received_export_count"] == 42270
    assert any(
        b["id"] == "url:http://probis.cmm.ki.si/?what=database"
        for b in trace["bibliography"]
    )
    assertions[0]["source_metadata"]["native_row"]["fields"].clear()
    assert envelope == before


def test_native_duplicates_and_documented_example_mismatch_do_not_create_representative_relations():
    client = FixtureProBiSClient()
    assert len(map_chain_catalog(get_chain_catalog("2ww9.L", client=client))) == 5
    actual = map_chain_catalog(get_chain_catalog("1ytb.A", client=client))
    assert (
        len(actual) == 1 and actual[0]["asserted_value"]["native_chain_literal"] == "A"
    )
    missing = get_chain_catalog("1ytb.B", client=client)
    assert map_chain_catalog(missing) == []
    assert missing["acquisition_trace"]["records"][0]["outcome"] == "not_found"
    assert map_chain_catalog(get_chain_catalog("5a2q.H", client=client)) == []


def test_unknown_columns_zero_repeated_values_and_padding_are_neither_scores_nor_ids():
    text = (
        ROW
        + ROW
        + ROW.replace("0\t1     ", "unknown-index\t  future  ").replace(
            "1.0\n", "unknown-measure\n"
        )
    )
    assertions = map_chain_catalog(read(text))
    assert len(assertions) == len({a["id"] for a in assertions}) == 3
    assert assertions[0]["asserted_value"] == {
        "column_1_literal": "0",
        "column_2_literal": "1     ",
        "native_pdb_literal": "5a2q",
        "native_chain_literal": "h",
        "column_5_literal": "1.0",
    }
    assert assertions[-1]["asserted_value"]["column_2_literal"] == "  future  "
    assert assertions[-1]["asserted_value"]["column_5_literal"] == "unknown-measure"


@pytest.mark.parametrize(
    "text",
    [
        None,
        {},
        "",
        "\n",
        "<html>error</html>",
        "index\tcount\tpdb\tchain\tvalue\n",
        ROW + "\n",
        ROW.replace("\t1.0\n", "\n"),
        ROW.replace("\t1.0\n", "\t1.0\textra\n"),
        ROW.replace("5a2q", "5A2Q"),
        ROW.replace("\th\t", "\t\t"),
        ROW.replace("\th\t", "\thh\t"),
        ROW.replace("\th\t", "\th/\t"),
        ROW.replace("1     ", "      "),
        ROW.replace("1.0", "1\x00.0"),
        NATIVE + ROW.replace("5a2q", "wrong"),
    ],
)
def test_malformed_header_empty_or_unrelated_late_rows_fail_before_selection(text):
    with pytest.raises(ConnectorError):
        read(text)


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        True,
        1,
        "",
        "5A2Q.h",
        "5a2q",
        "pdb:5a2q.h",
        "5a2q.hh",
        "5a2q.h/",
        "5a2q.h?",
        "0a2q.h",
        "5a2q.h\nother",
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_invalid_query_does_not_reach_transport_even_when_digestion_is_skipped(
    identifier, skip
):
    class Forbidden:
        def chain_catalog(self, *args):
            pytest.fail("Invalid query reached catalog transport")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_chain_catalog(identifier, client=Forbidden(), skip_digestion=skip)


@pytest.mark.parametrize(
    "context",
    [
        {"source": "other"},
        {"kind": "alignments"},
        {"version": "2015-07-31"},
        {"query": response_query("5a2q.H")},
        {"truncated": True},
        {"truncated": None},
    ],
)
def test_custom_source_query_kind_date_revision_and_cut_are_not_reassigned(context):
    with pytest.raises(ConnectorError):
        read(**context)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "alignments"),
        ("version", "2015-07-31"),
        ("query", {"chain_literal": ID}),
        ("query", {**response_query(ID), "artifact": "current.txt"}),
        ("truncated", None),
    ],
)
def test_mapping_cannot_change_catalog_scope_or_invent_scientific_revision(key, value):
    envelope = read()
    envelope[key] = value
    with pytest.raises(ConnectorError):
        map_chain_catalog(envelope)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_tsv_and_gzip_preserve_original_time_hash_padding_and_terms(
    tmp_path, compressed
):
    raw = gzip.compress(NATIVE.encode()) if compressed else NATIVE.encode()
    path = tmp_path / ("catalog.tsv.gz" if compressed else "catalog.tsv")
    path.write_bytes(raw)
    scope = metadata()
    scope.update(
        retrieved_at="2026-10-07T21:00:00+00:00", terms={"licence": "NOT-STATED"}
    )
    client = SnapshotProBiSClient(
        path,
        source_metadata=scope,
        expected_sha256=hashlib.sha256(raw).hexdigest().upper(),
    )
    scope["query"]["artifact"] = "current.txt"
    envelope = get_chain_catalog(ID, client=client)
    assert (
        envelope["record"] == NATIVE
        and envelope["retrieved_at"] == "2026-10-07T21:00:00+00:00"
    )
    receipt = envelope["snapshot_receipt"]
    assert receipt["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert (
        receipt["file_format"] == "tsv" and receipt["source_access_observed"] is False
    )
    assert receipt["declared_terms"] == {"licence": "NOT-STATED"}
    assert (
        map_chain_catalog(envelope)[0]["source_metadata"]["snapshot_receipt"] == receipt
    )
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_chain_catalog(
            ID,
            client=SnapshotProBiSClient(
                path, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "alignments"),
        ("version", "2015-07-31"),
        ("query", response_query("5a2q.H")),
        ("query", {**response_query(ID), "artifact": "current.txt"}),
    ],
)
def test_snapshot_cannot_relabel_source_query_or_revision(tmp_path, key, value):
    path = tmp_path / "catalog.tsv"
    path.write_text(NATIVE, encoding="utf-8", newline="")
    scope = metadata()
    scope[key] = value
    with pytest.raises(ConnectorError):
        get_chain_catalog(ID, client=SnapshotProBiSClient(path, source_metadata=scope))


@pytest.mark.parametrize(
    "raw,compressed",
    [
        (b"", False),
        (b"\xff", False),
        (b"<html>failed</html>", False),
        (b"not gzip", True),
        (gzip.compress(NATIVE.encode())[:-4], True),
    ],
)
def test_unreadable_supplied_files_do_not_become_native_not_listed(
    tmp_path, raw, compressed
):
    path = tmp_path / ("catalog.gz" if compressed else "catalog.tsv")
    path.write_bytes(raw)
    with pytest.raises(ConnectorError):
        get_chain_catalog(
            ID, client=SnapshotProBiSClient(path, source_metadata=metadata())
        )


def test_unavailable_fixture_or_http_failure_does_not_become_negative_binding_knowledge(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    with pytest.raises(ConnectorError):
        get_chain_catalog(ID, client=FixtureProBiSClient(tmp_path))

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 404, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_chain_catalog(ID)


def test_one_native_catalog_get_and_replay_preserve_all_rows_time_and_hash(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    raw = NATIVE.encode()
    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(raw)
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = "text/plain"
        return response

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "probis.db")
    with archive.recording():
        first = get_chain_catalog(ID)

    def forbidden(*args, **kwargs):
        pytest.fail("Replay attempted network or structural calculation")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_chain_catalog(ID)
    assert calls == [URL] and first["record"] == second["record"] == NATIVE
    assert first["retrieved_at"] == second["retrieved_at"]
    assert (
        first["download_sha256"]
        == second["download_sha256"]
        == hashlib.sha256(raw).hexdigest()
    )
    assert map_chain_catalog(first) == map_chain_catalog(second)
    assert second["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert archive.sources()["ProBiS-Database"]["retention"]["share"] == "unknown"


def test_data_terms_and_dated_filename_do_not_become_software_article_or_revision_grants():
    assert source_terms()["ProBiS-Database"]["licence"] == "NOT-STATED"
    assert verdict("ProBiS-Database", "redistribution")["verdict"] == "unknown"
    assert retention("ProBiS-Database")["keep"] == "internal"
    assert response_query(ID)["artifact"] == ARTIFACT
