"""IntAct result rows retain native participant identity, scope and interpretation."""

import copy
import hashlib
import io
import json
from collections import Counter
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import retention, verdict
from sabueso.mappings.intact import COLUMNS, map_interactions, response_query
from sabueso.tools.db.intact import FixtureIntActClient, get_interactions

BODY = Path("temp_data/intact/interactions__P60174.mitab")
CONTEXT = BODY.with_suffix(".headers.json")


def native_row():
    return BODY.read_text(encoding="utf-8").splitlines()[0].split("\t")


class Client:
    def __init__(self, rows=None, total=None, identifier="P60174", max_results=200):
        rows = [native_row()] if rows is None else rows
        self.result = {
            "record": ""
            if not rows
            else "\n".join("\t".join(row) for row in rows) + "\n",
            "response_headers": {
                "X-PSICQUIC-Count": str(len(rows) if total is None else total)
            },
            "response_query": response_query(identifier, max_results),
            "retrieved_at": "2026-01-01",
            "version": None,
        }

    def interactions(self, identifier, limit):
        return self.result


def test_full_native_page_preserves_all_columns_and_distinct_interaction_semantics():
    envelope = get_interactions("p60174", client=FixtureIntActClient())
    before = copy.deepcopy(envelope)
    assertions = map_interactions(envelope)
    assert envelope == before and len(assertions) == 80
    assert envelope["record"].encode() == BODY.read_bytes()
    assert envelope["version"] is None and envelope["retrieved_at"] is None
    scope = envelope["scope"]
    assert (scope["total_results"], scope["observed_rows"], scope["returned_rows"]) == (
        80,
        80,
        80,
    )
    assert envelope["truncated"] is False
    values = [a["asserted_value"] for a in assertions]
    assert Counter(v["native"]["complex_expansion"] for v in values) == {
        'psi-mi:"MI:1060"(spoke expansion)': 67,
        "-": 13,
    }
    assert Counter(v["query_matches"][0]["column"] for v in values) == {
        "id_a": 3,
        "id_b": 77,
    }
    assert Counter(v["native"]["interaction_type"] for v in values) == {
        'psi-mi:"MI:0914"(association)': 56,
        'psi-mi:"MI:0915"(physical association)': 13,
        'psi-mi:"MI:2364"(proximity)': 11,
    }
    for index, assertion in enumerate(assertions):
        assert assertion["subject_ref"] == "uniprot:P60174"
        assert (
            assertion["source"]["name"] == "IntAct"
            and assertion["source"]["version"] is None
        )
        assert assertion["field_path"] == "interactions.observations.intact"
        native = assertion["asserted_value"]["native"]
        assert tuple(native) == COLUMNS
        assert list(native.values()) == envelope["record"].splitlines()[index].split(
            "\t"
        )
        assert "is_direct" not in assertion["asserted_value"]
        assert "evidence_class" not in assertion and "knowledge_class" not in assertion
    first = assertions[0]["asserted_value"]["native"]
    assert first["confidence"] == "author score:LacZ4|intact-miscore:0.37"
    assert first["publication"] == "pubmed:16169070|imex:IM-16517|mint:MINT-5217955"
    receipt = envelope["snapshot_receipt"]
    assert (
        receipt["document_sha256"]
        == "48b43fc580ad3ba7af9a2446ca6041168768938cca29bb5017c7924cad914762"
    )
    assert receipt["header_sha256"] == hashlib.sha256(CONTEXT.read_bytes()).hexdigest()
    access = envelope["acquisition_trace"]["records"][0]
    assert access["access"] == "supplied_file" and access["network_attempts"] == 0
    assert access["source_version"]["value"] is None
    assert (
        "native_publication_and_method_metadata_not_fetched"
        in access["bibliography_gaps"]
    )
    assertions[0]["asserted_value"]["native"]["confidence"] = "changed"
    assert envelope == before


@pytest.mark.parametrize("negative", ["true", "false", "-"])
def test_native_negation_features_parameters_and_unknown_scores_are_literal(negative):
    row = native_row()
    changes = {
        "negative": negative,
        "confidence": "author score:high|custom-score:0",
        "parameters": "kd:1.0e-7(textual native context)",
        "features_a": "mutation:?>164(native feature)",
        "stoichiometry_a": "0",
        "host_taxon": "taxid:-5(in silico)",
        "interaction_type": 'psi-mi:"MI:2364"(proximity)',
    }
    for column, value in changes.items():
        row[COLUMNS.index(column)] = value
    assertion = map_interactions(get_interactions("P60174", client=Client([row])))[0]
    for column, value in changes.items():
        assert assertion["asserted_value"]["native"][column] == value
    assert assertion["source"]["version"] is None


@pytest.mark.parametrize("column", ["id_a", "id_b", "alt_id_a", "alt_id_b"])
def test_query_matches_use_explicit_namespaced_primary_or_alternative_IDs(column):
    row = native_row()
    row[0:4] = ["intact:EBI-1", "chebi:CHEBI-1", "-", "-"]
    row[COLUMNS.index(column)] = 'other:"P60174|other"|"uniprotkb":"P60174"'
    assertion = map_interactions(get_interactions("P60174", client=Client([row])))[0]
    matches = assertion["asserted_value"]["query_matches"]
    assert len(matches) == 1 and matches[0]["column"] == column
    assert matches[0]["alternative_index"] == 1
    assert matches[0]["native"] == '"uniprotkb":"P60174"'
    assert (
        assertion["asserted_value"]["native"]["id_b"].startswith("chebi:")
        if column != "id_b"
        else True
    )


def test_self_interaction_and_repeated_native_record_occurrences_survive():
    row = native_row()
    row[1] = row[0]
    envelope = get_interactions("P60174", client=Client([row, row]))
    assertions = map_interactions(envelope)
    assert len(assertions) == 2 and assertions[0]["id"] != assertions[1]["id"]
    assert [m["column"] for m in assertions[0]["asserted_value"]["query_matches"]] == [
        "id_a",
        "id_b",
    ]
    assert (
        assertions[0]["source_metadata"]["native_interaction_ids"]
        == assertions[1]["source_metadata"]["native_interaction_ids"]
    )


@pytest.mark.parametrize(
    "false_match",
    [
        "intact:P60174",
        "uniprotkb:P60174-1",
        "uniprotkb:Q15047",
        'uniprotkb:"P60174|Q15047"',
    ],
)
def test_neither_participant_or_other_namespace_isoform_alias_xref_is_not_query_identity(
    false_match,
):
    row = native_row()
    row[:4] = [false_match, "chebi:123", "-", "-"]
    row[4] = "uniprotkb:P60174(gene name)"
    row[22] = "uniprotkb:P60174(see-also)"
    with pytest.raises(ConnectorError, match="exact requested"):
        get_interactions("P60174", client=Client([row]))


def test_explicit_isoform_query_does_not_match_the_base_accession():
    row = native_row()
    row[0] = "uniprotkb:P60174-1"
    client = Client([row], identifier="P60174-1")
    assertion = map_interactions(get_interactions("P60174-1", client=client))[0]
    assert assertion["subject_ref"] == "uniprot:P60174-1"
    client.result["record"] = client.result["record"].replace(
        "uniprotkb:P60174-1", "uniprotkb:P60174"
    )
    with pytest.raises(ConnectorError):
        get_interactions("P60174-1", client=client)


def test_supplied_fixture_is_validated_in_full_before_a_smaller_result_cap(tmp_path):
    envelope = get_interactions("P60174", limit=2, client=FixtureIntActClient())
    assert len(map_interactions(envelope)) == 2 and envelope["truncated"] is True
    assert envelope["scope"]["observed_rows"] == 80 and envelope[
        "record"
    ] == BODY.read_text(encoding="utf-8")
    directory = tmp_path / "intact"
    directory.mkdir()
    (directory / BODY.name).write_text(
        BODY.read_text(encoding="utf-8") + "invalid row\n", encoding="utf-8", newline=""
    )
    (directory / CONTEXT.name).write_bytes(CONTEXT.read_bytes())
    with pytest.raises(ConnectorError, match="42 nonempty"):
        get_interactions("P60174", limit=2, client=FixtureIntActClient(tmp_path))


def test_bounded_native_page_marks_unqueried_continuation_and_known_zero_is_distinct():
    envelope = get_interactions(
        "P60174", limit=1, client=Client(total=2, max_results=1)
    )
    assert envelope["truncated"] is True and envelope["scope"]["total_results"] == 2
    assert len(map_interactions(envelope)) == 1
    envelope = get_interactions("P60174", client=Client([]))
    assert envelope["truncated"] is False and map_interactions(envelope) == []
    assert envelope["record"] == "" and envelope["scope"]["total_results"] == 0


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.update(record=""),
        lambda r: r["response_headers"].clear(),
        lambda r: r["response_headers"].update({"X-PSICQUIC-Count": "unknown"}),
        lambda r: r["response_headers"].update({"X-PSICQUIC-Count": "2"}),
        lambda r: r["response_headers"].update({"Authorization": "unwanted"}),
        lambda r: r["response_query"].update(miql="id:Q15047"),
        lambda r: r["response_query"].update(first_result=1),
        lambda r: r["response_query"].update(first_result=False),
        lambda r: r["response_query"].update(format="tab25"),
        lambda r: r.update(version="service-1.5.3"),
        lambda r: r.update(record=r["record"].replace("\tfalse\t", "\tunknown\t")),
        lambda r: r.update(record="\t".join(native_row()[:15])),
        lambda r: r.update(record=r["record"] + "\n"),
        lambda r: r.update(
            record=r["record"].replace("uniprotkb:P60174\t", '"uniprotkb:P60174\t', 1)
        ),
    ],
)
def test_bad_count_shape_scope_revision_or_identity_never_becomes_an_empty_result(
    mutate,
):
    client = Client()
    mutate(client.result)
    with pytest.raises(ConnectorError):
        get_interactions("P60174", client=client)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source", "UniProt"),
        ("kind", "other"),
        ("version", "1.5.3"),
        ("truncated", True),
        ("scope", {}),
    ],
)
def test_mapper_checks_original_envelope_scope(field, value):
    envelope = get_interactions("P60174", client=Client())
    envelope[field] = value
    with pytest.raises(ConnectorError):
        map_interactions(envelope)


@pytest.mark.parametrize(
    "identifier", ["P60174 OR *", "P60174-0", "P60174/../../", True, None]
)
def test_invalid_query_is_refused_before_access_even_with_digestion_skipped(identifier):
    class Forbidden:
        def interactions(self, *args):
            pytest.fail("Invalid query reached IntAct.")

    for skip in (False, True):
        with pytest.raises((ArgumentError, ConnectorError)):
            get_interactions(identifier, client=Forbidden(), skip_digestion=skip)


@pytest.mark.parametrize("limit", [0, -1, True, "2", None, 201])
def test_bad_single_page_limit_never_reaches_access(limit):
    class Forbidden:
        def interactions(self, *args):
            pytest.fail("Invalid limit reached IntAct.")

    for skip in (False, True):
        with pytest.raises((ArgumentError, ConnectorError)):
            get_interactions(
                "P60174", limit=limit, client=Forbidden(), skip_digestion=skip
            )


def test_missing_body_or_headers_is_unavailable_not_a_negative_observation(tmp_path):
    with pytest.raises(ConnectorError) as error:
        get_interactions("P60174", client=FixtureIntActClient(tmp_path))
    assert error.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


@pytest.mark.parametrize("status", [404, 500])
def test_http_failures_are_failed_access(status, monkeypatch):
    import sabueso.tools.db._http as http

    monkeypatch.setattr(http, "RETRIES", 0)

    def failure(request, timeout):
        raise HTTPError(request.full_url, status, "failure", {}, None)

    monkeypatch.setattr(http, "_urlopen", failure)
    with pytest.raises(ConnectorError) as error:
        get_interactions("P60174")
    record = error.value.acquisition_trace["records"][0]
    assert record["outcome"] == "failed" and record["network_attempts"] == 1


def test_shared_archive_keeps_native_count_service_headers_and_original_time(
    tmp_path, monkeypatch
):
    import sabueso.tools.db._http as http

    calls = []
    context = json.loads(CONTEXT.read_bytes())

    class Response(io.BytesIO):
        status = 200

        def __init__(self):
            super().__init__(BODY.read_bytes())
            self.headers = Message()
            for key, value in context["response_headers"].items():
                self.headers[key] = value
            self.headers["Set-Cookie"] = "never stored"

    def wire(request, timeout):
        calls.append((request.get_method(), request.full_url))
        return Response()

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "intact.db")
    with archive.recording():
        original = get_interactions("P60174")

    def forbidden(*args, **kwargs):
        pytest.fail("Replay reached the network.")

    monkeypatch.setattr(http, "_urlopen", forbidden)
    with archive.replaying():
        replay = get_interactions("P60174")
    assert calls == [
        (
            "GET",
            "https://www.ebi.ac.uk/Tools/webservices/psicquic/intact/webservices/current/search/query/id%3AP60174?format=tab27&firstResult=0&maxResults=200",
        )
    ]
    assert original["record"] == replay["record"]
    assert original["retrieved_at"] == replay["retrieved_at"]
    assert (
        original["response_headers"]
        == replay["response_headers"]
        == context["response_headers"]
    )
    assert map_interactions(original) == map_interactions(replay)
    a, b = (e["acquisition_trace"]["records"][0] for e in (original, replay))
    assert a["network_attempts"] == 1 and a["received_responses"] == 1
    assert b["access"] == "replay" and b["network_attempts"] == 0
    assert b["received_responses"] == 1


def test_native_zero_count_online_empty_body_is_empty_but_missing_count_is_failure(
    monkeypatch,
):
    import sabueso.tools.db._http as http

    class Response(io.BytesIO):
        status = 200

        def __init__(self, count):
            super().__init__(b"")
            self.headers = Message()
            if count is not None:
                self.headers["X-PSICQUIC-Count"] = count

    monkeypatch.setattr(http, "_urlopen", lambda request, timeout: Response("0"))
    envelope = get_interactions("P60174")
    assert envelope["acquisition_trace"]["records"][0]["outcome"] == "empty"
    monkeypatch.setattr(http, "_urlopen", lambda request, timeout: Response(None))
    with pytest.raises(ConnectorError) as error:
        get_interactions("P60174")
    assert error.value.acquisition_trace["records"][0]["outcome"] == "failed"


def test_intact_data_terms_are_independent_of_software_and_linked_article_rights():
    assert verdict("IntAct", "commercial_product")["verdict"] == "allowed"
    assert retention("IntAct")["conditions"] == ["attribution"]
