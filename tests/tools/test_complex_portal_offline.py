"""Native complex membership, support/feature scope and original single-GET access."""

import copy
import gzip
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
from sabueso.mappings.complex_portal import map_complex, map_participants
from sabueso.tools.db.complex_portal import (
    FixtureComplexPortalClient,
    SnapshotComplexPortalClient,
    get_complex,
)

DIRECTORY = Path("temp_data/complex_portal")


def native(identifier="CPX-2158"):
    return json.loads((DIRECTORY / f"complex__{identifier}.json").read_bytes())


class Client:
    def __init__(self, payload, **context):
        self.payload = payload
        self.context = context

    def complex(self, identifier):
        return {
            "record": self.payload,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


@pytest.mark.parametrize(
    "identifier,count", [("CPX-2158", 3), ("CPX-3055", 7), ("CPX-14819", 5)]
)
def test_native_complex_and_all_participants_keep_original_source_context(
    identifier, count
):
    envelope = get_complex(identifier.lower(), client=FixtureComplexPortalClient())
    before = copy.deepcopy(envelope)
    (context,) = map_complex(envelope)
    members = map_participants(envelope)
    assert context["asserted_value"] == native(identifier)
    assert len(members) == len({a["id"] for a in members}) == count
    for index, assertion in enumerate(members):
        assert assertion["asserted_value"] == {
            "complex_id": identifier,
            "native_participant": native(identifier)["participants"][index],
        }
        assert assertion["subject_ref"] == f"complexportal:{identifier}"
        assert assertion["source"]["version"] is None
        metadata = assertion["source_metadata"]
        assert metadata["native_participant_index"] == index
        assert (
            metadata["native_complex_context"]["evidenceType"]
            == native(identifier)["evidenceType"]
        )
        assert (
            metadata["native_complex_context"]["releaseDates"]
            == native(identifier)["releaseDates"]
        )
        assert "no_binary_expansion" in metadata["mapping_scope"]["membership"]
        assert "knowledge_class" not in assertion
    access = envelope["acquisition_trace"]["records"][0]
    assert access["count"] == 1 and access["participant_count"] == count
    assert access["native_evidence_type"] == native(identifier)["evidenceType"]
    assert access["source_version"]["value"] is None
    assert access["retrieved_at"] is None and access["network_attempts"] == 0
    assert access["access"] == "supplied_file"
    assert access["snapshot_receipt"]["source_access_observed"] is False
    assert any(
        r["id"] == "url:https://www.ebi.ac.uk/complexportal/"
        for r in access["bibliography"]
    )
    assert any("release_dates_separate" in gap for gap in access["bibliography_gaps"])
    context["asserted_value"]["participants"].clear()
    members[0]["asserted_value"]["native_participant"]["linkedFeatures"].clear()
    members[0]["source_metadata"]["native_complex_context"]["crossReferences"].clear()
    assert envelope == before


def test_hstim_ml_prediction_null_stoichiometry_and_native_stars_are_not_experimental_classes():
    envelope = get_complex("CPX-14819", client=FixtureComplexPortalClient())
    (context,) = map_complex(envelope)
    members = map_participants(envelope)
    row = next(
        a
        for a in members
        if a["asserted_value"]["native_participant"]["identifier"] == "P60174"
    )
    assert row["asserted_value"]["native_participant"]["stochiometry"] is None
    assert row["subject_ref"] == "complexportal:CPX-14819"
    assert context["asserted_value"]["predictedComplex"] is True
    assert context["asserted_value"]["evidenceType"]["identifier"] == "ECO:0008004"
    assert context["asserted_value"]["evidenceType"]["confidenceScore"] == 1
    assert context["asserted_value"]["institution"] == "HuMap"
    assert context["source"]["version"] is None
    assert (
        "probability" not in context["asserted_value"]
        and "evidence_class" not in row["asserted_value"]
    )


def test_small_molecule_features_and_unreturned_graph_references_stay_literal():
    envelope = get_complex("CPX-2158", client=FixtureComplexPortalClient())
    members = map_participants(envelope)
    heme = members[0]["asserted_value"]["native_participant"]
    assert heme["identifier"] == "CHEBI:30413" and heme["interactorTypeMI"] == "MI:0328"
    assert heme["stochiometry"] == "minValue: 4, maxValue: 4"
    # The native feature's participantId names another participant; it is not
    # silently reassigned to the owner of this feature array.
    assert heme["linkedFeatures"][0]["participantId"] == "P69905"
    assert heme["linkedFeatures"][0]["ranges"] == ["59-59", "88-88"]
    hba = members[1]["asserted_value"]["native_participant"]
    assert hba["linkedFeatures"][0]["ranges"] == ["?-?"]
    assert hba["linkedFeatures"][-1]["linkedFeatures"] == ["EBI-9979823"]
    feature_ids = {
        f["featureAc"]
        for p in envelope["record"]["participants"]
        for f in p["linkedFeatures"]
    }
    assert "EBI-9979823" not in feature_ids
    assert (
        "no_sequence_numbering_projection"
        in members[1]["source_metadata"]["mapping_scope"]["features"]
    )


def test_duplicate_native_occurrences_and_changed_support_are_independent():
    payload = native()
    original = map_participants(get_complex("CPX-2158", client=Client(payload)))
    payload["participants"].append(copy.deepcopy(payload["participants"][0]))
    members = map_participants(get_complex("CPX-2158", client=Client(payload)))
    assert len(members) == len({a["id"] for a in members}) == 4
    assert members[0]["asserted_value"] == members[-1]["asserted_value"]
    assert members[0]["id"] != members[-1]["id"]
    assert original[0]["asserted_value"] == members[0]["asserted_value"]
    assert original[0]["id"] != members[0]["id"]


def test_native_zero_null_ranges_unknown_types_isoforms_and_nested_complex_refs_are_not_rewritten():
    payload = native()
    payload["participants"][0].update(
        identifier="CPX-1556",
        interactorTypeMI="MI:0314",
        interactorType="complex",
        stochiometry="minValue: 0, maxValue: 0",
    )
    payload["participants"][1].update(
        identifier="P69905-2", stochiometry="minValue: 1, maxValue: 2"
    )
    payload["participants"][2].update(
        identifier="URS_TEST_9606",
        interactorTypeMI=None,
        interactorType="unqualified native type",
        stochiometry=None,
    )
    payload["participants"][2]["linkedFeatures"][0]["ranges"] = ["?-?", "n-n", "c-c"]
    payload["future_context"] = {"score": 0, "unknown": None}
    members = map_participants(get_complex("CPX-2158", client=Client(payload)))
    assert [a["asserted_value"]["native_participant"] for a in members] == payload[
        "participants"
    ]
    assert all(a["subject_ref"] == "complexportal:CPX-2158" for a in members)
    assert (
        members[0]["source_metadata"]["native_complex_context"]["future_context"]
        == payload["future_context"]
    )


def test_explicit_unstated_prediction_and_eco_context_do_not_default_to_curated():
    payload = native()
    payload.update(predictedComplex=None, evidenceType=None, releaseDates=[])
    assertion = map_complex(get_complex("CPX-2158", client=Client(payload)))[0]
    assert assertion["asserted_value"]["predictedComplex"] is None
    assert assertion["asserted_value"]["evidenceType"] is None
    assert "knowledge_class" not in assertion


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        False,
        2158,
        "",
        "CPX-0",
        "CPX-02158",
        "CPX-2158.1",
        "EBI-9008420",
        "P60174",
        "hemoglobin",
        "CPX-2158/x",
        "CPX-2158?x=1",
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_unsafe_or_nonprimary_request_ids_fail_before_access(identifier, skip):
    class Forbidden:
        def complex(self, *args):
            pytest.fail("Invalid request reached a client")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_complex(identifier, client=Forbidden(), skip_digestion=skip)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda p: p.update(complexAc="CPX-2159"),
        lambda p: p.update(ac="EBI-0"),
        lambda p: p.update(name=None),
        lambda p: p.update(species=""),
        lambda p: p.update(participants=[]),
        lambda p: p.pop("participants"),
        lambda p: p.update(synonyms=None),
        lambda p: p.update(functions=[{}]),
        lambda p: p.update(releaseDates=["2026-13-01"]),
        lambda p: p.update(releaseDates=["20261006"]),
        lambda p: p.pop("predictedComplex"),
        lambda p: p.update(predictedComplex=0),
        lambda p: p.pop("evidenceType"),
        lambda p: p["evidenceType"].update(identifier="GO:0004807"),
        lambda p: p["evidenceType"].update(confidenceScore=True),
        lambda p: p["evidenceType"].update(confidenceScore=6),
        lambda p: p.update(crossReferences=[]),
        lambda p: p["crossReferences"][-2].update(identifier="CPX-2159"),
        lambda p: p["participants"][-1].update(identifier=""),
        lambda p: p["participants"][-1].update(interactorAC="P68871"),
        lambda p: p["participants"][-1].pop("stochiometry"),
        lambda p: p["participants"][-1].update(stochiometry=2),
        lambda p: p["participants"][-1].update(interactorTypeMI=False),
        lambda p: p["participants"][-1].update(otherFeatures=None),
        lambda p: p["participants"][-1]["linkedFeatures"][-1].update(featureAc="EBI-0"),
        lambda p: p["participants"][-1]["linkedFeatures"][-1].update(ranges=None),
        lambda p: p["participants"][-1]["linkedFeatures"][-1].update(
            linkedFeatures=[1]
        ),
        lambda p: p["participants"][-1]["linkedFeatures"][-1].update(
            crossReferences=None
        ),
        lambda p: p.update(future_context=float("inf")),
    ],
)
def test_whole_native_record_is_validated_including_last_participant(mutation):
    payload = native()
    mutation(payload)
    with pytest.raises(ConnectorError):
        get_complex("CPX-2158", client=Client(payload))


@pytest.mark.parametrize(
    "context", [{"version": "1"}, {"truncated": True}, {"truncated": 0}]
)
def test_custom_client_invented_revision_or_cut_is_rejected(context):
    with pytest.raises(ConnectorError):
        get_complex("CPX-2158", client=Client(native(), **context))


@pytest.mark.parametrize("mapper", [map_complex, map_participants])
@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(source="IntAct"),
        lambda e: e.update(kind="search"),
        lambda e: e.update(version="1"),
        lambda e: e.update(truncated=True),
        lambda e: e["query"].update(accession="P69905"),
        lambda e: e["query"].update(complex_id="CPX-3055"),
    ],
)
def test_direct_mappers_check_identity_and_scope(mapper, change):
    envelope = get_complex("CPX-2158", client=FixtureComplexPortalClient())
    change(envelope)
    with pytest.raises(ConnectorError):
        mapper(envelope)


def metadata():
    return {
        "source": "Complex Portal",
        "kind": "complex",
        "query": {"complex_id": "CPX-2158"},
        "retrieved_at": "2026-01-01T00:00:00+00:00",
    }


def test_query_bound_gzip_snapshot_verifies_original_bytes_without_remote_credit(
    tmp_path,
):
    raw = gzip.compress((DIRECTORY / "complex__CPX-2158.json").read_bytes())
    path = tmp_path / "supplied.json.gz"
    path.write_bytes(raw)
    declaration = metadata()
    client = SnapshotComplexPortalClient(
        path,
        source_metadata=declaration,
        expected_sha256=hashlib.sha256(raw).hexdigest(),
    )
    declaration["query"]["complex_id"] = "CPX-3055"
    envelope = get_complex("CPX-2158", client=client)
    assert envelope["record"] == native()
    receipt = envelope["snapshot_receipt"]
    assert receipt["source_access_observed"] is False
    assert receipt["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["digest_verification"] == "matched_caller_digest"
    assert receipt["compression"] == "gzip"
    assert envelope["retrieved_at"] == metadata()["retrieved_at"]
    assert envelope["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert all(
        a["source_metadata"]["snapshot_receipt"] == receipt
        for a in map_participants(envelope)
    )
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_complex(
            "CPX-2158",
            client=SnapshotComplexPortalClient(
                path, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "change",
    [
        lambda m: m.update(source="IntAct"),
        lambda m: m.update(kind="search"),
        lambda m: m.update(version="1"),
        lambda m: m["query"].update(complex_id="CPX-3055"),
        lambda m: m["query"].update(extra=True),
    ],
)
def test_snapshot_declarations_must_match_exact_source_and_query(change):
    declaration = metadata()
    change(declaration)
    with pytest.raises(ConnectorError):
        get_complex(
            "CPX-2158",
            client=SnapshotComplexPortalClient(
                DIRECTORY / "complex__CPX-2158.json", source_metadata=declaration
            ),
        )


@pytest.mark.parametrize(
    "document",
    [
        '{"complexAc":"CPX-2158","complexAc":"CPX-3055"}',
        '{"value":NaN}',
        '{"value":1e999}',
        "{}",
    ],
)
def test_bad_supplied_json_is_failed_not_an_empty_complex(tmp_path, document):
    path = tmp_path / "bad.json"
    path.write_text(document)
    with pytest.raises(ConnectorError):
        get_complex(
            "CPX-2158",
            client=SnapshotComplexPortalClient(path, source_metadata=metadata()),
        )


def test_missing_fixture_is_unavailable_without_complex_absence_claim(tmp_path):
    with pytest.raises(ConnectorError) as exc:
        get_complex("CPX-2158", client=FixtureComplexPortalClient(tmp_path))
    assert exc.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


@pytest.mark.parametrize("code", [404, 500])
def test_http_errors_are_failures_not_complex_absence(monkeypatch, code):
    import sabueso.tools.db.complex_portal as module

    def fail(url, **kwargs):
        raise HTTPError(url, code, "failure", None, None)

    monkeypatch.setattr(module, "urlopen", fail)
    with pytest.raises(ConnectorError) as exc:
        get_complex("CPX-2158")
    assert exc.value.acquisition_trace["records"][0]["outcome"] == "failed"


def test_single_get_archive_replay_retains_original_time_and_acquires_no_support_links(
    monkeypatch, tmp_path
):
    from sabueso.tools.db import _http as http

    calls = []

    class Answer(io.BytesIO):
        status = 200
        headers = Message()
        headers["Content-Type"] = "application/json"

    def wire(request, timeout):
        calls.append(request.full_url)
        return Answer((DIRECTORY / "complex__CPX-2158.json").read_bytes())

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "complex.db")
    with archive.recording():
        first = get_complex("CPX-2158")

    def forbidden(*args, **kwargs):
        pytest.fail("Replay or mapping queried a linked resource")

    monkeypatch.setattr(http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_complex("CPX-2158")
    assert calls == ["https://www.ebi.ac.uk/intact/complex-ws/complex/CPX-2158"]
    assert first["record"] == second["record"] == native()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert map_complex(first) == map_complex(second)
    assert map_participants(first) == map_participants(second)
    a, b = [e["acquisition_trace"]["records"][0] for e in (first, second)]
    assert a["network_attempts"] == a["received_responses"] == 1
    assert b["network_attempts"] == 0 and b["access"] == "replay"
    assert a["response_identity"] == b["response_identity"]


def test_complex_portal_cc0_data_grant_is_separate_from_software_terms():
    terms = source_terms()["Complex Portal"]
    assert terms["licence"] == "CC0-1.0"
    assert terms["statement"].endswith("about/license_privacy.md")
    assert verdict("Complex Portal", "redistribution")["verdict"] == "allowed"
