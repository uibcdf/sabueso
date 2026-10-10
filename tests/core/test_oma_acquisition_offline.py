"""Orthology access retains source boundaries and original scientific support."""

import io
import json
import os
import subprocess
import sys
from datetime import timedelta
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import ackredit
import pytest

import sabueso
from sabueso.core.errors import ConnectorError, NotArchivedError, RecordNotFoundError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import _http, oma


@pytest.fixture(autouse=True)
def independent():
    with ackredit.session("public OMA observation"):
        yield


class Response(io.BytesIO):
    status = 200

    def __init__(self, payload, release=None, next_url=None):
        super().__init__(json.dumps(payload).encode())
        self.headers = Message()
        if release is not None:
            self.headers["X-UniProt-Release"] = release
        if next_url:
            self.headers["Link"] = f'<{next_url}>; rel="next"'


def serve(monkeypatch, answers):
    calls = []
    iterator = iter(answers)

    def respond(request, timeout):
        calls.append(request.full_url)
        answer = next(iterator)
        if isinstance(answer, Exception):
            raise answer
        return Response(*answer)

    monkeypatch.setattr(_http, "_urlopen", respond)
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)
    monkeypatch.setattr(oma, "UNSTABLE_PAUSE", 0)
    return calls


def native_name(name, accession, entry_type="UniProtKB reviewed (Swiss-Prot)"):
    return {"uniProtkbId": name, "primaryAccession": accession, "entryType": entry_type}


def build(client, accession="P60174", **options):
    return sabueso.resolve(
        accession,
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        oma_client=client,
        oma=options,
    )[0]


def own(card):
    return [
        r
        for r in card.acquisition_trace["records"]
        if r["operation"].startswith("oma_")
    ]


def test_public_getter_keeps_two_oma_operations_and_resource_credit(monkeypatch):
    xrefs = [{"xref": "P60174", "omaid": "HUMAN10804", "seq_match": "exact"}]
    rows = [{"omaid": "TRYCC03899", "canonicalid": "Q4DV43", "rel_type": "1:1"}]
    calls = serve(monkeypatch, [(xrefs, "unrelated header"), (rows, None)])
    with ackredit.capture("host") as host:
        result = oma.get_orthologs("P60174")
    assert result["record"] == {"xrefs": xrefs, "orthologs": rows}
    records = result["acquisition_trace"]["records"]
    assert [(r["source"], r["operation"]) for r in records] == [
        ("OMA", "oma_xrefs"),
        ("OMA", "oma_orthologs"),
    ]
    assert calls == [
        oma.API + "/protein/P60174/xref/",
        oma.API + "/protein/P60174/orthologs/",
    ]
    assert "OMA" in result["acquisition_trace"]["coverage"]["sources"]
    for record in records:
        assert record["source_version"] == {"value": None, "basis": "not_stated"}
        assert record["count"] == 1 and record["network_attempts"] == 1
        assert record["bibliography"][-1]["url"] == oma.API
        assert (
            "entry_and_orthology_method_publications_not_queried"
            in record["bibliography_gaps"]
        )
        portable = ackredit.Attribution.from_dict(record["provider"]["attribution"])
        assert "oma_operation_observation@1" in json.dumps(portable.to_dict())
        assert {i["id"] for i in portable.to_dict()["items"]} <= {
            i["id"] for i in host.attribution.to_dict()["items"]
        }


def test_protein_lookup_is_a_separate_source_record(monkeypatch):
    payload = {"omaid": "HUMAN10804", "canonicalid": "P60174"}
    calls = serve(monkeypatch, [(payload,)])
    with sabueso.attribution() as run:
        assert oma.OnlineOMAClient().protein("HUMAN10804")["record"] == payload
    (record,) = run.acquisitions
    assert record["query"] == {"entry_id": "HUMAN10804"}
    assert record["operation"] == "oma_protein" and record["count"] == 1
    assert calls == [oma.API + "/protein/HUMAN10804/"]


def test_ortholog_continuation_is_reported_without_unasked_followup(monkeypatch):
    next_url = oma.API + "/protein/P60174/orthologs/?page=2"
    calls = serve(monkeypatch, [([], None, next_url)])
    with sabueso.attribution() as run:
        assert oma.OnlineOMAClient().orthologs("P60174", "1:1")["record"] == []
    (record,) = run.acquisitions
    assert len(calls) == 1 and calls[0].endswith("?rel_type=1%3A1")
    assert record["count"] == 0 and record["outcome"] == "empty"
    assert record["truncated"] and record["incomplete"]
    assert record["orthology_context"]["continuations_not_followed"] == [next_url]
    assert record["orthology_context"]["completeness"] == "not_established"


@pytest.mark.parametrize(
    "releases,value,basis",
    [
        (("2026_03", "2026_03"), "2026_03", "X-UniProt-Release"),
        (("2026_03", "2026_04"), None, "conflicting_responses"),
        (("2026_03", None), None, "partly_not_stated"),
    ],
)
def test_name_batches_are_uniprot_statements_not_oma_or_identity_merges(
    monkeypatch, releases, value, basis
):
    monkeypatch.setattr(oma, "NAMES_PER_REQUEST", 2)
    calls = serve(
        monkeypatch,
        [
            (
                {
                    "results": [
                        native_name("A", "P1"),
                        native_name("A", "P0", "Inactive"),
                        native_name("B", "P2"),
                        native_name("B", "P3"),
                    ]
                },
                releases[0],
            ),
            (
                {"results": [native_name("C", "P1"), native_name("C", "P1")]},
                releases[1],
            ),
        ],
    )
    with sabueso.attribution() as run:
        result = oma.OnlineOMAClient().accessions(n for n in ["C", "A", "B", "A", ""])
    assert result == {"A": "P1", "C": "P1"}
    (record,) = run.acquisitions
    assert record["source"] == "UniProt" and record["operation"] == "oma_entry_names"
    assert record["query"]["names"] == ["C", "A", "B", "A", ""]
    assert [p["requested_names"] for p in record["pages"]] == [["A", "B"], ["C"]]
    assert record["pages"][0]["unresolved_names"] == ["B"]
    assert record["pages"][1]["resolved_names"] == {"C": "P1"}
    assert record["count"] == 2 and record["orthology_context"]["received_rows"] == 6
    assert record["source_version"] == {"value": value, "basis": basis}
    assert len(calls) == record["network_attempts"] == 2
    assert all(url.startswith(oma.UNIPROT_SEARCH) for url in calls)
    assert record["bibliography"][-1]["url"] == oma.UNIPROT_SEARCH
    assert "not_marked_Inactive" in record["orthology_context"]["resolution_basis"]


def test_empty_name_request_is_unqueried_and_has_no_resource_credit(monkeypatch):
    calls = serve(monkeypatch, [])
    with sabueso.attribution() as run:
        assert oma.OnlineOMAClient().accessions(iter([])) == {}
    (record,) = run.acquisitions
    assert not calls and record["network_attempts"] == 0
    assert record["outcome"] == "not_queried" and record["count"] is None
    assert record["provider"]["status"] == "not_attempted"
    assert not ackredit.get_attribution().to_dict()["items"]


@pytest.mark.parametrize("accession", [None, "", 42])
def test_unanswered_consumed_name_accession_is_a_connector_failure(
    monkeypatch, accession
):
    serve(monkeypatch, [({"results": [native_name("A", accession)]},)])
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        oma.OnlineOMAClient().accessions(["A"])
    (record,) = run.acquisitions
    assert record["outcome"] == "partial" and record["terminal_outcome"] == "failed"
    assert record["orthology_context"]["resolved_names"] is None


@pytest.mark.parametrize("fixture", [False, True])
@pytest.mark.parametrize("method", ["xrefs", "orthologs"])
def test_explicit_empty_rows_remain_distinct_from_failed_access(
    monkeypatch, tmp_path, fixture, method
):
    calls = serve(monkeypatch, [([],)])
    directory = tmp_path / "oma"
    directory.mkdir()
    name = "xref_X" if method == "xrefs" else "orthologs_X"
    (directory / (name + ".json")).write_text("[]")
    client = oma.FixtureOMAClient(tmp_path) if fixture else oma.OnlineOMAClient()
    with sabueso.attribution() as run:
        assert getattr(client, method)("X")["record"] == []
    (record,) = run.acquisitions
    assert record["outcome"] == "empty" and record["count"] == 0
    assert record["provider"]["status"] == "available"
    assert len(calls) == record["network_attempts"] == (0 if fixture else 1)


@pytest.mark.parametrize(
    "method,name,argument",
    [
        ("xrefs", "xref_X", "X"),
        ("orthologs", "orthologs_X", "X"),
        ("protein", "protein_X", "X"),
        ("accessions", "entry_names", ["A"]),
    ],
)
@pytest.mark.parametrize("failure", ["missing", "unreadable", "malformed"])
def test_local_input_failure_never_becomes_provider_absence(
    tmp_path, method, name, argument, failure
):
    directory = tmp_path / "oma"
    directory.mkdir()
    if failure != "missing":
        (directory / (name + ".json")).write_text(
            "not JSON" if failure == "unreadable" else "null"
        )
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        getattr(oma.FixtureOMAClient(tmp_path), method)(argument)
    (record,) = run.acquisitions
    assert record["outcome"] == ("unavailable" if failure == "missing" else "failed")
    assert record["count"] is None and record["network_attempts"] == 0
    assert record["provider"]["status"] == "not_attempted"


def test_outer_service_retries_are_visible_without_duplicate_completed_pages(
    monkeypatch,
):
    error = HTTPError(oma.API, 502, "test", None, None)
    calls = serve(monkeypatch, [error, error, error, ([],)])
    with sabueso.attribution() as run:
        assert oma.OnlineOMAClient().xrefs("X")["record"] == []
    (record,) = run.acquisitions
    assert len(calls) == record["network_attempts"] == 4
    assert len(record["requests"]) == 2 and len(record["completed_pages"]) == 1
    assert record["requests"][0]["retries"] == ["HTTP 502", "HTTP 502"]


def test_exhausted_outer_service_retries_remain_failure_not_empty(monkeypatch):
    calls = serve(monkeypatch, [HTTPError(oma.API, 502, "test", None, None)] * 12)
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        oma.OnlineOMAClient().xrefs("X")
    (record,) = run.acquisitions
    assert len(calls) == record["network_attempts"] == 12
    assert record["outcome"] == "failed" and record["count"] is None
    assert len(record["requests"]) == 4 and record["completed_pages"] == []


@pytest.mark.parametrize("failure", ["timeout", "404", "malformed"])
def test_later_name_batch_failure_preserves_completed_scope_without_partial_result(
    monkeypatch, failure
):
    monkeypatch.setattr(oma, "NAMES_PER_REQUEST", 1)
    second = (
        TimeoutError("test")
        if failure == "timeout"
        else HTTPError(oma.UNIPROT_SEARCH, 404, "test", None, None)
        if failure == "404"
        else ({"results": None},)
    )
    calls = serve(
        monkeypatch, [({"results": [native_name("A", "P1")]}, "2026_03"), second]
    )
    error = RecordNotFoundError if failure == "404" else ConnectorError
    with sabueso.attribution() as run, pytest.raises(error):
        oma.OnlineOMAClient().accessions(["A", "B"])
    (record,) = run.acquisitions
    assert len(calls) == 2 and record["outcome"] == "partial"
    assert record["count"] == 1 and len(record["completed_pages"]) == 1
    assert record["orthology_context"]["resolved_names"] is None
    assert record["pages"][0]["resolved_names"] == {"A": "P1"}
    assert record["provider"]["status"] == "available"


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_archived_name_resolution_keeps_original_credit_hashes_and_times(
    monkeypatch, tmp_path, mode
):
    calls = serve(monkeypatch, [({"results": [native_name("A", "P1")]}, "2026_03")])
    archive = sabueso.RetrievalArchive(tmp_path / "archive.db")
    with archive.recording(), sabueso.attribution() as first:
        original = oma.OnlineOMAClient().accessions(["A"])
    context = (
        archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying()
    )
    with context, sabueso.attribution() as second:
        restored = oma.OnlineOMAClient().accessions(["A"])
    (before,), (after,) = first.acquisitions, second.acquisitions
    assert original == restored == {"A": "P1"}
    assert (
        len(calls) == 1 and after["network_attempts"] == 0 and after["access"] == mode
    )
    assert (
        after["pages"] == before["pages"]
        and after["retrieved_at"] == before["retrieved_at"]
    )
    for field in ("response_sha256", "retrieved_at", "retrieval_ref"):
        assert after["requests"][0][field] == before["requests"][0][field]
    portable = ackredit.Attribution.from_dict(after["provider"]["attribution"])
    assert "UniProtKB search API" in portable.report(format="bibtex")


def test_unarchived_oma_request_has_no_completed_credit(tmp_path):
    with (
        sabueso.RetrievalArchive(tmp_path / "archive.db").replaying(),
        pytest.raises(NotArchivedError) as caught,
    ):
        oma.get_orthologs("P60174")
    (record,) = caught.value.acquisition_trace["records"]
    assert record["outcome"] == "not_queried" and record["count"] is None
    assert record["provider"]["status"] == "not_attempted"


def test_received_rows_are_separate_from_taxon_and_limit_selected_card_support():
    from sabueso._private.smonitor.warnings import EnrichmentTruncatedWarning

    with pytest.warns(EnrichmentTruncatedWarning):
        card = build(oma.FixtureOMAClient("temp_data"), taxa=[353153, 10090], limit=1)
    records = own(card)
    orthologs = next(r for r in records if r["operation"] == "oma_orthologs")
    assert orthologs["count"] == orthologs["orthology_context"]["received_rows"] == 7
    assert len(card.relationships("ortholog_of")) == 1
    (quality,) = [r for r in card.quality["enrichments"] if r["source"] == "OMA"]
    assert (
        quality["count"] == 1 and quality["total_count"] == 2 and quality["truncated"]
    )
    assert "not_card_selected_relations" in orthologs["count_basis"]


def test_modified_source_match_does_not_acquire_or_join_orthologs():
    card = build(oma.FixtureOMAClient("temp_data"), accession="P52270")
    assert [r["operation"] for r in own(card)] == ["oma_xrefs", "oma_protein"]
    assert not card.relationships("ortholog_of")
    assert "modified" in card.quality["enrichments"][-1]["detail"]


def test_observation_preserves_exact_card_assertions_relationships_and_pin():
    class Unobserved(oma.FixtureOMAClient):
        xrefs = oma.FixtureOMAClient.xrefs.__wrapped__
        protein = oma.FixtureOMAClient.protein.__wrapped__
        orthologs = oma.FixtureOMAClient.orthologs.__wrapped__
        accessions = oma.FixtureOMAClient.accessions.__wrapped__

    card = build(oma.FixtureOMAClient("temp_data", retrieved_at="original"))
    custom = build(Unobserved("temp_data", retrieved_at="original"))
    assert (
        card.to_dict() == custom.to_dict() and card.pinned_ref() == custom.pinned_ref()
    )
    assert [r["source"] for r in own(card)] == ["OMA", "OMA", "UniProt"]
    assert not own(custom)
    assert (
        len(
            [
                r
                for r in card.relationships("ortholog_of")
                if r["object_ref"] == "uniprot:Q8ZKP7"
            ]
        )
        == 2
    )


def test_missing_name_mapping_installs_no_partial_ortholog_assertions(tmp_path):
    from sabueso._private.smonitor.warnings import EnrichmentFailedWarning

    directory = tmp_path / "oma"
    directory.mkdir()
    for name in ("xref_P60174.json", "orthologs_P60174.json"):
        (directory / name).write_bytes((Path("temp_data/oma") / name).read_bytes())
    with pytest.warns(EnrichmentFailedWarning):
        card = build(oma.FixtureOMAClient(tmp_path))
    assert [r["outcome"] for r in own(card)] == ["received", "received", "unavailable"]
    assert not card.relationships("ortholog_of")
    rows = [
        r
        for r in card.knowledge_state()["rows"]
        if r["area"] == "relationships.ortholog_of"
    ]
    assert rows and all(
        r["state"] == "unavailable" and r["count"] is None for r in rows
    )


def test_unasked_oma_has_no_observation_or_resource_credit():
    card, _ = sabueso.resolve(
        "P60174", resolver=EntityResolver(FixtureUniProtClient("temp_data"))
    )
    assert not own(card)
    assert "url:" + oma.API not in {
        i["id"] for i in ackredit.get_attribution().to_dict()["items"]
    }


def test_independent_pinned_reader_restores_original_credit_without_fresh_operations(
    tmp_path,
):
    card = build(oma.FixtureOMAClient("temp_data", retrieved_at="original"))
    pin = sabueso.KnowledgeStore(tmp_path / "knowledge.db").save(card)
    saved = {"pin": pin, "card": card.to_dict(), "trace": card.acquisition_trace}
    sidecar = tmp_path / "original.json"
    sidecar.write_text(json.dumps(saved))
    command = """
import json,sys
from pathlib import Path
import ackredit,sabueso
from sabueso.core import attribution,source_acquisition
from sabueso.core.card import Card
from sabueso.tools.db import _http,oma
def forbidden(*args,**kwargs):
    raise RuntimeError('Saved reader must not acquire, derive or add credit')
sabueso.resolve=sabueso.refresh_card=_http._urlopen=forbidden
attribution._credit=source_acquisition._credit=forbidden
for cls in (oma.FixtureOMAClient,oma.OnlineOMAClient):
    cls.xrefs=cls.protein=cls.orthologs=cls.accessions=forbidden
Card.sequence_differences=Card.knowledge_state=forbidden
sabueso.__version__='999.reader'
path=Path(sys.argv[1]); saved=json.loads(path.read_text())
with ackredit.session('independent reader'),sabueso.attribution() as run:
    before=ackredit.get_attribution().to_dict()
    card=sabueso.KnowledgeStore(path.parent/'knowledge.db').load(saved['pin'])
    assert card.to_dict()==saved['card'] and card.acquisition_trace is None
    assert saved['trace']['card_ref']==card.pinned_ref()
    records=[r for r in saved['trace']['records'] if r['operation'].startswith('oma_')]
    assert len(records)==3
    for record in records:
        assert record['producer']['version']!='999.reader'
        portable=ackredit.Attribution.from_dict(record['provider']['attribution'])
        assert 'oma_operation_observation@1' in json.dumps(portable.to_dict())
        assert ('UniProt' if record['source']=='UniProt' else 'OMA REST API') in portable.report(format='bibtex')
    assert ackredit.get_attribution().to_dict()==before
    assert not run.acquisitions and not run.records
"""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-c", command, str(sidecar)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(sidecar.read_text()) == saved


@pytest.mark.parametrize("value", [None, "", 42])
def test_fixture_name_binding_requires_an_answered_accession(tmp_path, value):
    directory = tmp_path / "oma"
    directory.mkdir()
    (directory / "entry_names.json").write_text(json.dumps({"A": value}))
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        oma.FixtureOMAClient(tmp_path).accessions(["A"])
    (record,) = run.acquisitions
    assert record["outcome"] == "failed" and record["count"] is None


def test_empty_fixture_name_mapping_is_a_subset_not_global_name_absence(tmp_path):
    directory = tmp_path / "oma"
    directory.mkdir()
    (directory / "entry_names.json").write_text("{}")
    with sabueso.attribution() as run:
        assert oma.FixtureOMAClient(tmp_path).accessions(["A"]) == {}
    (record,) = run.acquisitions
    assert record["outcome"] == "empty" and record["count"] == 0
    assert record["orthology_context"]["scope"] == "fixture_subset"
    assert record["orthology_context"]["completeness"] == "not_established"


def test_empty_batch_before_failure_does_not_establish_complete_name_absence(
    monkeypatch,
):
    monkeypatch.setattr(oma, "NAMES_PER_REQUEST", 1)
    serve(monkeypatch, [({"results": []},), TimeoutError("test")])
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        oma.OnlineOMAClient().accessions(["A", "B"])
    (record,) = run.acquisitions
    assert record["outcome"] == "partial" and record["count"] == 0
    assert record["terminal_outcome"] == "failed" and record["incomplete"]


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_archived_failed_name_batches_preserve_partial_scope_not_absence(
    monkeypatch, tmp_path, mode
):
    monkeypatch.setattr(oma, "NAMES_PER_REQUEST", 1)
    calls = serve(
        monkeypatch,
        [
            ({"results": []}, "2026_03"),
            HTTPError(oma.UNIPROT_SEARCH, 404, "test", {}, None),
        ],
    )
    archive = sabueso.RetrievalArchive(tmp_path / "archive.db")
    with (
        archive.recording(),
        sabueso.attribution() as first,
        pytest.raises(RecordNotFoundError),
    ):
        oma.OnlineOMAClient().accessions(["A", "B"])
    context = (
        archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying()
    )
    with context, sabueso.attribution() as second, pytest.raises(RecordNotFoundError):
        oma.OnlineOMAClient().accessions(["A", "B"])
    (before,), (after,) = first.acquisitions, second.acquisitions
    assert len(calls) == 2 and after["network_attempts"] == 0
    assert after["outcome"] == "partial" and after["terminal_outcome"] == "not_found"
    assert after["count"] == 0 and after["orthology_context"]["resolved_names"] is None
    assert (
        after["pages"] == before["pages"]
        and after["orthology_context"] == before["orthology_context"]
    )
    assert [r["response_sha256"] for r in after["requests"]] == [
        r["response_sha256"] for r in before["requests"]
    ]
