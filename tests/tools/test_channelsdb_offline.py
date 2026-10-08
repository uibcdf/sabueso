"""ChannelsDB native annotation scope, numbering gaps and original acquisition."""

import copy
import gzip
import hashlib
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import source_terms
from sabueso.mappings.channelsdb import URL, map_annotations
from sabueso.tools.db.channelsdb import (
    FixtureChannelsDBClient,
    SnapshotChannelsDBClient,
    get_annotations,
)

PATH = Path("temp_data/channelsdb/annotations__1tqn.json")


def native():
    return json.loads(PATH.read_bytes())


class Client:
    def __init__(self, record, **context):
        self.record, self.context = record, context

    def annotations(self, identifier):
        return {
            "record": self.record,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def read(record, **context):
    return get_annotations("1tqn", client=Client(record, **context))


def metadata():
    return {
        "source": "ChannelsDB",
        "kind": "pdb_annotations",
        "query": {"pdb_id": "1tqn"},
    }


def test_native_groups_references_reactions_and_html_entities_stay_unplaced():
    assert len(PATH.read_bytes()) == 13127
    assert (
        hashlib.sha256(PATH.read_bytes()).hexdigest()
        == "9279b3cf4e1329addc20ffd861e18969f65698daf860d310ebb7d11d89d64c5c"
    )
    e = get_annotations("1TQN", client=FixtureChannelsDBClient())
    before = copy.deepcopy(e)
    a = map_annotations(e)
    assert len(a) == 23 and e["record"] == native() and e["truncated"] is False
    assert e["query"] == {"pdb_id": "1tqn"}
    assert a[0]["asserted_value"]["UniProtId"] == "P08684"
    assert len(a[0]["asserted_value"]["Catalytics"]) == 43
    assert a[1]["asserted_value"]["Text"].startswith("G &rarr; D:")
    assert a[-1]["asserted_value"] == {
        "Id": "442",
        "Chain": "A",
        "Reference": "1TQN",
        "ReferenceType": "PDB",
        "Text": "Binding Site: axial binding residue",
    }
    for s in a:
        assert s["subject_ref"] == "pdb:1tqn"
        assert s["source"]["version"] is s["retrieved_at"] is None
        assert "location" not in s["asserted_value"]
        assert "sequence" not in s["asserted_value"]
        assert "no_canonical" in s["source_metadata"]["mapping_scope"]["residues"]
    assert a[0]["source_metadata"]["native_group"] == "EntryAnnotations"
    assert all(s["source_metadata"]["native_group"] == "UniProt" for s in a[1:])
    trace = e["acquisition_trace"]["records"][0]
    assert trace["received_counts"] == {
        "EntryAnnotations": 1,
        "ChannelsDB": 0,
        "UniProt": 22,
    }
    assert trace["count"] == 23 and trace["network_attempts"] == 0
    assert trace["access"] == "supplied_file" and trace["retrieved_at"] is None
    assert "doi:10.1093/nar/gkad1012" in json.dumps(trace["bibliography"])
    a[0]["asserted_value"]["Catalytics"].clear()
    a[1]["source_metadata"]["query"].clear()
    assert e == before
    assert source_terms()["ChannelsDB"]["licence"] == "NOT-STATED"


def test_duplicate_conflicting_occurrences_and_cross_group_equal_ids_never_merge():
    p = native()
    r = p["ResidueAnnotations"]
    r["ChannelsDB"] = [copy.deepcopy(r["UniProt"][0])]
    r["UniProt"].append(copy.deepcopy(r["UniProt"][0]))
    r["UniProt"][-1]["Text"] = "Independent conflicting native declaration"
    p["EntryAnnotations"] *= 2
    p["future_context"] = {"literal": None}
    a = map_annotations(read(p))
    assert len(a) == 26 and len({s["id"] for s in a}) == 26
    assert a[2]["asserted_value"]["Id"] == a[3]["asserted_value"]["Id"]
    assert (
        a[2]["source_metadata"]["native_group"]
        != a[3]["source_metadata"]["native_group"]
    )
    assert a[3]["asserted_value"]["Text"] != a[-1]["asserted_value"]["Text"]


def test_literal_negative_insertion_multichar_chain_and_unknown_reference_are_not_guessed():
    p = native()
    row = p["ResidueAnnotations"]["UniProt"][0]
    row.update(
        Id="-3A",
        Chain="AA",
        ReferenceType="future_kind",
        Reference="",
        Text="",
        future={"x": None},
    )
    p["EntryAnnotations"][0].update(Function="", Name="", Catalytics=["", "literal"])
    a = map_annotations(read(p))
    assert a[1]["asserted_value"] == row
    assert a[1]["asserted_value"]["Chain"] == "AA"
    assert a[0]["asserted_value"]["Function"] == ""


def test_explicit_empty_native_groups_do_not_prove_no_channels_or_function():
    p = {
        "EntryAnnotations": [],
        "ResidueAnnotations": {"ChannelsDB": [], "UniProt": []},
    }
    e = read(p)
    assert map_annotations(e) == []
    assert e["acquisition_trace"]["records"] == []  # undecorated custom client


@pytest.mark.parametrize(
    "payload",
    [None, [], {}, {"detail": "blocked"}, {"Annotations": [], "Channels": {}}],
)
def test_non_native_error_and_geometry_bodies_are_not_annotation_negatives(payload):
    with pytest.raises(ConnectorError):
        read(payload)


@pytest.mark.parametrize("field", ["UniProtId", "Function", "Name", "Catalytics"])
@pytest.mark.parametrize("value", [None, 0, {}, True])
def test_malformed_entry_context_is_rejected_before_any_mapping(field, value):
    p = native()
    p["EntryAnnotations"][0][field] = value
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize("field", ["Id", "Chain", "Reference", "ReferenceType", "Text"])
@pytest.mark.parametrize("value", [None, 0, [], True])
def test_malformed_residue_context_is_rejected_including_late_rows(field, value):
    p = native()
    p["ResidueAnnotations"]["UniProt"][-1][field] = value
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_entry",
        "missing_group",
        "future_group",
        "empty_id",
        "empty_chain",
        "reaction_type",
        "nonfinite",
        "nonarray_group",
    ],
)
def test_missing_unknown_or_malformed_native_groups_and_literals_fail(mutation):
    p = native()
    r = p["ResidueAnnotations"]
    if mutation == "missing_entry":
        p.pop("EntryAnnotations")
    elif mutation == "missing_group":
        r.pop("ChannelsDB")
    elif mutation == "future_group":
        r["future"] = []
    elif mutation == "empty_id":
        r["UniProt"][0]["Id"] = ""
    elif mutation == "empty_chain":
        r["UniProt"][0]["Chain"] = ""
    elif mutation == "reaction_type":
        p["EntryAnnotations"][0]["Catalytics"].append(0)
    elif mutation == "nonfinite":
        p["future"] = float("inf")
    else:
        r["ChannelsDB"] = {}
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize(
    "identifier", [None, "", "0tqn", "1tqn?x", "1tqn/", "pdb:1tqn", "1TqNXX", 1]
)
@pytest.mark.parametrize("skip", [False, True])
def test_unsafe_identifier_never_reaches_client(identifier, skip):
    class Forbidden:
        def annotations(self, identifier):
            pytest.fail("Invalid request reached client")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_annotations(identifier, client=Forbidden(), skip_digestion=skip)


@pytest.mark.parametrize(
    "context",
    [
        {"source": "other"},
        {"kind": "channels"},
        {"query": {"pdb_id": "1hti"}},
        {"version": "1.0.0"},
        {"truncated": True},
        {"truncated": None},
    ],
)
def test_custom_client_cannot_override_query_revision_or_cut(context):
    with pytest.raises(ConnectorError):
        read(native(), **context)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "channels"),
        ("query", {}),
        ("query", {"pdb_id": "1TQN"}),
        ("version", "1.0.0"),
        ("truncated", None),
    ],
)
def test_mapping_requires_canonical_source_query_and_full_received_dto(key, value):
    e = read(native())
    e[key] = value
    with pytest.raises(ConnectorError):
        map_annotations(e)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_snapshot_keeps_bytes_hash_time_and_declared_terms(tmp_path, compressed):
    raw = gzip.compress(PATH.read_bytes()) if compressed else PATH.read_bytes()
    p = tmp_path / ("native.json.gz" if compressed else "native.json")
    p.write_bytes(raw)
    m = metadata()
    m.update(retrieved_at="2026-10-07T12:00:00+00:00", terms={"licence": "NOT-STATED"})
    client = SnapshotChannelsDBClient(
        p, source_metadata=m, expected_sha256=hashlib.sha256(raw).hexdigest()
    )
    m["query"]["pdb_id"] = "1hti"
    e = get_annotations("1tqn", client=client)
    assert e["record"] == native() and e["retrieved_at"] == "2026-10-07T12:00:00+00:00"
    receipt = e["snapshot_receipt"]
    assert receipt["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["declared_terms"] == {"licence": "NOT-STATED"}
    assert receipt["source_access_observed"] is False
    assert map_annotations(e)[0]["source_metadata"]["snapshot_receipt"] == receipt
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_annotations(
            "1tqn",
            client=SnapshotChannelsDBClient(
                p, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "channels"),
        ("version", "1.0.0"),
        ("query", {"pdb_id": "1hti"}),
        ("query", {"pdb_id": "1tqn", "assembly": "1"}),
    ],
)
def test_snapshot_declarations_must_match_exact_query_scope(tmp_path, key, value):
    m = metadata()
    m[key] = value
    with pytest.raises(ConnectorError):
        get_annotations(
            "1tqn", client=SnapshotChannelsDBClient(PATH, source_metadata=m)
        )


@pytest.mark.parametrize(
    "raw", [b'{"a":1,"a":2}', b'{"x":NaN}', b"\xff", b"<html>blocked</html>"]
)
def test_unreadable_snapshot_is_not_empty(tmp_path, raw):
    p = tmp_path / "native.json"
    p.write_bytes(raw)
    with pytest.raises(ConnectorError):
        get_annotations(
            "1tqn", client=SnapshotChannelsDBClient(p, source_metadata=metadata())
        )


def test_missing_fixture_and_snapshot_fail(tmp_path):
    for c in [
        FixtureChannelsDBClient(tmp_path),
        SnapshotChannelsDBClient(tmp_path / "missing.json", source_metadata=metadata()),
    ]:
        with pytest.raises(ConnectorError):
            get_annotations("1tqn", client=c)


def test_failed_http_is_not_a_native_empty_annotation_object(monkeypatch):
    from sabueso.tools.db import _http

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 404, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_annotations("1tqn")


def test_one_get_archive_replay_never_fetches_channels_assembly_or_references(
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
    archive = RetrievalArchive(tmp_path / "channels.db")
    with archive.recording():
        first = get_annotations("1TQN")

    def forbidden(*args, **kwargs):
        pytest.fail("Replay fetched another component")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_annotations("1tqn")
    assert calls == [URL + "1tqn"]
    assert first["record"] == second["record"] == native()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert (
        first["download_sha256"]
        == second["download_sha256"]
        == hashlib.sha256(PATH.read_bytes()).hexdigest()
    )
    assert map_annotations(first) == map_annotations(second)
    assert second["acquisition_trace"]["records"][0]["network_attempts"] == 0
