"""Supplied originals retain native claims and fail foreign bindings before I/O."""

import copy
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from sabueso.core.errors import ConnectorError
from sabueso.mappings import alphafill, glygen, ligysis, sifts
from sabueso.tools.db import alphafill as af_client
from sabueso.tools.db import glygen as gly_client
from sabueso.tools.db import ligysis as lig_client
from sabueso.tools.db import sifts as sifts_client

CASES = [
    (
        "AlphaFill",
        "metadata",
        {"accession": "P60174"},
        "alphafill/metadata__P60174.json",
        af_client.SnapshotAlphaFillClient,
        af_client.FixtureAlphaFillClient,
        af_client.get_metadata,
        ("p60174",),
        (alphafill.map_model, alphafill.map_transplants),
        (1, 86),
    ),
    (
        "GlyGen",
        "protein",
        {"accession": "P60174"},
        "glygen/protein__P60174.json",
        gly_client.SnapshotGlyGenClient,
        gly_client.FixtureGlyGenClient,
        gly_client.get_protein,
        ("p60174",),
        (glygen.map_glycosylation, glygen.map_phosphorylation),
        (3, 13),
    ),
    (
        "SIFTS",
        "mappings",
        {"pdb_id": "1hti"},
        "sifts/mappings__1hti.json",
        sifts_client.SnapshotSIFTSClient,
        sifts_client.FixtureSIFTSClient,
        sifts_client.get_mappings,
        ("1HTI",),
        (sifts.map_sequence_mappings,),
        (2,),
    ),
    (
        "LIGYSIS",
        "result_page",
        {"accession": "P60174", "segment": 1},
        "ligysis/result__P60174__1.html",
        lig_client.SnapshotLigysisClient,
        lig_client.FixtureLigysisClient,
        lig_client.get_result_page,
        ("p60174", 1),
        (
            ligysis.map_sites,
            ligysis.map_displayed_residues,
            ligysis.map_residue_correspondences,
        ),
        (2, 20, 4),
    ),
    (
        "LIGYSIS",
        "structure_mapping",
        {"accession": "P60174", "segment": 1, "pdb_id": "7t0q"},
        "ligysis/mapping__P60174__1__7t0q.json",
        lig_client.SnapshotLigysisClient,
        lig_client.FixtureLigysisClient,
        lig_client.get_structure_mapping,
        ("p60174", 1, "7T0Q"),
        (ligysis.map_structure_mapping,),
        (14,),
    ),
]

# The two native sources with reviewed repository fixtures qualify in public CI.
# Local-only original responses remain explicit optional qualification inputs.
NATIVE_CASES = [
    pytest.param(case, marks=pytest.mark.local_source_inputs)
    if case[0] in {"SIFTS", "LIGYSIS"}
    else case
    for case in CASES
]


def declaration(case):
    return {
        "source": case[0],
        "kind": case[1],
        "query": copy.deepcopy(case[2]),
        "retrieved_at": None,
        "version": None,
        "terms": {"license": "caller statement, not a permission grant"},
    }


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    from sabueso.tools.db import _http

    def forbidden(*args, **kwargs):
        raise AssertionError("Supplied-file intake must not request a source")

    monkeypatch.setattr(_http, "_urlopen", forbidden)


@pytest.mark.parametrize("case", NATIVE_CASES, ids=lambda c: c[0] + ":" + c[1])
@pytest.mark.parametrize("compressed", [False, True])
def test_original_claims_match_native_fixture_and_keep_supplied_receipt(
    case, compressed, tmp_path
):
    raw = (Path("temp_data") / case[3]).read_bytes()
    supplied = gzip.compress(raw, mtime=0) if compressed else raw
    path = tmp_path / ("original.gz" if compressed else "original")
    path.write_bytes(supplied)
    sha = hashlib.sha256(supplied).hexdigest()
    metadata = declaration(case)
    client = case[4](path, source_metadata=metadata, expected_sha256=sha.upper())
    metadata["query"].clear()  # Constructor detached its caller declaration.
    actual = case[6](*case[7], client=client)
    expected = case[6](*case[7], client=case[5]())
    assert actual["record"] == expected["record"]
    assert actual["retrieved_at"] is None and actual["version"] is None
    receipt = actual["snapshot_receipt"]
    assert receipt["document_sha256"] == sha
    assert receipt["compression"] == ("gzip" if compressed else None)
    assert receipt["digest_verification"] == "matched_caller_digest"
    assert receipt["source_metadata_basis"] == "caller_declaration"
    assert receipt["source_access_observed"] is False
    assert receipt["declared_terms"] == declaration(case)["terms"]
    assert receipt["read_at"] is not None
    (access,) = actual["acquisition_trace"]["records"]
    assert access["access"] == "supplied_file" and access["network_attempts"] == 0
    assert access["retrieved_at"] is None
    before = copy.deepcopy(actual)
    for mapper, count in zip(case[8], case[9]):
        rows, fixture_rows = mapper(actual), mapper(expected)
        assert len(rows) == len(fixture_rows) == count
        assert [r["asserted_value"] for r in rows] == [
            r["asserted_value"] for r in fixture_rows
        ]
        assert all(r["source_metadata"]["snapshot_receipt"] == receipt for r in rows)
        rows[0]["source_metadata"]["snapshot_receipt"].clear()
    assert actual == before


@pytest.mark.parametrize("case", CASES, ids=lambda c: c[0] + ":" + c[1])
@pytest.mark.parametrize("field", ["source", "kind", "query", "version"])
def test_foreign_binding_is_refused_before_any_file_access(case, field, monkeypatch):
    metadata = declaration(case)
    metadata[field] = {"foreign": True} if field == "query" else "foreign"

    def forbidden(*args, **kwargs):
        raise AssertionError("Binding validation must precede snapshot access")

    monkeypatch.setattr("sabueso.tools.db._snapshot.load_source_snapshot", forbidden)
    client = case[4]("does-not-exist", source_metadata=metadata)
    with pytest.raises(ConnectorError, match="source/kind/query/revision"):
        case[6](*case[7], client=client)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c[0] + ":" + c[1])
def test_bad_hash_precedes_decoding_and_missing_file_stays_unavailable(case, tmp_path):
    path = tmp_path / "original"
    client = case[4](path, source_metadata=declaration(case))
    with pytest.raises(ConnectorError) as missing:
        case[6](*case[7], client=client)
    assert missing.value.acquisition_trace["records"][0]["outcome"] == "unavailable"
    path.write_bytes(b"\xff not native JSON or HTML")
    client = case[4](path, source_metadata=declaration(case), expected_sha256="0" * 64)
    with pytest.raises(ConnectorError, match="SHA-256"):
        case[6](*case[7], client=client)


@pytest.mark.parametrize("case", NATIVE_CASES, ids=lambda c: c[0] + ":" + c[1])
def test_valid_binding_and_hash_do_not_override_native_identity_validation(
    case, tmp_path
):
    raw = (Path("temp_data") / case[3]).read_bytes()
    # Change the native echoed identity; the request declaration is still correct.
    old, new = (b"1hti", b"2hti") if case[0] == "SIFTS" else (b"P60174", b"P37840")
    if case[1] == "structure_mapping":
        old, new = b"7t0q", b"1hti"
    assert old in raw
    raw = raw.replace(old, new)
    path = tmp_path / "original"
    path.write_bytes(raw)
    client = case[4](
        path,
        source_metadata=declaration(case),
        expected_sha256=hashlib.sha256(raw).hexdigest(),
    )
    with pytest.raises(ConnectorError):
        case[6](*case[7], client=client)


@pytest.mark.parametrize(
    "case", [c for c in CASES if c[1] != "result_page"], ids=lambda c: c[0] + ":" + c[1]
)
def test_duplicate_json_keys_are_refused_in_each_native_reader(case, tmp_path):
    path = tmp_path / "original.json"
    path.write_text('{"id": 1, "id": 2}', encoding="utf-8", newline="")
    client = case[4](path, source_metadata=declaration(case))
    with pytest.raises(ConnectorError, match="Repeated JSON key"):
        case[6](*case[7], client=client)


def test_declared_retrieval_time_is_preserved_without_becoming_a_remote_observation():
    case = CASES[0]
    metadata = declaration(case)
    metadata["retrieved_at"] = "2026-01-01T00:00:00Z"
    source = case[6](
        *case[7], client=case[4](Path("temp_data") / case[3], source_metadata=metadata)
    )
    assert source["retrieved_at"] == metadata["retrieved_at"]
    assert source["snapshot_receipt"]["read_at"] != source["retrieved_at"]
    assert source["snapshot_receipt"]["source_access_observed"] is False
    assert source["snapshot_receipt"]["digest_verification"] == "not_requested"
    assert json.dumps(source, allow_nan=False)
