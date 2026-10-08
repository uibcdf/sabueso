"""Native SIGNOR headerless rows, exact participants and independent request scope."""

import copy
import gzip
import hashlib
import io
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import source_terms, verdict
from sabueso.mappings.signor import COLUMNS, NO_RESULTS, map_relations, parse_relations
from sabueso.tools.db.signor import (
    FixtureSignorClient,
    SnapshotSignorClient,
    get_relations,
)

DIRECTORY = Path("temp_data/signor")


def native(identifier="P60174", taxon=9606):
    return (
        (DIRECTORY / f"relations__{identifier}__{taxon}.tsv")
        .read_bytes()
        .decode("utf-8")
    )


def metadata(identifier="P60174", taxon=9606):
    return {
        "source": "SIGNOR",
        "kind": "causal_relations",
        "query": {"accession": identifier, "requested_organism": taxon},
        "retrieved_at": "2026-10-06T12:00:00+00:00",
    }


class Client:
    def __init__(self, text, **context):
        self.text = text
        self.context = context

    def relations(self, identifier, taxon_id):
        return {
            "record": self.text,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


@pytest.mark.parametrize("identifier,count", [("P60174", 3), ("P31749", 456)])
def test_all_native_occurrences_preserve_first_row_and_original_support(
    identifier, count
):
    e = get_relations(identifier.lower(), client=FixtureSignorClient())
    before = copy.deepcopy(e)
    out = map_relations(e)
    rows = parse_relations(native(identifier), identifier)
    assert e["record"] == native(identifier)
    assert len(out) == len({a["id"] for a in out}) == count
    assert [a["asserted_value"] for a in out] == [r["fields"] for r in rows]
    for i, a in enumerate(out):
        assert a["source"]["name"] == "SIGNOR" and a["source"]["version"] is None
        assert a["subject_ref"] == f"signor:uniprot:{identifier}"
        assert a["source_metadata"]["native_row_index"] == i
        assert len(a["source_metadata"]["native_columns"]) == 29
        assert a["source_metadata"]["native_columns"][-1] == ""
        assert "no_entity_merge" in a["source_metadata"]["mapping_scope"]["identity"]
        assert (
            a["source_metadata"]["native_publication_pointer"]
            == rows[i]["fields"]["PMID"]
        )
        assert "knowledge_class" not in a
    access = e["acquisition_trace"]["records"][0]
    assert access["count"] == count and access["retrieved_at"] is None
    assert access["network_attempts"] == 0 and access["access"] == "supplied_file"
    assert access["snapshot_receipt"]["source_access_observed"] is False
    assert any(
        r["id"] == "url:https://signor.uniroma2.it/" for r in access["bibliography"]
    )
    assert any("publications_not_fetched" in g for g in access["bibliography_gaps"])
    out[0]["asserted_value"].clear()
    out[0]["source_metadata"]["native_columns"].clear()
    assert e == before


def test_hstim_regulator_roles_and_chemical_modification_are_not_generic_binding():
    e = get_relations("P60174", client=FixtureSignorClient())
    out = map_relations(e)
    first = out[0]
    assert first["asserted_value"]["SIGNOR_ID"] == "SIGNOR-280136"
    assert first["asserted_value"]["IDA"] == "P12931"
    assert first["source_metadata"]["query_participant_sides"] == ["B"]
    assert first["asserted_value"]["EFFECT"] == "up-regulates quantity by stabilization"
    assert first["asserted_value"]["DIRECT"] == "t"
    assert (
        first["asserted_value"]["RESIDUE"] == first["asserted_value"]["SEQUENCE"] == ""
    )
    assert out[1]["asserted_value"]["IDB"] == "CHEBI:59776"
    assert out[1]["asserted_value"]["MECHANISM"] == "chemical modification"
    assert out[1]["source_metadata"]["query_participant_sides"] == ["A"]
    assert (
        "no_binding_or_experimental_class"
        in first["source_metadata"]["mapping_scope"]["causality"]
    )


def test_native_taxonomy_complexes_sites_and_score_literals_survive_without_reassignment():
    e = get_relations("P31749", client=FixtureSignorClient())
    out = map_relations(e)
    assert e["query"]["requested_organism"] == 9606
    assert {a["asserted_value"]["TAX_ID"] for a in out} == {
        "9606",
        "10090",
        "10116",
        "9534",
        "-1",
        "",
    }
    assert any(a["asserted_value"]["PMID"] == "Other" for a in out)
    assert any(a["asserted_value"]["TYPEB"] == "proteinfamily" for a in out)
    assert any(a["asserted_value"]["TYPEA"] == "complex" for a in out)
    assert any(a["asserted_value"]["DIRECT"] == "f" for a in out)
    assert (
        sum(a["source_metadata"]["query_participant_sides"] == ["A", "B"] for a in out)
        == 2
    )
    assert out[0]["asserted_value"]["RESIDUE"] == "Ser118"
    assert out[0]["asserted_value"]["SEQUENCE"] == "LHPPPQLsPFLQPHG"
    assert out[0]["asserted_value"]["SCORE"] == "0.777"
    assert (
        "no_current_sequence_axis"
        in out[0]["source_metadata"]["mapping_scope"]["coordinates"]
    )
    assert e["acquisition_trace"]["records"][0]["native_taxonomy_literals"] == [
        "",
        "-1",
        "10090",
        "10116",
        "9534",
        "9606",
    ]


def test_equal_native_rows_are_independent_and_response_changes_pin_support():
    text = native()
    first = map_relations(get_relations("P60174", client=Client(text)))
    extra = text.splitlines(keepends=True)[0]
    out = map_relations(get_relations("P60174", client=Client(text + extra)))
    assert len(out) == len({a["id"] for a in out}) == 4
    assert (
        out[0]["asserted_value"]
        == out[-1]["asserted_value"]
        == first[0]["asserted_value"]
    )
    assert out[0]["id"] != first[0]["id"]


def test_native_no_result_marker_is_a_query_declaration_not_gene_or_biological_absence():
    e = get_relations("P31749", taxon_id=10090, client=FixtureSignorClient())
    assert e["record"] == NO_RESULTS and map_relations(e) == []
    r = e["acquisition_trace"]["records"][0]
    assert r["outcome"] == "empty" and r["count"] == 0
    assert r["native_result_declaration"] == NO_RESULTS
    assert r["source_version"]["value"] is None


def test_literal_quotes_unknown_notes_and_documented_28_column_shape_are_not_repaired():
    values = native().splitlines()[0].split("\t")[:28]
    values[9] = "new mechanism"
    values[10] = "Ser9999|unknown"
    values[22] = ""
    values[25] = '"Quoted sentence"'
    values[27] = ""
    text = "\t".join(values) + "\n"
    (a,) = map_relations(get_relations("P60174", client=Client(text)))
    assert a["asserted_value"]["SENTENCE"] == '"Quoted sentence"'
    assert a["asserted_value"]["RESIDUE"] == "Ser9999|unknown"
    assert a["asserted_value"]["DIRECT"] == a["asserted_value"]["SCORE"] == ""
    assert a["source_metadata"]["native_columns"] == values


@pytest.mark.parametrize(
    "identifier",
    [
        "TPI1",
        "P60174-2",
        "../P60174",
        "P60174?organism=10090",
        "P60174,P31749",
        "SIGNOR-280136",
        "",
        None,
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_unsafe_or_unsupported_queries_fail_even_without_digestion(identifier, skip):
    with pytest.raises((ArgumentError, ConnectorError)):
        get_relations(identifier, client=Client(""), skip_digestion=skip)


@pytest.mark.parametrize("taxon", [None, True, 9606.0, "9606", -1, 0, 9534])
@pytest.mark.parametrize("skip", [False, True])
def test_unsupported_organism_requests_fail_even_without_digestion(taxon, skip):
    with pytest.raises((ArgumentError, ConnectorError)):
        get_relations("P60174", taxon_id=taxon, client=Client(""), skip_digestion=skip)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda v: v.__setitem__(6, "P31749"),
        lambda v: v.__setitem__(7, "PUBCHEM"),
        lambda v: v.__setitem__(5, "proteinfamily"),
        lambda v: v.__setitem__(26, "280136"),
        lambda v: v.__setitem__(22, "true"),
        lambda v: v.__setitem__(12, "human"),
        lambda v: v.__setitem__(0, ""),
        lambda v: v.__setitem__(28, "unexpected"),
        lambda v: v.pop(),
        lambda v: v.append(""),
    ],
)
def test_malformed_last_row_and_nonmatching_namespace_fail_before_partial_mapping(
    mutate,
):
    lines = native().splitlines()
    values = lines[0].split("\t")
    mutate(values)
    # Removing the optional trailer is qualified; removing another field is not.
    if len(values) == 28:
        values.pop()
    text = native() + "\t".join(values) + "\n"
    with pytest.raises(ConnectorError):
        get_relations("P60174", client=Client(text))
    e = {
        "source": "SIGNOR",
        "kind": "causal_relations",
        "query": metadata()["query"],
        "version": None,
        "truncated": False,
        "record": text,
    }
    with pytest.raises(ConnectorError):
        map_relations(e)


@pytest.mark.parametrize(
    "text",
    [
        None,
        {},
        [],
        "<html>failure</html>",
        " ",
        "\n",
        "No result found.\n",
        "\t".join(COLUMNS),
    ],
)
def test_wrappers_html_header_and_unqualified_empty_documents_are_not_native_rows(text):
    with pytest.raises(ConnectorError):
        get_relations("P60174", client=Client(text))


@pytest.mark.parametrize(
    "context", [{"version": "4.0"}, {"truncated": True}, {"truncated": None}]
)
def test_client_cuts_or_website_release_as_record_revision_refused(context):
    with pytest.raises(ConnectorError):
        get_relations("P60174", client=Client(native(), **context))


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(source="IntAct"),
        lambda e: e.update(kind="network"),
        lambda e: e.update(version="4.0"),
        lambda e: e.update(truncated=True),
        lambda e: e["query"].update(accession="P31749"),
        lambda e: e["query"].update(requested_organism=9534),
        lambda e: e["query"].update(extra=True),
    ],
)
def test_mapper_requires_qualified_source_query_and_scope(change):
    e = get_relations("P60174", client=Client(native()))
    change(e)
    with pytest.raises(ConnectorError):
        map_relations(e)


def test_bound_native_gzip_snapshot_checks_original_bytes_and_copies_declarations(
    tmp_path,
):
    raw = gzip.compress(native().encode())
    path = tmp_path / "native.tsv.gz"
    path.write_bytes(raw)
    declared = metadata()
    client = SnapshotSignorClient(
        path, source_metadata=declared, expected_sha256=hashlib.sha256(raw).hexdigest()
    )
    declared["query"]["accession"] = "P31749"
    e = get_relations("P60174", client=client)
    receipt = e["snapshot_receipt"]
    assert e["record"] == native() and e["retrieved_at"] == metadata()["retrieved_at"]
    assert receipt["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert (
        receipt["compression"] == "gzip" and receipt["source_access_observed"] is False
    )
    assert receipt["digest_verification"] == "matched_caller_digest"
    assert e["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert all(
        a["source_metadata"]["snapshot_receipt"] == receipt for a in map_relations(e)
    )
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_relations(
            "P60174",
            client=SnapshotSignorClient(
                path, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "change",
    [
        lambda m: m.update(source="IntAct"),
        lambda m: m.update(kind="network"),
        lambda m: m.update(version="4.0"),
        lambda m: m["query"].update(accession="P31749"),
        lambda m: m["query"].update(requested_organism=10090),
        lambda m: m["query"].update(extra=True),
    ],
)
def test_supplied_declarations_must_match_source_and_exact_request(change):
    m = metadata()
    change(m)
    with pytest.raises(ConnectorError):
        get_relations(
            "P60174",
            client=SnapshotSignorClient(
                DIRECTORY / "relations__P60174__9606.tsv", source_metadata=m
            ),
        )


def test_bad_gzip_or_utf8_remain_access_failures(tmp_path):
    for name, raw in [("bad.tsv.gz", b"notgzip"), ("bad.tsv", b"\xff")]:
        p = tmp_path / name
        p.write_bytes(raw)
        with pytest.raises(ConnectorError):
            get_relations(
                "P60174", client=SnapshotSignorClient(p, source_metadata=metadata())
            )


def test_missing_native_file_remains_unavailable(tmp_path):
    with pytest.raises(ConnectorError) as exc:
        get_relations("P60174", client=FixtureSignorClient(tmp_path))
    assert exc.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


@pytest.mark.parametrize("code", [404, 500])
def test_http_failure_is_not_the_native_no_result_declaration(monkeypatch, code):
    import sabueso.tools.db.signor as m

    def fail(url, **kw):
        raise HTTPError(url, code, "failure", None, None)

    monkeypatch.setattr(m, "urlopen", fail)
    with pytest.raises(ConnectorError) as exc:
        get_relations("P60174")
    assert exc.value.acquisition_trace["records"][0]["outcome"] == "failed"


def test_one_get_archive_replay_keeps_first_row_original_time_and_no_publication_lookup(
    monkeypatch, tmp_path
):
    from sabueso.tools.db import _http as http

    calls = []

    class Answer(io.BytesIO):
        status = 200
        headers = Message()
        headers["Content-Type"] = "text/tab-separated-values"

    def wire(request, timeout):
        calls.append(request.full_url)
        return Answer(native().encode())

    monkeypatch.setattr(http, "_urlopen", wire)
    a = RetrievalArchive(tmp_path / "signor.db")
    with a.recording():
        first = get_relations("P60174")

    def forbidden(*args, **kw):
        pytest.fail("Mapping/replay queried linked publications or sequences")

    monkeypatch.setattr(http, "_urlopen", forbidden)
    with a.replaying():
        second = get_relations("P60174")
    assert calls == ["https://signor.uniroma2.it/getData.php?id=P60174&organism=9606"]
    assert first["record"] == second["record"] == native()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert map_relations(first) == map_relations(second)
    r, s = [e["acquisition_trace"]["records"][0] for e in (first, second)]
    assert r["network_attempts"] == r["received_responses"] == 1
    assert s["network_attempts"] == 0 and s["access"] == "replay"
    assert r["response_identity"] == s["response_identity"]


def test_data_terms_are_signor_cc_by_without_borrowing_linked_article_rights():
    t = source_terms()["SIGNOR"]
    assert (
        t["licence"] == "CC-BY-4.0"
        and t["statement"] == "https://signor.uniroma2.it/documentation/"
    )
    assert verdict("SIGNOR", "redistribution")["obligations"] == ["attribution"]
