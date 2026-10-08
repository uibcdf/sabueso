"""Original channel membership is retained without repairing source representations."""

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
from sabueso.mappings.channelsdb import (
    CHANNELS_URL,
    map_channel_annotations,
    map_channel_memberships,
)
from sabueso.tools.db.channelsdb import (
    FixtureChannelsDBClient,
    SnapshotChannelsDBClient,
    get_channels,
)

PATH = Path("temp_data/channelsdb/channels__1tqn.json")
RAW = PATH.read_bytes()
SHA = "f279ce91ee43ec6df7854923b8c46b723c31c2ebca204ae0309c3923ba5dd7f7"


def envelope():
    return get_channels("1TQN", client=FixtureChannelsDBClient())


def first(source):
    return source["record"]["Channels"]["CSATunnels_MOLE"][0]


def test_full_original_keeps_all_groups_layers_tokens_and_separate_references():
    assert len(RAW) == 751462 and hashlib.sha256(RAW).hexdigest() == SHA
    source = envelope()
    before = copy.deepcopy(source)
    rows = map_channel_memberships(source)
    comments = map_channel_annotations(source)
    assert len(rows) == 26 and len(comments) == 7
    assert len({r["id"] for r in rows + comments}) == 33
    values = [r["asserted_value"] for r in rows]
    assert sum(len(v["native_layers"]) for v in values) == 910
    assert sum(len(v["native_residue_flow"]) for v in values) == 1225
    assert sum(len(v["native_het_residues"]) for v in values) == 1059
    assert (
        sum(
            len(layer["native_residues"])
            for v in values
            for layer in v["native_layers"]
        )
        == 3338
    )
    assert values[0]["native_header"] == {
        "Id": "20.06",
        "Type": "Solvent channel",
        "Cavity": "1",
        "Auto": False,
    }
    assert values[0]["native_residue_flow"][:2] == ["THR 309 A", "HEM 508 B"]
    assert values[3]["native_header"]["Auto"] == "true"
    # CAVER's named HetResidues list contains ordinary residue labels too.
    assert values[3]["native_het_residues"] == values[3]["native_residue_flow"]
    # Source layer arrays differ in cardinality; neither is zipped or repaired.
    layer = values[3]["native_layers"][0]
    assert len(layer["native_residues"]) == 4 and len(layer["native_flow_indices"]) == 5
    assert comments[0]["asserted_value"]["Id"] == comments[1]["asserted_value"]["Id"]
    assert (
        comments[0]["asserted_value"]["Reference"]
        != comments[1]["asserted_value"]["Reference"]
    )
    for row in rows + comments:
        assert row["subject_ref"].startswith("channelsdb:channel_occurrence:1tqn:")
        assert row["source"]["version"] is row["retrieved_at"] is None
        assert row["source_metadata"]["snapshot_receipt"]["document_sha256"] == SHA
        assert "location" not in row and "evidence_class" not in row
    (access,) = source["acquisition_trace"]["records"]
    assert access["access"] == "supplied_file" and access["network_attempts"] == 0
    assert access["count"] == 33 and len(access["received_counts"]) == 13
    rows[0]["asserted_value"]["native_layers"].clear()
    comments[0]["source_metadata"]["snapshot_receipt"]["path"] = "changed"
    assert source == before


def test_duplicate_channels_cross_group_ids_opaque_tokens_and_empty_layers_survive():
    source = envelope()
    row = first(source)
    row.update(Id=0, Type="future_type", Cavity=-2, Auto="future_flag")
    row["Layers"].update(
        ResidueFlow=["UNK -2 AA", "UNK -2 AA", "ALA 4B a Backbone"],
        HetResidues=["ALA 4B a Backbone"],
        LayersInfo=[
            {
                "Residues": ["different native token"],
                "FlowIndices": ["999", "-1", "opaque"],
            },
            {"Residues": [], "FlowIndices": []},
        ],
    )
    source["record"]["Channels"]["CSATunnels_MOLE"].append(copy.deepcopy(row))
    source["record"]["Channels"]["ReviewedChannels_Caver"] = [copy.deepcopy(row)]
    rows = map_channel_memberships(source)
    assert len(rows) == 28 and len({r["id"] for r in rows}) == 28
    selected = rows[0]["asserted_value"]
    assert selected["native_header"]["Auto"] == "future_flag"
    assert selected["native_residue_flow"] == row["Layers"]["ResidueFlow"]
    assert selected["native_layers"][0]["native_flow_indices"] == [
        "999",
        "-1",
        "opaque",
    ]
    assert selected["native_layers"][1]["native_residues"] == []


def test_empty_received_groups_and_blank_comments_are_not_missing_or_no_tunnels():
    source = envelope()
    for key in source["record"]["Channels"]:
        source["record"]["Channels"][key] = []
    source["record"]["Annotations"] = []
    assert map_channel_memberships(source) == map_channel_annotations(source) == []
    source["record"]["Annotations"] = [
        {
            "Id": "opaque",
            "Name": "",
            "Description": "",
            "Reference": "",
            "ReferenceType": "future",
        }
    ]
    assert map_channel_annotations(source)[0]["asserted_value"]["Reference"] == ""


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e["record"].pop("Annotations"),
        lambda e: e["record"].update(Annotations=None),
        lambda e: e["record"]["Channels"].pop("AlphaFillTunnels_Caver"),
        lambda e: e["record"]["Channels"].update(FutureChannels=[]),
        lambda e: e["record"]["Channels"].update(ReviewedChannels_Caver={}),
        lambda e: e["record"]["Annotations"][-1].update(ReferenceType=None),
        lambda e: first(e).update(Id=True),
        lambda e: first(e).update(Id=""),
        lambda e: first(e).update(Cavity=True),
        lambda e: first(e).update(Auto=1),
        lambda e: first(e).update(Layers=None),
        lambda e: first(e)["Layers"].pop("ResidueFlow"),
        lambda e: first(e)["Layers"].update(HetResidues=[None]),
        lambda e: first(e)["Layers"].update(LayersInfo=None),
        lambda e: first(e)["Layers"]["LayersInfo"][-1].update(Residues=[""]),
        lambda e: first(e)["Layers"]["LayersInfo"][-1].update(FlowIndices=[True]),
        lambda e: first(e)["Layers"]["LayersInfo"][-1].pop("FlowIndices"),
        lambda e: e["record"].update(future=float("nan")),
    ],
)
def test_every_known_table_is_validated_before_either_mapper_outputs(change):
    source = envelope()
    change(source)
    with pytest.raises(ConnectorError):
        map_channel_memberships(source)
    with pytest.raises(ConnectorError):
        map_channel_annotations(source)


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(source="MOLEonline"),
        lambda e: e.update(kind="pdb_annotations"),
        lambda e: e.update(version="1.0.0"),
        lambda e: e.update(truncated=True),
        lambda e: e.pop("truncated"),
        lambda e: e.update(query=None),
        lambda e: e["query"].update(pdb_id="1TQN"),
        lambda e: e["query"].update(extra=True),
    ],
)
def test_foreign_context_revision_cut_and_nonexact_envelopes_are_refused(change):
    source = envelope()
    change(source)
    with pytest.raises(ConnectorError):
        map_channel_memberships(source)


@pytest.mark.parametrize("identifier", [None, "", "../1tqn", "P08684", True])
def test_invalid_public_query_never_reaches_transport(identifier, monkeypatch):
    monkeypatch.setattr(
        "sabueso.tools.db.channelsdb.urlopen",
        lambda *a, **k: pytest.fail("Unexpected access"),
    )
    with pytest.raises((ArgumentError, ConnectorError)):
        get_channels(identifier)


def test_bound_gzip_snapshot_retains_original_digest_time_terms_and_zero_network(
    tmp_path,
):
    path = tmp_path / "channels.json.gz"
    raw = gzip.compress(RAW)
    path.write_bytes(raw)
    metadata = {
        "source": "ChannelsDB",
        "kind": "pdb_channels",
        "query": {"pdb_id": "1tqn"},
        "retrieved_at": "2026-10-08T08:55:00+00:00",
        "terms": {"licence": "NOT-STATED"},
    }
    source = get_channels(
        "1tqn",
        client=SnapshotChannelsDBClient(
            path,
            source_metadata=metadata,
            expected_sha256=hashlib.sha256(raw).hexdigest(),
        ),
    )
    assert source["retrieved_at"] == metadata["retrieved_at"]
    assert (
        source["snapshot_receipt"]["document_sha256"] == hashlib.sha256(raw).hexdigest()
    )
    assert source["snapshot_receipt"]["declared_terms"] == metadata["terms"]
    assert source["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert len(map_channel_memberships(source)) == 26
    metadata["query"] = {"pdb_id": "3tbg"}
    with pytest.raises(ConnectorError):
        get_channels(
            "1tqn", client=SnapshotChannelsDBClient(path, source_metadata=metadata)
        )
    with pytest.raises(ConnectorError):
        get_channels(
            "1tqn",
            client=SnapshotChannelsDBClient(
                path,
                source_metadata={**metadata, "query": {"pdb_id": "1tqn"}},
                expected_sha256="0" * 64,
            ),
        )


def test_unavailable_or_malformed_file_is_failed_access(tmp_path):
    with pytest.raises(ConnectorError):
        get_channels("1tqn", client=FixtureChannelsDBClient(tmp_path))
    directory = tmp_path / "channelsdb"
    directory.mkdir()
    (directory / PATH.name).write_text(
        '{"Channels":{},"Channels":{}}', encoding="utf-8", newline=""
    )
    with pytest.raises(ConnectorError):
        get_channels("1tqn", client=FixtureChannelsDBClient(tmp_path))


def test_one_public_get_and_zero_network_replay_keep_original_time_and_hash(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    calls = []

    class Response(io.BytesIO):
        status = 200

        def __init__(self):
            super().__init__(RAW)
            self.headers = Message()
            self.headers["Content-Type"] = "application/json"

    def wire(request, timeout):
        assert request.get_method() == "GET" and request.data is None
        assert "sabueso" in request.get_header("User-agent").lower()
        calls.append(request.full_url)
        return Response()

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "channels.sqlite")
    with archive.recording():
        source = get_channels("1tqn")
    monkeypatch.setattr(
        _http, "_urlopen", lambda *a, **k: pytest.fail("Unexpected replay network")
    )
    with archive.replaying():
        replay = get_channels("1tqn")
    assert calls == [CHANNELS_URL + "1tqn"]
    assert source["retrieved_at"] == replay["retrieved_at"]
    assert source["download_sha256"] == replay["download_sha256"] == SHA
    assert map_channel_memberships(source) == map_channel_memberships(replay)
    assert map_channel_annotations(source) == map_channel_annotations(replay)
    assert replay["acquisition_trace"]["records"][0]["network_attempts"] == 0


def test_http_404_is_failure_not_no_channel_membership(monkeypatch):
    from sabueso.tools.db import _http

    def fail(request, timeout):
        raise HTTPError(
            request.full_url,
            404,
            "Not found",
            {},
            io.BytesIO(b'{"detail":"Not found"}'),
        )

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_channels("1tqn")


@pytest.mark.parametrize(
    "context",
    [
        {"source": "other"},
        {"kind": "pdb_annotations"},
        {"version": "1.0.0"},
        {"query": {"pdb_id": "3tbg"}},
        {"truncated": True},
    ],
)
def test_custom_client_cannot_rebind_foreign_source_or_cut_native_data(context):
    class Client:
        def channels(self, identifier):
            return {
                "record": json.loads(RAW),
                "retrieved_at": None,
                "version": None,
                **context,
            }

    with pytest.raises(ConnectorError):
        get_channels("1tqn", client=Client())


def test_skipped_digestion_still_refuses_unsafe_structure_before_access(monkeypatch):
    monkeypatch.setattr(
        "sabueso.tools.db.channelsdb.urlopen",
        lambda *a, **k: pytest.fail("Unexpected access"),
    )
    with pytest.raises(ConnectorError):
        get_channels("../1tqn", skip_digestion=True)
