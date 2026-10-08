"""Native domain support, independent numbering axes and explicit supplied intake."""

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
from sabueso.mappings.cath import map_domain
from sabueso.tools.db.cath import (
    FixtureCathClient,
    SnapshotCathClient,
    get_domain_summary,
)

RELEASE = "v4_4_0"
DIRECTORY = Path("temp_data/cath") / RELEASE


def native(identifier="1htiA00"):
    return json.loads((DIRECTORY / f"domain_summary__{identifier}.json").read_bytes())


class Client:
    def __init__(self, payload, **context):
        self.payload = payload
        self.context = context

    def domain_summary(self, identifier, release):
        return {
            "record": self.payload,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


@pytest.mark.parametrize("identifier", ["1htiA00", "1cukA01", "3g06A01", "3a85A01"])
def test_full_native_domain_summary_retains_support_without_protein_identity(
    identifier,
):
    envelope = get_domain_summary(identifier, RELEASE, client=FixtureCathClient())
    original = copy.deepcopy(envelope)
    (assertion,) = map_domain(envelope)
    assert envelope["record"] == native(identifier)
    assert assertion["asserted_value"] == native(identifier)["data"]
    assert assertion["subject_ref"] == f"cath:{RELEASE}:{identifier}"
    assert assertion["source"]["version"] is None
    metadata = assertion["source_metadata"]
    assert metadata["native_response"] == envelope["record"]
    assert metadata["requested_release"] == RELEASE
    assert "no_UniProt" in metadata["mapping_scope"]["identity"]
    access = envelope["acquisition_trace"]["records"][0]
    assert access["count"] == 1 and access["residue_count"] == len(
        native(identifier)["data"]["residues"]
    )
    assert access["source_version"]["value"] is None
    assert access["requested_release"] == RELEASE
    assert access["access"] == "supplied_file"
    assert access["network_attempts"] == 0 and access["retrieved_at"] is None
    assert access["snapshot_receipt"]["source_access_observed"] is False
    assert any(
        b["id"] == "url:https://www.cathdb.info/" for b in access["bibliography"]
    )
    assert any(
        "release_is_requested_route" in gap for gap in access["bibliography_gaps"]
    )
    assertion["asserted_value"]["residues"].clear()
    metadata["native_response"]["data"]["ec_terms"].clear()
    assert envelope == original


def test_unresolved_and_discontinuous_domain_sequences_are_not_canonical_offsets():
    data = map_domain(
        get_domain_summary("3g06A01", RELEASE, client=FixtureCathClient())
    )[0]["asserted_value"]
    assert len(data["combs_sequence"]) == 325 and len(data["atom_sequence"]) == 316
    assert sum(row["pdbres"] is None for row in data["residues"]) == 9
    assert data["residues"][9] == {"aa": "A", "seqres": 10, "pdbres": "171"}
    data = map_domain(
        get_domain_summary("3a85A01", RELEASE, client=FixtureCathClient())
    )[0]["asserted_value"]
    assert len(data["combs_sequence"]) == len(data["atom_sequence"]) == 120
    assert len(data["combs_segments"]) == len(data["pdb_segments"]) == 2
    assert [data["residues"][i]["seqres"] for i in (11, 12)] == [12, 103]
    assert [data["residues"][i]["pdbres"] for i in (11, 12)] == ["30", "121"]


def test_native_term_alternatives_and_duplicate_locations_survive_without_reclassification():
    payload = native()
    payload["data"]["residues"][0]["pdbres"] = "0"
    payload["data"]["residues"][1]["pdbres"] = "-1A"
    payload["data"]["residues"][2]["pdbres"] = "-1A"
    payload["data"]["future_context"] = {"literal": None, "score": 0}
    envelope = get_domain_summary("1htiA00", RELEASE, client=Client(payload))
    (assertion,) = map_domain(envelope)
    assert assertion["asserted_value"] == payload["data"]
    assert [row["evidence"] for row in assertion["asserted_value"]["go_terms"][:3]] == [
        "IDA",
        "NAS",
        "TAS",
    ]
    assert [row["ec_code"] for row in assertion["asserted_value"]["ec_terms"]] == [
        "4.2.3.3",
        "5.3.1.1",
    ]
    assert "experimental" not in assertion["asserted_value"]
    assert "uniprot_ref" not in assertion["source_metadata"]


def test_release_and_changed_native_support_keep_independent_assertion_ids():
    payload = native()
    a = map_domain(get_domain_summary("1htiA00", RELEASE, client=Client(payload)))[0]
    b = map_domain(get_domain_summary("1htiA00", "v4_3_0", client=Client(payload)))[0]
    assert a["asserted_value"] == b["asserted_value"]
    assert a["subject_ref"] != b["subject_ref"] and a["id"] != b["id"]
    changed = copy.deepcopy(payload)
    changed["data"]["go_terms"].append(copy.deepcopy(changed["data"]["go_terms"][0]))
    c = map_domain(get_domain_summary("1htiA00", RELEASE, client=Client(changed)))[0]
    assert c["id"] != a["id"] and c["subject_ref"] == a["subject_ref"]


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        False,
        123,
        "",
        "P60174",
        "1hti",
        "1htiA0",
        "1htiA001",
        "1htiA00/x",
        "1htiA00?x=1",
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_unsafe_domain_ids_fail_before_access(identifier, skip):
    class Forbidden:
        def domain_summary(self, *args):
            pytest.fail("Invalid domain reached a client")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_domain_summary(identifier, RELEASE, client=Forbidden(), skip_digestion=skip)


@pytest.mark.parametrize(
    "release",
    [
        None,
        True,
        4,
        "",
        "latest",
        "latest_release",
        "v4.4.0",
        "v04_4_0",
        "v4_4_0/x",
        "v4_4_0?x=1",
    ],
)
def test_fixed_release_selector_is_required_before_access(release):
    with pytest.raises((ArgumentError, ConnectorError)):
        get_domain_summary("1htiA00", release, client=object())


def test_domain_chain_case_is_kept_while_pdb_code_is_normalized():
    assert (
        get_domain_summary("1HTIA00", RELEASE, client=FixtureCathClient())["query"][
            "domain_id"
        ]
        == "1htiA00"
    )
    with pytest.raises(ConnectorError):
        get_domain_summary("1htia00", RELEASE, client=Client(native()))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda p: p.update(success=False),
        lambda p: p.update(success=1),
        lambda p: p.update(data=[]),
        lambda p: p["data"].update(domain_id="1htiB00"),
        lambda p: p["data"].update(pdb_code="1cbs"),
        lambda p: p["data"].update(cath_id="2.20.20.70.1.7.2.3.6"),
        lambda p: p["data"].update(superfamily_id="3.20.20.71"),
        lambda p: p["data"].update(funfam_number=True),
        lambda p: p["data"].pop("ssg5_number"),
        lambda p: p["data"].update(atom_length=247),
        lambda p: p["data"].update(atom_sequence="A"),
        lambda p: p["data"].update(combs_sequence="A"),
        lambda p: p["data"].update(combs_segments=[]),
        lambda p: p["data"]["combs_segments"][0].update(stop=249),
        lambda p: p["data"]["combs_segments"][0].update(start=True),
        lambda p: p["data"]["pdb_segments"][0].update(chain_code="a"),
        lambda p: p["data"]["pdb_segments"][0].update(start=1),
        lambda p: p["data"]["residues"][-1].update(seqres=247),
        lambda p: p["data"]["residues"][-1].update(aa="A"),
        lambda p: p["data"]["residues"][-1].pop("pdbres"),
        lambda p: p["data"]["residues"][-1].update(pdbres=False),
        lambda p: p["data"].update(go_terms=None),
        lambda p: p["data"].update(ec_terms=["unknown"]),
        lambda p: p["data"].update(future_value=float("inf")),
    ],
)
def test_incomplete_or_inconsistent_native_support_fails_before_mapping(mutation):
    payload = native()
    mutation(payload)
    with pytest.raises(ConnectorError):
        get_domain_summary("1htiA00", RELEASE, client=Client(payload))


@pytest.mark.parametrize(
    "context", [{"version": RELEASE}, {"truncated": True}, {"truncated": 0}]
)
def test_custom_client_cuts_and_guessed_versions_are_refused(context):
    with pytest.raises(ConnectorError):
        get_domain_summary("1htiA00", RELEASE, client=Client(native(), **context))


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(source="UniProt"),
        lambda e: e.update(kind="search"),
        lambda e: e.update(version=RELEASE),
        lambda e: e.update(truncated=True),
        lambda e: e["query"].update(accession="P60174"),
        lambda e: e["query"].update(release="latest"),
        lambda e: e["query"].update(domain_id="1htiB00"),
    ],
)
def test_direct_mapper_checks_source_query_and_scope(change):
    envelope = get_domain_summary("1htiA00", RELEASE, client=FixtureCathClient())
    change(envelope)
    with pytest.raises(ConnectorError):
        map_domain(envelope)


def metadata():
    return {
        "source": "CATH",
        "kind": "domain_summary",
        "query": {"domain_id": "1htiA00", "release": RELEASE},
        "retrieved_at": "2026-01-01T00:00:00+00:00",
    }


def test_bound_supplied_gzip_checks_original_bytes_and_retains_declared_access(
    tmp_path,
):
    raw = gzip.compress((DIRECTORY / "domain_summary__1htiA00.json").read_bytes())
    path = tmp_path / "external.json.gz"
    path.write_bytes(raw)
    declared = metadata()
    client = SnapshotCathClient(
        path, source_metadata=declared, expected_sha256=hashlib.sha256(raw).hexdigest()
    )
    declared["query"]["domain_id"] = "1htiB00"
    envelope = get_domain_summary("1htiA00", RELEASE, client=client)
    assert envelope["record"] == native()
    receipt = envelope["snapshot_receipt"]
    assert receipt["compression"] == "gzip"
    assert receipt["digest_verification"] == "matched_caller_digest"
    assert receipt["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["source_access_observed"] is False
    assert envelope["retrieved_at"] == metadata()["retrieved_at"]
    assert envelope["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert map_domain(envelope)[0]["source_metadata"]["snapshot_receipt"] == receipt
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_domain_summary(
            "1htiA00",
            RELEASE,
            client=SnapshotCathClient(
                path, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "change",
    [
        lambda m: m.update(source="UniProt"),
        lambda m: m.update(kind="search"),
        lambda m: m["query"].update(domain_id="1htiB00"),
        lambda m: m["query"].update(release="v4_3_0"),
        lambda m: m["query"].update(extra=True),
        lambda m: m.update(version=RELEASE),
    ],
)
def test_supplied_snapshot_must_declare_exact_source_domain_and_route(change):
    declared = metadata()
    change(declared)
    with pytest.raises(ConnectorError):
        get_domain_summary(
            "1htiA00",
            RELEASE,
            client=SnapshotCathClient(
                DIRECTORY / "domain_summary__1htiA00.json", source_metadata=declared
            ),
        )


@pytest.mark.parametrize(
    "document",
    [
        '{"success":true,"success":false}',
        '{"success":true,"data":NaN}',
        '{"success":true,"data":1e999}',
        "{}",
    ],
)
def test_supplied_invalid_json_is_failed_not_empty(tmp_path, document):
    path = tmp_path / "invalid.json"
    path.write_text(document, encoding="utf-8", newline="")
    with pytest.raises(ConnectorError):
        get_domain_summary(
            "1htiA00",
            RELEASE,
            client=SnapshotCathClient(path, source_metadata=metadata()),
        )


def test_missing_fixture_is_unavailable_without_domain_absence_claim(tmp_path):
    with pytest.raises(ConnectorError) as exc:
        get_domain_summary("1htiA00", RELEASE, client=FixtureCathClient(tmp_path))
    assert exc.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


@pytest.mark.parametrize("code", [404, 500])
def test_http_errors_are_failed_access_not_biological_absence(monkeypatch, code):
    import sabueso.tools.db.cath as module

    def fail(url, **kwargs):
        raise HTTPError(url, code, "failure", None, None)

    monkeypatch.setattr(module, "urlopen", fail)
    with pytest.raises(ConnectorError) as exc:
        get_domain_summary("1htiA00", RELEASE)
    assert exc.value.acquisition_trace["records"][0]["outcome"] == "failed"


def test_single_get_archive_replay_preserves_original_time_and_follows_no_links(
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
        return Answer((DIRECTORY / "domain_summary__1htiA00.json").read_bytes())

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "cath.db")
    with archive.recording():
        first = get_domain_summary("1htiA00", RELEASE)

    def forbidden(*args, **kwargs):
        pytest.fail("Replay/mapping followed a native link")

    monkeypatch.setattr(http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_domain_summary("1htiA00", RELEASE)
    assert calls == [
        "https://www.cathdb.info/version/v4_4_0/api/rest/domain_summary/1htiA00?content-type=application/json"
    ]
    assert first["record"] == second["record"] == native()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert map_domain(first) == map_domain(second)
    a, b = [e["acquisition_trace"]["records"][0] for e in (first, second)]
    assert a["network_attempts"] == a["received_responses"] == 1
    assert b["network_attempts"] == 0 and b["access"] == "replay"
    assert a["response_identity"] == b["response_identity"]


def test_cath_data_terms_keep_attribution_separate_from_parent_resources():
    assert source_terms()["CATH"]["licence"] == "CC-BY-4.0"
    result = verdict("CATH", "redistribution")
    assert result["verdict"] == "allowed"
    assert "attribution" in result["obligations"]
