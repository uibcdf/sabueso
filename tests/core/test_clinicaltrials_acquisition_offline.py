"""Registry observation and bibliography preserve source scope and frozen cards."""

import io
import json
from copy import deepcopy
from datetime import timedelta
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import ackredit
import pytest

import sabueso
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.tools.db import _http, europepmc
from sabueso.tools.db import clinicaltrials as ct

ONE, TWO = "NCT00000001", "NCT00000002"
REFERENCE = {
    "pmid": "26323937",
    "type": "DERIVED",
    "citation": "Synthetic native citation; no title/author/year parsing.",
}


def study(identifier, *, references=False):
    protocol = {
        "identificationModule": {
            "nctId": identifier,
            "briefTitle": "Synthetic registry title",
        },
        "statusModule": {
            "lastUpdatePostDateStruct": {"date": "2026-01-01", "type": "ACTUAL"}
        },
    }
    if references:
        protocol["referencesModule"] = {"references": [deepcopy(REFERENCE)]}
    return {"protocolSection": protocol}


@pytest.fixture(autouse=True)
def independent_session():
    with ackredit.session("registry traceability"):
        yield


class Response(io.BytesIO):
    status = 200

    def __init__(self, payload):
        super().__init__(json.dumps(payload).encode())
        self.headers = Message()


def serve(monkeypatch, *, pages=None, version=None, fail=None):
    calls = []
    monkeypatch.setattr(_http.time, "sleep", lambda _: None)

    def response(request, timeout):
        url = urlsplit(request.full_url)
        assert url.hostname == "clinicaltrials.gov", (
            "Registry lookup must not follow reference targets"
        )
        endpoint = url.path.rsplit("/", 1)[-1]
        query = parse_qs(url.query)
        token = query.get("pageToken", [None])[0]
        calls.append((endpoint, deepcopy(query)))
        if fail == endpoint or fail == token and token is not None:
            raise HTTPError(request.full_url, 500, "synthetic failure", Message(), None)
        if endpoint == "version":
            return Response(
                version
                if version is not None
                else {
                    "dataTimestamp": "2026-01-02T09:00:00",
                    "apiVersion": "2.synthetic",
                }
            )
        if pages is not None:
            return Response(pages[token])
        identifiers = query["filter.ids"][0].split(",")
        refs = "protocolSection.referencesModule" in query["fields"][0]
        return Response(
            {
                "studies": [
                    study(identifier, references=refs) for identifier in identifiers
                ]
            }
        )

    monkeypatch.setattr(_http, "_urlopen", response)
    return calls


def lookup(operation, identifiers=None, client=None, **kwargs):
    function = ct.get_studies if operation == "studies" else ct.get_study_references
    return function(
        identifiers if identifiers is not None else [ONE], client=client, **kwargs
    )


def observed(result):
    (record,) = result["acquisition_trace"]["records"]
    return record


def pointer_items(record):
    return [
        item
        for item in record["bibliography"]
        if item["id"].startswith("sabueso:clinicaltrials-cited-reference:")
    ]


@pytest.mark.parametrize("operation", ["studies", "study_references"])
def test_native_query_versions_update_dates_and_registry_roles(monkeypatch, operation):
    calls = serve(monkeypatch)
    with ackredit.capture("host") as host:
        result = lookup(operation, [" nct00000001 ", ONE])
    record = observed(result)
    assert result["record"]["studies"][ONE] == study(
        ONE, references=operation == "study_references"
    )
    assert record["normalized_query"] == {"nct_ids": [ONE]}
    assert record["source_version"]["value"] == "2026-01-02T09:00:00"
    assert record["source_version"]["basis"] == "registry_data_timestamp"
    assert (
        record["source_version"]["scope"]
        == "client_reported_data_timestamp_not_verified_per_page"
    )
    assert record["clinical_context"]["api_version"] == "2.synthetic"
    assert (
        record["entries"][0]["study"]["protocolSection"]["statusModule"]
        == study(ONE)["protocolSection"]["statusModule"]
    )
    assert record["entries"][0]["response_identity"]["hash"]
    assert record["network_attempts"] == len(calls) == 2
    assert all(request.get("response_sha256") for request in record["requests"])
    for portable in (host.attribution.to_dict(), record["provider"]["attribution"]):
        assert any("source_registry_record" in use["roles"] for use in portable["uses"])
        cited = [
            use for use in portable["uses"] if "source_cited_reference" in use["roles"]
        ]
        assert bool(cited) == (operation == "study_references")
        assert all(
            use["context"]["source"] == "ClinicalTrials.gov" for use in portable["uses"]
        )
    if operation == "studies":
        assert calls[-1][1]["fields"][0] == ",".join(ct.FIELDS)
        assert "registry_references_not_requested" in [
            gap.get("reason")
            for gap in record["bibliography_gaps"]
            if isinstance(gap, dict)
        ]
    else:
        (citation,) = pointer_items(record)
        assert citation["url"] == "https://pubmed.ncbi.nlm.nih.gov/26323937/"
        assert not {"title", "authors", "year", "doi"}.intersection(citation)
        assert REFERENCE["citation"] in citation["note"]


@pytest.mark.parametrize("operation", ["studies", "study_references"])
def test_declared_pagination_and_empty_intermediate_pages_are_followed(
    monkeypatch, operation
):
    pages = {
        None: {"studies": [study(ONE)], "nextPageToken": "second"},
        "second": {"studies": [], "nextPageToken": "third"},
        "third": {"studies": [study(TWO)]},
    }
    calls = serve(monkeypatch, pages=pages)
    result = lookup(operation, [ONE, TWO])
    record = observed(result)
    assert (
        list(result["record"]["studies"]) == [ONE, TWO]
        and result["record"]["missing"] == []
    )
    assert len(calls) == 4 and record["count"] == 2
    assert [entry["page_index"] for entry in record["entries"]] == [1, 3]
    queries = [query for endpoint, query in calls if endpoint == "studies"]
    assert [
        {key: value for key, value in query.items() if key != "pageToken"}
        for query in queries
    ] == [queries[0]] * 3
    assert record["outcome"] == "received" and record["incomplete"] is False


def test_chunking_preserves_each_requested_batch(monkeypatch):
    monkeypatch.setattr(ct, "BATCH", 1)
    calls = serve(monkeypatch)
    result = lookup("studies", [TWO, ONE])
    assert [
        query["filter.ids"] for endpoint, query in calls if endpoint == "studies"
    ] == [[ONE], [TWO]]
    assert observed(result)["count"] == 2


@pytest.mark.parametrize("operation", ["studies", "study_references"])
@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_archive_keeps_original_native_pages_bibliography_and_time(
    monkeypatch, tmp_path, operation, mode
):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "archive.db")
    with archive.recording():
        first = lookup(operation)
    manager = (
        archive.replaying() if mode == "replay" else archive.reusing(timedelta(days=1))
    )
    with manager, ackredit.capture("later") as host:
        second = lookup(operation)
    one, two = observed(first), observed(second)
    assert len(calls) == 2 and two["access"] == mode and two["network_attempts"] == 0
    for key in (
        "retrieved_at",
        "source_version",
        "response_identity",
        "pages",
        "entries",
        "clinical_context",
        "bibliography",
        "bibliography_gaps",
    ):
        assert one[key] == two[key]
    assert any(
        "source_registry_record" in use["roles"]
        for use in host.attribution.to_dict()["uses"]
    )


@pytest.mark.parametrize("operation", ["studies", "study_references"])
def test_received_pages_are_preserved_before_later_failure(monkeypatch, operation):
    serve(
        monkeypatch,
        pages={
            None: {"studies": [study(ONE, references=True)], "nextPageToken": "failed"}
        },
        fail="failed",
    )
    with pytest.raises(ConnectorError) as caught:
        lookup(operation, [ONE, TWO])
    record = observed({"acquisition_trace": caught.value.acquisition_trace})
    assert record["outcome"] == "partial" and record["terminal_outcome"] == "failed"
    assert record["count"] == 1 and record["incomplete"] is True
    assert record["clinical_context"]["received_nct_ids"] == [ONE]
    assert "missing" not in record
    assert record["provider"]["status"] == "available"
    assert (
        len(pointer_items(record)) == 1
        and record["requests"][-1]["outcome"] == "failed"
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"studies": None},
        {"studies": {}},
        {"studies": [None]},
        {"studies": [{"protocolSection": {}}]},
        {"studies": [study(TWO)]},
        {"studies": [], "nextPageToken": 1},
        {"studies": [], "nextPageToken": ""},
    ],
)
def test_unreadable_or_unrelated_pages_do_not_establish_absence(monkeypatch, payload):
    serve(monkeypatch, pages={None: payload})
    with pytest.raises(ConnectorError) as caught:
        lookup("studies")
    record = observed({"acquisition_trace": caught.value.acquisition_trace})
    assert record["outcome"] == "partial" and record["terminal_outcome"] == "failed"
    assert record["count"] == 0 and "missing" not in record
    assert record["pages"][-1]["outcome"] == "unobserved"
    assert record["pages"][-1]["response_identity"]["hash"]
    assert not any(
        item["id"].startswith("sabueso:clinicaltrials-registry-record:")
        for item in record["bibliography"]
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        [],
        {"error": "native failure"},
        {"dataTimestamp": 1},
        {"dataTimestamp": "native", "apiVersion": []},
    ],
)
def test_invalid_version_endpoint_is_failed_without_source_credit(monkeypatch, payload):
    calls = serve(monkeypatch, version=payload)
    with pytest.raises(ConnectorError) as caught:
        lookup("studies")
    record = observed({"acquisition_trace": caught.value.acquisition_trace})
    assert len(calls) == 1 and record["outcome"] == "failed"
    assert record["provider"]["status"] == "not_attempted"


@pytest.mark.parametrize("conflict", [False, True])
def test_identical_duplicate_occurrences_survive_but_conflicts_are_refused(
    monkeypatch, conflict
):
    second = study(ONE, references=True)
    if conflict:
        second["protocolSection"]["identificationModule"]["briefTitle"] = (
            "Contradictory native title"
        )
    serve(monkeypatch, pages={None: {"studies": [study(ONE, references=True), second]}})
    if conflict:
        with pytest.raises(ConnectorError) as caught:
            lookup("study_references")
        record = observed({"acquisition_trace": caught.value.acquisition_trace})
        assert record["outcome"] == "partial"
        assert (
            len(
                [
                    item
                    for item in record["bibliography"]
                    if item["id"].startswith("sabueso:clinicaltrials-registry-record:")
                ]
            )
            == 2
        )
    else:
        result = lookup("study_references")
        record = observed(result)
        assert len(result["record"]["studies"]) == 1
    assert record["count"] == 1 and len(record["entries"]) == 2
    assert len(record["clinical_context"]["citation_occurrences"]) == 2


def test_repeated_pagination_token_refuses_completion(monkeypatch):
    serve(
        monkeypatch,
        pages={
            None: {"studies": [], "nextPageToken": "same"},
            "same": {"studies": [study(ONE)], "nextPageToken": "same"},
        },
    )
    with pytest.raises(ConnectorError) as caught:
        lookup("studies")
    record = observed({"acquisition_trace": caught.value.acquisition_trace})
    assert (
        record["outcome"] == "partial"
        and record["count"] == 1
        and "missing" not in record
    )


@pytest.mark.parametrize("case", ["empty", "no_input", "offline", "version_failure"])
def test_unqueried_failed_and_evaluated_empty_are_distinct(monkeypatch, tmp_path, case):
    calls = serve(
        monkeypatch,
        pages={None: {"studies": []}},
        fail="version" if case == "version_failure" else None,
    )
    with sabueso.attribution() as run:
        if case == "offline":
            with (
                sabueso.RetrievalArchive(tmp_path / "archive.db").replaying(),
                pytest.raises(ConnectorError),
            ):
                lookup("studies")
        elif case == "version_failure":
            with pytest.raises(ConnectorError):
                lookup("studies")
        else:
            lookup(
                "studies",
                [] if case == "no_input" else [ONE],
                skip_digestion=case == "no_input",
            )
    (record,) = run.acquisitions
    assert (
        record["outcome"]
        == {
            "empty": "empty",
            "no_input": "not_queried",
            "offline": "not_queried",
            "version_failure": "failed",
        }[case]
    )
    assert record["count"] == 0
    assert record["provider"]["status"] == (
        "available" if case == "empty" else "not_attempted"
    )
    if case == "empty":
        assert record["missing"] == [ONE]
    if case in {"offline", "no_input"}:
        assert not calls


@pytest.mark.parametrize("operation", ["studies", "study_references"])
def test_missing_fixture_file_and_unsaved_ids_are_unavailable(
    monkeypatch, tmp_path, operation
):
    client = ct.FixtureClinicalTrialsClient(tmp_path)
    with pytest.raises(ConnectorError) as caught:
        lookup(operation, client=client)
    record = observed({"acquisition_trace": caught.value.acquisition_trace})
    assert (
        record["outcome"] == "unavailable"
        and record["provider"]["status"] == "not_attempted"
    )
    directory = tmp_path / "clinicaltrials"
    directory.mkdir()
    filename = "studies.json" if operation == "studies" else "references.json"
    (directory / filename).write_text(
        json.dumps({"version": "native", "studies": {ONE: study(ONE)}})
    )
    with pytest.raises(ConnectorError) as caught:
        lookup(operation, [ONE, TWO], client)
    record = observed({"acquisition_trace": caught.value.acquisition_trace})
    assert (
        record["outcome"] == "partial" and record["terminal_outcome"] == "unavailable"
    )
    assert (
        record["count"] == 1
        and record["provider"]["status"] == "available"
        and "missing" not in record
    )


def test_fixture_declared_negative_is_distinct_from_an_unsaved_record(tmp_path):
    directory = tmp_path / "clinicaltrials"
    directory.mkdir()
    (directory / "studies.json").write_text(
        json.dumps({"version": "original", "studies": {}, "missing": [ONE]})
    )
    result = lookup("studies", client=ct.FixtureClinicalTrialsClient(tmp_path))
    assert observed(result)["outcome"] == "empty" and result["record"]["missing"] == [
        ONE
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"studies": []},
        {"version": [], "studies": {}},
        {"studies": {ONE: study(TWO)}},
        {"studies": {}, "missing": None},
        {"studies": {ONE: study(ONE)}, "missing": [ONE]},
    ],
)
def test_malformed_fixture_data_is_not_absence(tmp_path, payload):
    directory = tmp_path / "clinicaltrials"
    directory.mkdir()
    (directory / "studies.json").write_text(json.dumps(payload))
    with pytest.raises(ConnectorError):
        lookup("studies", client=ct.FixtureClinicalTrialsClient(tmp_path))


@pytest.mark.parametrize("operation", ["studies", "study_references"])
def test_generator_query_is_retained_when_public_digestion_is_bypassed(
    monkeypatch, operation
):
    serve(monkeypatch)
    result = lookup(operation, (value for value in [ONE, ONE]), skip_digestion=True)
    assert result["query"] == {"nct_ids": [ONE, ONE]}
    assert observed(result)["normalized_query"] == {"nct_ids": [ONE]}


@pytest.mark.parametrize(
    "module,reason",
    [
        (None, "registry_references_module_malformed"),
        ({"references": {}}, "registry_reference_list_malformed"),
        ({"references": [None]}, "registry_reference_malformed"),
        ({"references": [{"pmid": "invalid"}]}, "registry_reference_pointer_unusable"),
        (
            {"references": [{"citation": "Verbatim bibliography without PMID"}]},
            "registry_reference_structured_metadata_not_projected",
        ),
    ],
)
def test_malformed_and_citation_only_native_references_keep_explicit_gaps(
    monkeypatch, module, reason
):
    native = study(ONE)
    native["protocolSection"]["referencesModule"] = module
    serve(monkeypatch, pages={None: {"studies": [native]}})
    result = lookup("study_references")
    record = observed(result)
    assert result["record"]["studies"][ONE] == native
    assert reason in [
        gap.get("reason")
        for gap in record["bibliography_gaps"]
        if isinstance(gap, dict)
    ]
    assert record["provider"]["status"] == "available"


def test_retractions_links_and_participant_dataset_pointers_are_not_followed(
    monkeypatch,
):
    native = study(ONE, references=True)
    module = native["protocolSection"]["referencesModule"]
    module["references"][0]["retractions"] = [
        {"pmid": "18585495", "source": "native declaration"}
    ]
    module["seeAlsoLinks"] = [
        {"label": "Native website", "url": "https://example.org/native"}
    ]
    module["availIpds"] = [
        {
            "id": "dataset-native",
            "type": "STUDY_PROTOCOL",
            "url": "https://example.org/data",
        }
    ]
    calls = serve(monkeypatch, pages={None: {"studies": [native]}})
    record = observed(lookup("study_references"))
    assert len(calls) == 2 and len(pointer_items(record)) == 4
    assert {
        occ["relation"] for occ in record["clinical_context"]["citation_occurrences"]
    } == {"references", "retractions", "seeAlsoLinks", "availIpds"}
    assert (
        record["clinical_context"]["reference_target_access"]
        == "not_queried_by_this_operation"
    )


def test_real_public_references_then_explicit_article_metadata_preserve_workflow_bibliography(
    monkeypatch, tmp_path
):
    def refuse(*args, **kwargs):
        raise AssertionError("Public fixtures must not make network requests")

    monkeypatch.setattr(_http, "_urlopen", refuse)
    full_host = {
        "id": "doi:10.1056/NEJMoa1507574",
        "type": "article",
        "title": "Full host metadata",
        "authors": ["Host"],
        "year": 2015,
    }
    ackredit.register_item(**full_host)
    ackredit.track_item(full_host["id"])
    with ackredit.capture("explicit bibliography") as host:
        registry = ct.get_study_references(
            ["NCT00123916"], client=ct.FixtureClinicalTrialsClient("temp_data")
        )
        record = observed(registry)
        native = registry["record"]["studies"]["NCT00123916"]["protocolSection"][
            "referencesModule"
        ]
        pmids = [reference["pmid"] for reference in native["references"]]
        assert pmids == ["18585495", "26323937", "19753491"]
        assert all(
            use["context"]["source"] == "ClinicalTrials.gov"
            for use in record["provider"]["attribution"]["uses"]
        )
        articles = [
            europepmc.get_article(
                "pubmed:" + pmid, client=europepmc.FixtureEuropePMCClient("temp_data")
            )
            for pmid in pmids
        ]
    assert record["clinical_context"]["api_version"] == "2.0.5"
    assert record["source_version"]["value"] == "2026-10-05T09:00:05"
    assert (
        len(pointer_items(record)) == 5
    )  # Three publications and two declared websites.
    assert [
        len(article["record"]["articles"][0]["authorList"]["author"])
        for article in articles
    ] == [9, 22, 9]
    assert all(
        "abstractText" not in article["record"]["articles"][0] for article in articles
    )
    assert (
        next(
            item
            for item in ackredit.get_attribution().to_dict()["items"]
            if item["id"] == full_host["id"]
        )
        == full_host
    )
    saved = tmp_path / "workflow.json"
    saved.write_text(json.dumps(host.attribution.to_dict()))
    before = ackredit.get_attribution().to_dict()
    monkeypatch.setattr(ackredit, "register_item", refuse)
    monkeypatch.setattr(ackredit, "track_item", refuse)
    restored = ackredit.Attribution.from_dict(json.loads(saved.read_text()))
    csl = json.loads(restored.report(format="csl-json"))
    bibliography = next(
        item
        for item in csl
        if item.get("DOI", "").casefold() == "10.1056/nejmoa1507574"
    )
    assert len(bibliography["author"]) == 22
    assert "10.1056/nejmoa1507574" in restored.report(format="bibtex").lower()
    assert ackredit.get_attribution().to_dict() == before


def test_actual_clinical_card_payload_is_unchanged_and_missing_fixture_cannot_create_negative_registry(
    monkeypatch, tmp_path
):
    from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
    from sabueso.tools.db.chembl import FixtureChEMBLClient
    from sabueso.tools.db.pdb_ccd import FixtureCCDClient
    from sabueso.tools.db.unichem import FixtureUniChemClient

    clients = dict(
        chembl_client=FixtureChEMBLClient("temp_data"),
        ccd_client=FixtureCCDClient("temp_data"),
        unichem_client=FixtureUniChemClient("temp_data"),
    )
    card, _ = sabueso.resolve(
        "chembl:CHEMBL110",
        trials={},
        clinicaltrials_client=ct.FixtureClinicalTrialsClient("temp_data"),
        **clients,
    )
    registry = [
        record
        for record in card.acquisition_trace["records"]
        if record["source"] == "ClinicalTrials.gov"
    ]
    assert len(registry) == 1 and registry[0]["count"] == 16
    assert "acquisition_trace" not in card.to_dict()
    raw = json.loads(Path("temp_data/clinicaltrials/studies.json").read_text())[
        "studies"
    ]
    native_assertions = [
        assertion
        for assertion in card.to_dict()["source_assertion_store"]
        if assertion["source"]["name"] == "ClinicalTrials.gov"
    ]
    assert len(native_assertions) == 16
    assert {
        assertion["asserted_value"]["protocolSection"]["identificationModule"][
            "nctId"
        ]: assertion["asserted_value"]
        for assertion in native_assertions
    } == raw
    with pytest.warns(EnrichmentFailedWarning):
        unavailable, _ = sabueso.resolve(
            "chembl:CHEMBL110",
            trials={},
            clinicaltrials_client=ct.FixtureClinicalTrialsClient(tmp_path),
            **clients,
        )
    assert unavailable.clinical()["trials"] == []
    assert len(unavailable.clinical()["not_fetched"]) == 16
    assert (
        next(
            record
            for record in unavailable.acquisition_trace["records"]
            if record["source"] == "ClinicalTrials.gov"
        )["outcome"]
        == "unavailable"
    )


def test_parallel_queries_preserve_separate_native_query_contexts(monkeypatch):
    serve(monkeypatch)
    with ackredit.capture("parallel") as host, sabueso.attribution() as run:
        results = _http.gather(
            lambda identifier: ct.OnlineClinicalTrialsClient().studies([identifier]),
            [ONE, TWO],
            workers=2,
        )
    assert len(results) == len(run.acquisitions) == 2
    assert {
        record["normalized_query"]["nct_ids"][0] for record in run.acquisitions
    } == {ONE, TWO}
    assert {
        use["context"]["normalized_query"]["nct_ids"][0]
        for use in host.attribution.to_dict()["uses"]
        if "source_registry_record" in use["roles"]
    } == {ONE, TWO}


def test_provider_failure_preserves_the_scientific_result(monkeypatch):
    from sabueso._private.smonitor.warnings import AttributionTrackingWarning
    from sabueso.core import attribution as adapter

    client = ct.FixtureClinicalTrialsClient("temp_data")
    before = client.studies(["NCT00123916"])

    def unavailable():
        raise RuntimeError("Synthetic provider failure")

    monkeypatch.setattr(adapter, "_load_backend", unavailable)
    with sabueso.attribution() as run, pytest.warns(AttributionTrackingWarning):
        after = client.studies(["NCT00123916"])
    assert after == before and run.acquisitions[0]["provider"]["status"] == "failed"


def test_fixture_with_no_saved_query_answer_is_unavailable_not_partial(tmp_path):
    directory = tmp_path / "clinicaltrials"
    directory.mkdir()
    (directory / "studies.json").write_text(
        json.dumps({"version": "native", "studies": {TWO: study(TWO)}})
    )
    with pytest.raises(ConnectorError) as caught:
        lookup("studies", [ONE], ct.FixtureClinicalTrialsClient(tmp_path))
    record = observed({"acquisition_trace": caught.value.acquisition_trace})
    assert record["outcome"] == "unavailable" and record["count"] == 0
    assert record["provider"]["status"] == "not_attempted"


@pytest.mark.parametrize("operation", ["studies", "study_references"])
def test_public_empty_identifiers_are_refused_through_argdigest(operation):
    with pytest.raises(ArgumentError):
        lookup(operation, [])
