"""Native BRENDA EC-class RDF fidelity, failure states and exact archive replay."""

import copy
import gzip
import hashlib
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import source_terms
from sabueso.mappings.brenda import (
    EC_ROOT,
    LANG_STRING,
    STRING,
    URL,
    map_enzyme_class,
    response_query,
)
from sabueso.tools.db.brenda import (
    FixtureBrendaClient,
    SnapshotBrendaClient,
    get_enzyme_class,
)

PATH = Path("temp_data/brenda/enzyme_class__5.3.1.1.json")
NATIVE = json.loads(PATH.read_text())


class Client:
    def __init__(self, payload=NATIVE, **context):
        self.payload, self.context = payload, context

    def enzyme_class(self, identifier):
        return {"record": self.payload, "version": None, **self.context}


def read(payload=NATIVE, **context):
    return get_enzyme_class("5.3.1.1", client=Client(payload, **context))


def metadata():
    return {
        "source": "BRENDA",
        "kind": "enzyme_class",
        "query": response_query("5.3.1.1"),
    }


def test_originals_keep_ec_identity_systematic_names_and_unknown_revision():
    assert hashlib.sha256(PATH.read_bytes()).hexdigest() == (
        "9c1b4c3cc16247040a01d6112c420a7e06cae0342498a4e3e1af7120424eff30"
    )
    for ec, label in [
        ("5.3.1.1", "triose-phosphate isomerase"),
        ("2.7.1.1", "hexokinase"),
    ]:
        envelope = get_enzyme_class(ec, client=FixtureBrendaClient())
        before = copy.deepcopy(envelope)
        assertions = map_enzyme_class(envelope)
        assert len(assertions) == 1
        a = assertions[0]
        assert a["subject_ref"] == f"brenda:ec:{ec}"
        assert a["asserted_value"]["ec"]["value"] == EC_ROOT + ec
        assert a["asserted_value"]["label"]["value"] == label
        assert a["source"]["version"] is envelope["version"] is None
        assert a["source_metadata"]["native_response"] == envelope["record"]
        assert envelope["acquisition_trace"]["records"][0]["count"] == 1
        a["asserted_value"].clear()
        assert envelope == before


def test_original_empty_solutions_do_not_assert_absent_activity():
    e = get_enzyme_class("7.99.99.99999", client=FixtureBrendaClient())
    assert e["record"]["results"]["bindings"] == []
    assert map_enzyme_class(e) == []
    t = e["acquisition_trace"]["records"][0]
    assert t["outcome"] == "not_found" and t["network_attempts"] == 0


def test_unbound_optional_is_distinct_from_native_empty_literal():
    a = map_enzyme_class(read())[0]
    assert a["asserted_value"]["description"] == {"type": "literal", "value": ""}
    p = copy.deepcopy(NATIVE)
    del p["results"]["bindings"][0]["description"]
    assert "description" not in map_enzyme_class(read(p))[0]["asserted_value"]


def test_repeated_conflicting_solutions_retain_independent_support():
    p = copy.deepcopy(NATIVE)
    p["results"]["bindings"] *= 2
    p["results"]["bindings"].append(copy.deepcopy(p["results"]["bindings"][0]))
    p["results"]["bindings"][-1]["label"]["value"] = "different native label"
    a = map_enzyme_class(read(p))
    assert len(a) == 3 and len({x["id"] for x in a}) == 3
    assert [x["source_metadata"]["binding_index"] for x in a] == [0, 1, 2]
    assert a[-1]["asserted_value"]["label"]["value"] == "different native label"


@pytest.mark.parametrize(
    "node",
    [
        {"type": "literal", "value": "texte", "xml:lang": "fr"},
        {
            "type": "literal",
            "value": "texte",
            "datatype": LANG_STRING,
            "xml:lang": "fr",
        },
        {"type": "typed-literal", "value": "text", "datatype": STRING},
        {"type": "literal", "value": "", "datatype": STRING},
    ],
)
def test_rdf_language_datatype_and_blank_survive(node):
    p = copy.deepcopy(NATIVE)
    p["results"]["bindings"][0]["description"] = node
    assert map_enzyme_class(read(p))[0]["asserted_value"]["description"] == node


@pytest.mark.parametrize(
    "node",
    [
        None,
        "text",
        {},
        {"type": "uri", "value": "text"},
        {"type": "literal", "value": 0},
        {"type": "literal", "value": float("nan")},
        {"type": "literal", "value": "text", "datatype": "numeric"},
        {"type": "literal", "value": "text", "xml:lang": None},
        {"type": "literal", "value": "text", "xml:lang": ""},
        {"type": "literal", "value": "text", "datatype": STRING, "xml:lang": "fr"},
        {"type": "literal", "value": "text", "datatype": LANG_STRING},
        {"type": "typed-literal", "value": "text"},
        {"type": "literal", "value": "text", "other": "text"},
    ],
)
def test_unsupported_rdf_nodes_fail_including_late_rows(node):
    p = copy.deepcopy(NATIVE)
    p["results"]["bindings"].append(copy.deepcopy(p["results"]["bindings"][0]))
    p["results"]["bindings"][-1]["name"] = node
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"error": "failed"},
        {"head": {"vars": []}, "results": {"bindings": []}},
        {"head": NATIVE["head"], "results": {"bindings": None}},
        {"head": NATIVE["head"], "results": {"bindings": []}, "truncated": True},
    ],
)
def test_malformed_error_and_unknown_cut_bodies_are_not_empty_results(payload):
    with pytest.raises(ConnectorError):
        read(payload)


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r.pop("label"),
        lambda r: r.update(ec={"type": "uri", "value": EC_ROOT + "2.7.1.1"}),
        lambda r: r.update(ec={"type": "literal", "value": EC_ROOT + "5.3.1.1"}),
        lambda r: r.update(other={"type": "literal", "value": "extra"}),
    ],
)
def test_native_identity_and_required_binding_scope_fail(change):
    p = copy.deepcopy(NATIVE)
    change(p["results"]["bindings"][0])
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        "",
        "P60174",
        "EC:5.3.1.1",
        "5.3.1.-",
        "5.3.1",
        "5.03.1.1",
        "5.3.1.1> } UNION {",
        "5.3.1.1/",
        "５.3.1.1",
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_unsafe_ec_scope_fails_with_or_without_digestion(identifier, skip):
    with pytest.raises((ConnectorError, ArgumentError)):
        get_enzyme_class(identifier, client=Client(), skip_digestion=skip)


@pytest.mark.parametrize(
    "context",
    [
        {"version": "2026.1"},
        {"truncated": True},
        {"source": "Other"},
        {"kind": "kinetics"},
        {"query": response_query("2.7.1.1")},
    ],
)
def test_client_scope_revision_or_cut_is_not_resealed(context):
    with pytest.raises(ConnectorError):
        read(**context)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_snapshot_preserves_hash_time_and_declared_terms(tmp_path, compressed):
    raw = PATH.read_bytes()
    if compressed:
        raw = gzip.compress(raw)
    path = tmp_path / ("native.json.gz" if compressed else "native.json")
    path.write_bytes(raw)
    declared = metadata()
    declared.update(
        retrieved_at="2026-10-07T22:00:00+00:00", terms={"licence": "declared"}
    )
    before = copy.deepcopy(declared)
    e = get_enzyme_class(
        "5.3.1.1",
        client=SnapshotBrendaClient(
            path,
            source_metadata=declared,
            expected_sha256=hashlib.sha256(raw).hexdigest(),
        ),
    )
    assert e["retrieved_at"] == declared["retrieved_at"]
    assert e["snapshot_receipt"]["source_access_observed"] is False
    assert e["snapshot_receipt"]["declared_terms"] == declared["terms"]
    assert declared == before
    with pytest.raises(ConnectorError):
        get_enzyme_class(
            "5.3.1.1",
            client=SnapshotBrendaClient(
                path, source_metadata=declared, expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("source", "Other"),
        ("kind", "kinetics"),
        ("query", response_query("2.7.1.1")),
        ("version", "2026.1"),
    ],
)
def test_foreign_snapshot_binding_fails(tmp_path, field, value):
    path = tmp_path / "native.json"
    path.write_bytes(PATH.read_bytes())
    declared = metadata()
    declared[field] = value
    with pytest.raises(ConnectorError):
        get_enzyme_class(
            "5.3.1.1", client=SnapshotBrendaClient(path, source_metadata=declared)
        )


def test_missing_fixture_and_failed_http_are_not_absent_classes(tmp_path, monkeypatch):
    from sabueso.tools.db import _http

    with pytest.raises(ConnectorError):
        get_enzyme_class("5.3.1.1", client=FixtureBrendaClient(tmp_path))

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 503, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_enzyme_class("5.3.1.1")


def test_exact_one_get_and_zero_network_replay_keep_original_support(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(PATH.read_bytes())
        response.status = 200
        response.headers = Message()
        return response

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "archive.sqlite")
    with archive.recording():
        first = get_enzyme_class("5.3.1.1")
    assert len(calls) == 1 and calls[0].startswith(URL + "?")
    q = parse_qs(urlparse(calls[0]).query)
    assert q == {"query": [response_query("5.3.1.1")["sparql"]], "format": ["json"]}
    assert "LIMIT" not in q["query"][0] and "OFFSET" not in q["query"][0]
    with archive.replaying():
        replay = get_enzyme_class("5.3.1.1")
    assert len(calls) == 1 and replay["retrieved_at"] == first["retrieved_at"]
    assert map_enzyme_class(replay) == map_enzyme_class(first)
    assert replay["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert source_terms()["BRENDA"]["licence"] == "CC-BY-4.0"
