"""MEROPS native classification occurrences, unresolved coverage and source rights."""

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
from sabueso.core.terms import USES, retention, source_terms, verdict
from sabueso.mappings.merops import (
    URL,
    map_assignments,
    parse_assignments,
    response_query,
)
from sabueso.tools.db.merops import (
    FixtureMEROPSClient,
    SnapshotMEROPSClient,
    get_assignments,
)

PATH = Path("temp_data/merops/accession_assignments.tsv")
ID = "swissprot:P29466"
NATIVE = "swissprot:P29466\tC14A\t9606\r\nswissprot:\tQ80ZF\tP2A\t10090\r\n"


class Client:
    def __init__(self, text, **context):
        self.text, self.context = text, context

    def assignments(self, identifier):
        return {
            "record": self.text,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def read(text=NATIVE, identifier=ID, **context):
    return get_assignments(identifier, client=Client(text, **context))


def metadata(identifier=ID):
    return {
        "source": "MEROPS",
        "kind": "accession_assignments",
        "query": response_query(identifier),
    }


def test_original_export_all_rows_issues_prefixes_and_native_support_survive():
    raw = PATH.read_bytes()
    assert len(raw) == 2914699
    assert (
        hashlib.sha256(raw).hexdigest()
        == "9758b658cd7d5f043311d5babf439590baf88b97623ad2a5d42e7e6827abc711"
    )
    envelope = get_assignments(ID, client=FixtureMEROPSClient())
    before = copy.deepcopy(envelope)
    assert envelope["record"].encode() == raw and envelope["truncated"] is False
    assert envelope["selection_complete"] is False
    issues = envelope["representation_issues"]
    assert [x["native_row"]["line"] for x in issues] == [67322, 67435, 83822, 108853]
    assert [x["native_row"]["fields"] for x in issues] == [
        ["swissprot:", "Q80ZF", "P2A", "10090"],
        ["swissprot:", "Q6UWY", "S1A", "9606"],
        ["swissprot:", "Q32Q9", "S9", "10090"],
        ['swissprot:"Q96CC', "S54", "9606"],
    ]
    assert all(x["rule"] == "merops_accession_rows@1" for x in issues)
    rows = parse_assignments(envelope["record"])
    assert len(rows) == 116744
    assert sum(len(r["fields"]) == 3 and r["fields"][2] == "" for r in rows) == 8
    assert (
        sum(len(r["fields"]) == 3 and r["fields"][2].startswith(" ") for r in rows)
        == 147
    )
    assertions = map_assignments(envelope)
    assert len(assertions) == 1
    assertion = assertions[0]
    assert assertion["subject_ref"] == "merops:accession:swissprot:P29466"
    assert assertion["field_path"] == "annotations.peptidase_inhibitor_classifications"
    assert assertion["asserted_value"] == {
        "accession_literal": ID,
        "family_literal": "C14A",
        "taxonomy_literal": "9606",
    }
    support = assertion["source_metadata"]
    assert support["native_row"]["line"] == 9307
    assert support["received_export_count"] == 116744
    assert support["representation_issues"] == issues
    assert assertion["source"]["version"] is assertion["retrieved_at"] is None
    trace = envelope["acquisition_trace"]["records"][0]
    assert trace["outcome"] == "received" and trace["count"] == 1
    assert (
        trace["selection_complete"] is False
        and trace["received_export_count"] == 116744
    )
    assert trace["network_attempts"] == 0
    assert any(
        b["id"] == "url:https://www.ebi.ac.uk/merops/" for b in trace["bibliography"]
    )
    assertions[0]["source_metadata"]["representation_issues"].clear()
    assertions[0]["asserted_value"].clear()
    assert envelope == before


def test_unknown_match_with_unresolved_rows_is_never_complete_not_found(tmp_path):
    path = tmp_path / "native.tsv"
    path.write_bytes(NATIVE.encode())
    envelope = get_assignments(
        "swissprot:Q80ZF",
        client=SnapshotMEROPSClient(path, source_metadata=metadata("swissprot:Q80ZF")),
    )
    assert map_assignments(envelope) == []
    assert envelope["selection_complete"] is False
    assert envelope["acquisition_trace"]["records"][0]["outcome"] == "received"
    path.write_bytes(b"swissprot:Other\tI1\t\n")
    clean = get_assignments(
        ID, client=SnapshotMEROPSClient(path, source_metadata=metadata())
    )
    assert clean["selection_complete"] is True
    assert clean["acquisition_trace"]["records"][0]["outcome"] == "not_found"
    assert map_assignments(clean) == []


def test_repeated_conflicting_rows_spaces_blank_taxonomy_and_namespace_survive():
    text = "PIR:Query.1\tI1\t 9606\r\nPIR:Query.1\tS1A\t\r\nPIR:Query.1\tI1\t 9606\r\nTrembl:Query.1\tI1\t9606\r\n"
    assertions = map_assignments(read(text, "PIR:Query.1"))
    assert len(assertions) == 3 and len({x["id"] for x in assertions}) == 3
    assert [x["asserted_value"]["family_literal"] for x in assertions] == [
        "I1",
        "S1A",
        "I1",
    ]
    assert [x["asserted_value"]["taxonomy_literal"] for x in assertions] == [
        " 9606",
        "",
        " 9606",
    ]
    assert [x["source_metadata"]["native_row"]["line"] for x in assertions] == [1, 2, 3]
    assert not map_assignments(read(text, "PIR:query.1"))
    assert not map_assignments(read(text, "PIR:Query"))
    assert len(map_assignments(read(text, "Trembl:Query.1"))) == 1
    assert all(
        set(x["asserted_value"])
        == {"accession_literal", "family_literal", "taxonomy_literal"}
        for x in assertions
    )


@pytest.mark.parametrize(
    "text",
    [
        None,
        {},
        "",
        "\n",
        "<html>failed</html>",
        "accession\tfamily\ttaxonomy\n",
        "swissprot:P29466\tC14A\n",
        "swissprot:P29466\tC14A\t9606\textra\n",
        "swissprot:\tC14A\t9606\n",
        "UniProt:P29466\tC14A\t9606\n",
        "swissprot:P29466\t\t9606\n",
        "swissprot:P29466\tC14A\tNaN\n",
        NATIVE + "malformed\n",
        NATIVE + "swissprot:\tunsafe/id\tS1A\t9606\n",
        NATIVE + "swissprot:P29466\tC14A\t9606\textra\textra\n",
    ],
)
def test_errors_headers_and_malformed_late_rows_fail_before_any_selection(text):
    with pytest.raises(ConnectorError):
        read(text)


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        True,
        2,
        "",
        "P29466",
        "swissprot:",
        "SWISSPROT:P29466",
        "swissprot:P29466/",
        "swissprot:P29466 other",
        "swissprot:P29466?",
        "swissprot:P29466\nother",
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_unsupported_identifiers_never_reach_transport(identifier, skip):
    class Forbidden:
        def assignments(self, identifier):
            pytest.fail("Invalid query reached transport")

    with pytest.raises((ConnectorError, ArgumentError)):
        get_assignments(identifier, client=Forbidden(), skip_digestion=skip)


@pytest.mark.parametrize(
    "context",
    [
        {"source": "other"},
        {"kind": "cleavage"},
        {"version": "12.5"},
        {"query": response_query("swissprot:other")},
        {"truncated": True},
        {"truncated": None},
    ],
)
def test_custom_client_scope_revision_and_cut_cannot_be_reassigned(context):
    with pytest.raises(ConnectorError):
        read(**context)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "cleavage"),
        ("version", "12.4"),
        ("truncated", None),
        ("query", {"accession_literal": ID}),
        ("representation_issues", []),
        ("selection_complete", True),
    ],
)
def test_mapping_rejects_changed_scope_or_concealed_representation_issues(key, value):
    envelope = read()
    envelope[key] = value
    with pytest.raises(ConnectorError):
        map_assignments(envelope)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_native_snapshots_preserve_text_hash_original_time_and_terms(
    tmp_path, compressed
):
    raw = NATIVE.encode()
    raw = gzip.compress(raw) if compressed else raw
    path = tmp_path / ("native.tsv.gz" if compressed else "native.tsv")
    path.write_bytes(raw)
    scope = metadata()
    scope.update(
        retrieved_at="2026-10-07T12:00:00+00:00",
        terms={"licence": "GNU-LIBRARY-GPL-UNVERSIONED"},
    )
    client = SnapshotMEROPSClient(
        path,
        source_metadata=scope,
        expected_sha256=hashlib.sha256(raw).hexdigest().upper(),
    )
    scope["query"]["accession_literal"] = "swissprot:other"
    envelope = get_assignments(ID, client=client)
    assert envelope["record"] == NATIVE
    assert envelope["retrieved_at"] == "2026-10-07T12:00:00+00:00"
    receipt = envelope["snapshot_receipt"]
    assert receipt["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["native_format"].startswith("MEROPS_headerless")
    assert receipt["declared_terms"] == {"licence": "GNU-LIBRARY-GPL-UNVERSIONED"}
    assert receipt["source_access_observed"] is False
    assert (
        map_assignments(envelope)[0]["source_metadata"]["snapshot_receipt"] == receipt
    )
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_assignments(
            ID,
            client=SnapshotMEROPSClient(
                path, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "cleavage"),
        ("version", "12.5"),
        ("query", response_query("swissprot:p29466")),
        ("query", {**response_query(ID), "taxon": 9606}),
    ],
)
def test_supplied_metadata_cannot_change_native_source_kind_case_or_revision(
    key, value
):
    scope = metadata()
    scope[key] = value
    with pytest.raises(ConnectorError):
        get_assignments(ID, client=SnapshotMEROPSClient(PATH, source_metadata=scope))


@pytest.mark.parametrize(
    "raw,compressed",
    [
        (b"\xff", False),
        (b"<html>blocked</html>", False),
        (b"", False),
        (b"not gzip", True),
        (gzip.compress(NATIVE.encode())[:-4], True),
    ],
)
def test_unreadable_snapshots_never_become_a_missing_match(tmp_path, raw, compressed):
    path = tmp_path / ("native.tsv.gz" if compressed else "native.tsv")
    path.write_bytes(raw)
    with pytest.raises(ConnectorError):
        get_assignments(
            ID, client=SnapshotMEROPSClient(path, source_metadata=metadata())
        )


def test_missing_fixtures_fail_distinctly(tmp_path):
    for client in [
        FixtureMEROPSClient(tmp_path),
        SnapshotMEROPSClient(tmp_path / "missing.tsv", source_metadata=metadata()),
    ]:
        with pytest.raises(ConnectorError):
            get_assignments(ID, client=client)


def test_http_failure_is_not_an_empty_or_unlisted_export(monkeypatch):
    from sabueso.tools.db import _http

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 404, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_assignments(ID)


def test_full_original_archive_replay_retains_issues_and_uses_zero_network(
    monkeypatch, tmp_path
):
    from sabueso.tools.db import _http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(PATH.read_bytes())
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = "text/plain"
        return response

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "merops.db")
    with archive.recording():
        first = get_assignments(ID)

    def forbidden(*args, **kwargs):
        pytest.fail("Replay attempted network or acquired a linked record")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_assignments(ID)
    assert calls == [URL]
    assert first["record"] == second["record"] == PATH.read_bytes().decode()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert (
        first["download_sha256"]
        == second["download_sha256"]
        == hashlib.sha256(PATH.read_bytes()).hexdigest()
    )
    assert map_assignments(first) == map_assignments(second)
    assert second["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert archive.sources()["MEROPS"]["retention"]["share"] == "unknown"


@pytest.mark.parametrize("use", USES)
def test_declared_unversioned_library_licence_is_preserved_without_allowed_verdict(use):
    assert source_terms()["MEROPS"]["licence"] == "GNU-LIBRARY-GPL-UNVERSIONED"
    answer = verdict("MEROPS", use)
    assert (
        answer["verdict"] == "unknown" and answer["reason"] == "licence_not_classified"
    )
    assert answer["statement"].endswith("/merops/about/availability.shtml")
    assert answer["caveats"]
    kept = retention("MEROPS")
    assert kept["keep"] == "internal" and kept["share"] == "unknown"
    assert kept["reason"] == "licence_not_classified" and kept["caveats"]


def test_quoted_native_literal_is_not_repaired_into_another_accession():
    literal = 'swissprot:"Q96CC'
    text = literal + "\tS54\t9606\r\n"
    envelope = read(text, literal)
    assertions = map_assignments(envelope)
    assert (
        len(assertions) == 1
        and assertions[0]["asserted_value"]["accession_literal"] == literal
    )
    assert assertions[0]["subject_ref"] == "merops:accession:" + literal
    assert (
        envelope["representation_issues"][0]["issue"]
        == "quoted_accession_literal_unresolved"
    )
    assert envelope["selection_complete"] is False
    assert not map_assignments(read(text, "swissprot:Q96CC"))
