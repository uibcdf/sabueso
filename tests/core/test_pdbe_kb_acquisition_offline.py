"""PDBe-KB aggregate observation preserves scientific results and attribution.

Wire examples are synthetic; card regressions use declared frozen public responses.
"""

import io
import json
from datetime import timedelta
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError, URLError

import ackredit
import pytest

import sabueso
from sabueso.core import attribution as adapter
from sabueso.core.card import Card
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import _http, pdbe_kb

KINDS = ("ligand_sites", "interface_residues")
RECORD = {
    "dataType": "synthetic aggregate",
    "sequence": "SYNTHETIC",
    "data": [
        {
            "accession": "BTS",
            "name": "Synthetic group",
            "additionalData": {"type": "UNP", "pdbEntries": ["1sux"]},
            "residues": [
                {
                    "startIndex": 71,
                    "endIndex": 71,
                    "indexType": "UNIPROT",
                    "allPDBEntries": ["1sux", "2oma"],
                    "interactingPDBEntries": [
                        {"pdbId": "1sux", "entityId": 1, "chainIds": "B,A"}
                    ],
                },
                {"startIndex": 72, "endIndex": 72, "indexType": "PDB"},
            ],
        }
    ],
}


@pytest.fixture(autouse=True)
def independent_workflow():
    with ackredit.session("PDBe-KB observation"):
        yield


class Response(io.BytesIO):
    status = 200

    def __init__(self, payload):
        super().__init__(json.dumps(payload).encode())
        self.headers = Message()


def serve(monkeypatch, *, payload=None, error=None):
    calls = []
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)

    def response(request, timeout):
        calls.append(request)
        if error == "timeout":
            raise URLError(TimeoutError("synthetic timeout"))
        if error == "malformed":
            result = Response(None)
            result.seek(0)
            result.write(b"not JSON")
            result.seek(0)
            return result
        if error:
            raise HTTPError(request.full_url, error, "synthetic", Message(), None)
        return Response({"P52270": RECORD} if payload is None else payload)

    monkeypatch.setattr(_http, "_urlopen", response)
    return calls


def lookup(kind, client=None):
    return getattr(pdbe_kb, "get_" + kind)("P52270", client=client)


def observed(result):
    (event,) = result["acquisition_trace"]["records"]
    return event


@pytest.mark.parametrize("kind", KINDS)
def test_original_query_raw_records_structural_scope_and_portable_citations(
    monkeypatch, kind
):
    calls = serve(monkeypatch)
    with ackredit.capture("enclosing workflow") as host:
        result = lookup(kind)
    event = observed(result)
    assert result["record"] == RECORD and result["version"] is None
    assert event["source"] == "PDBe-KB" and event["operation"] == kind
    assert event["query"] == {"accession": "P52270"}
    assert event["source_version"] == {"value": None, "basis": "not_stated"}
    assert event["outcome"] == "received" and event["count"] == 1
    assert (
        event["count_basis"]
        == "source_returned_aggregate_groups_not_mapped_relationships"
    )
    (request,) = event["requests"]
    assert request["method"] == "GET" and request["response_sha256"]
    assert request["url"] == f"{pdbe_kb.PDBE_GRAPH_API}/uniprot/{kind}/P52270"
    assert event["network_attempts"] == len(calls) == 1
    assert event["response_identity"]["hash"] == digest(canonical_json(RECORD))
    (entry,) = event["entries"]
    assert entry["record_index"] == 0 and entry["accession"] == "BTS"
    assert entry["index_types"] == ["PDB", "UNIPROT"]
    assert entry["all_pdb_ids"] == ["1sux", "2oma"]
    assert entry["listed_pdb_ids"] == ["1sux"]
    assert (
        entry["interacting_entries"]
        == RECORD["data"][0]["residues"][0]["interactingPDBEntries"]
    )
    assert "not consulted" in event["structural_context"]["reference_basis"]
    assert "sequence" not in canonical_json(event)
    paper = next(
        b for b in event["bibliography"] if b.get("doi") == "10.1093/nar/gkab988"
    )
    assert paper["doi"] == "10.1093/nar/gkab988" and paper["year"] == 2022
    assert (
        "underlying_structure_primary_citations_not_returned"
        in event["bibliography_gaps"]
    )
    portable = ackredit.Attribution.from_dict(event["provider"]["attribution"])
    roles = {role for use in portable.to_dict()["uses"] for role in use["roles"]}
    assert roles == {"executed_software", "resource_access", "resource_description"}
    assert portable.report(format="bibtex")
    assert any(
        use["context"].get("structural_context") == event["structural_context"]
        for use in host.attribution.to_dict()["uses"]
    )


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_archive_reuse_keeps_original_time_wire_and_aggregate_identities(
    monkeypatch, tmp_path, kind, mode
):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "pdbe.db")
    with archive.recording():
        original = observed(lookup(kind))
    context = (
        archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying()
    )
    with context:
        reused = observed(lookup(kind))
    assert len(calls) == 1 and reused["network_attempts"] == 0
    assert reused["access"] == mode and reused["id"] != original["id"]
    for key in (
        "retrieved_at",
        "source_version",
        "response_identity",
        "entries",
        "pages",
    ):
        assert reused[key] == original[key]
    for key in ("response_sha256", "retrieval_ref", "retrieved_at"):
        assert reused["requests"][0][key] == original["requests"][0][key]
    assert reused["provider"]["status"] == "available"


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("payload", [{}, {"P52270": {}}, {"P52270": {"data": []}}])
def test_evaluated_empty_answers_keep_original_return_or_exception(
    monkeypatch, kind, payload
):
    serve(monkeypatch, payload=payload)
    with sabueso.attribution() as run:
        if payload.get("P52270"):
            result = lookup(kind)
            assert result["record"] == {"data": []}
        else:
            with pytest.raises(RecordNotFoundError) as caught:
                lookup(kind)
            assert caught.value.acquisition_trace["records"] == run.acquisitions
    (event,) = run.acquisitions
    assert event["outcome"] == "empty" and event["count"] == 0
    assert event["provider"]["status"] == "available" and event["pages"]


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("error", [404, 500, "timeout", "malformed"])
def test_http_absence_and_original_failures_keep_retry_facts(monkeypatch, kind, error):
    calls = serve(monkeypatch, error=error)
    with (
        sabueso.attribution() as run,
        pytest.raises(
            RecordNotFoundError if error == 404 else ConnectorError
        ) as caught,
    ):
        lookup(kind)
    (event,) = run.acquisitions
    assert caught.value.acquisition_trace["records"] == [event]
    assert event["outcome"] == ("not_found" if error == 404 else "failed")
    assert event["provider"]["status"] == (
        "available" if error == 404 else "not_attempted"
    )
    assert (
        event["network_attempts"]
        == len(calls)
        == (_http.RETRIES + 1 if error in (500, "malformed") else 1)
    )
    assert not event["pages"]


@pytest.mark.parametrize("kind", KINDS)
def test_missing_fixture_offline_unqueried_and_simulated_failure_are_distinct(
    monkeypatch, tmp_path, kind
):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "missing.db")
    with (
        sabueso.attribution() as run,
        archive.replaying(),
        pytest.raises(ConnectorError),
    ):
        lookup(kind)
    assert run.acquisitions[0]["outcome"] == "not_queried" and not calls
    with pytest.raises(RecordNotFoundError) as caught:
        lookup(kind, pdbe_kb.FixturePDBeKBClient(tmp_path))
    event = caught.value.acquisition_trace["records"][0]
    assert event["outcome"] == "unavailable" and event["access"] == "fixture"
    assert event["provider"]["status"] == "not_attempted"
    with pytest.raises(ConnectorError) as caught:
        lookup(kind, pdbe_kb.FixturePDBeKBClient(tmp_path, failing={"P52270"}))
    assert caught.value.acquisition_trace["records"][0]["outcome"] == "failed"


@pytest.mark.parametrize("kind", KINDS)
def test_declared_empty_fixture_preserves_its_original_time(tmp_path, kind):
    directory = tmp_path / "pdbe_kb"
    directory.mkdir()
    (directory / f"{kind}__P52270.json").write_text("{}", encoding="utf-8")
    result = lookup(
        kind, pdbe_kb.FixturePDBeKBClient(tmp_path, retrieved_at="original")
    )
    event = observed(result)
    assert result["record"] == {} and event["outcome"] == "empty"
    assert event["retrieved_at"] == "original" and event["network_attempts"] == 0
    assert event["provider"]["status"] == "available"


@pytest.mark.parametrize("kind", KINDS)
def test_decoded_unexpected_envelope_keeps_original_failure_and_receipt(
    monkeypatch, kind
):
    serve(monkeypatch, payload=[RECORD])
    with pytest.raises(AttributeError) as caught:
        lookup(kind)
    event = caught.value.acquisition_trace["records"][0]
    assert event["outcome"] == "failed" and event["received_responses"] == 1
    assert event["pages"] and event["provider"]["status"] == "not_attempted"


def test_both_card_enrichers_refresh_pins_and_saved_readers_remain_inert(tmp_path):
    options = {
        "resolver": EntityResolver(FixtureUniProtClient("temp_data")),
        "ligand_sites": True,
        "interfaces": True,
        "pdbe_kb_client": pdbe_kb.FixturePDBeKBClient(
            "temp_data", retrieved_at="original"
        ),
    }
    card, resolution = sabueso.resolve("P52270", **options)
    events = [r for r in card.acquisition_trace["records"] if r["source"] == "PDBe-KB"]
    assert [r["operation"] for r in events] == list(KINDS)
    for event in events:
        raw = json.loads(
            Path(f"temp_data/pdbe_kb/{event['operation']}__P52270.json").read_text()
        )
        assert event["count"] == len(raw["data"])
        assert event["response_identity"]["hash"] == digest(canonical_json(raw))
        assert event["retrieved_at"] == "original" and event["access"] == "fixture"
    assert card.acquisition_trace == resolution.acquisition_trace
    assert card.acquisition_trace["card_ref"] == card.pinned_ref()
    assert "acquisition_trace" not in card.to_dict()
    saved = card.acquisition_trace
    saved["records"].clear()
    assert card.acquisition_trace["records"]
    card.to_json(str(tmp_path / "card.json"))
    before = ackredit.get_attribution().to_dict()
    restored = Card.from_json(str(tmp_path / "card.json"))
    assert (
        restored.acquisition_trace is None
        and restored.snapshot_id() == card.snapshot_id()
    )
    restored.ligand_sites()
    restored.oligomer()
    ackredit.Attribution.from_dict(events[0]["provider"]["attribution"]).report(
        format="bibtex"
    )
    assert json.loads(json.dumps(events)) == events
    assert ackredit.get_attribution().to_dict() == before
    refreshed, resolution = sabueso.refresh_card(card, **options)
    assert refreshed.acquisition_trace["card_ref"] == refreshed.pinned_ref()
    assert (
        len(
            [
                r
                for r in resolution.acquisition_trace["records"]
                if r["source"] == "PDBe-KB"
            ]
        )
        == 2
    )


def test_provider_failure_nested_collectors_and_custom_clients(monkeypatch):
    serve(monkeypatch)
    with sabueso.attribution() as outer:
        with sabueso.attribution() as inner:
            result = lookup("ligand_sites")
    assert (
        outer.acquisitions
        == inner.acquisitions
        == result["acquisition_trace"]["records"]
    )
    monkeypatch.setattr(
        adapter,
        "_load_backend",
        lambda: (_ for _ in ()).throw(RuntimeError("synthetic provider failure")),
    )
    with pytest.warns(Warning, match="Attribution failed"):
        result = lookup("ligand_sites")
    assert (
        result["record"] == RECORD
        and observed(result)["provider"]["status"] == "failed"
    )

    class Custom:
        def ligand_sites(self, accession):
            return {"record": RECORD, "retrieved_at": "custom"}

    result = lookup("ligand_sites", Custom())
    assert result["record"] == RECORD and result["acquisition_trace"]["records"] == []
    assert (
        result["acquisition_trace"]["coverage"]["other_sources_and_custom_clients"]
        == "not_observed"
    )


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("fixture", [True, False])
def test_direct_methods_keep_exact_scientific_envelopes(monkeypatch, kind, fixture):
    serve(monkeypatch)
    client = (
        pdbe_kb.FixturePDBeKBClient("temp_data", retrieved_at="original")
        if fixture
        else pdbe_kb.OnlinePDBeKBClient()
    )
    with sabueso.attribution() as run:
        result = getattr(client, kind)("P52270")
    assert set(result) == {"accession", "record", "retrieved_at"}
    expected = (
        json.loads(Path(f"temp_data/pdbe_kb/{kind}__P52270.json").read_text())
        if fixture
        else RECORD
    )
    assert result["record"] == expected
    assert len(run.acquisitions) == 1 and run.acquisitions[0]["operation"] == kind


@pytest.mark.parametrize("kind", KINDS)
def test_malformed_fixture_is_original_decode_failure_without_completed_credit(
    tmp_path, kind
):
    directory = tmp_path / "pdbe_kb"
    directory.mkdir()
    (directory / f"{kind}__P52270.json").write_text("not JSON", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError) as caught:
        lookup(kind, pdbe_kb.FixturePDBeKBClient(tmp_path))
    event = caught.value.acquisition_trace["records"][0]
    assert event["outcome"] == "failed" and event["access"] == "fixture"
    assert event["provider"]["status"] == "not_attempted" and not event["pages"]


def test_source_group_counts_do_not_invent_mapped_relationships(monkeypatch):
    serve(monkeypatch, payload={"P52270": {"data": [{"residues": []}, None]}})
    result = lookup("ligand_sites")
    event = observed(result)
    assert result["record"] == {"data": [{"residues": []}, None]}
    assert event["count"] == 2
    assert event["entries"][0]["accession"] is None
    assert event["entries"][1] == {"record_index": 1, "outcome": "unobserved"}


def test_concurrent_operations_keep_separate_contexts_in_enclosing_capture(monkeypatch):
    serve(monkeypatch)
    with (
        sabueso.attribution() as run,
        ackredit.capture("parallel aggregate queries") as host,
    ):
        results = _http.gather(lookup, KINDS, workers=2)
    assert {r["operation"] for r in run.acquisitions} == set(KINDS)
    assert {observed(result)["operation"] for _, result in results} == set(KINDS)
    assert {
        use["context"].get("operation")
        for use in host.attribution.to_dict()["uses"]
        if use["context"].get("source") == "PDBe-KB"
    } == set(KINDS)


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("record", [{"dataType": "synthetic"}, {"data": None}])
def test_unstated_aggregate_data_does_not_become_an_empty_group_count(
    monkeypatch, kind, record
):
    serve(monkeypatch, payload={"P52270": record})
    result = lookup(kind)
    event = observed(result)
    assert result["record"] == record
    assert event["outcome"] == "received" and event["count"] is None
    assert event["structural_context"]["aggregate_data_basis"] == "not_stated"
    assert event["structural_context"]["returned_group_count"] is None
    assert event["provider"]["status"] == "available"
