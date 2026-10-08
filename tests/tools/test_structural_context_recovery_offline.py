"""Native EPPIC/PDB-REDO context remains scoped, dimensioned and reproducible."""

import copy
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest
import pyunitwizard as puw

from sabueso import RetrievalArchive
from sabueso.core.errors import ConnectorError
from sabueso.core.terms import retention, verdict
from sabueso.mappings.eppic import map_assemblies, map_interfaces
from sabueso.mappings.pdb_redo import map_refinement, map_versions
from sabueso.tools.db.eppic import FixtureEPPICClient, get_annotations
from sabueso.tools.db.pdb_redo import FixturePDBRedoClient, get_entry, get_versions


def eppic_native():
    return {
        component: json.loads(
            Path(f"temp_data/eppic/{component}__1hti.json").read_text(encoding="utf-8")
        )
        for component in ("entry", "interfaces", "assemblies")
    }


def redo_native(component="entry"):
    return json.loads(
        Path(f"temp_data/pdb_redo/{component}__1cbs.json").read_text(encoding="utf-8")
    )


class EPPICClient:
    def __init__(self, records):
        self.records = records

    def component(self, identifier, component):
        times = {
            "entry": "2026-01-01",
            "interfaces": "2026-01-02",
            "assemblies": "2026-01-03",
        }
        return {
            "record": self.records[component],
            "retrieved_at": times[component],
            "version": None,
        }


class RedoClient:
    def __init__(self, payload):
        self.payload = payload

    def component(self, identifier, component):
        return {"record": self.payload, "retrieved_at": "2026-01-01", "version": None}


def test_eppic_native_calls_alternatives_unit_cell_and_quantities_are_detached():
    envelope = get_annotations("1HTI", client=FixtureEPPICClient())
    before = copy.deepcopy(envelope)
    with puw.context(standard_units=["nanometer", "ps", "K", "mole", "dalton"]):
        interfaces, assemblies = map_interfaces(envelope), map_assemblies(envelope)
    assert len(interfaces) == 9 and len(assemblies) == 3
    assert envelope == before and envelope["version"] is None
    assert interfaces[0]["asserted_value"]["area"] == {
        "value": 1683.6265653733565,
        "unit": "angstrom ** 2",
    }
    assert interfaces[0]["asserted_value"]["chain1"] == "B"
    assert interfaces[0]["asserted_value"]["chain2"] == "A"
    assert interfaces[0]["asserted_value"]["interfaceScores"][0]["confidence"] == -1.0
    assert (
        interfaces[0]["source_metadata"]["native_entry"]["runParameters"][
            "eppicVersion"
        ]
        == "NA"
    )
    assert (
        interfaces[0]["source_metadata"]["native_entry"]["runParameters"][
            "uniProtVersion"
        ]
        == "2026_01"
    )
    assert [a["asserted_value"]["id"] for a in assemblies] == [1, 2, 0]
    assert assemblies[-1]["asserted_value"]["unitCellAssembly"] is True
    assert assemblies[-1]["asserted_value"]["assemblyContents"] is None
    assert {
        s["callName"] for a in assemblies for s in a["asserted_value"]["assemblyScores"]
    } == {"xtal", "bio"}
    for assertion in interfaces + assemblies:
        assert assertion["subject_ref"] == "pdb:1HTI"
        assert (
            assertion["source"]["name"] == "EPPIC"
            and assertion["source"]["version"] is None
        )
        assert "evidence_class" not in assertion["asserted_value"]
    assert [a["count"] for a in envelope["acquisition_trace"]["records"]] == [1, 9, 3]
    assert all(
        a["access"] == "supplied_file"
        and a["network_attempts"] == 0
        and a["retrieved_at"] is None
        for a in envelope["acquisition_trace"]["records"]
    )
    interfaces[0]["source_metadata"]["native_entry"]["runParameters"].clear()
    assemblies[0]["asserted_value"]["assemblyContents"].clear()
    assert envelope == before


def test_eppic_component_times_optional_coverage_and_unknown_methods_remain_native():
    payload = eppic_native()
    payload["entry"]["exhaustiveAssemblyEnumeration"] = False
    payload["interfaces"][0]["interfaceScores"][0].update(
        method="future-method", score=-5, callName="undecided"
    )
    envelope = get_annotations("1hti", client=EPPICClient(payload))
    assert (
        envelope["truncated"] is False
    )  # No client cap; not exhaustive biological coverage.
    interface = map_interfaces(envelope)[0]
    assembly = map_assemblies(envelope)[0]
    assert interface["retrieved_at"] == "2026-01-02"
    assert assembly["retrieved_at"] == "2026-01-03"
    assert (
        interface["source_metadata"]["component_metadata"]["entry"]["retrieved_at"]
        == "2026-01-01"
    )
    assert (
        interface["source_metadata"]["native_entry"]["exhaustiveAssemblyEnumeration"]
        is False
    )
    assert interface["asserted_value"]["interfaceScores"][0]["score"] == -5
    assert envelope["acquisition_trace"]["records"] == []


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p["entry"].update(entryId="2hti"),
        lambda p: p["entry"].update(pdbCode="2hti"),
        lambda p: p["entry"].update(runParameters=None),
        lambda p: p["entry"].pop("exhaustiveAssemblyEnumeration"),
        lambda p: p["interfaces"][0].update(pdbCode="2hti"),
        lambda p: p["interfaces"][0].update(interfaceId=True),
        lambda p: p["interfaces"][0].update(interfaceId=0),
        lambda p: p["interfaces"][0].update(clusterId=0),
        lambda p: p["interfaces"].append(copy.deepcopy(p["interfaces"][0])),
        lambda p: p["interfaces"][0].update(chain1=""),
        lambda p: p["interfaces"][0].update(operator=None),
        lambda p: p["interfaces"][0].update(area=-1),
        lambda p: p["interfaces"][0].update(area=True),
        lambda p: p["interfaces"][0].update(area=float("nan")),
        lambda p: p["interfaces"][0].update(infinite=1),
        lambda p: p["interfaces"][0].update(interfaceScores=None),
        lambda p: p["interfaces"][0]["interfaceScores"][0].update(interfaceId=2),
        lambda p: p["interfaces"][0]["interfaceScores"][0].update(interfaceId=True),
        lambda p: p["interfaces"][0]["interfaceScores"][0].update(score=True),
        lambda p: p["interfaces"][0]["interfaceScores"][0].update(
            confidence=float("inf")
        ),
        lambda p: p["interfaces"][0]["interfaceScores"][0].update(callName=None),
        lambda p: p["interfaces"][0]["interfaceScores"].append(
            copy.deepcopy(p["interfaces"][0]["interfaceScores"][0])
        ),
        lambda p: p["assemblies"][0].update(id=True),
        lambda p: p["assemblies"][0].update(id=-1),
        lambda p: p["assemblies"].append(copy.deepcopy(p["assemblies"][0])),
        lambda p: p["assemblies"][0].update(unitCellAssembly=None),
        lambda p: p["assemblies"][0].update(assemblyContents=None),
        lambda p: p["assemblies"][1]["interfaceClusters"][0].update(pdbCode="2hti"),
        lambda p: p["assemblies"][1]["interfaceClusters"][0].update(clusterId=999),
        lambda p: p["assemblies"][0].update(assemblyScores=None),
        lambda p: p["assemblies"][0]["assemblyScores"][0].update(method=""),
        lambda p: p["assemblies"][0]["assemblyScores"][0].update(callReason=5),
    ],
)
def test_eppic_invalid_native_identity_domain_or_bundle_is_refused(change):
    payload = eppic_native()
    change(payload)
    with pytest.raises(ConnectorError):
        get_annotations("1hti", client=EPPICClient(payload))


def test_eppic_explicit_empty_collections_differ_from_unavailable_components(tmp_path):
    payload = eppic_native()
    payload.update(interfaces=[], assemblies=[])
    envelope = get_annotations("1hti", client=EPPICClient(payload))
    assert map_interfaces(envelope) == map_assemblies(envelope) == []
    directory = tmp_path / "eppic"
    directory.mkdir()
    (directory / "entry__1hti.json").write_bytes(
        Path("temp_data/eppic/entry__1hti.json").read_bytes()
    )
    with pytest.raises(ConnectorError) as caught:
        get_annotations("1hti", client=FixtureEPPICClient(tmp_path))
    assert [r["outcome"] for r in caught.value.acquisition_trace["records"]] == [
        "received",
        "unavailable",
    ]


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(source="Other"),
        lambda e: e.update(version="3.4.0"),
        lambda e: e.update(truncated=True),
        lambda e: e.update(query={"pdb_id": "2hti"}),
        lambda e: e["component_metadata"]["interfaces"].update(response_hash="changed"),
    ],
)
def test_eppic_mapper_refuses_altered_binding_or_component_receipts(change):
    envelope = get_annotations("1hti", client=FixtureEPPICClient())
    change(envelope)
    with pytest.raises(ConnectorError):
        map_interfaces(envelope)


def test_pdb_redo_native_stages_versions_and_unknown_record_revision_are_detached():
    envelope = get_entry("1CBS", client=FixturePDBRedoClient())
    versions = get_versions("1CBS", client=FixturePDBRedoClient())
    before = copy.deepcopy(envelope)
    (assertion,) = map_refinement(envelope)
    stages = assertion["asserted_value"]["r_factor_stages"]
    assert stages == {
        "deposited": {"RFACT": 0.2, "RFREE": 0.237},
        "baseline_refmac": {"RCAL": 0.1781, "RFCAL": 0.1826},
        "restrained_refinement": {"RTLS": 0.1589, "RFTLS": 0.19},
        "final_pdb_redo": {"RFIN": 0.1602, "RFFIN": 0.1941},
    }
    assert assertion["asserted_value"]["pipeline_context"] == {
        "VERSION": 8.22,
        "TIME": "2026-09-02",
        "EXPTYP": "X-ray",
    }
    assert (
        assertion["source_metadata"]["native_record"]["rama-angles"]
        == envelope["record"]["rama-angles"]
    )
    assert "coordinates_url" not in envelope["record"]
    (provenance,) = map_versions(versions)
    assert provenance["asserted_value"] == versions["record"]
    assert (
        provenance["asserted_value"]["data"]["coordinates_revision_minor_mmCIF"] == "3"
    )
    assert provenance["asserted_value"]["software"]["pdb-redo"] == {
        "version": "8.22",
        "used": True,
    }
    assert provenance["asserted_value"]["software"]["gemmi"]["used"] is False
    assert assertion["source"]["version"] is envelope["version"] is None
    assert assertion["subject_ref"] == provenance["subject_ref"] == "pdb:1CBS"
    assertion["source_metadata"]["native_record"]["properties"].clear()
    assert envelope == before


def test_pdb_redo_null_zero_and_unstated_factors_remain_distinct():
    payload = redo_native()
    payload["properties"].update(RFACT=0.0, RFREE=None)
    del payload["properties"]["RCAL"]
    (assertion,) = map_refinement(get_entry("1cbs", client=RedoClient(payload)))
    stages = assertion["asserted_value"]["r_factor_stages"]
    assert stages["deposited"] == {"RFACT": 0.0, "RFREE": None}
    assert "RCAL" not in stages["baseline_refmac"]
    payload["properties"] = {"future_metadata": "literal"}
    assert map_refinement(get_entry("1cbs", client=RedoClient(payload))) == []


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(pdbid="2cbs"),
        lambda p: p.update(properties=None),
        lambda p: p["properties"].update(RFREE=True),
        lambda p: p["properties"].update(RFFIN=-1),
        lambda p: p["properties"].update(RFCAL=101),
        lambda p: p["properties"].update(RFACT="0.2"),
        lambda p: p["properties"].update(RFIN=float("inf")),
        lambda p: p["properties"].update(VERSION=True),
        lambda p: p["properties"].update(VERSION=0),
        lambda p: p["properties"].update(TIME="2026-02-30"),
        lambda p: p["properties"].update(TIME=20260902),
        lambda p: p.update(unknown=float("nan")),
    ],
)
def test_pdb_redo_bad_identity_native_factors_or_pipeline_context_fail(change):
    payload = redo_native()
    change(payload)
    with pytest.raises(ConnectorError):
        get_entry("1cbs", client=RedoClient(payload))


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p["data"].update(PDBID="2cbs"),
        lambda p: p.update(data=None),
        lambda p: p.update(software=[]),
        lambda p: p["software"]["pdb-redo"].update(used=1),
        lambda p: p["software"]["pdb-redo"].update(version=8.22),
    ],
)
def test_pdb_redo_version_binding_and_native_software_types_are_checked(change):
    payload = redo_native("versions")
    change(payload)
    with pytest.raises(ConnectorError):
        get_versions("1cbs", client=RedoClient(payload))


@pytest.mark.parametrize(
    "identifier", ["../1hti", "pdb:1hti", "1hti/extra", "pdb_00001hti", "", None]
)
def test_invalid_ids_never_reach_either_structural_source(identifier):
    class Forbidden:
        def component(self, identifier, component):
            raise AssertionError("Invalid identity must not query")

    for function in (get_annotations, get_entry, get_versions):
        with pytest.raises(Exception) as caught:
            function(identifier, client=Forbidden())
        assert not isinstance(caught.value, AssertionError)


class Response(io.BytesIO):
    status = 200

    def __init__(self, raw):
        super().__init__(raw)
        self.headers = Message()
        self.headers["Content-Type"] = "application/json"


def test_online_contexts_archive_replay_keep_every_component_original_time(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    calls = []

    def download(request, timeout):
        url = request.full_url
        calls.append(url)
        if "eppic-rest" in url:
            component = url.split("/")[-2]
            component = "entry" if component == "pdb" else component
            path = f"temp_data/eppic/{component}__1hti.json"
        else:
            component = "entry" if url.endswith("data.json") else "versions"
            path = f"temp_data/pdb_redo/{component}__1cbs.json"
        return Response(Path(path).read_bytes())

    monkeypatch.setattr(_http, "_urlopen", download)
    archive = RetrievalArchive(tmp_path / "context.db")
    with archive.recording():
        original = get_annotations("1hti"), get_entry("1cbs"), get_versions("1cbs")

    def forbidden(*args, **kwargs):
        raise AssertionError("Archive replay must not query sources")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        replay = get_annotations("1hti"), get_entry("1cbs"), get_versions("1cbs")
    assert len(calls) == 5
    assert original[0]["component_metadata"] == replay[0]["component_metadata"]
    assert map_interfaces(original[0]) == map_interfaces(replay[0])
    assert map_assemblies(original[0]) == map_assemblies(replay[0])
    assert map_refinement(original[1]) == map_refinement(replay[1])
    assert map_versions(original[2]) == map_versions(replay[2])
    assert all(
        r["access"] == "replay"
        for e in replay
        for r in e["acquisition_trace"]["records"]
    )


def test_eppic_later_failure_keeps_successful_entry_access_separate(monkeypatch):
    from sabueso.tools.db import _http

    def download(request, timeout):
        if "/pdb/" in request.full_url:
            return Response(Path("temp_data/eppic/entry__1hti.json").read_bytes())
        raise HTTPError(request.full_url, 404, "Missing route", Message(), None)

    monkeypatch.setattr(_http, "_urlopen", download)
    with pytest.raises(ConnectorError) as caught:
        get_annotations("1hti")
    trace = caught.value.acquisition_trace["records"]
    assert [r["outcome"] for r in trace] == ["received", "failed"]
    assert [r["received_responses"] for r in trace] == [
        1,
        0,
    ]  # The simulated HTTP error has no body.
    assert [r["network_attempts"] for r in trace] == [1, 1]
    assert trace[0]["response_identity"]["hash"]


@pytest.mark.parametrize("status", [404, 500])
def test_pdb_redo_http_failure_does_not_prove_record_absence(status, monkeypatch):
    from sabueso.tools.db import _http

    def download(request, timeout):
        raise HTTPError(request.full_url, status, "Service failure", Message(), None)

    monkeypatch.setattr(_http, "_urlopen", download)
    with pytest.raises(ConnectorError) as caught:
        get_entry("1hti")
    assert caught.value.acquisition_trace["records"][0]["outcome"] == "failed"


def test_missing_redo_fixture_is_unavailable_and_wrong_source_envelope_is_refused(
    tmp_path,
):
    with pytest.raises(ConnectorError) as caught:
        get_entry("1cbs", client=FixturePDBRedoClient(tmp_path))
    assert caught.value.acquisition_trace["records"][0]["outcome"] == "unavailable"
    envelope = get_entry("1cbs", client=FixturePDBRedoClient())
    for key, value in (
        ("source", "Other"),
        ("kind", "versions"),
        ("version", "8.22"),
        ("truncated", True),
    ):
        changed = {**envelope, key: value}
        with pytest.raises(ConnectorError):
            map_refinement(changed)


def test_structural_provider_terms_keep_unknown_and_stated_reuse_distinct():
    assert verdict("EPPIC", "commercial_product")["verdict"] == "unknown"
    assert retention("EPPIC")["share"] == "unknown"
    assert retention("EPPIC")["reason"] == "licence_not_stated"
    assert verdict("PDB-REDO", "commercial_product")["verdict"] == "allowed"
    assert verdict("PDB-REDO", "derived_dataset")["obligations"] == ["attribution"]
    assert retention("PDB-REDO")["conditions"] == ["attribution"]


@pytest.mark.parametrize("source", ["AAindex", "SIFTS", "PDBe Validation", "EPPIC"])
def test_unstated_reuse_licence_never_grants_raw_response_redistribution(source):
    result = retention(source)
    assert result["keep"] == "internal" and result["share"] == "unknown"
    assert (
        result["licence"] == "NOT-STATED" and result["reason"] == "licence_not_stated"
    )
