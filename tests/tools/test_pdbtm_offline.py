"""PDBTM original XML, native axes, conditional terms and acquisition support."""

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
from sabueso.mappings.pdbtm import (
    BASE,
    COPYRIGHT,
    decode_xml,
    map_topology,
    native_hash,
    parse_topology,
    response_query,
)
from sabueso.tools.db.pdbtm import FixturePDBTMClient, SnapshotPDBTMClient, get_topology

ID = "1c3w"
PATH = Path("temp_data/pdbtm/1c3w.xml")
# Synthetic format cases are constructed independently of the unchanged fixture.
CHAIN = """<CHAIN CHAINID="a" NUM_TM="0" TYPE="future-type"><SEQ> ACDE\nFG </SEQ>
<REGION seq_beg="1" seq_end="2" pdb_beg="-3A" pdb_end="-2B" type="future-code"/>
<REGION seq_beg="3" seq_end="6" pdb_beg="107" pdb_end="120" type="H"/></CHAIN>"""
NATIVE = f'''<?xml version="1.0" encoding="iso-8859-1"?>
<pdbtm xmlns="https://pdbtm.unitmp.org" ID="{ID}" TMP="yes">
<COPYRIGHT>{COPYRIGHT}</COPYRIGHT><CREATE_DATE>2003-08-11</CREATE_DATE>
<MODIFICATION><DATE>2005-01-01</DATE><DESCR>synthetic format case</DESCR></MODIFICATION>
<MEMBRANE><NORMAL X="0" Y="0" Z="17.25"/></MEMBRANE>{CHAIN}</pdbtm>'''


class Client:
    def __init__(self, text, **context):
        self.text, self.context = text, context

    def topology(self, identifier):
        return {
            "record": self.text,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def read(text=NATIVE, identifier=ID, **context):
    return get_topology(identifier, client=Client(text, **context))


def metadata():
    return {
        "source": "PDBTM",
        "kind": "transmembrane_topology",
        "query": response_query(ID),
    }


def test_original_native_xml_retains_three_independent_chains_45_regions_and_copyright():
    raw = PATH.read_bytes()
    assert len(raw) == 6866
    assert (
        hashlib.sha256(raw).hexdigest()
        == "37ae24e30f12457eb91fb9198c5a7a6643e46e33efa0c039048784ff5b7ac55e"
    )
    envelope = get_topology(ID, client=FixturePDBTMClient())
    before = copy.deepcopy(envelope)
    assert envelope["record"].encode("iso-8859-1") == raw
    assert envelope["native_document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert envelope["version"] is envelope["retrieved_at"] is None
    assert envelope["truncated"] is False
    assertions = map_topology(envelope)
    assert len(assertions) == len({a["id"] for a in assertions}) == 3
    assert [a["asserted_value"]["chain_attributes"]["CHAINID"] for a in assertions] == [
        "A",
        "B",
        "C",
    ]
    assert all(a["subject_ref"] == "pdbtm:structure:1c3w" for a in assertions)
    assert all(
        a["field_path"] == "annotations.transmembrane_topology" for a in assertions
    )
    first = assertions[0]
    value = first["asserted_value"]
    assert value["chain_attributes"] == {"CHAINID": "A", "NUM_TM": "7", "TYPE": "alpha"}
    assert value["entry_tmp_literal"] == "yes"
    assert len("".join(value["sequence_text"].split())) == 222
    assert all(len(a["asserted_value"]["regions"]) == 15 for a in assertions)
    # The native numbering offset changes; endpoints do not imply an exact map.
    assert value["regions"][9] == {
        "seq_beg": "130",
        "seq_end": "152",
        "pdb_beg": "134",
        "pdb_end": "156",
        "type": "H",
    }
    assert value["regions"][10] == {
        "seq_beg": "153",
        "seq_end": "161",
        "pdb_beg": "162",
        "pdb_end": "170",
        "type": "2",
    }
    assert all(
        a["source_metadata"]["original_xml"].encode("iso-8859-1") == raw
        for a in assertions
    )
    assert 'NEW_CHAINID="B"' in first["source_metadata"]["original_xml"]
    assert "TMRES" not in value and "NORMAL" not in value and "TMATRIX" not in value
    assert all(a["source_metadata"]["received_region_count"] == 45 for a in assertions)
    trace = envelope["acquisition_trace"]["records"][0]
    assert trace["outcome"] == "received" and trace["count"] == 3
    assert trace["received_region_count"] == 45 and trace["network_attempts"] == 0
    assert any(
        item["id"] == "url:https://pdbtm.unitmp.org/" for item in trace["bibliography"]
    )
    first["asserted_value"]["regions"][0].clear()
    first["source_metadata"]["entry_attributes"].clear()
    assert envelope == before


def test_duplicate_generated_chains_zero_counts_unknown_types_and_insertions_survive():
    envelope = read(
        NATIVE.replace(
            CHAIN, CHAIN + CHAIN + CHAIN.replace('NUM_TM="0"', 'NUM_TM="02"')
        )
    )
    assertions = map_topology(envelope)
    assert len(assertions) == len({a["id"] for a in assertions}) == 3
    assert [a["asserted_value"]["chain_attributes"]["NUM_TM"] for a in assertions] == [
        "0",
        "0",
        "02",
    ]
    assert [a["source_metadata"]["chain_occurrence"] for a in assertions] == [0, 1, 2]
    assert all(
        a["asserted_value"]["chain_attributes"]["CHAINID"] == "a" for a in assertions
    )
    first = assertions[0]["asserted_value"]
    assert first["sequence_text"] == " ACDE\nFG "
    assert first["regions"][0]["pdb_beg"] == "-3A"
    assert first["regions"][0]["type"] == "future-code"
    assert first["regions"][1]["pdb_end"] == "120"


@pytest.mark.parametrize("encoding", ["iso-8859-1", "utf-8"])
def test_declared_encoding_preserves_non_ascii_document_bytes_and_separate_xml_character_data(
    encoding,
):
    text = (
        NATIVE.replace("iso-8859-1", encoding)
        .replace("synthetic format case", "synthetic café")
        .replace(" ACDE\nFG ", " ACDE&#10;FG ")
    )
    raw = text.encode(encoding)
    assert decode_xml(raw) == text
    envelope = read(text)
    assert (
        envelope["native_document_sha256"]
        == hashlib.sha256(raw).hexdigest()
        == native_hash(text)
    )
    assertion = map_topology(envelope)[0]
    assert assertion["source_metadata"]["original_xml"] == text
    assert assertion["asserted_value"]["sequence_text"] == " ACDE\nFG "


@pytest.mark.parametrize(
    "text",
    [
        None,
        {},
        "",
        "<html>error</html>",
        "<pdbtm>",
        NATIVE.replace("https://pdbtm.unitmp.org", "https://other.org"),
        NATIVE.replace('ID="1c3w"', 'ID="1c3x"'),
        NATIVE.replace("<COPYRIGHT>", "<OTHER>").replace("</COPYRIGHT>", "</OTHER>"),
        NATIVE.replace(COPYRIGHT, "New use conditions"),
        NATIVE.replace(
            "</COPYRIGHT>", "</COPYRIGHT><COPYRIGHT>additional conditions</COPYRIGHT>"
        ),
        NATIVE.replace('TMP="yes"', 'TMP=""'),
        NATIVE.replace('NUM_TM="0"', 'NUM_TM="-1"'),
        NATIVE.replace('TYPE="future-type"', 'TYPE=""'),
        NATIVE.replace('CHAINID="a"', 'CHAINID=""'),
        NATIVE.replace(" ACDE\nFG ", ""),
        NATIVE.replace(" ACDE\nFG ", " A?CDEFG "),
        NATIVE.replace("<SEQ>", "<SEQ><extra/>"),
        NATIVE.replace('seq_beg="1"', 'seq_beg="0"'),
        NATIVE.replace('seq_end="2"', 'seq_end="0"'),
        NATIVE.replace('seq_end="6"', 'seq_end="7"'),
        NATIVE.replace('pdb_beg="-3A"', 'pdb_beg=""'),
        NATIVE.replace('pdb_end="120"', 'pdb_end="12:0"'),
        NATIVE.replace('type="future-code"', 'type=""'),
        NATIVE.replace("</pdbtm>", "<UNSUPPORTED/></pdbtm>"),
        NATIVE.replace(CHAIN, CHAIN + CHAIN.replace('seq_end="6"', 'seq_end="999"')),
        NATIVE.replace(CHAIN, ""),
        NATIVE.replace("<pdbtm", '<!DOCTYPE pdbtm [<!ENTITY x "data">]><pdbtm', 1),
        NATIVE.replace("iso-8859-1", "utf-16"),
    ],
)
def test_malformed_late_chains_wrong_identity_changed_terms_or_unsupported_xml_fail(
    text,
):
    with pytest.raises(ConnectorError):
        read(text)


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        True,
        1,
        "",
        "1C3W",
        "pdb:1c3w",
        "1c3w.A",
        "1c3w/",
        "1c3w?",
        "0c3w",
        "1c3w\nother",
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_invalid_query_never_reaches_transport_even_with_skipped_digestion(
    identifier, skip
):
    class Forbidden:
        def topology(self, *args):
            pytest.fail("Invalid query reached PDBTM transport")

    with pytest.raises((ConnectorError, ArgumentError)):
        get_topology(identifier, client=Forbidden(), skip_digestion=skip)


@pytest.mark.parametrize(
    "context",
    [
        {"source": "other"},
        {"kind": "coordinates"},
        {"version": "20250404"},
        {"query": response_query("1c3x")},
        {"truncated": True},
        {"truncated": None},
        {"native_document_sha256": "0" * 64},
    ],
)
def test_client_source_query_revision_cut_and_document_hash_are_not_reassigned(context):
    with pytest.raises(ConnectorError):
        read(**context)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "coordinates"),
        ("version", "20250404"),
        ("truncated", None),
        ("query", {"pdb_id": ID}),
        ("query", {**response_query(ID), "chain": "A"}),
        ("native_document_sha256", "0" * 64),
    ],
)
def test_mapping_rejects_changed_scope_or_invented_revision(key, value):
    envelope = read()
    envelope[key] = value
    with pytest.raises(ConnectorError):
        map_topology(envelope)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_xml_gzip_keep_original_time_hash_terms_and_statement(
    tmp_path, compressed
):
    raw = NATIVE.encode("iso-8859-1")
    body = gzip.compress(raw) if compressed else raw
    path = tmp_path / ("entry.xml.gz" if compressed else "entry.xml")
    path.write_bytes(body)
    scope = metadata()
    scope.update(
        retrieved_at="2026-10-07T20:00:00+00:00", terms={"licence": "PDBTM-CONDITIONAL"}
    )
    client = SnapshotPDBTMClient(
        path,
        source_metadata=scope,
        expected_sha256=hashlib.sha256(body).hexdigest().upper(),
    )
    scope["query"]["pdb_id"] = "1c3x"
    envelope = get_topology(ID, client=client)
    assert (
        envelope["record"] == NATIVE
        and envelope["retrieved_at"] == "2026-10-07T20:00:00+00:00"
    )
    receipt = envelope["snapshot_receipt"]
    assert receipt["document_sha256"] == hashlib.sha256(body).hexdigest()
    assert (
        receipt["native_format"] == "pdbtm_xml"
        and receipt["native_encoding"] == "iso-8859-1"
    )
    assert (
        receipt["declared_terms"]["licence"] == "PDBTM-CONDITIONAL"
        and receipt["source_access_observed"] is False
    )
    assert map_topology(envelope)[0]["source_metadata"]["snapshot_receipt"] == receipt
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_topology(
            ID,
            client=SnapshotPDBTMClient(
                path, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "coordinates"),
        ("version", "20250404"),
        ("query", response_query("1c3x")),
        ("query", {**response_query(ID), "chain": "A"}),
    ],
)
def test_snapshot_cannot_relabel_source_query_or_revision(tmp_path, key, value):
    path = tmp_path / "entry.xml"
    path.write_bytes(NATIVE.encode("iso-8859-1"))
    scope = metadata()
    scope[key] = value
    with pytest.raises(ConnectorError):
        get_topology(ID, client=SnapshotPDBTMClient(path, source_metadata=scope))


@pytest.mark.parametrize(
    "body,compressed",
    [
        (b"", False),
        (b"<html>failed</html>", False),
        (b"\xff", False),
        (b"not gzip", True),
        (gzip.compress(NATIVE.encode())[:-4], True),
    ],
)
def test_unreadable_snapshot_does_not_become_negative_membrane_knowledge(
    tmp_path, body, compressed
):
    path = tmp_path / ("entry.xml.gz" if compressed else "entry.xml")
    path.write_bytes(body)
    with pytest.raises(ConnectorError):
        get_topology(ID, client=SnapshotPDBTMClient(path, source_metadata=metadata()))


def test_unavailable_fixture_http_failure_and_empty_chain_representation_fail_explicitly(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    with pytest.raises(ConnectorError):
        get_topology(ID, client=FixturePDBTMClient(tmp_path))
    with pytest.raises(ConnectorError):
        parse_topology(NATIVE.replace(CHAIN, ""), ID)

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 404, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_topology(ID)


def test_one_native_xml_get_and_replay_preserve_encoding_copyright_and_all_support(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    text = NATIVE.replace("synthetic format case", "synthetic café")
    raw = text.encode("iso-8859-1")
    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(raw)
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = "application/xml"
        return response

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "pdbtm.db")
    with archive.recording():
        first = get_topology(ID)

    def forbidden(*args, **kwargs):
        pytest.fail("Replay attempted network, coordinates or transform execution")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_topology(ID)
    assert calls == [BASE + ID + ".xml"]
    assert first["record"] == second["record"] == text
    assert first["retrieved_at"] == second["retrieved_at"]
    assert (
        first["native_document_sha256"]
        == second["native_document_sha256"]
        == hashlib.sha256(raw).hexdigest()
    )
    assert map_topology(first) == map_topology(second)
    assert second["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert archive.sources()["PDBTM"]["retention"]["share"] == "unknown"


def test_conditional_terms_do_not_become_a_general_noncommercial_or_open_data_grant():
    assert source_terms()["PDBTM"]["licence"] == "PDBTM-CONDITIONAL"
    assert (
        retention("PDBTM")["keep"] == "internal"
        and retention("PDBTM")["share"] == "unknown"
    )
    assert all(verdict("PDBTM", use)["verdict"] == "unknown" for use in USES)
