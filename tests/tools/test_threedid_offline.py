"""3did DMI block grammar, independent instances, native axes and traceability."""

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
from sabueso.mappings.threedid import (
    URL,
    map_motif_interactions,
    parse_motif_interactions,
    response_query,
)
from sabueso.tools.db.threedid import (
    FixtureThreeDIDClient,
    SnapshotThreeDIDClient,
    get_motif_interactions,
)

PATH = Path("temp_data/3did/3did_dmi_flat.gz")
ID = "7m5l"
HEAD = "#=ID\tPCNA_C\t(Pfam)\tPCNA_C_LIG_0-0\t(PLoS_CB_2010)\n#=PT\tQ..[ILM]..F[FY] (Feb 2025)\n"
ROW = "#=3D\t7m5l\tB:127-254\tE:2-11\tQCSMTCFY\t0\t0\n"
NATIVE = HEAD + ROW + "//\n"


class Client:
    def __init__(self, text, **context):
        self.text, self.context = text, context

    def motif_interactions(self, identifier):
        return {
            "record": self.text,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def read(text=NATIVE, identifier=ID, **context):
    return get_motif_interactions(identifier, client=Client(text, **context))


def metadata():
    return {
        "source": "3did",
        "kind": "domain_motif_interactions",
        "query": response_query(ID),
    }


def test_original_full_export_retains_blocks_patterns_structures_and_native_support():
    raw = PATH.read_bytes()
    assert len(raw) == 149724
    assert (
        hashlib.sha256(raw).hexdigest()
        == "ef3d339e7643efb3ae2ed1857ecbbc3c350d3cf08ff9ef79daea4c667907bdfb"
    )
    decoded = gzip.decompress(raw)
    assert len(decoded) == 826632
    assert (
        hashlib.sha256(decoded).hexdigest()
        == "85fd69fb419b994eb4c506c466e469a22af3bc16af7b042da64f2c58637c93aa"
    )
    envelope = get_motif_interactions(ID, client=FixtureThreeDIDClient())
    before = copy.deepcopy(envelope)
    assert envelope["record"].encode() == decoded and envelope["truncated"] is False
    blocks = parse_motif_interactions(envelope["record"])
    assert len(blocks) == 1657 and sum(len(b["instances"]) for b in blocks) == 17478
    assertions = map_motif_interactions(envelope)
    assert len(assertions) == len({a["id"] for a in assertions}) == 6
    assert all(a["subject_ref"] == "3did:structure:7m5l" for a in assertions)
    assert all(
        a["field_path"] == "annotations.domain_motif_interactions" for a in assertions
    )
    first = assertions[0]
    assert first["asserted_value"] == {
        "domain_name": "PCNA_C",
        "domain_source_literal": "(Pfam)",
        "motif_name": "PCNA_C_LIG_0-0",
        "motif_source_literal": "(PLoS_CB_2010)",
        "pattern_literal": "Q..[ILM]..F[FY] (Feb 2025)",
        "pdb_id": ID,
        "domain_range_literal": "B:127-254",
        "motif_range_literal": "E:2-11",
        "motif_sequence_literal": "QCSMTCFY",
        "contextual_contacts_literal": "0",
        "topology_literal": "0",
    }
    assert first["source_metadata"]["native_row"]["line"] == 3
    assert first["source"]["version"] is first["retrieved_at"] is None
    assert [a["asserted_value"]["domain_name"] for a in assertions] == [
        "PCNA_C"
    ] * 3 + ["PCNA_N"] * 3
    assert all(a["source_metadata"]["received_pair_count"] == 1657 for a in assertions)
    trace = envelope["acquisition_trace"]["records"][0]
    assert trace["outcome"] == "received" and trace["count"] == 6
    assert (
        trace["received_pair_count"] == 1657
        and trace["received_instance_count"] == 17478
    )
    assert trace["network_attempts"] == 0
    assert any(
        b["id"] == "url:https://3did.irbbarcelona.org/" for b in trace["bibliography"]
    )
    first["asserted_value"].clear()
    first["source_metadata"]["native_id"]["fields"].clear()
    assert envelope == before


def test_conflicting_duplicate_instances_dates_ranges_and_chain_tokens_are_not_repaired():
    rows = [
        ROW,
        ROW,
        ROW.replace("\t0\t0", "\t3\t12"),
        ROW.replace("B:127-254", "ee:-3A-10B"),
        ROW.replace("7m5l", "7m5m"),
    ]
    # Invalid regex text is an opaque provider pattern, never executed or corrected.
    head = HEAD.replace("Q..[ILM]..F[FY] (Feb 2025)", "[ (unknown date)")
    assertions = map_motif_interactions(read(head + "".join(rows) + "//\n"))
    assert len(assertions) == len({a["id"] for a in assertions}) == 4
    assert assertions[3]["asserted_value"]["domain_range_literal"] == "ee:-3A-10B"
    assert all(
        a["asserted_value"]["motif_range_literal"] == "E:2-11" for a in assertions
    )
    assert all(
        a["asserted_value"]["motif_sequence_literal"] == "QCSMTCFY" for a in assertions
    )
    assert all(
        a["asserted_value"]["pattern_literal"] == "[ (unknown date)" for a in assertions
    )
    assert assertions[2]["asserted_value"]["contextual_contacts_literal"] == "3"
    assert [a["source_metadata"]["native_row"]["line"] for a in assertions] == [
        3,
        4,
        5,
        6,
    ]
    assert all(a["source_metadata"]["received_instance_count"] == 5 for a in assertions)
    assert len(map_motif_interactions(read(NATIVE + NATIVE))) == 2


@pytest.mark.parametrize(
    "text",
    [
        None,
        {},
        "",
        "\n",
        "<html>failed</html>",
        ROW + "//\n",
        HEAD + "//\n",
        HEAD + ROW,
        HEAD + HEAD + ROW + "//\n",
        NATIVE + "//\n",
        NATIVE + "malformed\n",
        HEAD + ROW + "#=PT\tlate\n//\n",
        HEAD.replace("#=PT", "#=XX") + ROW + "//\n",
        NATIVE.replace("(Pfam)", ""),
        NATIVE.replace("QCSMTCFY", ""),
        NATIVE.replace("B:127-254", "B:127"),
        NATIVE.replace("7m5l", "7M5L"),
        NATIVE.replace("\t0\t0", "\t-1\t0"),
        NATIVE.replace("\t0\t0", "\t0\tNaN"),
        NATIVE.replace("QCSMTCFY", "QC\x00S"),
        NATIVE + HEAD + ROW.replace("7m5l", "wrong") + "//\n",
    ],
)
def test_missing_parent_pattern_or_terminator_and_late_malformed_rows_fail(text):
    with pytest.raises(ConnectorError):
        read(text)


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        True,
        7,
        "",
        "7M5L",
        "pdb:7m5l",
        "7m5l.B",
        "7m5l/",
        "7m5l?",
        "0m5l",
        "7m5l\nother",
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_invalid_queries_fail_before_transport_even_when_digestion_is_skipped(
    identifier, skip
):
    class Forbidden:
        def motif_interactions(self, *args):
            pytest.fail("Invalid query reached transport")

    with pytest.raises((ConnectorError, ArgumentError)):
        get_motif_interactions(identifier, client=Forbidden(), skip_digestion=skip)


@pytest.mark.parametrize(
    "context",
    [
        {"source": "other"},
        {"kind": "domain_domain_interactions"},
        {"version": "2024_12"},
        {"query": response_query("7m5m")},
        {"truncated": True},
        {"truncated": None},
    ],
)
def test_custom_client_source_query_export_revision_and_cut_are_not_reassigned(context):
    with pytest.raises(ConnectorError):
        read(**context)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "profile_interfaces"),
        ("version", "2025"),
        ("truncated", None),
        ("query", {"pdb_id": ID}),
        ("query", {**response_query(ID), "chain": "B"}),
    ],
)
def test_mapping_rejects_changed_scope_and_invented_revision(key, value):
    envelope = read()
    envelope[key] = value
    with pytest.raises(ConnectorError):
        map_motif_interactions(envelope)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_text_and_gzip_keep_full_original_time_hash_and_declared_terms(
    tmp_path, compressed
):
    raw = gzip.compress(NATIVE.encode()) if compressed else NATIVE.encode()
    path = tmp_path / ("native.txt.gz" if compressed else "native.txt")
    path.write_bytes(raw)
    scope = metadata()
    scope.update(
        retrieved_at="2026-10-07T20:00:00+00:00", terms={"licence": "NOT-STATED"}
    )
    client = SnapshotThreeDIDClient(
        path,
        source_metadata=scope,
        expected_sha256=hashlib.sha256(raw).hexdigest().upper(),
    )
    scope["query"]["pdb_id"] = "7m5m"
    envelope = get_motif_interactions(ID, client=client)
    assert (
        envelope["record"] == NATIVE
        and envelope["retrieved_at"] == "2026-10-07T20:00:00+00:00"
    )
    receipt = envelope["snapshot_receipt"]
    assert receipt["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["file_format"] == "text"
    assert (
        receipt["declared_terms"] == {"licence": "NOT-STATED"}
        and receipt["source_access_observed"] is False
    )
    assert (
        map_motif_interactions(envelope)[0]["source_metadata"]["snapshot_receipt"]
        == receipt
    )
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_motif_interactions(
            ID,
            client=SnapshotThreeDIDClient(
                path, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "profile_interfaces"),
        ("version", "2024_12"),
        ("query", response_query("7m5m")),
        ("query", {**response_query(ID), "chain": "B"}),
    ],
)
def test_snapshot_metadata_cannot_relabel_native_source_query_or_revision(
    tmp_path, key, value
):
    path = tmp_path / "native.txt"
    path.write_text(NATIVE)
    scope = metadata()
    scope[key] = value
    with pytest.raises(ConnectorError):
        get_motif_interactions(
            ID, client=SnapshotThreeDIDClient(path, source_metadata=scope)
        )


@pytest.mark.parametrize(
    "raw,compressed",
    [
        (b"\xff", False),
        (b"", False),
        (b"<html>failed</html>", False),
        (b"not gzip", True),
        (gzip.compress(NATIVE.encode())[:-4], True),
    ],
)
def test_unreadable_snapshots_are_not_missing_interactions(tmp_path, raw, compressed):
    path = tmp_path / ("native.gz" if compressed else "native.txt")
    path.write_bytes(raw)
    with pytest.raises(ConnectorError):
        get_motif_interactions(
            ID, client=SnapshotThreeDIDClient(path, source_metadata=metadata())
        )


def test_missing_fixture_http_failure_and_received_not_listed_remain_distinct(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    with pytest.raises(ConnectorError):
        get_motif_interactions(ID, client=FixtureThreeDIDClient(tmp_path))
    path = tmp_path / "native.txt"
    path.write_text(NATIVE.replace(ID, "7m5m"))
    empty = get_motif_interactions(
        ID, client=SnapshotThreeDIDClient(path, source_metadata=metadata())
    )
    assert not map_motif_interactions(empty)
    assert empty["acquisition_trace"]["records"][0]["outcome"] == "not_found"

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 404, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_motif_interactions(ID)


def test_one_native_gzip_get_and_archive_replay_keep_all_original_support(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    raw = gzip.compress(NATIVE.encode())
    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(raw)
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = "application/x-gzip"
        return response

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "3did.db")
    with archive.recording():
        first = get_motif_interactions(ID)

    def forbidden(*args, **kwargs):
        pytest.fail("Replay attempted network, coordinates or motif search")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_motif_interactions(ID)
    assert calls == [URL]
    assert first["record"] == second["record"] == NATIVE
    assert first["retrieved_at"] == second["retrieved_at"]
    assert (
        first["download_sha256"]
        == second["download_sha256"]
        == hashlib.sha256(raw).hexdigest()
    )
    assert map_motif_interactions(first) == map_motif_interactions(second)
    assert second["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert archive.sources()["3did"]["retention"]["share"] == "unknown"


def test_export_data_terms_are_unknown_without_borrowing_article_or_software_licences():
    assert source_terms()["3did"]["licence"] == "NOT-STATED"
    assert verdict("3did", "redistribution")["verdict"] == "unknown"
    assert retention("3did")["share"] == "unknown"
