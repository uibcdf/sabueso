"""HPA native categorical scope, complete raw context, identity and licensed replay."""

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
from sabueso.core.terms import retention, source_terms
from sabueso.mappings.hpa import CATEGORIES, map_gene_summary
from sabueso.tools.db.hpa import (
    FixtureHpaClient,
    SnapshotHpaClient,
    get_gene_profile,
)

GENE = "ENSG00000111669"
PATH = Path("temp_data/hpa/profile__ENSG00000111669.json")
SOURCE = "Human Protein Atlas"


def native():
    return json.loads(PATH.read_bytes())


class Client:
    def __init__(self, payload, **context):
        self.payload = payload
        self.context = context

    def gene_profile(self, identifier):
        return {
            "record": self.payload,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def metadata():
    return {
        "source": SOURCE,
        "kind": "gene_profile",
        "query": {"gene_id": GENE, "format": "single_gene_json_subset"},
        "retrieved_at": "2026-10-06T12:00:00+00:00",
    }


def test_native_rna_and_protein_categories_retain_context_without_unit_projection():
    envelope = get_gene_profile(GENE, client=FixtureHpaClient())
    before = copy.deepcopy(envelope)
    assertions = map_gene_summary(envelope)
    assert envelope["record"] == native()
    assert len(assertions) == len({a["id"] for a in assertions}) == 22
    assert {a["asserted_value"]["native_field"] for a in assertions} == set(CATEGORIES)
    categories = {
        a["asserted_value"]["native_field"]: a["asserted_value"]["native_value"]
        for a in assertions
    }
    assert categories["RNA tissue specificity"] == "Tissue enhanced"
    assert categories["Protein cell type specificity"] == "Cell type enhanced"
    assert (
        categories["RNA single nuclei brain specificity"] == "Low cell type specificity"
    )
    for a in assertions:
        assert a["subject_ref"] == f"hpa:{GENE}"
        assert a["source"]["version"] is None
        assert a["source_metadata"]["native_uniprot_references"] == ["P60174"]
        assert "knowledge_class" not in a
        assert set(a["asserted_value"]) == {"native_field", "native_value"}
        assert a["source_metadata"]["mapping_scope"]["quantities"].startswith(
            "not_projected"
        )
    assert envelope["record"]["RNA tissue specific nTPM"]["skeletal muscle"] == "2315.7"
    assert (
        envelope["record"]["Protein tissue specific Intensity"]["skeletal muscle"]
        == "5032737874.0"
    )
    assert (
        envelope["record"]["Blood concentration - Conc. blood MS [pg/L]"] == "83000000"
    )
    assert "RNA mouse brain regional specificity" not in categories
    assert envelope == before
    assertions[0]["source_metadata"]["native_uniprot_references"].clear()
    assert envelope == before
    access = envelope["acquisition_trace"]["records"][0]
    assert access["count"] == 1 and access["categorical_field_count"] == 22
    assert access["network_attempts"] == 0 and access["retrieved_at"] is None
    assert access["snapshot_receipt"]["source_access_observed"] is False


def test_stated_null_missing_category_and_quantitative_only_context_are_distinct():
    payload = native()
    payload["RNA tissue specificity"] = None
    del payload["Protein tissue distribution"]
    assertions = map_gene_summary(get_gene_profile(GENE, client=Client(payload)))
    categories = {
        a["asserted_value"]["native_field"]: a["asserted_value"]["native_value"]
        for a in assertions
    }
    assert (
        "RNA tissue specificity" in categories
        and categories["RNA tissue specificity"] is None
    )
    assert "Protein tissue distribution" not in categories
    assert len(assertions) == 21


@pytest.mark.parametrize(
    "identifier",
    [
        "TPI1",
        "P60174",
        GENE + ".1",
        GENE.lower(),
        "ENSMUSG00000023456",
        GENE + "/x",
        GENE + ",ENSG00000000001",
    ],
)
@pytest.mark.parametrize("skip", [False, True])
def test_exact_gene_identity_is_required_even_without_digestion(identifier, skip):
    with pytest.raises((ArgumentError, ConnectorError)):
        get_gene_profile(identifier, client=Client(native()), skip_digestion=skip)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        [native()],
        {**native(), "Ensembl": "ENSG00000000001"},
        {**native(), "Gene": None},
        {**native(), "Uniprot": "P60174"},
        {**native(), "Uniprot": [None]},
        {**native(), "RNA tissue specificity": 1},
        {**native(), "RNA tissue specificity": ""},
        {**native(), "extra": float("nan")},
    ],
)
def test_malformed_object_is_not_accepted_or_reported_as_no_expression(payload):
    with pytest.raises(ConnectorError):
        get_gene_profile(GENE, client=Client(payload))


@pytest.mark.parametrize(
    "context", [{"version": "25.1"}, {"truncated": True}, {"truncated": None}]
)
def test_unqualified_revision_or_cut_is_refused(context):
    with pytest.raises(ConnectorError):
        get_gene_profile(GENE, client=Client(native(), **context))


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "tissue_assay"),
        ("query", {"gene_id": GENE, "format": "xml"}),
        ("version", "25.1"),
        ("truncated", True),
    ],
)
def test_mapping_requires_exact_qualified_envelope(key, value):
    envelope = get_gene_profile(GENE, client=FixtureHpaClient())
    envelope[key] = value
    with pytest.raises(ConnectorError):
        map_gene_summary(envelope)


def test_bound_gzip_snapshot_checks_original_hash_without_new_access_credit(tmp_path):
    path = tmp_path / "profile.json.gz"
    path.write_bytes(gzip.compress(PATH.read_bytes()))
    declared = metadata()
    client = SnapshotHpaClient(
        path,
        source_metadata=declared,
        expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    declared["query"]["gene_id"] = "ENSG00000000001"
    envelope = get_gene_profile(GENE, client=client)
    assert envelope["record"] == native()
    assert envelope["retrieved_at"] == "2026-10-06T12:00:00+00:00"
    assert envelope["snapshot_receipt"]["source_access_observed"] is False
    assert (
        envelope["snapshot_receipt"]["document_sha256"]
        == hashlib.sha256(path.read_bytes()).hexdigest()
    )
    assert all(
        a["retrieved_at"] == envelope["retrieved_at"]
        for a in map_gene_summary(envelope)
    )
    with pytest.raises((ConnectorError, ArgumentError)):
        get_gene_profile(
            GENE,
            client=SnapshotHpaClient(
                path, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "assays"),
        ("query", {"gene_id": GENE + ".1", "format": "single_gene_json_subset"}),
        ("version", "25.1"),
    ],
)
def test_supplied_snapshot_binding_is_checked(tmp_path, key, value):
    path = tmp_path / "profile.json"
    path.write_bytes(PATH.read_bytes())
    declared = metadata()
    declared[key] = value
    with pytest.raises(ConnectorError):
        get_gene_profile(GENE, client=SnapshotHpaClient(path, source_metadata=declared))


def test_missing_fixture_is_unavailable_not_a_source_negative(tmp_path):
    with pytest.raises(ConnectorError):
        get_gene_profile(GENE, client=FixtureHpaClient(tmp_path))


@pytest.mark.parametrize("code", [404, 410, 429, 503])
def test_http_error_is_failed_access(monkeypatch, code):
    from sabueso.tools.db import hpa

    def fail(*args, **kwargs):
        raise HTTPError("https://www.proteinatlas.org/", code, "failure", {}, None)

    monkeypatch.setattr(hpa, "urlopen", fail)
    with pytest.raises(ConnectorError):
        get_gene_profile(GENE)


def test_one_get_archive_replay_keeps_original_scope_time_and_terms(
    monkeypatch, tmp_path
):
    from sabueso.tools.db import _http as http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(PATH.read_bytes())
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = "application/json"
        return response

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "hpa.db")
    with archive.recording():
        envelope = get_gene_profile(GENE)

    def forbidden(*args, **kwargs):
        raise AssertionError("Archive replay must not contact HPA or linked datasets.")

    monkeypatch.setattr(http, "_urlopen", forbidden)
    with archive.replaying():
        replay = get_gene_profile(GENE)
    assert calls == [f"https://www.proteinatlas.org/{GENE}.json"]
    assert replay["record"] == envelope["record"]
    assert replay["retrieved_at"] == envelope["retrieved_at"]
    assert map_gene_summary(replay) == map_gene_summary(envelope)
    terms = source_terms()[SOURCE]
    assert terms["licence"] == "CC-BY-4.0"
    assert terms["statement"] == "https://www.proteinatlas.org/about/licence"
    assert retention(SOURCE)["keep"] == "yes"
    assert "third-party" in " ".join(terms["caveats"]).lower()
