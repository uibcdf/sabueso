"""Native indication references retain their source basis without target access."""

import io
import json
from copy import deepcopy
from datetime import timedelta
from email.message import Message
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import ackredit
import pytest

import sabueso
from sabueso.core.errors import ConnectorError
from sabueso.core.source_acquisition import capture_acquisitions
from sabueso.tools.db import _http, chembl

REF = {
    "ref_type": "ClinicalTrials",
    "ref_id": "NCT00000001,NCT00000002",
    "ref_url": "https://clinicaltrials.gov/search?term=NCT00000001%20OR%20NCT00000002",
}
ROW = {
    "drugind_id": 1,
    "molecule_chembl_id": "CHEMBL110",
    "parent_molecule_chembl_id": None,
    "efo_id": "MONDO:0001444",
    "efo_term": None,
    "mesh_id": "D014355",
    "mesh_heading": None,
    "max_phase_for_ind": 4,
    "indication_refs": [REF],
}


@pytest.fixture(autouse=True)
def independent_session():
    with ackredit.session("native indication references"):
        yield


class Response(io.BytesIO):
    status = 200

    def __init__(self, payload):
        super().__init__(json.dumps(payload).encode())
        self.headers = Message()


def serve(monkeypatch, rows=None, *, fail=None):
    rows = [deepcopy(ROW)] if rows is None else rows
    calls = []
    monkeypatch.setattr(chembl, "PAGE_SIZE", 1)
    monkeypatch.setattr(_http.time, "sleep", lambda _: None)

    def response(request, timeout):
        url = urlsplit(request.full_url)
        assert url.hostname == "www.ebi.ac.uk", (
            "Reference targets must not be consulted"
        )
        path = url.path.rsplit("/", 1)[-1]
        query = parse_qs(url.query)
        offset = int(query.get("offset", [0])[0])
        calls.append((path, query))
        if fail == path or fail == offset and path == "drug_indication.json":
            raise HTTPError(request.full_url, 500, "synthetic failure", Message(), None)
        if path == "status.json":
            return Response({"chembl_db_version": "ChEMBL_synthetic"})
        assert path == "drug_indication.json"
        return Response(
            {
                "drug_indications": deepcopy(rows[offset : offset + 1]),
                "page_meta": {
                    "total_count": len(rows),
                    "next": "next" if offset + 1 < len(rows) else None,
                },
            }
        )

    monkeypatch.setattr(_http, "_urlopen", response)
    return calls


def lookup(operation, client=None):
    if operation == "indications":
        return chembl.get_indications(["CHEMBL110"], client=client)
    return disease_lookup(["MONDO:0001444"], client=client)


@capture_acquisitions
def disease_lookup(identifiers, client=None):
    return {
        "record": (client or chembl.OnlineChEMBLClient()).indications_for(identifiers)
    }


def references(record):
    return [
        item
        for item in record["bibliography"]
        if item["id"].startswith("sabueso:chembl-indication-reference:")
    ]


@pytest.mark.parametrize("operation", ["indications", "indications_for"])
def test_native_reference_and_exact_page_basis_enter_both_captures(
    monkeypatch, operation
):
    calls = serve(monkeypatch)
    with ackredit.capture("host") as host:
        result = lookup(operation)
    (record,) = result["acquisition_trace"]["records"]
    assert result["record"]["indications"]["CHEMBL110"] == [ROW]
    assert record["source_version"]["value"] == "ChEMBL_synthetic"
    context = record["indication_reference_context"]
    assert context["rule"] == "chembl_indication_references@1"
    assert context["target_access"] == "not_queried_by_this_operation"
    observation = context["observations"][0]
    assert observation["query"] == record["completed_pages"][0]["query"]
    assert (
        observation["response_identity"]
        == record["completed_pages"][0]["response_identity"]
    )
    assert observation["rows"][0]["indication_refs"] == [REF]
    (item,) = references(record)
    assert item["type"] == "web" and item["url"] == REF["ref_url"]
    assert not {"title", "authors", "year", "doi"}.intersection(item)
    assert len(calls) == 2
    for portable in (host.attribution.to_dict(), record["provider"]["attribution"]):
        uses = [
            use for use in portable["uses"] if "source_cited_reference" in use["roles"]
        ]
        assert len(uses) == 1
        assert (
            uses[0]["context"]["cited_reference_occurrences"]
            == context["citation_occurrences"]
        )
        assert uses[0]["context"]["source"] == "ChEMBL"
        assert all(
            use["context"].get("source") != "ClinicalTrials.gov"
            for use in portable["uses"]
        )


def test_public_fixture_retains_trials_labels_and_classification_without_enrichment(
    monkeypatch,
):
    def refuse(*args, **kwargs):
        raise AssertionError("Fixture references are not extra source accesses")

    monkeypatch.setattr(_http, "_urlopen", refuse)
    result = lookup("indications", chembl.FixtureChEMBLClient("temp_data"))
    (record,) = result["acquisition_trace"]["records"]
    observation = record["indication_reference_context"]["observations"][0]
    assert observation["basis"] == "decoded_client_result"
    assert observation["response_identity"] == record["response_identity"]
    native = [
        ref
        for row in result["record"]["indications"]["CHEMBL110"]
        for ref in row["indication_refs"]
    ]
    assert {ref["ref_type"] for ref in native} == {
        "ATC",
        "ClinicalTrials",
        "DailyMed",
        "FDA",
    }
    assert len(record["indication_reference_context"]["citation_occurrences"]) == len(
        native
    )
    assert len(references(record)) == len(
        {json.dumps(ref, sort_keys=True) for ref in native}
    )
    assert all(
        item["type"] == "web" and "year" not in item for item in references(record)
    )
    assert any(
        occurrence["native_reference"]["ref_id"] == "NCT03191162,NCT03981523"
        for occurrence in record["indication_reference_context"]["citation_occurrences"]
    )


def test_overlapping_disease_queries_keep_every_occurrence_despite_return_dedup(
    monkeypatch,
):
    serve(monkeypatch)
    result = disease_lookup(["MONDO:0001444", "MESH:D014355"])
    (record,) = result["acquisition_trace"]["records"]
    assert len(result["record"]["indications"]["CHEMBL110"]) == 1
    context = record["indication_reference_context"]
    assert len(context["observations"]) == len(context["citation_occurrences"]) == 2
    assert len(references(record)) == 1
    assert {occ["observation_index"] for occ in context["citation_occurrences"]} == {
        0,
        1,
    }
    assert "efo_id__in" in context["observations"][0]["query"]
    assert "mesh_id__in" in context["observations"][1]["query"]


def test_multiple_rows_and_alternative_native_forms_are_not_identity_merged(
    monkeypatch,
):
    alternative = {**REF, "ref_url": REF["ref_url"] + "&view=other"}
    rows = [
        deepcopy(ROW),
        {
            **deepcopy(ROW),
            "drugind_id": 2,
            "molecule_chembl_id": "CHEMBL25",
            "indication_refs": [REF, alternative],
        },
    ]
    serve(monkeypatch, rows)
    result = lookup("indications")
    (record,) = result["acquisition_trace"]["records"]
    assert len(references(record)) == 2
    context = record["indication_reference_context"]
    assert len(context["citation_occurrences"]) == 3
    assert [
        obs["rows"][0]["molecule_chembl_id"] for obs in context["observations"]
    ] == ["CHEMBL110", "CHEMBL25"]


@pytest.mark.parametrize("operation", ["indications", "indications_for"])
@pytest.mark.parametrize("failure", [1, "status.json"])
def test_completed_reference_pages_survive_later_failure(
    monkeypatch, operation, failure
):
    serve(monkeypatch, [ROW, {**ROW, "drugind_id": 2}], fail=failure)
    with pytest.raises(ConnectorError) as caught:
        lookup(operation)
    (record,) = caught.value.acquisition_trace["records"]
    assert (
        record["outcome"] == "partial" and record["provider"]["status"] == "available"
    )
    context = record["indication_reference_context"]
    expected = 1 if failure == 1 else 2
    assert (
        len(context["observations"]) == len(context["citation_occurrences"]) == expected
    )
    assert record["source_version"]["value"] is None
    assert len(references(record)) == 1
    assert record["requests"][-1]["outcome"] == "failed"


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_archive_reference_credit_retains_original_time_version_and_native_forms(
    monkeypatch, tmp_path, mode
):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "archive.db")
    with archive.recording():
        first = lookup("indications")
    manager = (
        archive.replaying() if mode == "replay" else archive.reusing(timedelta(days=1))
    )
    with manager, ackredit.capture("later host") as host:
        second = lookup("indications")
    one, two = [result["acquisition_trace"]["records"][0] for result in (first, second)]
    assert len(calls) == 2 and two["network_attempts"] == 0 and two["access"] == mode
    for key in (
        "retrieved_at",
        "source_version",
        "response_identity",
        "indication_reference_context",
        "bibliography",
        "bibliography_gaps",
    ):
        assert one[key] == two[key]
    assert any(
        "source_cited_reference" in use["roles"]
        for use in host.attribution.to_dict()["uses"]
    )


@pytest.mark.parametrize("case", ["empty", "missing_fixture", "no_input", "failed"])
def test_no_reference_credit_is_invented_for_unobserved_rows(
    monkeypatch, tmp_path, case
):
    serve(monkeypatch, [], fail="drug_indication.json" if case == "failed" else None)
    with sabueso.attribution() as run:
        if case == "failed":
            with pytest.raises(ConnectorError):
                lookup("indications")
        elif case == "missing_fixture":
            lookup("indications", chembl.FixtureChEMBLClient(tmp_path))
        elif case == "no_input":
            chembl.get_indications([], skip_digestion=True)
        else:
            lookup("indications")
    (record,) = run.acquisitions
    assert not references(record)
    assert not record["indication_reference_context"]["citation_occurrences"]
    assert (
        record["outcome"]
        == {
            "empty": "empty",
            "missing_fixture": "unavailable",
            "no_input": "not_queried",
            "failed": "failed",
        }[case]
    )


@pytest.mark.parametrize(
    "native,expected_count,gap",
    [
        (None, 0, "indication_references_not_stated"),
        ([], 0, "indication_references_not_stated"),
        ("malformed", 0, "indication_references_malformed"),
        ([None], 0, "indication_reference_malformed"),
        ([{}], 0, "indication_reference_pointer_unusable"),
        (
            [{"ref_type": "Unknown", "ref_id": "opaque"}],
            1,
            "indication_reference_fields_not_stated",
        ),
        (
            [{"ref_url": "https://example.org/native"}],
            1,
            "indication_reference_fields_not_stated",
        ),
        (
            [{"ref_id": "native", "ref_url": "not a URL"}],
            1,
            "indication_reference_url_not_supported",
        ),
        ([{"ref_url": "http://[broken"}], 0, "indication_reference_url_not_supported"),
        (
            [{"ref_id": ["wrong type"], "ref_url": "ftp://example.org/native"}],
            0,
            "indication_reference_pointer_unusable",
        ),
    ],
)
def test_missing_malformed_and_identifier_only_pointers_preserve_raw_return(
    monkeypatch, native, expected_count, gap
):
    row = {**ROW, "indication_refs": native}
    serve(monkeypatch, [row])
    result = lookup("indications")
    (record,) = result["acquisition_trace"]["records"]
    assert result["record"]["indications"]["CHEMBL110"] == [row]
    assert record["provider"]["status"] == "available"
    assert len(references(record)) == expected_count
    assert gap in [
        entry.get("reason")
        for entry in record["bibliography_gaps"]
        if isinstance(entry, dict)
    ]
    assert (
        record["indication_reference_context"]["observations"][0]["rows"][0][
            "indication_refs"
        ]
        == native
    )


def test_saved_bibliography_exports_without_requests_credit_or_host_overwrite(
    monkeypatch,
):
    serve(monkeypatch)
    host_item = {
        "id": "url:" + REF["ref_url"],
        "type": "web",
        "title": "Full host metadata",
        "year": 2026,
    }
    ackredit.register_item(**host_item)
    ackredit.track_item(host_item["id"])
    with ackredit.capture("host") as host:
        result = lookup("indications")
    record = result["acquisition_trace"]["records"][0]
    saved = json.dumps(record)
    current = ackredit.get_attribution().to_dict()
    assert (
        next(item for item in current["items"] if item["id"] == host_item["id"])
        == host_item
    )

    def refuse(*args, **kwargs):
        raise AssertionError("Saved readers must not access sources or add credit")

    monkeypatch.setattr(_http, "_urlopen", refuse)
    monkeypatch.setattr(ackredit, "register_item", refuse)
    monkeypatch.setattr(ackredit, "track_item", refuse)
    restored = json.loads(saved)
    original = ackredit.Attribution.from_dict(restored["provider"]["attribution"])
    assert REF["ref_id"] in original.report(format="bibtex")
    assert REF["ref_url"].replace("%", r"\%") in original.report(format="bibtex")
    csl = json.loads(original.report(format="csl-json"))
    item = next(item for item in csl if item["id"] == references(record)[0]["id"])
    assert item["URL"] == REF["ref_url"] and "issued" not in item
    assert ackredit.get_attribution().to_dict() == current
    for key in ("items", "uses"):
        assert original.to_dict()[key] == host.attribution.to_dict()[key]


def test_threaded_reference_occurrences_remain_bound_to_each_query(monkeypatch):
    serve(monkeypatch)
    with ackredit.capture("parallel") as host, sabueso.attribution() as run:
        _http.gather(
            lambda value: chembl.OnlineChEMBLClient().indications([value]),
            ["CHEMBL110", "CHEMBL25"],
            workers=2,
        )
    assert len(run.acquisitions) == 2
    assert {record["query"]["chembl_ids"][0] for record in run.acquisitions} == {
        "CHEMBL110",
        "CHEMBL25",
    }
    uses = [
        use
        for use in host.attribution.to_dict()["uses"]
        if "source_cited_reference" in use["roles"]
    ]
    assert {use["context"]["query"]["chembl_ids"][0] for use in uses} == {
        "CHEMBL110",
        "CHEMBL25",
    }
    assert all(
        use["context"]["cited_reference_occurrences"][0]["native_reference"] == REF
        for use in uses
    )


@pytest.mark.parametrize("operation", ["indications", "indications_for"])
def test_native_generator_queries_are_consumed_once_and_missing_ref_field_is_explicit(
    monkeypatch, operation
):
    row = {key: value for key, value in ROW.items() if key != "indication_refs"}
    serve(monkeypatch, [row])
    client = chembl.OnlineChEMBLClient()
    identifiers = ["CHEMBL110"] if operation == "indications" else ["MONDO:0001444"]
    with sabueso.attribution() as run:
        result = getattr(client, operation)(value for value in identifiers * 2)
    (record,) = run.acquisitions
    assert (
        record["query"]["chembl_ids" if operation == "indications" else "disease_ids"]
        == identifiers
    )
    assert result["indications"]["CHEMBL110"][0]["indication_refs"] is None
    assert (
        "indication_refs"
        not in record["indication_reference_context"]["observations"][0]["rows"][0]
    )
    assert not references(record)
    assert any(
        isinstance(gap, dict) and gap["reason"] == "indication_references_not_stated"
        for gap in record["bibliography_gaps"]
    )
