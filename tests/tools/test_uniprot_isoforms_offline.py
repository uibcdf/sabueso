"""Explicit native isoform identity, independent sequence scope and access receipts."""

import copy
import hashlib
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.mappings.uniprot_isoforms import map_isoform_sequence
from sabueso.tools.db.uniprot import FixtureUniProtIsoformClient, get_isoform_sequence

DIRECTORY = Path("temp_data/uniprot_isoforms")


def native():
    return json.loads((DIRECTORY / "P60174.json").read_bytes())


def fasta(sequence, identifier="P60174-3"):
    header = (DIRECTORY / "P60174-3.fasta").read_text().splitlines()[0]
    return header.replace("|P60174-3|", f"|{identifier}|") + "\n" + sequence + "\n"


def declarations(payload):
    return next(
        c["isoforms"]
        for c in payload["comments"]
        if c["commentType"] == "ALTERNATIVE PRODUCTS"
    )


class Client:
    def __init__(self, payload=None, fasta=None, version=None):
        self.payload = native() if payload is None else payload
        self.fasta = fasta
        self.version = version
        self.calls = []

    def parent(self, identifier):
        self.calls.append(("parent", identifier))
        return {"record": self.payload, "retrieved_at": "2026-01-01", "version": None}

    def sequence(self, identifier):
        self.calls.append(("sequence", identifier))
        return {
            "record": self.fasta
            if self.fasta is not None
            else (DIRECTORY / f"{identifier}.fasta").read_text(),
            "retrieved_at": "2026-01-02",
            "version": self.version,
        }


@pytest.mark.parametrize(
    "identifier,length,name,status",
    [
        ("P60174-1", 249, "1", "Displayed"),
        ("P60174-3", 286, "2", "Described"),
        ("P60174-4", 167, "3", "Described"),
    ],
)
def test_native_hstim_keeps_exact_isoform_name_id_and_independent_revisions(
    identifier, length, name, status
):
    envelope = get_isoform_sequence(
        identifier.lower(), client=FixtureUniProtIsoformClient()
    )
    before = copy.deepcopy(envelope)
    (assertion,) = map_isoform_sequence(envelope)
    value, metadata = assertion["asserted_value"], assertion["source_metadata"]
    assert value["isoform_id"] == identifier and value["length"] == length
    assert metadata["native_isoform_declaration"]["name"]["value"] == name
    assert metadata["native_isoform_declaration"]["isoformSequenceStatus"] == status
    assert value["sequence_id"] == metadata["sequence"]["id"] == "UniProt:" + identifier
    assert (
        metadata["sequence"]["uniprot_ref"]
        == assertion["subject_ref"]
        == "uniprot:P60174"
    )
    assert metadata["sequence"]["revision"] is assertion["source"]["version"] is None
    assert metadata["parent_entry"]["version"] == "212"
    assert metadata["parent_entry"]["record"]["entryAudit"]["sequenceVersion"] == 4
    assert metadata["parent_entry"]["record"] == native()
    assert (
        metadata["isoform_sequence"]["record"]
        == (DIRECTORY / f"{identifier}.fasta").read_text()
    )
    assert (
        metadata["sequence"]["sha256"]
        == hashlib.sha256(value["value"].encode()).hexdigest()
    )
    assert "no_canonical_offset" in metadata["mapping_scope"]["coordinates"]
    parent, sequence = envelope["acquisition_trace"]["records"]
    assert parent["source_version"]["value"] == 212
    assert sequence["source_version"]["value"] is None
    assert (
        sequence["sequence_length"] == length and sequence["database_release"] is None
    )
    for component in (parent, sequence):
        assert (
            component["access"] == "supplied_file" and component["retrieved_at"] is None
        )
        assert component["network_attempts"] == 0
        assert any(
            "isoform_sequence_revision" in gap for gap in component["bibliography_gaps"]
        )
        assert component["snapshot_receipt"]["source_access_observed"] is False
    assertion["source_metadata"]["parent_entry"]["record"]["comments"].clear()
    assert envelope == before


def test_source_isoform_sequence_is_readable_without_canonical_annotations_or_card_mutation():
    path = Path("temp_data/frozen_cards/schema_0.3.12__P60174.json")
    card = Card.from_dict(json.loads(path.read_text()))
    before = card.to_dict()
    (assertion,) = map_isoform_sequence(
        get_isoform_sequence("P60174-3", client=FixtureUniProtIsoformClient())
    )
    view = card.residue_knowledge(
        3, sequence_ref="UniProt:P60174-3", source_assertions=[assertion]
    )
    assert view["amino_acid"] == "E" and view["stored_annotations"] is None
    assert view["sequence_basis"] == "source_sequence_declaration"
    assert card.get_residue(3)["amino_acid"] == "P"
    assert view["sequence_support"]["support"][0]["assertion"] == assertion
    assert card.to_dict() == before


def test_not_declared_is_scoped_to_parent_and_does_not_request_guessed_name_suffix():
    client = Client()
    envelope = get_isoform_sequence("P60174-2", client=client)
    assert envelope["record"]["selection_status"] == "not_declared"
    assert (
        envelope["record"]["isoform_sequence"] is None
        and map_isoform_sequence(envelope) == []
    )
    assert client.calls == [("parent", "P60174-2")]
    assert envelope["record"]["parent_entry"]["record"] == native()


@pytest.mark.parametrize(
    "status,outcome",
    [
        ("Not described", "sequence_not_stated"),
        ("External", "external_sequence_not_followed"),
        ("future_status", "sequence_status_unqualified"),
    ],
)
def test_unsupported_or_unknown_sequence_status_keeps_declarations_and_queries_no_fasta(
    status, outcome
):
    payload = native()
    declarations(payload)[1]["isoformSequenceStatus"] = status
    client = Client(payload)
    envelope = get_isoform_sequence("P60174-3", client=client)
    assert (
        envelope["record"]["selection_status"] == outcome
        and map_isoform_sequence(envelope) == []
    )
    assert client.calls == [("parent", "P60174-3")]


@pytest.mark.parametrize(
    "mode,outcome",
    [
        ("missing_comments", "not_stated"),
        ("missing_isoforms", "not_stated"),
        ("empty_isoforms", "not_declared"),
    ],
)
def test_missing_declaration_scope_and_explicit_empty_arrays_stay_distinct(
    mode, outcome
):
    payload = native()
    comment = next(
        c for c in payload["comments"] if c["commentType"] == "ALTERNATIVE PRODUCTS"
    )
    if mode == "missing_comments":
        payload.pop("comments")
    elif mode == "missing_isoforms":
        comment.pop("isoforms")
    else:
        comment["isoforms"] = []
    client = Client(payload)
    envelope = get_isoform_sequence("P60174-3", client=client)
    assert envelope["record"]["selection_status"] == outcome
    assert client.calls == [("parent", "P60174-3")]


def test_same_sequence_different_ids_and_changed_parent_support_remain_independent():
    payload = native()
    declarations(payload).append(
        {
            "name": {"value": "another native label"},
            "isoformIds": ["P60174-99"],
            "isoformSequenceStatus": "Displayed",
        }
    )
    (a,) = map_isoform_sequence(
        get_isoform_sequence("P60174-1", client=Client(payload))
    )
    document = (
        (DIRECTORY / "P60174-1.fasta").read_text().replace("|P60174-1|", "|P60174-99|")
    )
    (b,) = map_isoform_sequence(
        get_isoform_sequence("P60174-99", client=Client(payload, document))
    )
    assert a["asserted_value"]["value"] == b["asserted_value"]["value"]
    assert (
        a["id"] != b["id"]
        and a["asserted_value"]["sequence_id"] != b["asserted_value"]["sequence_id"]
    )
    changed = copy.deepcopy(payload)
    changed["entryAudit"]["entryVersion"] += 1
    (c,) = map_isoform_sequence(
        get_isoform_sequence("P60174-1", client=Client(changed))
    )
    assert a["asserted_value"] == c["asserted_value"] and a["id"] != c["id"]
    assert c["source"]["version"] is None


def test_partial_declaration_scope_does_not_establish_not_listed_absence():
    payload = native()
    payload["comments"].append(
        {"commentType": "ALTERNATIVE PRODUCTS", "events": ["Alternative splicing"]}
    )
    client = Client(payload)
    envelope = get_isoform_sequence("P60174-2", client=client)
    assert envelope["record"]["selection_status"] == "not_stated"
    assert client.calls == [("parent", "P60174-2")]


@pytest.mark.parametrize("component", ["parent", "sequence"])
def test_custom_client_truncated_components_are_not_declared_complete(component):
    class Truncated(Client):
        def parent(self, identifier):
            result = super().parent(identifier)
            if component == "parent":
                result["truncated"] = True
            return result

        def sequence(self, identifier):
            result = super().sequence(identifier)
            if component == "sequence":
                result["truncated"] = True
            return result

    with pytest.raises(ConnectorError):
        get_isoform_sequence("P60174-3", client=Truncated())


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(primaryAccession="P00938"),
        lambda p: p.update(entryType="Inactive"),
        lambda p: p["sequence"].update(length=True),
        lambda p: p["sequence"].update(value="AC D"),
        lambda p: p["sequence"].update(md5="0" * 32),
        lambda p: p.update(entryAudit=[]),
        lambda p: p["entryAudit"].update(sequenceVersion=True),
        lambda p: p.update(comments=None),
        lambda p: declarations(p).append(copy.deepcopy(declarations(p)[0])),
        lambda p: declarations(p).append(None),
        lambda p: declarations(p)[0].update(isoformIds=["../P60174-1"]),
        lambda p: declarations(p)[0].update(isoformIds=[]),
        lambda p: declarations(p)[0].update(isoformSequenceStatus=None),
        lambda p: declarations(p)[1].update(sequenceIds=[]),
        lambda p: declarations(p)[1].update(sequenceIds=["VSP_060722", "VSP_060722"]),
        lambda p: declarations(p)[1].update(sequenceIds=[True]),
        lambda p: declarations(p)[2].update(name={"value": None}),
        lambda p: declarations(p)[2].update(future=float("inf")),
    ],
)
def test_malformed_parent_or_any_unselected_declaration_fails_before_fasta(change):
    payload = native()
    change(payload)
    client = Client(payload)
    with pytest.raises(ConnectorError):
        get_isoform_sequence("P60174-3", client=client)
    assert client.calls == [("parent", "P60174-3")]


@pytest.mark.parametrize(
    "document",
    [
        "",
        fasta("MAT", "P60174"),
        fasta("MAT", "P60174-4"),
        fasta(""),
        fasta("MA-T"),
        fasta("MA T"),
        fasta("mat"),
        fasta("MAT*"),
        fasta("MÅT"),
        fasta("MAT") + fasta("MAT", "P60174-4"),
        fasta("MAT").replace(">sp|", ">tr|", 1),
        "<html>error</html>",
    ],
)
def test_malformed_or_wrong_fasta_is_not_repaired_or_canonical_fallback(document):
    with pytest.raises(ConnectorError):
        get_isoform_sequence("P60174-3", client=Client(fasta=document))


def test_displayed_sequence_disagreement_and_client_revision_are_refused():
    document = (DIRECTORY / "P60174-1.fasta").read_text().replace("MAPSR", "AAPSR")
    with pytest.raises(ConnectorError):
        get_isoform_sequence("P60174-1", client=Client(fasta=document))
    with pytest.raises(ConnectorError):
        get_isoform_sequence("P60174-3", client=Client(version="4"))


@pytest.mark.parametrize(
    "identifier",
    [
        "P60174",
        "TPIS_HUMAN",
        "P60174-0",
        "P60174-01",
        "../P60174-3",
        "P60174-3?x",
        "P60174-3/",
        True,
        3,
    ],
)
def test_unsafe_or_implicit_id_never_reaches_client_even_with_skip(identifier):
    class NoAccess:
        def parent(self, identifier):
            pytest.fail("Invalid isoform reached client")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_isoform_sequence(identifier, client=NoAccess(), skip_digestion=True)


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(source="UniParc"),
        lambda e: e.update(kind="entry"),
        lambda e: e.update(version="212"),
        lambda e: e.update(truncated=True),
        lambda e: e["query"].update(page=1),
        lambda e: e["record"].update(selection_status="not_declared"),
        lambda e: e["record"]["parent_entry"].update(version="211"),
        lambda e: e["record"]["parent_entry"].update(truncated=True),
        lambda e: e["record"]["parent_entry"]["record"].update(entryAudit=[]),
        lambda e: e["record"]["isoform_sequence"]["query"].update(
            isoform_id="P60174-4"
        ),
        lambda e: e["record"]["isoform_sequence"].update(version="4"),
        lambda e: e["record"]["isoform_sequence"].update(truncated=True),
    ],
)
def test_mapper_refuses_unsupported_component_scope_before_mapping(change):
    envelope = get_isoform_sequence("P60174-3", client=Client())
    change(envelope)
    with pytest.raises(ConnectorError):
        map_isoform_sequence(envelope)


@pytest.mark.parametrize("missing", ["parent", "sequence"])
def test_missing_component_fixture_is_unavailable_and_keeps_successful_parent(
    tmp_path, missing
):
    directory = tmp_path / "uniprot_isoforms"
    directory.mkdir()
    if missing == "sequence":
        (directory / "P60174.json").write_bytes(
            (DIRECTORY / "P60174.json").read_bytes()
        )
    with pytest.raises(ConnectorError) as error:
        get_isoform_sequence("P60174-3", client=FixtureUniProtIsoformClient(tmp_path))
    records = error.value.acquisition_trace["records"]
    assert records[-1]["outcome"] == "unavailable"
    if missing == "sequence":
        assert len(records) == 2 and records[0]["outcome"] == "received"


class Answer(io.BytesIO):
    status = 200
    headers = Message()
    headers["Content-Type"] = "text/plain"
    headers["X-UniProt-Release"] = "2026_03"


@pytest.mark.parametrize(
    "body",
    [b'{"primaryAccession":"P60174","primaryAccession":"P00938"}', b'{"sequence":NaN}'],
)
def test_malformed_parent_wire_json_fails_before_any_fasta_request(body, monkeypatch):
    import sabueso.tools.db._http as http

    calls = []

    def wire(request, timeout):
        calls.append(request.full_url)
        answer = Answer(body)
        answer.headers = Message()
        answer.headers["Content-Type"] = "application/json"
        return answer

    monkeypatch.setattr(http, "_urlopen", wire)
    with pytest.raises(ConnectorError) as error:
        get_isoform_sequence("P60174-3")
    assert calls == ["https://rest.uniprot.org/uniprotkb/P60174.json"]
    assert error.value.acquisition_trace["records"][0]["outcome"] == "failed"


@pytest.mark.parametrize(
    "stage,status", [("parent", 404), ("sequence", 404), ("sequence", 500)]
)
def test_http_failure_does_not_become_not_declared(stage, status, monkeypatch):
    import sabueso.tools.db._http as http

    monkeypatch.setattr(http, "RETRIES", 0)

    def wire(request, timeout):
        if stage == "parent" or request.full_url.endswith(".fasta"):
            raise HTTPError(request.full_url, status, "failed", {}, None)
        answer = Answer((DIRECTORY / "P60174.json").read_bytes())
        answer.headers = Message()
        answer.headers["Content-Type"] = "application/json"
        return answer

    monkeypatch.setattr(http, "_urlopen", wire)
    with pytest.raises(ConnectorError) as error:
        get_isoform_sequence("P60174-3")
    records = error.value.acquisition_trace["records"]
    assert records[-1]["outcome"] == "failed"
    if stage == "sequence":
        assert len(records) == 2 and records[0]["outcome"] == "received"


def test_shared_archive_replay_keeps_two_original_component_times_and_never_fetches_other_isoforms(
    tmp_path, monkeypatch
):
    import sabueso.tools.db._http as http

    calls = []

    def wire(request, timeout):
        calls.append(request.full_url)
        path = DIRECTORY / request.full_url.rsplit("/", 1)[1]
        answer = Answer(path.read_bytes())
        answer.headers = Message()
        answer.headers["Content-Type"] = (
            "application/json" if path.suffix == ".json" else "text/plain"
        )
        answer.headers["X-UniProt-Release"] = "2026_03"
        return answer

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "isoforms.db")
    with archive.recording():
        first = get_isoform_sequence("P60174-3")

    def fail(*args, **kwargs):
        pytest.fail("Replay/mapping fetched an unqueried isoform or linked resource")

    monkeypatch.setattr(http, "_urlopen", fail)
    with archive.replaying():
        second = get_isoform_sequence("P60174-3")
    assert calls == [
        "https://rest.uniprot.org/uniprotkb/P60174.json",
        "https://rest.uniprot.org/uniprotkb/P60174-3.fasta",
    ]
    assert first["record"] == second["record"] and map_isoform_sequence(
        first
    ) == map_isoform_sequence(second)
    assert first["record"]["isoform_sequence"]["database_release"] == "2026_03"
    assert first["version"] is None
    for a, b in zip(
        first["acquisition_trace"]["records"],
        second["acquisition_trace"]["records"],
        strict=True,
    ):
        assert a["retrieved_at"] == b["retrieved_at"]
        assert a["network_attempts"] == a["received_responses"] == 1
        assert b["access"] == "replay" and b["network_attempts"] == 0
        assert a["response_identity"] == b["response_identity"]
