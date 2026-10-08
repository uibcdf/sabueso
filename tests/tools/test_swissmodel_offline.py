"""Native Repository occurrences, source sequence identity and bounded transport."""

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
from sabueso.core.terms import source_terms, verdict
from sabueso.mappings.swissmodel import SOURCE, map_structures
from sabueso.tools.db.swissmodel import FixtureSwissModelClient, get_metadata

PATH = Path("temp_data/swissmodel/metadata__P60174.json")


def native():
    return json.loads(PATH.read_bytes())


def rows(payload):
    return payload["result"]["structures"]


def model(payload):
    return next(r for r in rows(payload) if r["provider"] == "SWISSMODEL")


def segment(payload):
    return rows(payload)[0]["chains"][0]["segments"][0]


class Client:
    def __init__(self, payload):
        self.payload = payload

    def metadata(self, identifier):
        return {"record": self.payload, "retrieved_at": "2026-01-01", "version": None}


def test_native_hstim_preserves_all_providers_chains_and_score_dictionary():
    envelope = get_metadata("p60174", client=FixtureSwissModelClient())
    before = copy.deepcopy(envelope)
    assertions = map_structures(envelope)
    assert len(assertions) == 30 and len({a["id"] for a in assertions}) == 30
    payload = native()
    assert sum(len(c["segments"]) for r in rows(payload) for c in r["chains"]) == 57
    for index, assertion in enumerate(assertions):
        assert assertion["asserted_value"]["native_structure"] == rows(payload)[index]
        assert assertion["subject_ref"] == "uniprot:P60174"
        assert assertion["source"]["name"] == SOURCE
        assert assertion["source"]["version"] is None
        assert (
            assertion["source_metadata"]["sequence"]["value"]
            == payload["result"]["sequence"]
        )
        assert assertion["source_metadata"]["sequence"]["revision"] is None
        assert assertion["source_metadata"]["sequence"]["crc64"] == "73844175635F858E"
        assert assertion["source_metadata"]["native_structure_index"] == index
        assert (
            "no_current_UniProt"
            in assertion["source_metadata"]["mapping_scope"]["coordinates"]
        )
        assert "quality_class" not in assertion["asserted_value"]
        assert "model_id" not in assertion["asserted_value"]
    homology = next(
        a
        for a in assertions
        if a["asserted_value"]["native_structure"]["provider"] == "SWISSMODEL"
    )
    value = homology["asserted_value"]["native_structure"]
    assert value["template"] == "4poc.1.A" and value["identity"] == 100.0
    assert len(value["qmean"]) == 18 and value["qmean"]["cbeta_z_score"] == -1.358
    assert value["md5"] == payload["result"]["md5"]
    assert [
        (c["segments"][0]["uniprot"]["from"], c["segments"][0]["smtl"]["from"])
        for c in value["chains"]
    ] == [(4, 9), (3, 8)]
    first = assertions[0]["asserted_value"]["native_structure"]
    assert first["template"] == "1klu" and first["method"] == "X-RAY DIFFRACTION"
    assert isinstance(first["in_complex_with"], dict)
    assert (
        segment(payload)["uniprot"]["from"] == 23
        and segment(payload)["pdb"]["from"] == 1
    )
    access = envelope["acquisition_trace"]["records"][0]
    assert access["count"] == 30 and access["provider_counts"] == {
        "PDB": 29,
        "SWISSMODEL": 1,
    }
    assert access["source_version"]["value"] is None
    assert access["native_api_version"] == "2.0"
    assert access["retrieved_at"] is None and access["network_attempts"] == 0
    assert access["access"] == "supplied_file"
    assert (
        access["snapshot_receipt"]["document_sha256"]
        == hashlib.sha256(PATH.read_bytes()).hexdigest()
    )
    ids = {c["id"] for c in access["bibliography"]}
    assert {"doi:10.1093/nar/gkw1132", "doi:10.1093/nar/gky427"} <= ids
    assert any(
        "primary_publications_not_fetched" in gap for gap in access["bibliography_gaps"]
    )
    assertions[0]["asserted_value"]["native_structure"]["chains"].clear()
    homology["source_metadata"]["native_result_context"]["uniprot_entries"].clear()
    assert envelope == before


def test_equal_native_occurrences_target_md5_and_templates_do_not_merge():
    payload = native()
    rows(payload).append(copy.deepcopy(rows(payload)[0]))
    assertions = map_structures(get_metadata("P60174", client=Client(payload)))
    assert len(assertions) == len({a["id"] for a in assertions}) == 31
    assert assertions[0]["asserted_value"] == assertions[-1]["asserted_value"]
    assert (
        assertions[0]["source_metadata"]["native_structure_hash"]
        == assertions[-1]["source_metadata"]["native_structure_hash"]
    )
    assert (
        len({a["asserted_value"]["native_structure"]["md5"] for a in assertions}) == 1
    )


def test_different_source_sequence_stays_distinct_without_canonical_revision_guess():
    original, changed = native(), native()
    result = changed["result"]
    result["sequence"] = "A" + result["sequence"][1:]
    result["md5"] = hashlib.md5(result["sequence"].encode()).hexdigest()
    for row in rows(changed):
        row["md5"] = result["md5"]
    a = map_structures(get_metadata("P60174", client=Client(original)))
    b = map_structures(get_metadata("P60174", client=Client(changed)))
    assert (
        a[0]["asserted_value"]["target_sequence_id"]
        != b[0]["asserted_value"]["target_sequence_id"]
    )
    assert {r["id"] for r in a}.isdisjoint(r["id"] for r in b)
    assert a[0]["source"]["version"] is b[0]["source"]["version"] is None


def test_zero_null_missing_and_unknown_native_context_survive_without_rescoring():
    payload = native()
    row = model(payload)
    row.update(
        gmqe=0,
        similarity=None,
        qmean={"positive": 0, "negative": -99, "missing": None},
        provider="FUTURE_PROVIDER",
    )
    row.pop("template_qsqe")
    payload["result"]["uniprot_entries"].append(
        {"ac": "P00938", "id": "OTHER_ENTRY", "isoid": 2}
    )
    payload["result"]["future_context"] = {"literal": None}
    payload["future_service_context"] = {"literal": "raw"}
    assertion = map_structures(get_metadata("P60174", client=Client(payload)))[-1]
    assert assertion["asserted_value"]["native_structure"] == row
    assert assertion["subject_ref"] == "uniprot:P60174"
    assert assertion["source_metadata"]["native_result_context"]["future_context"] == {
        "literal": None
    }
    assert assertion["source_metadata"]["native_response_context"][
        "future_service_context"
    ] == {"literal": "raw"}


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(api_version="3.0"),
        lambda p: p.update(query_date="2026-10-06"),
        lambda p: p["query"].update(ac="P00938"),
        lambda p: p["query"].update(identifiers="P00938"),
        lambda p: p["query"].update(provider=None),
        lambda p: p["query"].update(range="3-249"),
        lambda p: p["result"].update(sequence_length=True),
        lambda p: p["result"].update(sequence_length=248),
        lambda p: p["result"].update(sequence="AC D"),
        lambda p: p["result"].update(md5="0" * 32),
        lambda p: p["result"].update(crc64=None),
        lambda p: p["result"].update(uniprot_entries=[]),
        lambda p: p["result"]["uniprot_entries"][0].update(ac="P00938"),
        lambda p: p["result"]["uniprot_entries"][0].update(isoid=True),
        lambda p: p["result"].pop("structures"),
        lambda p: p["result"].update(structures=None),
        lambda p: rows(p).append(None),
        lambda p: rows(p)[0].update(md5="model_id"),
        lambda p: rows(p)[0].update(coverage=float("nan")),
        lambda p: rows(p)[0].update(coverage=True),
        lambda p: rows(p)[0].update(coverage=2),
        lambda p: rows(p)[0].update(to=250),
        lambda p: rows(p)[0].update(**{"from": 24}),
        lambda p: rows(p)[0].update(coordinates=None),
        lambda p: model(p).update(qmean=0.902),
        lambda p: model(p).update(qmean={"score": True}),
        lambda p: model(p).update(gmqe="0.968"),
        lambda p: rows(p)[0].update(chains=[]),
        lambda p: rows(p)[0]["chains"][0].update(segments=[]),
        lambda p: segment(p).update(smtl=copy.deepcopy(segment(p)["pdb"])),
        lambda p: segment(p).pop("pdb"),
        lambda p: segment(p)["uniprot"].update(aligned_sequence="A" * 15),
        lambda p: segment(p)["pdb"].update(aligned_sequence="A"),
        lambda p: segment(p)["uniprot"].update(**{"from": 0}),
        lambda p: segment(p)["pdb"].update(**{"from": True}),
        lambda p: rows(p)[-1].update(future=float("inf")),
    ],
)
def test_malformed_identity_sequence_scope_or_any_returned_alignment_is_refused(change):
    payload = native()
    change(payload)
    with pytest.raises(ConnectorError):
        get_metadata("P60174", client=Client(payload))


@pytest.mark.parametrize("payload", [None, {}, [], "", {"result": {"structures": []}}])
def test_missing_native_metadata_is_not_an_empty_result(payload):
    with pytest.raises(ConnectorError):
        get_metadata("P60174", client=Client(payload))


def test_explicit_empty_structure_array_is_scoped_received_absence(tmp_path):
    payload = native()
    payload["result"]["structures"] = []
    directory = tmp_path / "swissmodel"
    directory.mkdir()
    (directory / PATH.name).write_text(
        json.dumps(payload), encoding="utf-8", newline=""
    )
    envelope = get_metadata("P60174", client=FixtureSwissModelClient(tmp_path))
    assert map_structures(envelope) == []
    access = envelope["acquisition_trace"]["records"][0]
    assert access["outcome"] == "empty" and access["count"] == 0
    assert "no_native_total" in access["completeness_scope"]


@pytest.mark.parametrize(
    "identifier",
    ["P60174-1", "TPIS_HUMAN", "../P60174", "P60174?x", "P60174/", "", 60174, True],
)
def test_bad_identifier_never_reaches_client_even_when_digestion_is_skipped(identifier):
    class NoAccess:
        def metadata(self, identifier):
            pytest.fail("Invalid identifier reached client")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_metadata(identifier, client=NoAccess(), skip_digestion=True)


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(source="UniProt"),
        lambda e: e.update(kind="models"),
        lambda e: e.update(version="2.0"),
        lambda e: e.update(truncated=True),
        lambda e: e["query"].update(provider="SWISSMODEL"),
        lambda e: e["query"].update(accession="P00938"),
    ],
)
def test_mapper_refuses_unsupported_envelope_before_mapping(change):
    envelope = get_metadata("P60174", client=FixtureSwissModelClient())
    change(envelope)
    with pytest.raises(ConnectorError):
        map_structures(envelope)


def test_missing_fixture_is_unavailable(tmp_path):
    with pytest.raises(ConnectorError) as error:
        get_metadata("P60174", client=FixtureSwissModelClient(tmp_path))
    assert error.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


@pytest.mark.parametrize("status", [404, 500])
def test_http_failure_does_not_claim_no_structures(status, monkeypatch):
    import sabueso.tools.db._http as http

    monkeypatch.setattr(http, "RETRIES", 0)

    def fail(request, timeout):
        raise HTTPError(request.full_url, status, "failed", {}, None)

    monkeypatch.setattr(http, "_urlopen", fail)
    with pytest.raises(ConnectorError) as error:
        get_metadata("P60174")
    access = error.value.acquisition_trace["records"][0]
    assert access["outcome"] == "failed" and access["network_attempts"] == 1


@pytest.mark.parametrize(
    "body",
    [
        b'{"api_version":"2.0","api_version":"1.0"}',
        b'{"result":NaN}',
        b"<html>error</html>",
    ],
)
def test_malformed_wire_json_is_not_repaired(body, monkeypatch):
    import sabueso.tools.db._http as http

    class Answer(io.BytesIO):
        status = 200
        headers = Message()
        headers["Content-Type"] = "application/json"

    monkeypatch.setattr(http, "_urlopen", lambda request, timeout: Answer(body))
    with pytest.raises(ConnectorError) as error:
        get_metadata("P60174")
    assert error.value.acquisition_trace["records"][0]["outcome"] == "failed"


def test_archive_replay_retains_original_time_all_rows_and_no_coordinate_access(
    tmp_path, monkeypatch
):
    import sabueso.tools.db._http as http

    calls = []

    class Answer(io.BytesIO):
        status = 200
        headers = Message()
        headers["Content-Type"] = "application/json"

    def wire(request, timeout):
        calls.append(request.full_url)
        return Answer(PATH.read_bytes())

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "swissmodel.db")
    with archive.recording():
        first = get_metadata("P60174")

    def fail(*args, **kwargs):
        pytest.fail("Replay/mapping accessed a linked resource")

    monkeypatch.setattr(http, "_urlopen", fail)
    with archive.replaying():
        second = get_metadata("P60174")
    assert calls == ["https://swissmodel.expasy.org/repository/uniprot/P60174.json"]
    assert first["record"] == second["record"] == native()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert map_structures(first) == map_structures(second)
    a, b = (e["acquisition_trace"]["records"][0] for e in (first, second))
    assert a["received_responses"] == a["network_attempts"] == 1
    assert b["access"] == "replay" and b["network_attempts"] == 0
    assert a["response_identity"] == b["response_identity"]


def test_repository_data_terms_retain_attribution_and_share_alike():
    terms = source_terms()[SOURCE]
    assert terms["licence"] == "CC-BY-SA-4.0"
    report = verdict(SOURCE, "redistribution")
    assert report["verdict"] == "allowed"
    assert {"attribution", "share_alike"} <= set(report["obligations"])
