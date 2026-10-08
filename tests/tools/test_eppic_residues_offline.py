"""EPPIC native per-side residue detail preserves numbering and calculated scope."""

import copy
import hashlib
import io
import json
from collections import Counter
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest
import pyunitwizard as puw

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.mappings.eppic import map_interface_residues
from sabueso.tools.db.eppic import FixtureEPPICClient, get_interface_residues

RESIDUES = Path("temp_data/eppic/interface_residues__1hti__1.json")
INTERFACES = Path("temp_data/eppic/interfaces__1hti.json")


class Client:
    def __init__(self, residues=None, context=None):
        self.residues = (
            json.loads(RESIDUES.read_bytes()) if residues is None else residues
        )
        self.context = (
            json.loads(INTERFACES.read_bytes()) if context is None else context
        )
        self.calls = []

    def component(self, identifier, component):
        self.calls.append((identifier, component))
        return {"record": self.context, "retrieved_at": "2026-01-01", "version": None}

    def interface_residues(self, identifier, interface_id):
        self.calls.append((identifier, interface_id))
        return {"record": self.residues, "retrieved_at": "2026-01-02", "version": None}


def test_full_native_rows_keep_sides_zero_areas_nan_and_independent_component_support():
    envelope = get_interface_residues("1HTI", 1, client=FixtureEPPICClient())
    before = copy.deepcopy(envelope)
    with puw.context(standard_units=["nanometer", "ps", "K", "mole", "dalton"]):
        assertions = map_interface_residues(envelope)
    assert len(assertions) == 496 and envelope == before
    values = [a["asserted_value"] for a in assertions]
    assert Counter(v["side"] for v in values) == {False: 248, True: 248}
    assert Counter(v["native_chain"] for v in values) == {"B": 248, "A": 248}
    assert Counter(v["region"] for v in values) == {0: 279, -1: 137, 1: 54, 2: 8, 3: 18}
    assert sum(v["burial_fraction"] == "NaN" for v in values) == 44
    assert any(v["buried_surface_area"]["value"] == 0 for v in values)
    assert values[0]["accessible_surface_area"] == {
        "value": 123.05148315429688,
        "unit": "angstrom ** 2",
    }
    assert envelope["query"] == {"pdb_id": "1hti", "interface_id": 1}
    assert envelope["version"] is None and envelope["retrieved_at"] is None
    assert envelope["truncated"] is False
    assert (
        hashlib.sha256(RESIDUES.read_bytes()).hexdigest()
        == "b21afdcf1aca5e0974eecc2dc3297808a4f59ed37aba56db5e40e9459b174c61"
    )
    for row, assertion in zip(envelope["record"]["residues"], assertions):
        assert (
            assertion["subject_ref"] == "pdb:1HTI"
            and assertion["source"]["version"] is None
        )
        assert assertion["source_metadata"]["native_residue"] == row
        assert (
            assertion["source_metadata"]["native_interface"]
            == envelope["record"]["interfaces"][0]
        )
        assert (
            assertion["source_metadata"]["component_metadata"]
            == envelope["component_metadata"]
        )
        assert "uniprot_position" not in assertion["asserted_value"]
    accesses = envelope["acquisition_trace"]["records"]
    assert [a["count"] for a in accesses] == [9, 496]
    assert all(
        a["access"] == "supplied_file" and a["network_attempts"] == 0 for a in accesses
    )
    receipt = envelope["component_metadata"]["residues"]["snapshot_receipt"]
    assert (
        receipt["document_sha256"] == hashlib.sha256(RESIDUES.read_bytes()).hexdigest()
    )
    assertions[0]["source_metadata"]["native_interface"]["chain1"] = "changed"
    assert envelope == before


def test_custom_components_retain_different_times_and_unknown_revision_without_acquisition_claim():
    client = Client()
    envelope = get_interface_residues("1hti", 1, client=client)
    assertion = map_interface_residues(envelope)[0]
    assert client.calls == [("1hti", "interfaces"), ("1hti", 1)]
    assert assertion["retrieved_at"] == "2026-01-02"
    assert (
        assertion["source_metadata"]["component_metadata"]["interfaces"]["retrieved_at"]
        == "2026-01-01"
    )
    assert envelope["acquisition_trace"]["records"] == []


def test_same_chain_names_same_serials_and_duplicate_rows_keep_distinct_occurrences():
    client = Client()
    client.context[0]["chain1"] = client.context[0]["chain2"] = "A"
    row = client.residues[0]
    other = {**row, "side": True}
    client.residues = [row, other, copy.deepcopy(row)]
    assertions = map_interface_residues(
        get_interface_residues("1hti", 1, client=client)
    )
    assert len({a["id"] for a in assertions}) == 3
    assert [a["asserted_value"]["side"] for a in assertions] == [False, True, False]
    assert all(a["asserted_value"]["native_chain"] == "A" for a in assertions)
    assert [a["source_metadata"]["native_row_index"] for a in assertions] == [0, 1, 2]


@pytest.mark.parametrize("serial", [-1, 0, -3, 901])
def test_serials_unknown_residue_labels_regions_entropy_and_fraction_remain_native(
    serial,
):
    row = {
        **Client().residues[0],
        "residueNumber": serial,
        "residueType": None,
        "region": 88,
        "entropyScore": -1,
        "burialFraction": "NaN",
    }
    assertion = map_interface_residues(
        get_interface_residues("1hti", 1, client=Client([row]))
    )[0]
    value = assertion["asserted_value"]
    assert value["native_residue_number"] == serial and value["residue_type"] is None
    assert value["region"] == 88 and value["entropy_score"] == -1
    assert value["burial_fraction"] == "NaN" and "region_label" not in value


@pytest.mark.parametrize(
    "field,value",
    [
        ("side", 1),
        ("residueNumber", True),
        ("residueNumber", "164A"),
        ("region", False),
        ("region", "core"),
        ("residueType", 1),
        ("asa", -1),
        ("asa", True),
        ("asa", "NaN"),
        ("bsa", None),
        ("bsa", float("inf")),
        ("burialFraction", float("nan")),
        ("burialFraction", None),
        ("burialFraction", True),
        ("burialFraction", 1.1),
        ("entropyScore", None),
    ],
)
def test_malformed_native_values_do_not_become_empty_or_zero(field, value):
    row = {**Client().residues[0], field: value}
    with pytest.raises(ConnectorError):
        get_interface_residues("1hti", 1, client=Client([row]))


@pytest.mark.parametrize("payload", [None, {}, [None], [{"side": False}]])
def test_missing_or_incomplete_table_fails(payload):
    client = Client()
    client.residues = payload
    with pytest.raises(ConnectorError):
        get_interface_residues("1hti", 1, client=client)


def test_explicit_empty_residue_array_still_has_native_context():
    envelope = get_interface_residues("1hti", 1, client=Client([]))
    assert (
        envelope["record"]["residues"] == [] and map_interface_residues(envelope) == []
    )
    assert len(envelope["record"]["interfaces"]) == 9


def test_missing_selected_interface_fails_before_detail_access():
    client = Client()
    with pytest.raises(ConnectorError, match="received native context"):
        get_interface_residues("1hti", 10, client=client)
    assert client.calls == [("1hti", "interfaces")]


@pytest.mark.parametrize("selected", [0, -1, True, "1", None])
def test_invalid_interface_id_fails_before_any_access_even_without_digestion(selected):
    client = Client()
    for skip in (False, True):
        with pytest.raises((ArgumentError, ConnectorError)):
            get_interface_residues("1hti", selected, client=client, skip_digestion=skip)
    assert client.calls == []


@pytest.mark.parametrize(
    "identifier", ["../../1hti", "private-job-123", "1hti?x=y", True]
)
def test_private_jobs_or_unsafe_pdb_queries_fail_before_access(identifier):
    client = Client()
    with pytest.raises((ArgumentError, ConnectorError)):
        get_interface_residues(identifier, 1, client=client, skip_digestion=True)
    assert client.calls == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("source", "other"),
        ("kind", "annotations"),
        ("version", "v3"),
        ("truncated", True),
    ],
)
def test_mapper_rejects_foreign_or_incomplete_envelope(field, value):
    envelope = get_interface_residues("1hti", 1, client=Client([]))
    envelope[field] = value
    with pytest.raises(ConnectorError):
        map_interface_residues(envelope)


def test_mapper_refuses_changed_native_context_or_component_hash():
    envelope = get_interface_residues("1hti", 1, client=Client([]))
    envelope["record"]["interfaces"][0]["chain1"] = "changed"
    with pytest.raises(ConnectorError, match="hash differs"):
        map_interface_residues(envelope)
    envelope["component_metadata"]["interfaces"]["response_hash"] = digest(
        canonical_json(envelope["record"]["interfaces"])
    )
    envelope["query"]["interface_id"] = 10
    with pytest.raises(ConnectorError, match="received native context"):
        map_interface_residues(envelope)


def test_missing_detail_fixture_retains_successful_context_receipt(tmp_path):
    path = tmp_path / "eppic"
    path.mkdir()
    (path / INTERFACES.name).write_bytes(INTERFACES.read_bytes())
    with pytest.raises(ConnectorError) as error:
        get_interface_residues("1hti", 1, client=FixtureEPPICClient(tmp_path))
    assert [a["outcome"] for a in error.value.acquisition_trace["records"]] == [
        "received",
        "unavailable",
    ]


def test_shared_two_get_archive_replays_original_sides_parameters_and_times(
    tmp_path, monkeypatch
):
    import sabueso.tools.db._http as http

    calls = []

    class Response(io.BytesIO):
        status = 200

        def __init__(self, path):
            super().__init__(path.read_bytes())
            self.headers = Message()
            self.headers["Content-Type"] = "application/json"

    def wire(request, timeout):
        calls.append((request.get_method(), request.full_url))
        return Response(
            RESIDUES if "interfaceResidues/" in request.full_url else INTERFACES
        )

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "eppic-residues.db")
    with archive.recording():
        original = get_interface_residues("1hti", 1)

    def forbidden(*args, **kwargs):
        pytest.fail("Replay reached the network.")

    monkeypatch.setattr(http, "_urlopen", forbidden)
    with archive.replaying():
        replay = get_interface_residues("1hti", 1)
    assert calls == [
        ("GET", "https://eppic-rest.rcsb.org/rest/api/v3/job/interfaces/1hti"),
        ("GET", "https://eppic-rest.rcsb.org/rest/api/v3/job/interfaceResidues/1hti/1"),
    ]
    assert map_interface_residues(original) == map_interface_residues(replay)
    assert original["component_metadata"] == replay["component_metadata"]
    assert original["retrieved_at"] == replay["retrieved_at"]
    assert all(
        a["network_attempts"] == 1 for a in original["acquisition_trace"]["records"]
    )
    assert all(
        a["access"] == "replay" and a["network_attempts"] == 0
        for a in replay["acquisition_trace"]["records"]
    )


@pytest.mark.parametrize("status", [404, 500])
def test_failed_later_detail_is_failed_access_with_successful_context_retained(
    status, monkeypatch
):
    import sabueso.tools.db._http as http

    monkeypatch.setattr(http, "RETRIES", 0)

    class Response(io.BytesIO):
        status = 200

        def __init__(self):
            super().__init__(INTERFACES.read_bytes())
            self.headers = Message()
            self.headers["Content-Type"] = "application/json"

    def wire(request, timeout):
        if "interfaceResidues/" in request.full_url:
            raise HTTPError(request.full_url, status, "failed", {}, None)
        return Response()

    monkeypatch.setattr(http, "_urlopen", wire)
    with pytest.raises(ConnectorError) as error:
        get_interface_residues("1hti", 1)
    access = error.value.acquisition_trace["records"]
    assert [a["outcome"] for a in access] == ["received", "failed"]
    assert access[1]["network_attempts"] == 1
