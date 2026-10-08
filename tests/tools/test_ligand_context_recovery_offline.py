"""AlphaFill model context and LIGYSIS site declarations keep their native scope."""

import copy
import hashlib
import io
import json
import re
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest
import pyunitwizard as puw

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import retention, verdict
from sabueso.mappings.alphafill import map_model, map_transplants
from sabueso.mappings.ligysis import map_sites, parse_result
from sabueso.tools.db.alphafill import FixtureAlphaFillClient, get_metadata
from sabueso.tools.db.ligysis import FixtureLigysisClient, get_result_page

ALPHAFILL = Path("temp_data/alphafill/metadata__P60174.json")
LIGYSIS = Path("temp_data/ligysis/result__P60174__1.html")


def fill_native():
    return json.loads(ALPHAFILL.read_bytes())


def page_native():
    return LIGYSIS.read_text(encoding="utf-8")


def replace_literal(document, variable, value):
    replacement = f"const {variable} = {json.dumps(value)};"
    return re.sub(
        rf"(?m)^\s*(?:const|let)\s+{variable}\s*=.*$",
        lambda match: replacement,
        document,
    )


class FillClient:
    def __init__(self, payload):
        self.payload = payload

    def metadata(self, identifier):
        return {"record": self.payload, "retrieved_at": "2026-01-01", "version": None}


class PageClient:
    def __init__(self, document):
        self.document = document

    def result_page(self, identifier, segment):
        return {"record": self.document, "retrieved_at": "2026-01-02", "version": None}


def test_alphafill_native_alternatives_keep_model_subject_units_and_zero_alignment():
    envelope = get_metadata("p60174", client=FixtureAlphaFillClient())
    before = copy.deepcopy(envelope)
    with puw.context(standard_units=["nanometer", "ps", "K", "mole", "dalton"]):
        models, transplants = map_model(envelope), map_transplants(envelope)
    assert len(models) == 1 and len(transplants) == 86
    assert envelope == before and envelope["version"] is None
    assert models[0]["subject_ref"] == "uniprot:P60174"
    assert models[0]["asserted_value"]["model_id"] == "AF-P60174-F1"
    assert models[0]["asserted_value"]["run_version"] == "2.1.1"
    assert models[0]["asserted_value"]["run_date"] == "2023-12-22"
    assert "url" not in models[0]["asserted_value"]
    assert len({a["id"] for a in transplants}) == 86
    first = transplants[0]["asserted_value"]
    assert first["alignment"] == {
        "af_start": 0,
        "pdb_start": 5,
        "length": 249,
        "identity": 1,
    }
    assert first["global_rmsd"] == {"value": 0.923648, "unit": "angstrom"}
    assert first["local_rmsd"] == {"value": 0.178902, "unit": "angstrom"}
    assert first["transplant_clash_score"] == {"value": 0.101073, "unit": "angstrom"}
    assert first["donor_numbering"]["pdb_auth_seq_id"] == "301"
    assert first["donor_numbering"]["pdb_auth_ins_code"] is None
    assert any(
        a["asserted_value"]["transplant_clash_score"]["value"] == 0 for a in transplants
    )
    assert (
        sum(
            "validation" in a["source_metadata"]["native_transplant"]
            for a in transplants
        )
        == 3
    )
    for assertion in models + transplants:
        assert assertion["source"]["version"] is None
        assert assertion["retrieved_at"] is None
        assert (
            "no_UniProt_residue_projection"
            in assertion["source_metadata"]["mapping_scope"]["coordinates"]
        )
    for assertion in transplants:
        assert assertion["subject_ref"] == "alphafill:AF-P60174-F1"
        assert "location" not in assertion["asserted_value"]
        assert (
            "not_observed_target_binding"
            in assertion["source_metadata"]["mapping_scope"]["interpretation"]
        )
    access = envelope["acquisition_trace"]["records"][0]
    assert access["access"] == "supplied_file" and access["network_attempts"] == 0
    assert access["hit_count"] == 55 and access["transplant_count"] == 86
    assert access["source_version"]["value"] is None
    assert (
        envelope["snapshot_receipt"]["document_sha256"]
        == hashlib.sha256(ALPHAFILL.read_bytes()).hexdigest()
    )
    transplants[0]["source_metadata"]["native_transplant"].clear()
    transplants[0]["source_metadata"]["snapshot_receipt"].clear()
    assert envelope == before


def test_native_fragment_compound_labels_nulls_and_optional_context_are_not_repaired():
    payload = fill_native()
    payload["id"] = "AF-P60174-F2"
    transplant = payload["hits"][0]["transplants"][0]
    transplant.update(
        compound_id="TEST_NATIVE", analogue_id="TEST_ANALOGUE", local_rmsd=None
    )
    transplant.pop("pae")
    transplant.update(
        pdb_auth_seq_id="-3", pdb_auth_ins_code="A", future_field={"kept": True}
    )
    clash = transplant["clash"]
    clash["ligand_atom_count"] = clash.pop("transplant_atom_count")
    envelope = get_metadata("P60174", client=FillClient(payload))
    assertion = map_transplants(envelope)[0]
    value = assertion["asserted_value"]
    assert value["model_ref"] == "alphafill:AF-P60174-F2"
    assert (
        value["compound_id"] == "TEST_NATIVE"
        and value["analogue_id"] == "TEST_ANALOGUE"
    )
    assert value["local_rmsd"] is None
    assert value["donor_numbering"]["pdb_auth_seq_id"] == "-3"
    assert value["donor_numbering"]["pdb_auth_ins_code"] == "A"
    assert assertion["source_metadata"]["native_transplant"] == transplant
    assert "pae" not in assertion["source_metadata"]["native_transplant"]
    assert "source" not in assertion["source_metadata"]["native_run"]
    assert envelope["acquisition_trace"]["records"] == []


@pytest.mark.parametrize("hits", [None, []])
def test_known_native_model_without_transplants_still_has_model_context(hits):
    payload = fill_native()
    payload["hits"] = hits
    envelope = get_metadata("P60174", client=FillClient(payload))
    assert len(map_model(envelope)) == 1 and map_transplants(envelope) == []
    assert envelope["record"]["hits"] == hits
    assert map_model(envelope)[0]["asserted_value"]["native_hits_state"] == (
        "null" if hits is None else "array"
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.clear(),
        lambda p: p.update(id="AF-P37840-F1"),
        lambda p: p.update(source="BFVD"),
        lambda p: p.update(date="20231222"),
        lambda p: p.update(date="2023-02-30"),
        lambda p: p.pop("hits"),
        lambda p: p.update(hits={}),
        lambda p: p.update(extra=float("nan")),
        lambda p: p["hits"][0].update(global_rmsd=-1),
        lambda p: p["hits"][0].update(global_rmsd=True),
        lambda p: p["hits"][0].update(pdb_id="../../bad"),
        lambda p: p["hits"][0]["alignment"].update(af_start=-1),
        lambda p: p["hits"][0]["alignment"].update(length=0),
        lambda p: p["hits"][0]["alignment"].update(identity=100),
        lambda p: p["hits"][0]["alignment"].update(identity=True),
        lambda p: p["hits"][0]["transplants"].append(
            copy.deepcopy(p["hits"][0]["transplants"][0])
        ),
        lambda p: p["hits"][0]["transplants"][0].update(pdb_auth_seq_id=301),
        lambda p: p["hits"][0]["transplants"][0].pop("pdb_auth_ins_code"),
        lambda p: p["hits"][0]["transplants"][0].pop("local_rmsd"),
        lambda p: p["hits"][0]["transplants"][0].update(local_rmsd=-1),
        lambda p: p["hits"][0]["transplants"][0]["clash"].update(score=-1),
        lambda p: p["hits"][0]["transplants"][0]["clash"].update(clash_count=True),
        lambda p: p["hits"][0]["transplants"][0]["clash"].pop("transplant_atom_count"),
        lambda p: p["hits"][0]["transplants"][0].update(
            validation={"transplant_rmsd": -1}
        ),
    ],
)
def test_invalid_alphafill_identity_numbering_or_metrics_are_refused(change):
    payload = fill_native()
    change(payload)
    with pytest.raises(ConnectorError):
        get_metadata("P60174", client=FillClient(payload))


def test_ligysis_complete_site_table_retains_original_page_and_provider_numbering():
    envelope = get_result_page("p60174", 1, client=FixtureLigysisClient())
    before = copy.deepcopy(envelope)
    with puw.context(standard_units=["nanometer", "ps", "K", "mole", "dalton"]):
        assertions = map_sites(envelope)
    assert envelope == before and len(assertions) == 2
    assert envelope["record"] == page_native()
    assert [a["asserted_value"]["site_id"] for a in assertions] == [0, 1]
    assert [a["asserted_value"]["site_size"] for a in assertions] == [20, 7]
    value = assertions[0]["asserted_value"]
    assert value["relative_solvent_accessibility"] == {"value": 21.1, "unit": "percent"}
    assert value["source_scores"] == {"DS": 2.0, "MES": 0.71, "FS": 0.52}
    assert value["source_cluster"] == 1
    assert value["numbering_context"] == {
        "provider_reference": "UniProt",
        "sequence_revision": None,
        "segment_bounds": {"end": 249, "start": 1},
    }
    assert (
        len(
            {
                n
                for a in assertions
                for n in a["asserted_value"]["source_residue_numbers"]
            }
        )
        == 27
    )
    for assertion in assertions:
        assert assertion["subject_ref"] == "uniprot:P60174"
        assert (
            assertion["source"]["version"] is None and assertion["retrieved_at"] is None
        )
        assert (
            "location" not in assertion["asserted_value"]
            and "ligands" not in assertion["asserted_value"]
        )
        assert assertion["source_metadata"]["native_segment_stats"] == {
            "bss": 2,
            "ligs": 9,
            "strucs": 8,
        }
        assert (
            assertion["source_metadata"]["response_sha256"]
            == hashlib.sha256(LIGYSIS.read_bytes()).hexdigest()
        )
    access = envelope["acquisition_trace"]["records"][0]
    assert access["access"] == "supplied_file" and access["network_attempts"] == 0
    assert access["segment"] == 1 and access["count"] == 2
    assert envelope["snapshot_receipt"]["file_format"] == "html"
    assert envelope["snapshot_receipt"]["source_access_observed"] is False
    assertions[0]["asserted_value"]["source_residue_numbers"].clear()
    assertions[0]["source_metadata"]["native_site_row"].clear()
    assert envelope == before


def test_ligysis_native_nan_zero_unknown_columns_and_explicit_empty_are_distinct():
    document = page_native()
    literals = parse_result(document, "P60174", 1)
    table = literals["chartData"]
    table.update(RSA=["NaN", 0], DS=["NaN", 0], future_column=["native", None])
    document = replace_literal(document, "chartData", table)
    assertions = map_sites(get_result_page("P60174", 1, client=PageClient(document)))
    assert assertions[0]["asserted_value"]["relative_solvent_accessibility"] is None
    assert assertions[0]["asserted_value"]["source_scores"]["DS"] == "NaN"
    assert assertions[0]["source_metadata"]["native_site_row"]["RSA"] == "NaN"
    assert assertions[1]["asserted_value"]["relative_solvent_accessibility"] == {
        "value": 0,
        "unit": "percent",
    }
    assert (
        assertions[0]["source_metadata"]["native_site_row"]["future_column"] == "native"
    )
    document = replace_literal(document, "chartData", {k: [] for k in table})
    document = replace_literal(document, "seg_ress_dict", {"ALL_BINDING": []})
    document = replace_literal(
        document, "segStats", {"P60174": {"1": {"bss": 0, "ligs": 0, "strucs": 0}}}
    )
    assert map_sites(get_result_page("P60174", 1, client=PageClient(document))) == []


@pytest.mark.parametrize(
    "variable,value",
    [
        ("proteinId", "P37840"),
        ("segmentId", "2"),
        ("segmentId", 1),
        ("segmentReps", {}),
        ("segmentReps", {"1": {"start": True, "end": 249}}),
        ("segStats", {"P60174": {"1": {"bss": 1, "ligs": 9, "strucs": 8}}}),
        ("segStats", {"P60174": {"1": {"bss": True, "ligs": 9, "strucs": 8}}}),
        ("seg_ress_dict", {"0": [12], "1": [222], "ALL_BINDING": [12, 222]}),
        ("chartData", {}),
    ],
)
def test_ligysis_wrong_identity_or_table_scope_is_refused(variable, value):
    document = replace_literal(page_native(), variable, value)
    with pytest.raises(ConnectorError):
        get_result_page("P60174", 1, client=PageClient(document))


@pytest.mark.parametrize(
    "key,value",
    [
        ("ID", [0, 0]),
        ("RSA", [101, 0]),
        ("FS", [1.1, 0]),
        ("MES", [-1, 0]),
        ("DS", [True, 0]),
        ("Cluster", [0, 1]),
        ("Size", [19, 7]),
    ],
)
def test_ligysis_invalid_provider_scores_and_site_counts_are_refused(key, value):
    literals = parse_result(page_native(), "P60174", 1)
    literals["chartData"][key] = value
    document = replace_literal(page_native(), "chartData", literals["chartData"])
    with pytest.raises(ConnectorError):
        get_result_page("P60174", 1, client=PageClient(document))


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r["0"].__setitem__(0, 250),
        lambda r: r["0"].__setitem__(0, True),
        lambda r: r["0"].__setitem__(0, r["0"][1]),
        lambda r: r["ALL_BINDING"].pop(),
        lambda r: r.update(unbound=[12]),
    ],
)
def test_ligysis_invalid_membership_never_becomes_a_residue_projection(change):
    literals = parse_result(page_native(), "P60174", 1)
    change(literals["seg_ress_dict"])
    document = replace_literal(
        page_native(), "seg_ress_dict", literals["seg_ress_dict"]
    )
    with pytest.raises(ConnectorError):
        get_result_page("P60174", 1, client=PageClient(document))


@pytest.mark.parametrize(
    "declaration",
    [
        "const proteinId = computeProtein();",
        'const proteinId = "P60174";\nconst proteinId = "P60174";',
        'const chartData = {"ID": [], "ID": []};',
        'const chartData = {"ID": [NaN]};',
        'var proteinId = "P60174";',
    ],
)
def test_changed_layout_expressions_duplicate_keys_and_nonfinite_json_fail_closed(
    declaration,
):
    variable = "chartData" if "chartData" in declaration else "proteinId"
    document = re.sub(
        rf"(?m)^\s*(?:const|let)\s+{variable}\s*=.*$",
        lambda match: declaration,
        page_native(),
    )
    with pytest.raises(ConnectorError):
        get_result_page("P60174", 1, client=PageClient(document))


@pytest.mark.parametrize(
    "identifier", ["P60174-1", "TPIS_HUMAN", "../P60174", "P60174?x", 123]
)
def test_invalid_identifiers_never_reach_either_source(identifier):
    class Forbidden:
        def metadata(self, identifier):
            pytest.fail("Invalid accession reached AlphaFill.")

        def result_page(self, identifier, segment):
            pytest.fail("Invalid accession reached LIGYSIS.")

    for call, args in (
        (get_metadata, (identifier,)),
        (get_result_page, (identifier, 1)),
    ):
        with pytest.raises((ArgumentError, ConnectorError)):
            call(*args, client=Forbidden())


@pytest.mark.parametrize("segment", [0, -1, True, "1", None])
def test_invalid_segment_is_refused_even_without_digestion(segment):
    class Forbidden:
        def result_page(self, identifier, segment):
            pytest.fail("Invalid segment reached LIGYSIS.")

    for skip in (False, True):
        with pytest.raises((ArgumentError, ConnectorError)):
            get_result_page("P60174", segment, client=Forbidden(), skip_digestion=skip)


@pytest.mark.parametrize("source", ["alphafill", "ligysis"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("source", "UniProt"),
        ("kind", "unknown"),
        ("version", "v4"),
        ("truncated", True),
    ],
)
def test_mappers_refuse_foreign_revisions_and_incomplete_scope(source, field, value):
    if source == "alphafill":
        envelope = get_metadata("P60174", client=FixtureAlphaFillClient())
        mapper = map_transplants
    else:
        envelope = get_result_page("P60174", 1, client=FixtureLigysisClient())
        mapper = map_sites
    envelope[field] = value
    with pytest.raises(ConnectorError):
        mapper(envelope)


@pytest.mark.parametrize("source", ["alphafill", "ligysis"])
def test_missing_fixture_is_unavailable_not_an_empty_scientific_result(
    source, tmp_path
):
    with pytest.raises(ConnectorError) as error:
        if source == "alphafill":
            get_metadata("P60174", client=FixtureAlphaFillClient(tmp_path))
        else:
            get_result_page("P60174", 1, client=FixtureLigysisClient(tmp_path))
    assert error.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


@pytest.mark.parametrize("source", ["alphafill", "ligysis"])
@pytest.mark.parametrize("status", [404, 500])
def test_http_failure_does_not_assert_absence(source, status, monkeypatch):
    import sabueso.tools.db._http as http

    monkeypatch.setattr(http, "RETRIES", 0)

    def fail(request, timeout):
        raise HTTPError(request.full_url, status, "failure", {}, None)

    monkeypatch.setattr(http, "_urlopen", fail)
    with pytest.raises(ConnectorError) as error:
        get_metadata("P60174") if source == "alphafill" else get_result_page(
            "P60174", 1
        )
    access = error.value.acquisition_trace["records"][0]
    assert access["outcome"] == "failed" and access["network_attempts"] == 1


def test_shared_transport_archives_only_two_gets_and_replays_original_time(
    tmp_path, monkeypatch
):
    import sabueso.tools.db._http as http

    calls = []

    class Response(io.BytesIO):
        status = 200

        def __init__(self, path, content_type):
            super().__init__(path.read_bytes())
            self.headers = Message()
            self.headers["Content-Type"] = content_type

    def wire(request, timeout):
        calls.append((request.get_method(), request.full_url))
        if "alphafill.eu" in request.full_url:
            return Response(ALPHAFILL, "application/json")
        return Response(LIGYSIS, "text/html; charset=utf-8")

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "ligand_context.db")
    with archive.recording():
        original = get_metadata("P60174"), get_result_page("P60174", 1)

    def forbidden(*args, **kwargs):
        pytest.fail("Replay reached the network.")

    monkeypatch.setattr(http, "_urlopen", forbidden)
    with archive.replaying():
        replay = get_metadata("P60174"), get_result_page("P60174", 1)
    assert calls == [
        ("GET", "https://alphafill.eu/v1/aff/P60174/json"),
        ("GET", "https://www.compbio.dundee.ac.uk/ligysis/results/P60174/1"),
    ]
    assert map_model(original[0]) == map_model(replay[0])
    assert map_transplants(original[0]) == map_transplants(replay[0])
    assert map_sites(original[1]) == map_sites(replay[1])
    for first, second in zip(original, replay):
        assert first["retrieved_at"] == second["retrieved_at"]
        a, b = (
            first["acquisition_trace"]["records"][0],
            second["acquisition_trace"]["records"][0],
        )
        assert a["network_attempts"] == 1 and a["received_responses"] == 1
        assert (
            b["access"] == "replay"
            and b["network_attempts"] == 0
            and b["received_responses"] == 1
        )


def test_data_terms_do_not_inherit_software_or_paper_licences():
    assert verdict("AlphaFill", "commercial_product")["verdict"] == "allowed"
    assert retention("AlphaFill")["conditions"] == ["attribution"]
    assert verdict("LIGYSIS", "commercial_product")["verdict"] == "unknown"
    assert retention("LIGYSIS")["share"] == "unknown"
    assert retention("LIGYSIS")["reason"] == "licence_not_stated"
