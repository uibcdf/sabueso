"""MetalPDB native identities, parent occurrences, units and acquisition scope."""

import copy
import gzip
import hashlib
import io
import json
from email.message import Message
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError

import pytest
import pyunitwizard as puw

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import source_terms
from sabueso.mappings.metalpdb import URL, map_sites, response_query
from sabueso.tools.db.metalpdb import (
    FixtureMetalPDBClient,
    SnapshotMetalPDBClient,
    get_site,
)

PATH = Path("temp_data/metalpdb/site__12ca_2.json")
TABLE = Path("temp_data/metalpdb/donor_distance_table__12ca_2.html")


def native():
    return json.loads(PATH.read_bytes())


class Client:
    def __init__(self, record, **context):
        self.record, self.context = record, context

    def site(self, identifier):
        return {
            "record": self.record,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def read(record, **context):
    return get_site("12ca_2", client=Client(record, **context))


def metadata():
    return {"source": "MetalPDB", "kind": "site", "query": response_query("12ca_2")}


class Rows(HTMLParser):
    """Read the original provider table only; no script, asset or link execution."""

    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        if tag in ("td", "th"):
            self.cell = []

    def handle_data(self, text):
        if self.cell is not None:
            self.cell.append(text)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join(" ".join(self.cell).split()))
            self.cell = None
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def test_provider_unit_header_and_rounded_donors_match_independent_native_api():
    parser = Rows()
    parser.feed(TABLE.read_text(encoding="utf-8"))
    assert parser.rows[0][6] == "Distance (Å)"
    source_rows = {r[0]: r for r in parser.rows[1:]}
    assert len(source_rows) == 3
    for ligand in native()[0]["metals"][0]["ligands"]:
        row = source_rows[
            f"{ligand['residue']}_{ligand['residue_pdb_number']}({ligand['chain']})"
        ]
        donor = ligand["donors"][0]
        assert row[4] == donor["atom"] and row[5] == donor["symbol"]
        assert row[6] == f"{donor['distance']:.3f}"


def test_native_site_keeps_original_parent_context_false_flag_and_quantity_units():
    e = get_site("12CA_2", client=FixtureMetalPDBClient())
    before = copy.deepcopy(e)
    with puw.context(standard_units=["nanometer", "ps", "K", "mole", "dalton"]):
        a = map_sites(e)[0]
    v = a["asserted_value"]
    assert e["query"] == {"site_id": "12ca_2"} and e["record"] == native()
    assert a["subject_ref"] == "metalpdb:site:12ca_2"
    assert v["uniprot"] == "P00918" and v["site_type"] == "Mononuclear"
    assert v["is_representative"] is False
    metal = v["metals"][0]
    assert metal["coordination"] == 3 and metal["atom_pdb_number"] == 2029
    assert metal["residue_pdb_number"] == 262 and "chain" not in metal
    assert metal["geometry"] == "tetrahedron with a vacancy (regular)"
    assert [ligand["residue_pdb_number"] for ligand in metal["ligands"]] == [
        94,
        119,
        96,
    ]
    distances = [ligand["donors"][0]["distance"] for ligand in metal["ligands"]]
    assert distances == [
        {"value": n, "unit": "angstrom"} for n in (2.4972444, 2.111593, 2.1122792)
    ]
    assert a["source_metadata"]["native_site"] == native()[0]
    assert (
        a["source_metadata"]["distance_unit_basis"]["provider_header"] == "Distance (Å)"
    )
    assert a["source"]["version"] is a["retrieved_at"] is None
    assert "location" not in v and "protein_ref" not in v and "evidence_class" not in v
    trace = e["acquisition_trace"]["records"][0]
    assert trace["count"] == 1 and trace["network_attempts"] == 0
    assert trace["access"] == "supplied_file" and trace["outcome"] == "received"
    assert any(
        b["id"] == "url:https://metalpdb.cerm.unifi.it/" for b in trace["bibliography"]
    )
    assert source_terms()["MetalPDB"]["licence"] == "NOT-STATED"
    a["asserted_value"]["metals"].clear()
    a["source_metadata"]["native_site"].clear()
    assert e == before


def test_duplicate_sites_metals_donors_and_conflicting_geometry_keep_occurrences():
    rows = native() * 2
    rows[1] = copy.deepcopy(rows[1])
    rows[1]["metals"][0]["geometry"] = "tetrahedron (regular)"
    rows[1]["metals"].append(copy.deepcopy(rows[1]["metals"][0]))
    donor_list = rows[1]["metals"][0]["ligands"][0]["donors"]
    donor_list.append(copy.deepcopy(donor_list[0]))
    a = map_sites(read(rows))
    assert len(a) == 2 and a[0]["id"] != a[1]["id"]
    assert [s["source_metadata"]["native_occurrence"] for s in a] == [1, 2]
    assert len(a[1]["asserted_value"]["metals"]) == 2
    assert len(a[1]["asserted_value"]["metals"][0]["ligands"][0]["donors"]) == 2
    assert (
        a[0]["asserted_value"]["metals"][0]["geometry"]
        != a[1]["asserted_value"]["metals"][0]["geometry"]
    )


def test_zero_distance_unknown_labels_negative_residue_numbers_and_native_chain_case():
    rows = native()
    row = rows[0]
    row.update(uniprot=None, cath=None, future_field={"kept": 7})
    metal = row["metals"][0]
    metal.update(geometry=None, pattern=None, coordination=0, residue_pdb_number=-2)
    ligand = metal["ligands"][0]
    ligand.update(chain="a", residue_pdb_number=0)
    ligand["donors"][0].update(distance=0, extra_field="original")
    a = map_sites(read(rows))[0]
    v = a["asserted_value"]
    assert v["uniprot"] is None and v["cath"] is None
    assert v["metals"][0]["coordination"] == 0 and v["metals"][0]["geometry"] is None
    ligand = v["metals"][0]["ligands"][0]
    assert ligand["chain"] == "a" and ligand["residue_pdb_number"] == 0
    assert ligand["donors"][0]["distance"] == {"value": 0, "unit": "angstrom"}
    assert a["source_metadata"]["native_site"] == row
    assert "future_field" not in v and "extra_field" not in ligand["donors"][0]


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r[0].update(site="12ca_1"),
        lambda r: r[0].update(pdb="1hti"),
        lambda r: r[0].update(site_type=1),
        lambda r: r[0].update(is_representative=0),
        lambda r: r[0].update(ec_number=["4.2.1.1"]),
        lambda r: r[0].pop("uniprot"),
        lambda r: r[0].update(metals=[]),
        lambda r: r[0].update(metals={}),
        lambda r: r[0]["metals"][0].update(coordination=True),
        lambda r: r[0]["metals"][0].update(atom_pdb_number=0),
        lambda r: r[0]["metals"][0].update(residue_pdb_number="262A"),
        lambda r: r[0]["metals"][0].update(geometry={}),
        lambda r: r[0]["metals"][0].update(ligands=None),
        lambda r: r[0]["metals"][0]["ligands"][0].update(chain=None),
        lambda r: r[0]["metals"][0]["ligands"][0].update(donors=[]),
        lambda r: r[0]["metals"][0]["ligands"][0]["donors"][0].update(distance=-1),
        lambda r: r[0]["metals"][0]["ligands"][0]["donors"][0].update(distance=True),
        lambda r: r[0]["metals"][0]["ligands"][0]["donors"][0].update(distance="2.497"),
        lambda r: r[0]["metals"][0]["ligands"][0]["donors"][0].update(distance=None),
        lambda r: r[0]["metals"][0]["ligands"][0]["donors"][0].update(
            distance_unit="nm"
        ),
        lambda r: r[0].update(future=float("nan")),
        lambda r: r.append({"site": "12ca_2", "pdb": "12ca"}),
    ],
)
def test_all_received_rows_validate_before_mapping_identity_units_and_late_errors(
    change,
):
    rows = native()
    change(rows)
    with pytest.raises(ConnectorError):
        read(rows)


@pytest.mark.parametrize(
    "payload", [{}, {"error": "unavailable"}, None, "<html>failure</html>"]
)
def test_error_or_foreign_bodies_are_not_empty_site_arrays(payload):
    with pytest.raises(ConnectorError):
        read(payload)


def test_explicit_empty_received_array_has_no_assertions_or_biological_absence():
    e = read([])
    assert e["record"] == [] and map_sites(e) == []
    assert e["truncated"] is False


@pytest.mark.parametrize(
    "identifier",
    [
        "P00918",
        "12ca",
        "12ca_0",
        "../12ca_2",
        "12ca_2,metal:Zn",
        "12ca_2?x",
        "12ca_a",
        None,
        True,
        12,
    ],
)
def test_unsafe_or_non_site_queries_never_reach_client_even_without_digestion(
    identifier,
):
    class Forbidden:
        def site(self, identifier):
            pytest.fail("Invalid site reached MetalPDB.")

    for skip in (False, True):
        with pytest.raises((ArgumentError, ConnectorError)):
            get_site(identifier, client=Forbidden(), skip_digestion=skip)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "PDB"),
        ("kind", "pdb"),
        ("query", {"site_id": "12ca_1"}),
        ("version", "2026-10"),
        ("truncated", True),
    ],
)
def test_foreign_context_or_cut_is_refused_before_source_assertions(key, value):
    with pytest.raises(ConnectorError):
        read(native(), **{key: value})
    e = read(native())
    e[key] = value
    with pytest.raises(ConnectorError):
        map_sites(e)


@pytest.mark.parametrize("compressed", [False, True])
def test_supplied_json_binds_site_raw_digest_and_original_time_without_network(
    tmp_path, compressed
):
    raw = PATH.read_bytes()
    p = tmp_path / ("site.json.gz" if compressed else "site.json")
    data = gzip.compress(raw) if compressed else raw
    p.write_bytes(data)
    m = metadata()
    m["retrieved_at"] = "2026-10-07T08:00:00+00:00"
    checksum = hashlib.sha256(data).hexdigest()
    e = get_site(
        "12ca_2",
        client=SnapshotMetalPDBClient(p, source_metadata=m, expected_sha256=checksum),
    )
    assert e["record"] == native() and e["retrieved_at"] == m["retrieved_at"]
    assert e["snapshot_receipt"]["document_sha256"] == checksum
    assert e["snapshot_receipt"]["source_access_observed"] is False
    assert e["acquisition_trace"]["records"][0]["network_attempts"] == 0
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_site(
            "12ca_2",
            client=SnapshotMetalPDBClient(
                p, source_metadata=m, expected_sha256="0" * 64
            ),
        )
    m["query"] = {"site_id": "12ca_1"}
    with pytest.raises(ConnectorError):
        get_site("12ca_2", client=SnapshotMetalPDBClient(p, source_metadata=m))


def test_missing_fixture_is_unavailable_not_an_empty_query(tmp_path):
    with pytest.raises(ConnectorError) as error:
        get_site("12ca_2", client=FixtureMetalPDBClient(tmp_path))
    assert error.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


@pytest.mark.parametrize("status", [404, 429, 500])
def test_http_failures_do_not_assert_absence(status, monkeypatch):
    import sabueso.tools.db._http as http

    monkeypatch.setattr(http, "RETRIES", 0)

    def fail(request, timeout):
        raise HTTPError(request.full_url, status, "failure", {}, None)

    monkeypatch.setattr(http, "_urlopen", fail)
    with pytest.raises(ConnectorError) as error:
        get_site("12ca_2")
    trace = error.value.acquisition_trace["records"][0]
    assert trace["outcome"] == "failed" and trace["network_attempts"] == 1


def test_one_api_get_preserves_raw_record_hash_time_and_replays_quantities(
    tmp_path, monkeypatch
):
    import sabueso.tools.db._http as http

    calls = []

    class Response(io.BytesIO):
        status = 200

        def __init__(self):
            super().__init__(PATH.read_bytes())
            self.headers = Message()
            self.headers["Content-Type"] = "application/json"

    def wire(request, timeout):
        calls.append((request.get_method(), request.full_url))
        return Response()

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "metalpdb.db")
    with archive.recording():
        first = get_site("12CA_2")

    def forbidden(*args, **kwargs):
        pytest.fail("Replay reached the network.")

    monkeypatch.setattr(http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_site("12ca_2")
    assert calls == [("GET", URL + "12ca_2")]
    assert first["record"] == second["record"] == native()
    assert first["download_sha256"] == hashlib.sha256(PATH.read_bytes()).hexdigest()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert map_sites(first) == map_sites(second)
    replay = second["acquisition_trace"]["records"][0]
    assert replay["access"] == "replay" and replay["network_attempts"] == 0
