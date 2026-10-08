"""Native TTD listing identity, release, literal fidelity and archive replay."""

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
from sabueso.core.terms import source_terms, verdict
from sabueso.mappings.ttd import URL, map_target_listing, parse_targets, response_query
from sabueso.tools.db.ttd import FixtureTTDClient, SnapshotTTDClient, get_target_listing

PATH = Path("temp_data/ttd/P2-01-TTD_uniprot_all.txt")
RAW = PATH.read_bytes()
NATIVE = RAW.decode()
PARSED = parse_targets(NATIVE)
HEAD = NATIVE[: NATIVE.index("TARGETID\tT00032")]
BLOCK = "TARGETID\tT59130\r\nUNIPROID\tTPIS_PLAFA\r\nTARGNAME\tBacterial Triosephosphate isomerase (Bact TPI)\r\nTARGTYPE\tLiterature-reported target\r\n"


class Client:
    def __init__(self, text=NATIVE, **context):
        self.text, self.context = text, context

    def target_listing(self, identifier):
        return {"record": self.text, "version": "10.1.01", **self.context}


def read(text=NATIVE, **context):
    return get_target_listing("T59130", client=Client(text, **context))


def metadata():
    return {
        "source": "TTD",
        "kind": "target_listing",
        "query": response_query("T59130"),
        "version": "10.1.01",
    }


def test_unchanged_export_all_blocks_placeholder_counts_and_native_inconsistency():
    assert (
        hashlib.sha256(RAW).hexdigest()
        == "74b2dbb4c03e14b01d02b54bdce45507da0da1e457859e1669cdf76b39feb22e"
    )
    assert len(PARSED["rows"]) == 4298
    assert sum(r["fields"]["UNIPROID"] == "NOUNIPROTAC" for r in PARSED["rows"]) == 613
    envelope = get_target_listing("T59130", client=FixtureTTDClient())
    before = copy.deepcopy(envelope)
    a = map_target_listing(envelope)[0]
    assert a["subject_ref"] == "ttd:target:T59130"
    assert a["asserted_value"]["UNIPROID"] == "TPIS_PLAFA"
    assert a["asserted_value"]["TARGNAME"].startswith("Bacterial")
    assert a["source"]["version"] == "10.1.01"
    assert a["source_metadata"]["release_date_literal"] == "2024.01.10"
    assert a["source_metadata"]["native_header_lines"] == PARSED["native_header_lines"]
    assert envelope["record"].encode() == RAW
    a["asserted_value"].clear()
    assert envelope == before


def test_unbound_native_placeholder_is_not_repaired_into_a_protein():
    a = map_target_listing(get_target_listing("T00064", client=FixtureTTDClient()))[0]
    assert a["asserted_value"]["UNIPROID"] == "NOUNIPROTAC"
    assert a["subject_ref"] == "ttd:target:T00064"


def test_no_match_is_received_export_not_absent_target_biology():
    e = get_target_listing("T00000", client=FixtureTTDClient())
    assert map_target_listing(e) == []
    trace = e["acquisition_trace"]["records"][0]
    assert trace["outcome"] == "not_found" and trace["received_export_count"] == 4298


def test_repeated_conflicting_blanks_and_future_types_survive():
    third = BLOCK.replace("TPIS_PLAFA", "").replace(
        "Literature-reported target", "future target type"
    )
    e = read(HEAD + BLOCK + "\r\n" + BLOCK + "\r\n" + third)
    a = map_target_listing(e)
    assert len(a) == 3 and len({r["id"] for r in a}) == 3
    assert a[2]["asserted_value"]["UNIPROID"] == ""
    assert a[2]["asserted_value"]["TARGTYPE"] == "future target type"
    assert a[0]["source_metadata"]["native_row"]["raw_lines"][0] == "TARGETID\tT59130"


@pytest.mark.parametrize(
    "body",
    [
        "TARGETID\tT12345\r\n",
        BLOCK.replace("UNIPROID\t", "OTHER\t"),
        BLOCK.replace("T59130", "P60174"),
        BLOCK + "EXTRA\tvalue\r\n",
        BLOCK.replace("TPIS_PLAFA", "TPIS\tPLAFA"),
        BLOCK.replace("TPIS_PLAFA", "TPIS\x00PLAFA"),
    ],
)
def test_late_malformed_blocks_fail_before_selected_mapping(body):
    with pytest.raises(ConnectorError):
        read(HEAD + BLOCK + "\r\n" + body)


@pytest.mark.parametrize(
    "text",
    [
        None,
        "",
        "<html>Error</html>",
        NATIVE.replace("Version 10.1.01 (2024.01.10)", "Version unknown"),
        NATIVE.replace("2024.01.10", "2024.02.31"),
        NATIVE.replace("Uniprot IDs for all TTD targets", "Drug information"),
        NATIVE.replace("UNIPROID\tUniprot ID", "UNIPROID\tAccession"),
    ],
)
def test_wrong_representation_header_date_or_release_fails(text):
    with pytest.raises(ConnectorError):
        read(text)


@pytest.mark.parametrize(
    "context",
    [
        {"source": "Other"},
        {"kind": "drug_listing"},
        {"query": response_query("T00032")},
        {"version": None},
        {"version": "2026"},
        {"truncated": True},
    ],
)
def test_client_binding_release_and_cut_not_resealed(context):
    with pytest.raises(ConnectorError):
        read(**context)


@pytest.mark.parametrize(
    "identifier",
    [None, "", "P60174", "T5913", "t59130", "T59130/", "ttd:T59130", "T５９１３０"],
)
@pytest.mark.parametrize("skip", [False, True])
def test_exact_native_target_scope_with_or_without_digestion(identifier, skip):
    with pytest.raises((ArgumentError, ConnectorError)):
        get_target_listing(identifier, client=Client(), skip_digestion=skip)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_original_snapshot_bytes_hash_time_and_declared_terms(
    tmp_path, compressed
):
    raw = gzip.compress(RAW) if compressed else RAW
    path = tmp_path / ("targets.txt.gz" if compressed else "targets.txt")
    path.write_bytes(raw)
    declaration = metadata()
    declaration.update(
        retrieved_at="2026-10-07T22:00:00+00:00", terms={"licence": "caller declared"}
    )
    before = copy.deepcopy(declaration)
    e = get_target_listing(
        "T59130",
        client=SnapshotTTDClient(
            path,
            source_metadata=declaration,
            expected_sha256=hashlib.sha256(raw).hexdigest(),
        ),
    )
    assert e["record"].encode() == RAW
    assert e["retrieved_at"] == declaration["retrieved_at"]
    assert e["snapshot_receipt"]["source_access_observed"] is False
    assert (
        e["snapshot_receipt"]["declared_terms"] == declaration["terms"]
        and declaration == before
    )
    with pytest.raises(ConnectorError):
        get_target_listing(
            "T59130",
            client=SnapshotTTDClient(
                path, source_metadata=declaration, expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "Other"),
        ("kind", "drugs"),
        ("query", response_query("T00032")),
        ("version", "current"),
    ],
)
def test_snapshot_foreign_declarations_fail(tmp_path, key, value):
    path = tmp_path / "targets.txt"
    path.write_bytes(RAW)
    declaration = metadata()
    declaration[key] = value
    with pytest.raises(ConnectorError):
        get_target_listing(
            "T59130", client=SnapshotTTDClient(path, source_metadata=declaration)
        )


def test_missing_and_failed_access_do_not_mean_not_listed(tmp_path, monkeypatch):
    from sabueso.tools.db import _http

    with pytest.raises(ConnectorError):
        get_target_listing("T59130", client=FixtureTTDClient(tmp_path))

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 403, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_target_listing("T59130")


def test_one_native_get_and_zero_network_replay_keep_header_hash_original_time(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(RAW)
        response.status = 200
        response.headers = Message()
        return response

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "archive.sqlite")
    with archive.recording():
        first = get_target_listing("T59130")
    with archive.replaying():
        replay = get_target_listing("T59130")
    assert (
        calls == [URL] and first["download_sha256"] == hashlib.sha256(RAW).hexdigest()
    )
    assert replay["retrieved_at"] == first["retrieved_at"]
    assert map_target_listing(replay) == map_target_listing(first)
    assert replay["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert source_terms()["TTD"]["licence"] == "NOT-STATED"
    assert verdict("TTD", "redistribution")["verdict"] == "unknown"
