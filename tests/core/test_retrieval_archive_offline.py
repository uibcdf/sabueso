"""The retrieval archive (#100): record what the sources answered, replay a build
without the network, and reuse fresh answers."""

import json
from datetime import timedelta
from email.message import Message
from urllib.error import URLError

import pytest

import sabueso
from sabueso.core.errors import NotArchivedError
from sabueso.tools.db import _http

FLAT = json.load(open("temp_data/pubchem/structures.json"))["lookups"][1]["query"]
PROPERTIES = open("temp_data/pubchem/3717450.json", "rb").read()


class _Answer:
    def __init__(self, body):
        self.body, self.status, self.headers = body, 200, Message()

    def read(self, *_):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None


def _network(asked):
    def serve(request, timeout):
        asked.append(request.full_url)
        if "/smiles/cids/" in request.full_url:
            return _Answer(b'{"IdentifierList": {"CID": [3717450]}}')
        if "/cid/3717450/property/" in request.full_url:
            return _Answer(PROPERTIES)
        raise AssertionError(f"unexpected request {request.full_url}")

    return serve


def _no_network(request, timeout):
    raise URLError("the network was asked")


def _build(**options):
    card, resolution = sabueso.resolve(f"smiles:{FLAT}", unichem=False, **options)
    assert resolution.status == "resolved", resolution.decision
    return card


def _without_manifest(card):
    data = card.to_dict()
    data["quality"].pop("retrievals")
    return data


def test_a_build_replays_without_the_network_identical(tmp_path, monkeypatch):
    archive = sabueso.RetrievalArchive(tmp_path / "a.db")
    asked = []
    monkeypatch.setattr(_http, "_urlopen", _network(asked))
    with archive.recording():
        recorded = _build()
    assert len(asked) == 2
    manifest = recorded.quality["retrievals"]
    assert manifest["mode"] == "record" and len(manifest["records"]) == 2
    # Statements carry the time their answer was read, as the record states it.
    times = {r["retrieved_at"] for r in manifest["records"]}
    sa_times = {sa["retrieved_at"] for sa in recorded.source_assertion_store.to_list()}
    assert sa_times <= times

    monkeypatch.setattr(_http, "_urlopen", _no_network)
    with archive.replaying(of=recorded):
        replayed = _build()
    assert replayed.quality["retrievals"]["mode"] == "replay"
    assert _without_manifest(replayed) == _without_manifest(recorded)
    # The same answers, in the order the build received them.
    assert [r["ref"] for r in replayed.quality["retrievals"]["records"]] == [
        r["ref"] for r in manifest["records"]
    ]
    with pytest.raises(ValueError):
        archive.replaying(of={"not": "a manifest"})


def test_what_the_archive_does_not_hold_is_not_queried(tmp_path, monkeypatch):
    archive = sabueso.RetrievalArchive(tmp_path / "a.db")
    monkeypatch.setattr(_http, "_urlopen", _network([]))
    with archive.recording():
        _build()
    monkeypatch.setattr(_http, "_urlopen", _no_network)
    import warnings

    with archive.replaying(), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        card, _ = sabueso.resolve(f"smiles:{FLAT}", unichem=True)
    # Not asked is not a failure: no "could not be consulted" warning.
    assert not [w for w in caught if "could not be consulted" in str(w.message)]
    (unichem,) = [e for e in card.quality["enrichments"] if e["source"] == "UniChem"]
    assert (unichem["status"], unichem["reason"]) == ("not_queried", "not_in_archive")
    with archive.replaying(), pytest.raises(NotArchivedError):
        _http.urlopen("https://example.org/never-asked")


def test_fresh_answers_are_reused_and_old_ones_asked_again(tmp_path, monkeypatch):
    archive = sabueso.RetrievalArchive(tmp_path / "a.db")
    asked = []
    monkeypatch.setattr(_http, "_urlopen", _network(asked))
    with archive.recording():
        _build()
    with archive.reusing(timedelta(days=30)):
        card = _build()
    assert len(asked) == 2  # nothing asked again
    assert card.quality["retrievals"]["mode"] == "reuse"
    assert card.quality["retrievals"]["max_age_seconds"] == 30 * 86400
    with archive.reusing(timedelta(microseconds=1)):
        _build()
    assert len(asked) == 4  # too old: asked again, and kept (the same answer read in
    # the same second is the same record)
    with pytest.raises(ValueError):
        archive.reusing(timedelta(0))


def test_each_answer_is_its_source_s_and_explain_links_a_statement_to_them(
    tmp_path, monkeypatch
):
    archive = sabueso.RetrievalArchive(tmp_path / "a.db")
    monkeypatch.setattr(_http, "_urlopen", _network([]))
    with archive.recording():
        card = _build()
    assert {r["source"] for r in card.quality["retrievals"]["records"]} == {"PubChem"}
    sa = card.source_assertion_store.to_list()[0]
    (explained,) = card.explain([sa["id"]])
    assert explained["retrievals"]["basis"] == "source_in_build"
    assert len(explained["retrievals"]["refs"]) == 2
    held = archive.sources()
    assert held["PubChem"]["records"] == 2
    assert held["PubChem"]["retention"]["keep"] == "yes"


def test_every_client_names_a_source_whose_terms_are_recorded():
    import re
    from pathlib import Path

    from sabueso.core.terms import source_terms

    known = set(source_terms())
    for path in Path("sabueso/tools/db").glob("*.py"):
        text = path.read_text()
        constant = re.search(r'^SOURCE = "([^"]+)"', text, re.M)
        for name in re.findall(r"stamp\(([^)]*)\)", text):
            if not name or path.name == "_http.py":
                continue
            value = constant.group(1) if name == "SOURCE" else name.strip('"')
            assert value in known, (path.name, value)


@pytest.mark.parametrize(
    "source, keep, share, conditions",
    [
        ("ChEMBL", "yes", "yes", ["attribution", "share_alike"]),
        ("Reactome", "yes", "yes", []),
        ("UniProt", "yes", "yes", ["attribution"]),
        ("PubChem BioAssay", "internal", "unknown", None),
        ("Nowhere", "internal", "unknown", None),
    ],
)
def test_retention_is_derived_from_the_licence(source, keep, share, conditions):
    from sabueso.core.terms import retention

    answer = retention(source)
    assert answer["rule"] == "retention_from_licence@1"
    assert (answer["keep"], answer["share"]) == (keep, share)
    if conditions is not None:
        assert answer["conditions"] == conditions
    else:
        assert answer["reason"] in ("per_record_terms", "no_terms_recorded")
