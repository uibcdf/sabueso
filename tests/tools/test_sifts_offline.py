"""SIFTS segment claims preserve structural numbering and separate native references."""

import copy
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ConnectorError
from sabueso.mappings.sifts import map_sequence_mappings, validate_mappings
from sabueso.tools.db.sifts import FixtureSIFTSClient, get_mappings

PATH = Path("temp_data/sifts/mappings__1hti.json")


def native():
    return json.loads(PATH.read_text())


def segment(payload):
    return payload["1hti"]["UniProt"]["P60174"]["mappings"][0]


class Client:
    def __init__(self, payload):
        self.payload = payload

    def mappings(self, identifier):
        return {"record": self.payload, "retrieved_at": "2026-01-01", "version": None}


def test_native_two_chain_mapping_is_detached_and_structure_subject_bound():
    envelope = get_mappings("1HTI", client=FixtureSIFTSClient())
    before = copy.deepcopy(envelope)
    assertions = map_sequence_mappings(envelope)
    assert envelope == before and len(assertions) == 2
    assert envelope["query"] == {"pdb_id": "1hti"} and envelope["version"] is None
    assert envelope["truncated"] is False
    for assertion, chain in zip(assertions, "AB"):
        value = assertion["asserted_value"]
        assert assertion["subject_ref"] == "pdb:1HTI"
        assert value["uniprot_ref"] == "uniprot:P60174"
        assert value["author_chain_id"] == chain == value["label_asym_id"]
        assert value["uniprot_range"] == {
            "start": 2,
            "end": 249,
            "indexing": "1-based-inclusive",
        }
        assert value["pdb_start"]["author_residue_number"] == 1
        assert value["pdb_end"]["residue_number"] == 248
        assert "database_inference" not in value.values()
    (access,) = envelope["acquisition_trace"]["records"]
    assert access["access"] == "supplied_file" and access["network_attempts"] == 0
    assert access["source"] == "SIFTS" and access["source_version"]["value"] is None
    assert access["provider"]["status"] == "available"
    assert access["retrieved_at"] is None
    assertions[0]["source_metadata"]["native_mapping"]["chain_id"] = "changed"
    assert envelope == before


def test_author_insertions_negative_numbering_and_gapped_segments_stay_native():
    payload = native()
    mapping = segment(payload)
    mapping["chain_id"] = "author-A"
    mapping["struct_asym_id"] = "label-9"
    mapping["start"].update(author_residue_number=-2, author_insertion_code="A")
    mapping["end"].update(author_residue_number=250, author_insertion_code="B")
    mapping["unp_end"] = 260  # endpoints alone cannot justify a linear residue offset
    value = map_sequence_mappings(get_mappings("1hti", client=Client(payload)))[0][
        "asserted_value"
    ]
    assert value["author_chain_id"] != value["label_asym_id"]
    assert value["pdb_start"]["author_insertion_code"] == "A"
    assert value["pdb_start"]["author_residue_number"] == -2
    assert value["uniprot_range"]["end"] == 260
    assert "offset" not in value and "sequence" not in value


def test_multiple_native_proteins_and_isoform_refs_are_never_folded_together():
    payload = native()
    reference = payload["1hti"]["UniProt"]["P60174"]
    payload["1hti"]["UniProt"]["P60174-3"] = copy.deepcopy(reference)
    payload["1hti"]["UniProt"]["P37840"] = copy.deepcopy(reference)
    assertions = map_sequence_mappings(get_mappings("1hti", client=Client(payload)))
    assert len(assertions) == 6
    assert {a["asserted_value"]["uniprot_ref"] for a in assertions} == {
        "uniprot:P60174",
        "uniprot:P60174-3",
        "uniprot:P37840",
    }
    assert len({a["id"] for a in assertions}) == 6


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(other={}),
        lambda p: p["1hti"].update(UniProt=None),
        lambda p: p["1hti"]["UniProt"].update(bad={"mappings": []}),
        lambda p: p["1hti"]["UniProt"]["P60174"].update(mappings=None),
        lambda p: segment(p).update(entity_id=True),
        lambda p: segment(p).update(entity_id=0),
        lambda p: segment(p).update(chain_id=""),
        lambda p: segment(p).update(struct_asym_id=None),
        lambda p: segment(p).update(unp_start=0),
        lambda p: segment(p).update(unp_start=True),
        lambda p: segment(p).update(unp_end=1),
        lambda p: segment(p).update(start=None),
        lambda p: segment(p)["start"].update(residue_number=0),
        lambda p: segment(p)["start"].update(residue_number=1.0),
        lambda p: segment(p)["start"].update(author_residue_number=True),
        lambda p: segment(p)["start"].update(author_insertion_code=5),
        lambda p: segment(p)["end"].update(residue_number=0),
        lambda p: segment(p).update(identity=float("nan")),
        lambda p: segment(p).update(identity=True),
        lambda p: segment(p).update(coverage=1.1),
        lambda p: p["1hti"]["UniProt"]["P60174"]["mappings"].append(
            copy.deepcopy(segment(p))
        ),
    ],
)
def test_invalid_identity_numbering_or_fraction_is_not_a_mapping_claim(change):
    payload = native()
    change(payload)
    with pytest.raises(ConnectorError):
        validate_mappings(payload, "1hti")


@pytest.mark.parametrize(
    "identifier", ["../1hti", "pdb:1hti", "1hti/extra", "pdb_00001hti", "", None]
)
def test_bad_pdb_id_is_refused_before_access(identifier):
    class Forbidden:
        def mappings(self, identifier):
            raise AssertionError("Invalid identity must not query a source")

    with pytest.raises(Exception) as caught:
        get_mappings(identifier, client=Forbidden())
    assert not isinstance(caught.value, AssertionError)


def test_explicit_empty_collection_unavailable_fixture_and_http_failure_differ(
    tmp_path, monkeypatch
):
    result = get_mappings("1hti", client=Client({"1hti": {"UniProt": {}}}))
    assert map_sequence_mappings(result) == [] and result["truncated"] is False
    with pytest.raises(ConnectorError) as missing:
        get_mappings("1hti", client=FixtureSIFTSClient(tmp_path))
    assert missing.value.acquisition_trace["records"][0]["outcome"] == "unavailable"
    from sabueso.tools.db import _http

    def failed(request, timeout):
        raise HTTPError(request.full_url, 404, "route missing", Message(), None)

    monkeypatch.setattr(_http, "_urlopen", failed)
    with pytest.raises(ConnectorError) as failure:
        get_mappings("1hti")
    assert failure.value.acquisition_trace["records"][0]["outcome"] == "failed"


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(source="Other"),
        lambda e: e.update(version="2026"),
        lambda e: e.update(truncated=True),
        lambda e: e.update(query={"pdb_id": "2hti"}),
    ],
)
def test_mapping_rejects_changed_source_revision_or_scope(change):
    envelope = get_mappings("1hti", client=FixtureSIFTSClient())
    change(envelope)
    with pytest.raises(ConnectorError):
        map_sequence_mappings(envelope)


def test_native_online_mapping_and_archive_replay_keep_original_time(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    calls = []

    class Response(io.BytesIO):
        status = 200

        def __init__(self, raw):
            super().__init__(raw)
            self.headers = Message()
            self.headers["Content-Type"] = "application/json"

    def download(request, timeout):
        calls.append(request.full_url)
        return Response(PATH.read_bytes())

    monkeypatch.setattr(_http, "_urlopen", download)
    archive = RetrievalArchive(tmp_path / "sifts.db")
    with archive.recording():
        original = get_mappings("1hti")

    def forbidden(*args, **kwargs):
        raise AssertionError("Replay must not query the network")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        replayed = get_mappings("1hti")
    assert calls == ["https://www.ebi.ac.uk/pdbe/api/mappings/uniprot/1hti"]
    assert original["retrieved_at"] == replayed["retrieved_at"]
    assert map_sequence_mappings(original) == map_sequence_mappings(replayed)
    assert replayed["acquisition_trace"]["records"][0]["access"] == "replay"
