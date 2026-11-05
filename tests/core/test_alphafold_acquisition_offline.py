"""AlphaFold DB acquisition retains model versions, scope and original attribution.

Wire cases are synthetic; public card cases use declared frozen responses.
"""

import io
import json
from copy import deepcopy
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
from sabueso.tools.db import _http, alphafold

MODEL = {
    "entryId": "AF-P52270-F1",
    "modelEntityId": "AF-P52270-F1",
    "latestVersion": 6,
    "allVersions": [2, 3, 4, 5, 6],
    "toolUsed": "AlphaFold Monomer v2.0 pipeline",
    "providerId": "GDM",
    "uniprotAccession": "P52270",
    "uniprotStart": 1,
    "uniprotEnd": 251,
    "modelCreatedDate": "2025-08-01T00:00:00Z",
    "sequenceVersionDate": "1996-10-01T00:00:00Z",
    "sequenceChecksum": "synthetic-checksum",
    "sequence": "SYNTHETIC",
    "pdbUrl": "https://alphafold.ebi.ac.uk/files/AF-P52270-F1-model_v6.pdb",
    "isComplex": False,
}
DEFAULT = object()


@pytest.fixture(autouse=True)
def independent_workflow():
    with ackredit.session("AlphaFold DB observation"):
        yield


class Response(io.BytesIO):
    status = 200

    def __init__(self, payload, *, raw=False):
        super().__init__(payload if raw else json.dumps(payload).encode())
        self.headers = Message()


def serve(monkeypatch, *, payload=DEFAULT, error=None):
    calls = []
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)

    def response(request, timeout):
        calls.append(request)
        if error == "timeout":
            raise URLError(TimeoutError("synthetic timeout"))
        if error == "malformed":
            return Response(b"not JSON", raw=True)
        if error:
            raise HTTPError(request.full_url, error, "synthetic", Message(), None)
        return Response([MODEL] if payload is DEFAULT else payload)

    monkeypatch.setattr(_http, "_urlopen", response)
    return calls


def lookup(accession="P52270", client=None):
    return alphafold.get_prediction(accession, client=client)


def event(result):
    (record,) = result["acquisition_trace"]["records"]
    return record


def test_native_model_query_version_and_recommended_bibliography_keep_distinct_roles(
    monkeypatch,
):
    calls = serve(monkeypatch)
    with ackredit.capture("enclosing model workflow") as host:
        result = lookup()
    record = event(result)
    assert result["record"] == [MODEL] and result["version"] == "v6"
    assert record["source"] == "AlphaFold DB" and record["operation"] == "prediction"
    assert record["query"] == {"accession": "P52270"}
    assert record["outcome"] == "received" and record["count"] == 1
    assert record["source_version"] == {
        "basis": "per_model_version",
        "value": [{"record_index": 0, "model_id": MODEL["entryId"], "value": 6}],
    }
    (entry,) = record["entries"]
    assert entry["source_version"] == {"value": 6, "basis": "model_version"}
    assert entry["model_metadata"]["allVersions"] == MODEL["allVersions"]
    assert entry["model_metadata"]["toolUsed"] == MODEL["toolUsed"]
    assert (
        entry["model_metadata"]["sequenceVersionDate"] == MODEL["sequenceVersionDate"]
    )
    assert entry["artifact_links"] == {"pdbUrl": MODEL["pdbUrl"]}
    assert "sequence" not in entry["model_metadata"]
    assert record["response_identity"]["hash"] == digest(canonical_json([MODEL]))
    assert record["network_attempts"] == len(calls) == 1
    assert record["requests"][0]["url"] == alphafold.ALPHAFOLD_API + "/P52270"
    assert record["requests"][0]["method"] == "GET"
    assert record["requests"][0]["response_sha256"]
    assert (
        record["structural_context"]["artifact_access"]
        == "declared_links_not_downloaded"
    )
    papers = {b["doi"]: b for b in record["bibliography"][1:]}
    assert set(papers) == {
        "10.1093/nar/gkad1011",
        "10.1093/nar/gkab1061",
        "10.1038/s41586-021-03819-2",
    }
    assert [papers[k]["year"] for k in papers] == [2024, 2022, 2021]
    portable = ackredit.Attribution.from_dict(record["provider"]["attribution"])
    assert {r for use in portable.to_dict()["uses"] for r in use["roles"]} == {
        "executed_software",
        "resource_access",
        "resource_description",
    }
    executed = [
        use["item_id"]
        for use in portable.to_dict()["uses"]
        if "executed_software" in use["roles"]
    ]
    assert executed == [record["bibliography"][0]["id"]]
    assert portable.report(format="bibtex")
    assert any(
        use["context"].get("source_version") == record["source_version"]
        for use in host.attribution.to_dict()["uses"]
    )


@pytest.mark.parametrize("fixture", [True, False])
def test_direct_client_returns_original_envelope(monkeypatch, fixture):
    serve(monkeypatch)
    client = (
        alphafold.FixtureAlphaFoldClient("temp_data")
        if fixture
        else alphafold.OnlineAlphaFoldClient()
    )
    with sabueso.attribution() as run:
        result = client.prediction("P52270")
    assert set(result) == {"accession", "retrieved_at", "record"}
    expected = (
        json.loads(Path("temp_data/alphafold/P52270.json").read_text())
        if fixture
        else [MODEL]
    )
    assert result["record"] == expected and len(run.acquisitions) == 1


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_original_models_versions_times_and_archive_receipts_survive_reuse(
    monkeypatch, tmp_path, mode
):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "models.db")
    with archive.recording():
        original = event(lookup())
    context = (
        archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying()
    )
    with context:
        reused = event(lookup())
    assert (
        len(calls) == 1 and reused["access"] == mode and reused["network_attempts"] == 0
    )
    assert reused["id"] != original["id"]
    for key in (
        "query",
        "source_version",
        "entries",
        "pages",
        "retrieved_at",
        "response_identity",
    ):
        assert reused[key] == original[key]
    for key in ("response_sha256", "retrieval_ref", "retrieved_at"):
        assert reused["requests"][0][key] == original["requests"][0][key]
    assert reused["provider"]["status"] == "available"


@pytest.mark.parametrize("error", [404, 500, "timeout", "malformed"])
def test_http_absence_failures_and_retry_facts_remain_original(monkeypatch, error):
    calls = serve(monkeypatch, error=error)
    with pytest.raises(
        RecordNotFoundError if error == 404 else ConnectorError
    ) as caught:
        lookup()
    record = caught.value.acquisition_trace["records"][0]
    assert record["outcome"] == ("not_found" if error == 404 else "failed")
    assert record["provider"]["status"] == (
        "available" if error == 404 else "not_attempted"
    )
    assert (
        record["network_attempts"]
        == len(calls)
        == (_http.RETRIES + 1 if error in (500, "malformed") else 1)
    )
    assert record["pages"] == [] and record["response_identity"] == {
        "basis": "not_received",
        "hash": None,
    }


def test_missing_api_record_never_claims_absence_from_proteome_archives(monkeypatch):
    # Synthetic transport for the documented public Titin example. A prediction
    # API miss says nothing about the provider's separate archive distribution.
    calls = serve(monkeypatch, error=404)
    with pytest.raises(RecordNotFoundError) as caught:
        lookup("Q8WZ42")
    trace = caught.value.acquisition_trace["records"][0]
    assert len(calls) == 1 and trace["requests"][0]["status"] == 404
    assert trace["outcome"] == "not_found"
    scope = trace["structural_context"]["access_scope"]
    assert scope["route"] == "prediction_api"
    assert scope["other_distributions"] == "not_queried"
    assert scope["database_wide_absence"] == "not_established"
    assert "prediction API" in str(caught.value)
    assert "other distribution routes were not checked" in str(caught.value)


@pytest.mark.parametrize("payload", [[], {}, None])
def test_unusable_api_lists_keep_empty_and_unobserved_scope_distinct(
    monkeypatch, payload
):
    calls = serve(monkeypatch, payload=payload)
    with pytest.raises(RecordNotFoundError) as caught:
        lookup()
    trace = caught.value.acquisition_trace["records"][0]
    assert len(calls) == 1
    assert trace["outcome"] == ("empty" if isinstance(payload, list) else "unobserved")
    assert (
        trace["structural_context"]["access_scope"]["database_wide_absence"]
        == "not_established"
    )
    assert "no usable model list" in str(caught.value)
    assert "other distribution routes were not checked" in str(caught.value)


def test_api_miss_replay_keeps_the_original_request_and_scope(monkeypatch, tmp_path):
    calls = serve(monkeypatch, error=404)
    archive = sabueso.RetrievalArchive(tmp_path / "api-missing.db")
    records = []
    messages = []
    for context in (archive.recording(), archive.replaying()):
        with context, pytest.raises(RecordNotFoundError) as caught:
            lookup("Q8WZ42")
        records.append(caught.value.acquisition_trace["records"][0])
        messages.append(str(caught.value))
    original, replay = records
    assert len(calls) == 1 and original["network_attempts"] == 1
    assert replay["access"] == "replay" and replay["network_attempts"] == 0
    assert original["outcome"] == replay["outcome"] == "not_found"
    assert original["structural_context"] == replay["structural_context"]
    assert (
        replay["requests"][0]["retrieved_at"] == original["requests"][0]["retrieved_at"]
    )
    assert messages[0] == messages[1]


def test_missing_fixture_does_not_claim_current_database_or_api_availability(tmp_path):
    with pytest.raises(RecordNotFoundError) as caught:
        lookup(client=alphafold.FixtureAlphaFoldClient(tmp_path))
    trace = caught.value.acquisition_trace["records"][0]
    assert trace["outcome"] == "unavailable" and trace["network_attempts"] == 0
    assert trace["structural_context"]["access_scope"]["route"] == "fixture"
    assert "Database availability was not checked" in str(caught.value)


@pytest.mark.parametrize("fixture_present", [False, True])
def test_new_card_distinguishes_missing_fixture_from_a_retained_empty_list(
    fixture_present, tmp_path
):
    from sabueso._private.smonitor.warnings import EnrichmentFailedWarning

    if fixture_present:
        (tmp_path / "alphafold").mkdir()
        (tmp_path / "alphafold/P52270.json").write_text("[]", encoding="utf-8")

    def build():
        return sabueso.resolve_protein_card(
            "P52270",
            EntityResolver(FixtureUniProtClient("temp_data")),
            predicted_structures=True,
            alphafold_client=alphafold.FixtureAlphaFoldClient(tmp_path),
        )[0]

    if fixture_present:
        card = build()
    else:
        with pytest.warns(EnrichmentFailedWarning):
            card = build()
    report = next(
        r for r in card.quality["enrichments"] if r["source"] == "AlphaFold DB"
    )
    row = next(
        r for r in card.knowledge_state()["rows"] if r["source"] == "AlphaFold DB"
    )
    assert not card.relationships("has_predicted_structure")
    if fixture_present:
        assert report["status"] == "added" and report["count"] == 0
        assert row["state"] == "not_stated" and row["count"] == 0
    else:
        assert report["status"] == "error" and row["state"] == "unavailable"
        assert row["count"] is None
        assert "Database availability was not checked" in row["basis"]["detail"]


def test_api_miss_detail_survives_card_human_agent_and_inert_saved_reading(
    monkeypatch, tmp_path
):
    # Counterfactual API404 on the existing public P52270 identity fixture, not
    # an observation that this actual protein lacks a model.
    calls = serve(monkeypatch, error=404)
    card, _ = sabueso.resolve_protein_card(
        "P52270",
        EntityResolver(FixtureUniProtClient("temp_data")),
        predicted_structures=True,
        alphafold_client=alphafold.OnlineAlphaFoldClient(),
    )
    record = next(
        r for r in card.quality["enrichments"] if r["source"] == "AlphaFold DB"
    )
    assert record["status"] == "not_found"
    assert "other distribution routes were not checked" in record["detail"]
    assert not card.relationships("has_predicted_structure")
    assert not [
        r
        for r in card.source_assertion_store.to_list()
        if r["source"]["name"] == "AlphaFold DB"
    ]
    explorer = card.explore()
    coverage = explorer.view("coverage").filter("source", equals="AlphaFold DB")
    item = coverage.items()[0]
    row = item.open().native_payload
    assert row["state"] == "not_stated" and row["basis"]["detail"] == record["detail"]
    agent = explorer.access.read(item.payload_location).page()
    basis = next(entry for entry in agent["items"] if entry["key"] == "basis")
    details = explorer.access.read(basis["location"]).page()
    detail = next(
        entry["value"] for entry in details["items"] if entry["key"] == "detail"
    )
    assert detail == record["detail"]
    assert "prediction API" in str(coverage)
    assert "distribution routes" in coverage._repr_html_()
    path = tmp_path / "api-scope.json.gz"
    coverage.save(path, compression="gzip")

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Saved source scope cannot rebuild Cards or query a provider"
        )

    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(_http, "_urlopen", forbidden)
    restored = sabueso.read_exploration(path)
    assert restored.native_payload == coverage.native_payload
    assert restored.items()[0].open().native_payload == row
    assert len(calls) == 1


def test_public_prediction_content_is_unchanged_by_explicit_distribution_scope():
    original = json.loads(Path("temp_data/alphafold/P52270.json").read_text())
    result = lookup(client=alphafold.FixtureAlphaFoldClient("temp_data"))
    assert result["record"] == original
    scope = event(result)["structural_context"]["access_scope"]
    assert scope["route"] == "fixture" and scope["other_distributions"] == "not_queried"


def test_evaluated_empty_response_keeps_original_exception_and_replay_time(
    monkeypatch, tmp_path
):
    calls = serve(monkeypatch, payload=[])
    archive = sabueso.RetrievalArchive(tmp_path / "empty.db")
    records = []
    for context in (archive.recording(), archive.replaying()):
        with context, pytest.raises(RecordNotFoundError) as caught:
            lookup()
        records.append(caught.value.acquisition_trace["records"][0])
    original, replayed = records
    assert original["outcome"] == replayed["outcome"] == "empty"
    assert (
        replayed["access"] == "replay"
        and replayed["network_attempts"] == 0
        and len(calls) == 1
    )
    assert replayed["retrieved_at"] == original["retrieved_at"]
    assert replayed["provider"]["status"] == "available"
    assert replayed["count"] == 0 and replayed["source_version"]["value"] is None


def test_missing_fixture_offline_unqueried_and_failed_fixture_remain_distinct(
    monkeypatch, tmp_path
):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "missing.db")
    with archive.replaying(), pytest.raises(ConnectorError) as caught:
        lookup()
    assert (
        caught.value.acquisition_trace["records"][0]["outcome"] == "not_queried"
        and not calls
    )
    with pytest.raises(RecordNotFoundError) as caught:
        lookup(client=alphafold.FixtureAlphaFoldClient(tmp_path))
    assert caught.value.acquisition_trace["records"][0]["outcome"] == "unavailable"
    with pytest.raises(ConnectorError) as caught:
        lookup(client=alphafold.FixtureAlphaFoldClient(tmp_path, failing={"P52270"}))
    record = caught.value.acquisition_trace["records"][0]
    assert (
        record["outcome"] == "failed"
        and record["provider"]["status"] == "not_attempted"
    )


def test_declared_empty_fixture_has_its_original_time_and_no_models(tmp_path):
    directory = tmp_path / "alphafold"
    directory.mkdir()
    (directory / "P52270.json").write_text("[]", encoding="utf-8")
    result = lookup(
        client=alphafold.FixtureAlphaFoldClient(tmp_path, retrieved_at="original")
    )
    record = event(result)
    assert result["record"] == [] and record["outcome"] == "empty"
    assert (
        record["retrieved_at"] == "original"
        and record["provider"]["status"] == "available"
    )


@pytest.mark.parametrize("version", [0, None, 7])
def test_native_per_model_versions_and_missing_latest_version_are_not_inferred(
    monkeypatch, version
):
    model = deepcopy(MODEL)
    model["latestVersion"] = version
    model["entryId"] = "other-native-entry"
    model["uniprotAccession"] = "P52270-2"
    serve(monkeypatch, payload=[MODEL, model])
    with sabueso.attribution() as run:
        raw = alphafold.OnlineAlphaFoldClient().prediction("P52270")
    assert raw["record"] == [MODEL, model]
    record = run.acquisitions[0]
    entry = record["entries"][1]
    assert entry["source_version"] == {
        "value": version,
        "basis": "model_version" if version is not None else "not_stated",
    }
    assert entry["model_metadata"]["modelEntityId"] == MODEL["modelEntityId"]
    assert (
        entry["model_id"] == "other-native-entry"
        and entry["identifier_basis"] == "entryId"
    )
    assert entry["model_metadata"]["uniprotAccession"] == "P52270-2"
    assert record["source_version"]["basis"] == "per_model_version"
    assert len(record["source_version"]["value"]) == (1 if version is None else 2)


@pytest.mark.parametrize("payload", [{}, None, {"unexpected": "envelope"}])
def test_non_list_payloads_never_become_completed_empty_model_queries(
    monkeypatch, payload
):
    serve(monkeypatch, payload=payload)
    with sabueso.attribution() as run:
        if payload:
            with pytest.raises(AttributeError):
                lookup()
        else:
            with pytest.raises(RecordNotFoundError):
                lookup()
    record = run.acquisitions[0]
    assert record["outcome"] == "unobserved" and record["count"] is None
    assert record["pages"] and record["provider"]["status"] == "not_attempted"


@pytest.mark.parametrize("payload", [[MODEL, None], [None]])
def test_invalid_list_members_preserve_original_public_failure_and_received_subset(
    monkeypatch, payload
):
    serve(monkeypatch, payload=payload)
    with pytest.raises(AttributeError) as caught:
        lookup()
    record = caught.value.acquisition_trace["records"][0]
    partial = len(payload) == 2
    assert caught.value.acquisition_trace["result_status"] == "failed"
    assert record["outcome"] == ("partial" if partial else "unobserved")
    assert record["completed_ids"] == ([MODEL["entryId"]] if partial else [])
    assert record["provider"]["status"] == ("available" if partial else "not_attempted")
    assert record["entries"][-1]["outcome"] == "unobserved"


def test_malformed_fixture_preserves_original_decode_failure(tmp_path):
    directory = tmp_path / "alphafold"
    directory.mkdir()
    (directory / "P52270.json").write_text("not JSON", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError) as caught:
        lookup(client=alphafold.FixtureAlphaFoldClient(tmp_path))
    record = caught.value.acquisition_trace["records"][0]
    assert record["access"] == "fixture" and record["outcome"] == "failed"
    assert record["provider"]["status"] == "not_attempted" and not record["pages"]


@pytest.mark.parametrize("accession", ["P52270", "P60174"])
def test_card_refresh_pins_original_support_and_saved_readers_remain_inert(
    tmp_path, accession
):
    options = {
        "resolver": EntityResolver(FixtureUniProtClient("temp_data")),
        "predicted_structures": True,
        "alphafold_client": alphafold.FixtureAlphaFoldClient(
            "temp_data", retrieved_at="original"
        ),
    }
    card, resolution = sabueso.resolve(accession, **options)
    record = next(
        r for r in card.acquisition_trace["records"] if r["source"] == "AlphaFold DB"
    )
    raw = json.loads(Path(f"temp_data/alphafold/{accession}.json").read_text())
    assert record["count"] == len(raw) and record["retrieved_at"] == "original"
    assert [e["model_metadata"]["uniprotAccession"] for e in record["entries"]] == [
        m["uniprotAccession"] for m in raw
    ]
    assert all(e["source_version"]["value"] == 6 for e in record["entries"])
    assert card.acquisition_trace == resolution.acquisition_trace
    assert card.acquisition_trace["card_ref"] == card.pinned_ref()
    plain, _ = sabueso.resolve(accession, resolver=options["resolver"])
    assert card.structures() == plain.structures()
    assert card.relationships("has_predicted_structure")
    saved = card.acquisition_trace
    saved["records"].clear()
    assert (
        card.acquisition_trace["records"] and "acquisition_trace" not in card.to_dict()
    )
    card.to_json(str(tmp_path / "card.json"))
    before = ackredit.get_attribution().to_dict()
    restored = Card.from_json(str(tmp_path / "card.json"))
    assert (
        restored.snapshot_id() == card.snapshot_id()
        and restored.acquisition_trace is None
    )
    assert restored.predicted_structures() == card.predicted_structures()
    ackredit.Attribution.from_dict(record["provider"]["attribution"]).report(
        format="bibtex"
    )
    assert json.loads(json.dumps(record)) == record
    assert ackredit.get_attribution().to_dict() == before
    refreshed, resolution = sabueso.refresh_card(card, **options)
    assert refreshed.acquisition_trace["card_ref"] == refreshed.pinned_ref()
    assert any(
        r["source"] == "AlphaFold DB" for r in resolution.acquisition_trace["records"]
    )


def test_provider_failure_nested_collectors_and_custom_gap(monkeypatch):
    serve(monkeypatch)
    with sabueso.attribution() as outer, sabueso.attribution() as inner:
        result = lookup()
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
        result = lookup()
    assert (
        result["record"] == [MODEL] and event(result)["provider"]["status"] == "failed"
    )

    class Custom:
        def prediction(self, accession):
            return {"record": [MODEL], "retrieved_at": "custom"}

    assert lookup(client=Custom())["acquisition_trace"]["records"] == []


def test_concurrent_queries_preserve_original_contexts_in_enclosing_capture(
    monkeypatch,
):
    serve(monkeypatch)
    with (
        ackredit.capture("parallel model queries") as host,
        sabueso.attribution() as run,
    ):
        results = _http.gather(lookup, ["P52270", "P60174"], workers=2)
    assert len(results) == len(run.acquisitions) == 2
    assert {
        use["context"]["query"]["accession"]
        for use in host.attribution.to_dict()["uses"]
        if use["context"].get("source") == "AlphaFold DB"
    } == {"P52270", "P60174"}


@pytest.mark.parametrize("missing", ["entryId", "latestVersion", "both_identifiers"])
def test_missing_identifiers_and_latest_version_stay_unknown_at_original_record_index(
    monkeypatch, missing
):
    model = deepcopy(MODEL)
    if missing == "both_identifiers":
        del model["entryId"], model["modelEntityId"]
    else:
        del model[missing]
    serve(monkeypatch, payload=[model])
    result = lookup()
    record = event(result)
    (entry,) = record["entries"]
    assert result["record"] == [model] and entry["record_index"] == 0
    if missing == "latestVersion":
        assert record["source_version"] == {"value": None, "basis": "not_stated"}
        assert entry["source_version"] == {"value": None, "basis": "not_stated"}
        assert entry["model_metadata"]["allVersions"] == MODEL["allVersions"]
    else:
        assert entry["identifier_basis"] == (
            "not_stated" if missing == "both_identifiers" else "modelEntityId"
        )
        assert entry["model_id"] == (
            None if missing == "both_identifiers" else MODEL["modelEntityId"]
        )
    assert record["provider"]["status"] == "available"


def test_repeated_model_ids_keep_distinct_versions_and_source_record_indices(
    monkeypatch,
):
    later = {**MODEL, "latestVersion": 7, "uniprotStart": 125, "uniprotEnd": 251}
    serve(monkeypatch, payload=[MODEL, later])
    result = lookup()
    record = event(result)
    assert result["record"] == [MODEL, later] and result["version"] == "v6; v7"
    assert record["count"] == 2
    assert record["source_version"]["value"] == [
        {"record_index": 0, "model_id": MODEL["entryId"], "value": 6},
        {"record_index": 1, "model_id": MODEL["entryId"], "value": 7},
    ]
    assert record["entries"][1]["model_metadata"]["uniprotStart"] == 125
