"""Native mapping POST declarations supply identity without repairing residue maps."""

import copy
import hashlib
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.mappings.ligysis import map_structure_mapping, validate_structure_mapping
from sabueso.tools.db.ligysis import FixtureLigysisClient, get_structure_mapping

PATH = Path("temp_data/ligysis/mapping__P60174__1__7t0q.json")
RAW = PATH.read_bytes()
SHA = "31cecd5b839f7c513fb2d330dfa618abc86b99d1756a8ab0ee37580e961be836"


def native():
    return json.loads(RAW)


def envelope():
    return get_structure_mapping("P60174", 1, "7T0Q", client=FixtureLigysisClient())


def test_original_four_tables_keep_independent_chain_identity_and_unknown_revisions():
    source = envelope()
    before = copy.deepcopy(source)
    rows = map_structure_mapping(source)
    assert len(RAW) == 9185 and hashlib.sha256(RAW).hexdigest() == SHA
    assert len(rows) == 14 and len({row["id"] for row in rows}) == 14
    assert [r["source_metadata"]["received_pair_count"] for r in rows[:4]] == [
        245,
        246,
        245,
        246,
    ]
    identities = [
        r for r in rows if r["source_metadata"]["native_table"] == "chain2acc"
    ]
    assert [r["asserted_value"] for r in identities] == [
        {"native_chain_key": "A", "native_accession": "P60174"},
        {"native_chain_key": "B", "native_accession": "P60174"},
    ]
    assert all(
        r["source_metadata"]["identity_basis"] == "native_chain2acc_declaration"
        for r in identities
    )
    assert [r["asserted_value"]["native_chain_key"] for r in rows[6:]] == list(
        "ABCDEFGH"
    )
    for row in rows:
        assert row["field_path"] == "annotations.ligysis_structure_mapping"
        assert row["subject_ref"].startswith("ligysis:structure_mapping:")
        assert row["source"]["version"] is None and row["retrieved_at"] is None
        assert "location" not in row and "evidence_class" not in row
        assert row["source_metadata"]["identity_context"]["chain_namespace"] is None
        assert row["source_metadata"]["snapshot_receipt"]["document_sha256"] == SHA
    (access,) = source["acquisition_trace"]["records"]
    assert access["access"] == "supplied_file" and access["network_attempts"] == 0
    assert access["native_table_counts"] == {
        "chain2acc": 2,
        "chains": 8,
        "pdb2up": 2,
        "up2pdb": 2,
    }
    rows[0]["asserted_value"]["native_pairs"]["4"] = 999
    rows[0]["source_metadata"]["snapshot_receipt"]["path"] = "changed"
    assert source == before


def test_heteromer_isoform_case_and_missing_parents_are_not_merged_or_filled():
    source = envelope()
    source["record"] = {
        "chain2acc": {"a": "P37840", "A": "P60174-3"},
        "chains": {"assembly-X": "a", "assembly-Y": "a"},
        "pdb2up": {"7t0q": {"orphan": {"04": 5, "4": 6, "0": -1}}},
        "up2pdb": {"7t0q": {"A": {"5": 999}}},
        "future": {"opaque": True},
    }
    rows = map_structure_mapping(source)
    assert len(rows) == 6
    assert rows[0]["asserted_value"]["native_chain_key"] == "orphan"
    assert rows[0]["asserted_value"]["native_pairs"] == {"04": 5, "4": 6, "0": -1}
    assert [r["asserted_value"]["native_accession"] for r in rows[2:4]] == [
        "P37840",
        "P60174-3",
    ]
    assert [r["asserted_value"]["native_original_chain_key"] for r in rows[4:]] == [
        "a",
        "a",
    ]
    assert "native_accession" not in rows[0]["asserted_value"]


def test_explicit_empty_tables_are_not_missing_or_biological_absence():
    source = envelope()
    source["record"] = {
        "chain2acc": {},
        "chains": {},
        "pdb2up": {"7t0q": {}},
        "up2pdb": {"7t0q": {}},
    }
    assert map_structure_mapping(source) == []
    source["record"]["pdb2up"]["7t0q"]["A"] = {}
    assert (
        map_structure_mapping(source)[0]["source_metadata"]["received_pair_count"] == 0
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.pop("chain2acc"),
        lambda p: p.update(chain2acc=[]),
        lambda p: p["chain2acc"].update(C=None),
        lambda p: p["chain2acc"].update(C=""),
        lambda p: p["chain2acc"].update(C="p60174"),
        lambda p: p["chain2acc"].update(C="P60174-0"),
        lambda p: p["chain2acc"].update(C="P60174-3-extra"),
        lambda p: p.update(chains=None),
        lambda p: p["chains"].update({"": "A"}),
        lambda p: p["chains"].update(C=1),
        lambda p: p.update(pdb2up={}),
        lambda p: p["pdb2up"].update(other={}),
        lambda p: p.update(up2pdb={"1hti": {}}),
        lambda p: p["up2pdb"].update({"7t0q": []}),
        lambda p: p["pdb2up"]["7t0q"].update(C=None),
        lambda p: p["pdb2up"]["7t0q"].update(C={"4A": 5}),
        lambda p: p["up2pdb"]["7t0q"].update(C={"5": True}),
        lambda p: p["up2pdb"]["7t0q"].update(C={"5": 4.5}),
        lambda p: p["up2pdb"]["7t0q"].update(C={"5": "4"}),
        lambda p: p.update(future=float("nan")),
    ],
)
def test_late_malformed_or_missing_native_tables_fail_before_any_output(change):
    source = envelope()
    change(source["record"])
    with pytest.raises(ConnectorError):
        map_structure_mapping(source)


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(source="SIFTS"),
        lambda e: e.update(kind="result_page"),
        lambda e: e.update(version="2026"),
        lambda e: e.update(truncated=True),
        lambda e: e.pop("truncated"),
        lambda e: e.update(query=None),
        lambda e: e["query"].update(pdb_id="1hti"),
        lambda e: e["query"].update(pdb_id="7T0Q"),
        lambda e: e["query"].update(accession="p60174"),
        lambda e: e["query"].update(segment=True),
        lambda e: e["query"].update(extra=True),
    ],
)
def test_foreign_revision_cut_or_ambiguous_query_is_refused(change):
    source = envelope()
    change(source)
    with pytest.raises(ConnectorError):
        map_structure_mapping(source)


@pytest.mark.parametrize(
    "query",
    [
        ("P60174", 1, "../7t0q"),
        ("P60174", 1, ""),
        ("P60174", 1, 7),
        ("P60174", True, "7t0q"),
        ("P60174", 0, "7t0q"),
    ],
)
def test_invalid_public_arguments_fail_before_access(query, monkeypatch):
    monkeypatch.setattr(
        "sabueso.tools.db.ligysis.urlopen",
        lambda *a, **k: pytest.fail("Unexpected access"),
    )
    with pytest.raises(ArgumentError):
        get_structure_mapping(*query)


def test_fixture_missing_and_malformed_are_failures(tmp_path):
    with pytest.raises(ConnectorError):
        get_structure_mapping(
            "P60174", 1, "1hti", client=FixtureLigysisClient(tmp_path)
        )
    path = tmp_path / "ligysis" / PATH.name
    path.parent.mkdir()
    path.write_text('{"chain2acc": {}, "chain2acc": {}}', encoding="utf-8", newline="")
    with pytest.raises(ConnectorError):
        get_structure_mapping(
            "P60174", 1, "7t0q", client=FixtureLigysisClient(tmp_path)
        )


def test_one_read_only_post_and_archive_replay_keep_wire_hash_and_original_time(
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

    def download(request, timeout):
        calls.append((request.full_url, request.get_method(), json.loads(request.data)))
        assert "sabueso" in request.get_header("User-agent").lower()
        return Response()

    monkeypatch.setattr(_http, "_urlopen", download)
    archive = RetrievalArchive(tmp_path / "ligysis_mapping.db")
    with archive.recording():
        original = get_structure_mapping("P60174", 1, "7t0q")
    monkeypatch.setattr(
        _http, "_urlopen", lambda *a, **k: pytest.fail("Unexpected replay network")
    )
    with archive.replaying():
        replay = get_structure_mapping("P60174", 1, "7t0q")
    assert calls == [
        (
            "https://www.compbio.dundee.ac.uk/ligysis/get-uniprot-mapping",
            "POST",
            {"proteinId": "P60174", "segmentId": "1", "pdbId": "7t0q"},
        )
    ]
    assert original["retrieved_at"] == replay["retrieved_at"]
    assert map_structure_mapping(original) == map_structure_mapping(replay)
    (access,) = replay["acquisition_trace"]["records"]
    assert access["access"] == "replay" and access["network_attempts"] == 0


def test_http_404_is_failed_access_not_no_chain_identity(monkeypatch):
    from sabueso.tools.db import _http

    def fail(request, timeout):
        raise HTTPError(
            request.full_url, 404, "Not found", {}, io.BytesIO(b"Not found")
        )

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_structure_mapping("P60174", 1, "7t0q")


def test_structure_validation_requires_received_mapping_object():
    with pytest.raises(ConnectorError):
        validate_structure_mapping(None, "7t0q")
